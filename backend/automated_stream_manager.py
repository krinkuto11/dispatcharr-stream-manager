#!/usr/bin/env python3
"""
Automated Stream Manager for Dispatcharr

This module handles the automated process of:
1. Updating M3U playlists
2. Discovering new streams and assigning them to channels via regex
3. Maintaining changelog of updates
"""

import json
import logging
import os
import re
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from api_utils import (
    refresh_m3u_playlists,
    get_m3u_accounts,
    get_streams,
    fetch_data_from_url,
    add_streams_to_channel,
    _get_base_url
)



# Custom logging filter to exclude HTTP-related logs
class HTTPLogFilter(logging.Filter):
    """Filter out HTTP-related log messages."""
    def filter(self, record):
        message = record.getMessage().lower()
        http_indicators = [
            'http request',
            'http response',
            'status code',
            'get /',
            'post /',
            'put /',
            'delete /',
            'patch /',
            '" with',
            '- - [',
            'werkzeug',
        ]
        return not any(indicator in message for indicator in http_indicators)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
for handler in logging.root.handlers:
    handler.addFilter(HTTPLogFilter())

# Configuration directory - persisted via Docker volume
CONFIG_DIR = Path(os.environ.get('CONFIG_DIR', '/app/data'))

class ChangelogManager:
    """Manages changelog entries for stream updates."""
    
    def __init__(self, changelog_file=None):
        if changelog_file is None:
            changelog_file = CONFIG_DIR / "changelog.json"
        self.changelog_file = Path(changelog_file)
        self.changelog = self._load_changelog()
    
    def _load_changelog(self) -> List[Dict]:
        """Load existing changelog or create empty one."""
        if self.changelog_file.exists():
            try:
                with open(self.changelog_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logging.warning(f"Could not load {self.changelog_file}, creating new changelog")
        return []
    
    def add_entry(self, action: str, details: Dict, timestamp: Optional[str] = None):
        """Add a new changelog entry."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        entry = {
            "timestamp": timestamp,
            "action": action,
            "details": details
        }
        
        self.changelog.append(entry)
        self._save_changelog()
        logging.info(f"Changelog entry added: {action}")
    
    def _save_changelog(self):
        """Save changelog to file."""
        # Ensure parent directory exists
        self.changelog_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.changelog_file, 'w') as f:
            json.dump(self.changelog, f, indent=2)
    
    def get_recent_entries(self, days: int = 7) -> List[Dict]:
        """Get changelog entries from the last N days, filtered and sorted."""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        
        for entry in self.changelog:
            try:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time >= cutoff:
                    # Filter out entries without meaningful channel updates
                    if self._has_channel_updates(entry):
                        recent.append(entry)
            except (ValueError, KeyError):
                continue
        
        # Sort by timestamp in reverse chronological order (newest first)
        recent.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return recent
    
    def _has_channel_updates(self, entry: Dict) -> bool:
        """Check if a changelog entry contains meaningful channel/stream updates."""
        details = entry.get('details', {})
        action = entry.get('action', '')
        
        # For playlist_refresh, only include if there were actual changes
        if action == 'playlist_refresh':
            added = details.get('added_streams', [])
            removed = details.get('removed_streams', [])
            return len(added) > 0 or len(removed) > 0
        
        # For streams_assigned, only include if streams were actually assigned
        if action == 'streams_assigned':
            total_assigned = details.get('total_assigned', 0)
            return total_assigned > 0
        
        # For other actions, include if success is True or not specified
        # (exclude failed operations without updates)
        if 'success' in details:
            return details['success'] is True
        
        return True  # Include entries without explicit success flag


class RegexChannelMatcher:
    """Handles regex-based channel matching for stream assignment."""
    
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = CONFIG_DIR / "channel_regex_config.json"
        self.config_file = Path(config_file)
        self.channel_patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Load regex patterns for channel matching."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logging.warning(f"Could not load {self.config_file}, creating default config")
        
        # Create default configuration
        default_config = {
            "patterns": {
                # Example patterns - these should be configured by the user
                # "1": {"name": "CNN", "regex": [".*CNN.*", ".*Cable News.*"], "enabled": True},
                # "2": {"name": "ESPN", "regex": [".*ESPN.*", ".*Sports.*"], "enabled": True}
            },
            "global_settings": {
                "case_sensitive": False,
                "require_exact_match": False
            }
        }
        
        self._save_patterns(default_config)
        return default_config
    
    def _save_patterns(self, patterns: Dict):
        """Save patterns to file."""
        # Ensure parent directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(patterns, f, indent=2)
    
    def add_channel_pattern(self, channel_id: str, name: str, regex_patterns: List[str], enabled: bool = True):
        """Add or update a channel pattern."""
        self.channel_patterns["patterns"][str(channel_id)] = {
            "name": name,
            "regex": regex_patterns,
            "enabled": enabled
        }
        self._save_patterns(self.channel_patterns)
        logging.info(f"Added/updated pattern for channel {channel_id}: {name}")
    
    def match_stream_to_channels(self, stream_name: str) -> List[str]:
        """Match a stream name to channel IDs based on regex patterns."""
        matches = []
        case_sensitive = self.channel_patterns.get("global_settings", {}).get("case_sensitive", False)
        
        search_name = stream_name if case_sensitive else stream_name.lower()
        
        for channel_id, config in self.channel_patterns.get("patterns", {}).items():
            if not config.get("enabled", True):
                continue
            
            for pattern in config.get("regex", []):
                search_pattern = pattern if case_sensitive else pattern.lower()
                
                # Convert literal spaces in pattern to flexible whitespace regex (\s+)
                # This allows matching streams with different whitespace characters
                # (non-breaking spaces, tabs, double spaces, etc.)
                search_pattern = re.sub(r' +', r'\\s+', search_pattern)
                
                try:
                    if re.search(search_pattern, search_name):
                        matches.append(channel_id)
                        logging.debug(f"Stream '{stream_name}' matched channel {channel_id} with pattern '{pattern}'")
                        break  # Only match once per channel
                except re.error as e:
                    logging.error(f"Invalid regex pattern '{pattern}' for channel {channel_id}: {e}")
        
        return matches
    
    def get_patterns(self) -> Dict:
        """Get current patterns configuration."""
        return self.channel_patterns


class AutomatedStreamManager:
    """Main automated stream management system."""
    
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = CONFIG_DIR / "automation_config.json"
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.changelog = ChangelogManager()
        self.regex_matcher = RegexChannelMatcher()
        
        self.running = False
        self.last_playlist_update = None
    
    def _load_config(self) -> Dict:
        """Load automation configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                logging.warning(f"Could not load {self.config_file}, creating default config")
        
        # Default configuration
        default_config = {
            "playlist_update_interval_minutes": 5,
            "enabled_m3u_accounts": [],  # Empty list means all accounts enabled
            "enabled_features": {
                "auto_playlist_update": True,
                "auto_stream_discovery": True,
                "changelog_tracking": True
            }
        }
        
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict):
        """Save configuration to file."""
        # Ensure parent directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update_config(self, updates: Dict):
        """Update configuration with new values."""
        self.config.update(updates)
        self._save_config(self.config)
        logging.info("Configuration updated")
    
    def refresh_playlists(self) -> bool:
        """Refresh M3U playlists and track changes."""
        try:
            if not self.config.get("enabled_features", {}).get("auto_playlist_update", True):
                logging.info("Playlist update is disabled in configuration")
                return False
            
            logging.info("Starting M3U playlist refresh...")
            
            # Get streams before refresh
            from api_utils import get_streams
            streams_before = get_streams(log_result=False) if self.config.get("enabled_features", {}).get("changelog_tracking", True) else []
            before_stream_ids = {s.get('id'): s.get('name', '') for s in streams_before if isinstance(s, dict) and s.get('id')}
            
            # Get all M3U accounts and filter out "custom" account
            all_accounts = get_m3u_accounts()
            if all_accounts:
                # Filter out "custom" account (it doesn't need refresh as it's for locally added streams)
                non_custom_accounts = [
                    acc for acc in all_accounts
                    if not (acc.get('name', '').lower() == 'custom' or 
                           (acc.get('server_url') is None and acc.get('file_path') is None))
                ]
                
                # Perform refresh - check if we need to filter by enabled accounts
                enabled_accounts = self.config.get("enabled_m3u_accounts", [])
                if enabled_accounts:
                    # Refresh only enabled accounts (and exclude custom)
                    non_custom_ids = [acc.get('id') for acc in non_custom_accounts if acc.get('id') is not None]
                    accounts_to_refresh = [acc_id for acc_id in enabled_accounts if acc_id in non_custom_ids]
                    for account_id in accounts_to_refresh:
                        logging.info(f"Refreshing M3U account {account_id}")
                        refresh_m3u_playlists(account_id=account_id)
                    if len(enabled_accounts) != len(accounts_to_refresh):
                        logging.info(f"Skipped {len(enabled_accounts) - len(accounts_to_refresh)} account(s) (custom or invalid)")
                else:
                    # Refresh all non-custom accounts
                    for account in non_custom_accounts:
                        account_id = account.get('id')
                        if account_id is not None:
                            logging.info(f"Refreshing M3U account {account_id}")
                            refresh_m3u_playlists(account_id=account_id)
                    if len(all_accounts) != len(non_custom_accounts):
                        logging.info(f"Skipped {len(all_accounts) - len(non_custom_accounts)} 'custom' account(s)")
            else:
                # Fallback: if we can't get accounts, refresh all (legacy behavior)
                logging.warning("Could not fetch M3U accounts, refreshing all as fallback")
                refresh_m3u_playlists()
            
            # Get streams after refresh - log this one since it shows the final result
            streams_after = get_streams(log_result=True) if self.config.get("enabled_features", {}).get("changelog_tracking", True) else []
            after_stream_ids = {s.get('id'): s.get('name', '') for s in streams_after if isinstance(s, dict) and s.get('id')}
            
            self.last_playlist_update = datetime.now()
            
            # Calculate differences
            added_stream_ids = set(after_stream_ids.keys()) - set(before_stream_ids.keys())
            removed_stream_ids = set(before_stream_ids.keys()) - set(after_stream_ids.keys())
            
            added_streams = [{"id": sid, "name": after_stream_ids[sid]} for sid in added_stream_ids]
            removed_streams = [{"id": sid, "name": before_stream_ids[sid]} for sid in removed_stream_ids]
            
            
            if self.config.get("enabled_features", {}).get("changelog_tracking", True):
                self.changelog.add_entry("playlist_refresh", {
                    "success": True,
                    "timestamp": self.last_playlist_update.isoformat(),
                    "total_streams": len(after_stream_ids),
                    "added_streams": added_streams[:50],  # Limit to first 50 for changelog size
                    "removed_streams": removed_streams[:50],  # Limit to first 50 for changelog size
                    "added_count": len(added_streams),
                    "removed_count": len(removed_streams)
                })
            
            logging.info(f"M3U playlist refresh completed successfully. Added: {len(added_streams)}, Removed: {len(removed_streams)}")
            
            # Mark channels for stream quality checking ONLY if streams were added or removed
            # This prevents unnecessary marking of all channels on every refresh
            if len(added_streams) > 0 or len(removed_streams) > 0:
                try:
                    # Get all channels that may have been affected
                    from api_utils import fetch_data_from_url, _get_base_url
                    base_url = _get_base_url()
                    channels_data = fetch_data_from_url(f"{base_url}/api/channels/channels/")
                    
                    if channels_data:
                        if isinstance(channels_data, dict) and 'results' in channels_data:
                            channels = channels_data['results']
                        else:
                            channels = channels_data
                        
                        # Mark all channels for checking with stream counts for 2-hour immunity
                        channel_ids = []
                        stream_counts = {}
                        for ch in channels:
                            if isinstance(ch, dict) and 'id' in ch:
                                ch_id = ch['id']
                                channel_ids.append(ch_id)
                                # Get stream count if available
                                if 'streams' in ch and isinstance(ch['streams'], list):
                                    stream_counts[ch_id] = len(ch['streams'])
                        
                        # Try to get stream checker service and mark channels
                        try:
                            from stream_checker_service import get_stream_checker_service
                            stream_checker = get_stream_checker_service()
                            stream_checker.update_tracker.mark_channels_updated(channel_ids, stream_counts=stream_counts)
                            logging.info(f"Marked {len(channel_ids)} channels for stream quality checking")
                            # Trigger immediate check instead of waiting for scheduled interval
                            stream_checker.trigger_check_updated_channels()
                        except Exception as sc_error:
                            logging.debug(f"Stream checker not available or error marking channels: {sc_error}")
                except Exception as ch_error:
                    logging.debug(f"Could not mark channels for stream checking: {ch_error}")
            else:
                logging.info("No stream changes detected, skipping channel marking")
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to refresh M3U playlists: {e}")
            
            
            if self.config.get("enabled_features", {}).get("changelog_tracking", True):
                self.changelog.add_entry("playlist_refresh", {
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
            return False
    
    def discover_and_assign_streams(self) -> Dict[str, int]:
        """Discover new streams and assign them to channels based on regex patterns."""
        if not self.config.get("enabled_features", {}).get("auto_stream_discovery", True):
            logging.info("Stream discovery is disabled in configuration")
            return {}
        
        try:
            logging.info("Starting stream discovery and assignment...")
            
            # Get all available streams (don't log, we already logged during refresh)
            all_streams = get_streams(log_result=False)
            if not all_streams:
                logging.warning("No streams found")
                return {}
            
            # Validate that all_streams is a list
            if not isinstance(all_streams, list):
                logging.error(f"Invalid streams response format: expected list, got {type(all_streams).__name__}")
                return {}
            
            # Get all channels
            base_url = _get_base_url()
            all_channels = fetch_data_from_url(f"{base_url}/api/channels/channels/")
            if not all_channels:
                logging.warning("No channels found")
                return {}
            
            # Validate that all_channels is a list
            if not isinstance(all_channels, list):
                logging.error(f"Invalid channels response format: expected list, got {type(all_channels).__name__}")
                return {}
            
            # Create a map of existing channel streams
            channel_streams = {}
            channel_names = {}  # Store channel names for changelog
            for channel in all_channels:
                # Validate that channel is a dictionary
                if not isinstance(channel, dict) or 'id' not in channel:
                    logging.warning(f"Invalid channel format encountered: {type(channel).__name__} - {channel}")
                    continue
                    
                channel_id = str(channel['id'])
                channel_names[channel_id] = channel.get('name', f'Channel {channel_id}')
                streams = fetch_data_from_url(f"{base_url}/api/channels/channels/{channel_id}/streams/")
                if streams:
                    # Validate that streams is a list and contains dictionaries
                    if isinstance(streams, list):
                        valid_stream_ids = set()
                        for s in streams:
                            if isinstance(s, dict) and 'id' in s:
                                valid_stream_ids.add(s['id'])
                            else:
                                logging.warning(f"Invalid stream format in channel {channel_id}: {type(s).__name__} - {s}")
                        channel_streams[channel_id] = valid_stream_ids
                    else:
                        logging.warning(f"Invalid streams format for channel {channel_id}: expected list, got {type(streams).__name__}")
                        channel_streams[channel_id] = set()
                else:
                    channel_streams[channel_id] = set()
            
            assignments = defaultdict(list)
            assignment_details = defaultdict(list)  # Track stream details for changelog
            assignment_count = {}
            
            # Process each stream
            for stream in all_streams:
                # Validate that stream is a dictionary before accessing attributes
                if not isinstance(stream, dict):
                    logging.warning(f"Invalid stream format encountered: {type(stream).__name__} - {stream}")
                    continue
                    
                stream_name = stream.get('name', '')
                stream_id = stream.get('id')
                
                if not stream_name or not stream_id:
                    continue
                
                # Find matching channels
                matching_channels = self.regex_matcher.match_stream_to_channels(stream_name)
                
                for channel_id in matching_channels:
                    # Check if stream is already in this channel
                    if channel_id in channel_streams and stream_id not in channel_streams[channel_id]:
                        assignments[channel_id].append(stream_id)
                        assignment_details[channel_id].append({
                            "stream_id": stream_id,
                            "stream_name": stream_name
                        })
            
            # Prepare detailed changelog data
            detailed_assignments = []
            
            # Assign streams to channels
            for channel_id, stream_ids in assignments.items():
                if stream_ids:
                    try:
                        added_count = add_streams_to_channel(int(channel_id), stream_ids)
                        assignment_count[channel_id] = added_count
                        
                        # Verify streams were added correctly
                        if added_count > 0:
                            try:
                                time.sleep(0.5)  # Brief delay for API processing
                                base_url = _get_base_url()
                                updated_streams = fetch_data_from_url(f"{base_url}/api/channels/channels/{channel_id}/streams/")
                                
                                if updated_streams and isinstance(updated_streams, list):
                                    updated_stream_ids = set(s.get('id') for s in updated_streams if isinstance(s, dict) and 'id' in s)
                                    expected_stream_ids = set(stream_ids)
                                    added_stream_ids = expected_stream_ids & updated_stream_ids
                                    
                                    if len(added_stream_ids) == added_count:
                                        logging.info(f"✓ Verified: {added_count} streams successfully added to channel {channel_id} ({channel_names.get(channel_id, f'Channel {channel_id}')})")
                                    else:
                                        logging.warning(f"⚠ Verification mismatch for channel {channel_id}: expected {added_count} streams, found {len(added_stream_ids)} in channel")
                                else:
                                    logging.warning(f"⚠ Could not verify stream addition for channel {channel_id}: invalid response")
                            except Exception as verify_error:
                                logging.warning(f"⚠ Could not verify stream addition for channel {channel_id}: {verify_error}")
                        
                        # Prepare detailed assignment info
                        channel_assignment = {
                            "channel_id": channel_id,
                            "channel_name": channel_names.get(channel_id, f'Channel {channel_id}'),
                            "stream_count": added_count,
                            "streams": assignment_details[channel_id][:20]  # Limit to first 20 for changelog
                        }
                        detailed_assignments.append(channel_assignment)
                        
                        
                    except Exception as e:
                        logging.error(f"Failed to assign streams to channel {channel_id}: {e}")
            
            # Add comprehensive changelog entry
            total_assigned = sum(assignment_count.values())
            if self.config.get("enabled_features", {}).get("changelog_tracking", True):
                self.changelog.add_entry("streams_assigned", {
                    "total_assigned": total_assigned,
                    "channel_count": len(assignment_count),
                    "assignments": detailed_assignments,
                    "timestamp": datetime.now().isoformat()
                })
            
            logging.info(f"Stream discovery completed. Assigned {total_assigned} new streams across {len(assignment_count)} channels")
            
            # Mark channels that received new streams for stream quality checking
            if total_assigned > 0 and assignment_count:
                try:
                    # Get updated stream counts for channels that received new streams
                    channel_ids_to_mark = []
                    stream_counts = {}
                    
                    for channel_id in assignment_count.keys():
                        if assignment_count[channel_id] > 0:
                            channel_ids_to_mark.append(int(channel_id))
                            # Fetch current stream count for this channel
                            try:
                                ch_streams = fetch_data_from_url(f"{base_url}/api/channels/channels/{channel_id}/streams/")
                                if ch_streams and isinstance(ch_streams, list):
                                    stream_counts[int(channel_id)] = len(ch_streams)
                            except Exception:
                                pass  # If we can't get count, marking will still work
                    
                    # Try to get stream checker service and mark channels
                    if channel_ids_to_mark:
                        try:
                            from stream_checker_service import get_stream_checker_service
                            stream_checker = get_stream_checker_service()
                            stream_checker.update_tracker.mark_channels_updated(channel_ids_to_mark, stream_counts=stream_counts)
                            logging.info(f"Marked {len(channel_ids_to_mark)} channels with new streams for stream quality checking")
                            # Trigger immediate check instead of waiting for scheduled interval
                            stream_checker.trigger_check_updated_channels()
                        except Exception as sc_error:
                            logging.debug(f"Stream checker not available or error marking channels: {sc_error}")
                except Exception as mark_error:
                    logging.debug(f"Could not mark channels for stream checking after discovery: {mark_error}")
            
            return assignment_count
            
        except Exception as e:
            logging.error(f"Stream discovery failed: {e}")
            if self.config.get("enabled_features", {}).get("changelog_tracking", True):
                self.changelog.add_entry("stream_discovery", {
                    "success": False,
                    "error": str(e)
                })
            return {}
    
    def should_run_playlist_update(self) -> bool:
        """Check if it's time to run playlist update."""
        if not self.last_playlist_update:
            return True
        
        interval = timedelta(minutes=self.config.get("playlist_update_interval_minutes", 5))
        return datetime.now() - self.last_playlist_update >= interval
    
    def run_automation_cycle(self):
        """Run one complete automation cycle."""
        # Only log and run if it's actually time to update
        if not self.should_run_playlist_update():
            return  # Skip silently until it's time
        
        logging.info("Starting automation cycle...")
        
        # 1. Update playlists
        success = self.refresh_playlists()
        if success:
            # Small delay to allow playlist processing
            time.sleep(10)
            
            # 2. Discover and assign new streams
            assignments = self.discover_and_assign_streams()
        
        logging.info("Automation cycle completed")
    def start_automation(self):
        """Start the automated stream management process."""
        if self.running:
            logging.warning("Automation is already running")
            return
        
        self.running = True
        logging.info("Starting automated stream management...")
        
        def automation_loop():
            while self.running:
                try:
                    self.run_automation_cycle()
                    
                    # Sleep for a minute before checking again
                    time.sleep(60)
                    
                except Exception as e:
                    logging.error(f"Error in automation loop: {e}")
                    time.sleep(60)  # Continue after error
        
        self.automation_thread = threading.Thread(target=automation_loop, daemon=True)
        self.automation_thread.start()
    
    def stop_automation(self):
        """Stop the automated stream management process."""
        if not self.running:
            logging.warning("Automation is not running")
            return
        
        self.running = False
        logging.info("Stopping automated stream management...")
        
        if hasattr(self, 'automation_thread'):
            self.automation_thread.join(timeout=5)
        
        logging.info("Automated stream management stopped")
    
    def get_status(self) -> Dict:
        """Get current status of the automation system."""
        return {
            "running": self.running,
            "last_playlist_update": self.last_playlist_update.isoformat() if self.last_playlist_update else None,
            "next_playlist_update": (
                self.last_playlist_update + timedelta(minutes=self.config.get("playlist_update_interval_minutes", 5))
            ).isoformat() if self.last_playlist_update else "immediate",
            "config": self.config,
            "recent_changelog": self.changelog.get_recent_entries(7)
        }