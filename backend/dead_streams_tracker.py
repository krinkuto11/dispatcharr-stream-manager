#!/usr/bin/env python3
"""
Dead Streams Tracker for StreamFlow.

This module tracks dead streams in a JSON file using stream URLs as unique keys.
Stream URLs are used instead of names because multiple streams can have the same name.
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict

# Configuration directory
CONFIG_DIR = Path(os.environ.get('CONFIG_DIR', '/app/data'))


class DeadStreamsTracker:
    """Tracks dead streams in a JSON file using stream URLs as keys."""
    
    def __init__(self, tracker_file=None):
        """Initialize the dead streams tracker.
        
        Args:
            tracker_file: Path to the JSON file for tracking dead streams.
                         Defaults to CONFIG_DIR/dead_streams.json
        """
        if tracker_file is None:
            tracker_file = CONFIG_DIR / 'dead_streams.json'
        self.tracker_file = Path(tracker_file)
        self.lock = threading.Lock()
        self.dead_streams = self._load_dead_streams()
    
    def _load_dead_streams(self) -> Dict[str, Dict]:
        """Load dead streams data from JSON file.
        
        Returns:
            Dict mapping stream URLs to stream metadata
        """
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logging.warning(f"Could not load dead streams from {self.tracker_file}: {e}")
        return {}
    
    def _save_dead_streams(self):
        """Save dead streams data to JSON file.
        
        Note: This method assumes the lock is already held by the caller.
        """
        try:
            self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracker_file, 'w') as f:
                json.dump(self.dead_streams, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save dead streams: {e}")
    
    def mark_as_dead(self, stream_url: str, stream_id: int, stream_name: str) -> bool:
        """Mark a stream as dead.
        
        Args:
            stream_url: The URL of the stream (used as unique key)
            stream_id: The stream ID in Dispatcharr
            stream_name: The name of the stream
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                self.dead_streams[stream_url] = {
                    'stream_id': stream_id,
                    'stream_name': stream_name,
                    'marked_dead_at': datetime.now().isoformat(),
                    'url': stream_url
                }
                self._save_dead_streams()
            logging.warning(f"🔴 MARKED STREAM AS DEAD: {stream_name} (URL: {stream_url})")
            return True
        except Exception as e:
            logging.error(f"❌ Error marking stream as dead: {e}")
            return False
    
    def mark_as_alive(self, stream_url: str) -> bool:
        """Mark a stream as alive (remove from dead streams).
        
        Args:
            stream_url: The URL of the stream
            
        Returns:
            bool: True if successful
        """
        try:
            with self.lock:
                if stream_url in self.dead_streams:
                    stream_info = self.dead_streams.pop(stream_url)
                    self._save_dead_streams()
                    logging.info(f"🟢 REVIVED STREAM: {stream_info.get('stream_name', 'Unknown')} (URL: {stream_url})")
                    return True
                else:
                    logging.debug(f"Stream not in dead list: {stream_url}")
                    return True
        except Exception as e:
            logging.error(f"❌ Error marking stream as alive: {e}")
            return False
    
    def is_dead(self, stream_url: str) -> bool:
        """Check if a stream is marked as dead.
        
        Args:
            stream_url: The URL of the stream
            
        Returns:
            bool: True if stream is dead
        """
        with self.lock:
            return stream_url in self.dead_streams
    
    def get_dead_streams(self) -> Dict[str, Dict]:
        """Get all dead streams.
        
        Returns:
            Dict mapping stream URLs to stream metadata
        """
        with self.lock:
            return self.dead_streams.copy()
    
    def cleanup_removed_streams(self, current_stream_urls: set) -> int:
        """Remove dead streams that are no longer in the playlist.
        
        Args:
            current_stream_urls: Set of URLs for streams currently in the playlist
            
        Returns:
            int: Number of dead streams removed from tracking
        """
        removed_count = 0
        try:
            with self.lock:
                # Find dead streams that are no longer in the current playlist
                dead_urls_to_remove = []
                for dead_url in self.dead_streams.keys():
                    if dead_url not in current_stream_urls:
                        dead_urls_to_remove.append(dead_url)
                
                # Remove them from tracking
                for url in dead_urls_to_remove:
                    stream_info = self.dead_streams.pop(url)
                    removed_count += 1
                    logging.info(f"🗑️ Removed dead stream from tracking (no longer in playlist): {stream_info.get('stream_name', 'Unknown')} (URL: {url})")
                
                # Save if we removed any
                if removed_count > 0:
                    self._save_dead_streams()
                    logging.info(f"Cleaned up {removed_count} dead stream(s) that are no longer in playlist")
            
            return removed_count
        except Exception as e:
            logging.error(f"❌ Error cleaning up removed streams: {e}")
            return 0
