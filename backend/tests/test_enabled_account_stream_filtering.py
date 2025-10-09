#!/usr/bin/env python3
"""
Test that discover_and_assign_streams respects enabled_m3u_accounts configuration.
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automated_stream_manager import AutomatedStreamManager


class TestEnabledAccountStreamFiltering(unittest.TestCase):
    """Test that streams from disabled M3U accounts are not matched with channels."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('automated_stream_manager.add_streams_to_channel')
    @patch('automated_stream_manager.fetch_data_from_url')
    @patch('automated_stream_manager.get_streams')
    def test_only_enabled_account_streams_matched(self, mock_get_streams, mock_fetch, mock_add_streams):
        """Test that only streams from enabled accounts are matched with channels."""
        # Setup: Account 1 is enabled, Account 2 is not
        # We have streams from both accounts
        mock_get_streams.return_value = [
            {'id': 101, 'name': 'UK: BBC One HD', 'm3u_account_id': 1, 'is_custom': False},
            {'id': 102, 'name': 'UK: BBC Two HD', 'm3u_account_id': 1, 'is_custom': False},
            {'id': 201, 'name': 'UK: ITV HD', 'm3u_account_id': 2, 'is_custom': False},
            {'id': 202, 'name': 'UK: Channel 4 HD', 'm3u_account_id': 2, 'is_custom': False},
        ]
        
        # Mock channels
        def fetch_side_effect(url):
            if url == 'http://test/api/channels/channels/':
                return [{'id': 1, 'name': 'UK Channels'}]
            elif url == 'http://test/api/channels/channels/1/streams/':
                return []
            return []
        
        mock_fetch.side_effect = fetch_side_effect
        
        mock_add_streams.return_value = 2
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager._get_base_url', return_value='http://test'):
                manager = AutomatedStreamManager()
                
                # Configure regex to match all UK streams
                patterns = {
                    'patterns': {
                        '1': {
                            'name': 'UK Channels',
                            'regex': [r'UK:'],
                            'enabled': True
                        }
                    },
                    'global_settings': {
                        'case_sensitive': False
                    }
                }
                manager.regex_matcher.channel_patterns = patterns
                # Save to file so reload_patterns() works
                manager.regex_matcher._save_patterns(patterns)
                
                # Enable only account 1
                manager.config['enabled_m3u_accounts'] = [1]
                manager.config['enabled_features']['changelog_tracking'] = False
                
                # Run stream discovery
                result = manager.discover_and_assign_streams()
                
                # Verify only streams from account 1 were added
                self.assertTrue(mock_add_streams.called)
                call_args = mock_add_streams.call_args[0]
                channel_id = call_args[0]
                stream_ids = call_args[1]
                
                # Should only include streams 101 and 102 (from account 1)
                self.assertEqual(channel_id, 1)
                self.assertEqual(set(stream_ids), {101, 102})
                # Should NOT include streams 201 and 202 (from account 2)
                self.assertNotIn(201, stream_ids)
                self.assertNotIn(202, stream_ids)
    
    @patch('automated_stream_manager.add_streams_to_channel')
    @patch('automated_stream_manager.fetch_data_from_url')
    @patch('automated_stream_manager.get_streams')
    def test_custom_streams_always_included(self, mock_get_streams, mock_fetch, mock_add_streams):
        """Test that custom streams are always matched regardless of enabled_m3u_accounts."""
        mock_get_streams.return_value = [
            {'id': 101, 'name': 'UK: BBC One HD', 'm3u_account_id': 1, 'is_custom': False},
            {'id': 301, 'name': 'UK: My Custom Stream', 'is_custom': True},  # Custom stream
        ]
        
        # Mock channels
        def fetch_side_effect(url):
            if url == 'http://test/api/channels/channels/':
                return [{'id': 1, 'name': 'UK Channels'}]
            elif url == 'http://test/api/channels/channels/1/streams/':
                return []
            return []
        
        mock_fetch.side_effect = fetch_side_effect
        
        mock_add_streams.return_value = 2
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager._get_base_url', return_value='http://test'):
                manager = AutomatedStreamManager()
                
                # Configure regex to match all UK streams
                patterns = {
                    'patterns': {
                        '1': {
                            'name': 'UK Channels',
                            'regex': [r'UK:'],
                            'enabled': True
                        }
                    },
                    'global_settings': {
                        'case_sensitive': False
                    }
                }
                manager.regex_matcher.channel_patterns = patterns
                # Save to file so reload_patterns() works
                manager.regex_matcher._save_patterns(patterns)
                
                # Enable only account 1 (not custom)
                manager.config['enabled_m3u_accounts'] = [1]
                manager.config['enabled_features']['changelog_tracking'] = False
                
                # Run stream discovery
                result = manager.discover_and_assign_streams()
                
                # Verify both account 1 streams and custom streams were added
                self.assertTrue(mock_add_streams.called)
                call_args = mock_add_streams.call_args[0]
                stream_ids = call_args[1]
                
                # Should include both streams from account 1 AND custom streams
                self.assertEqual(set(stream_ids), {101, 301})
    
    @patch('automated_stream_manager.add_streams_to_channel')
    @patch('automated_stream_manager.fetch_data_from_url')
    @patch('automated_stream_manager.get_streams')
    def test_empty_enabled_accounts_matches_all(self, mock_get_streams, mock_fetch, mock_add_streams):
        """Test that empty enabled_m3u_accounts list means all accounts are enabled."""
        mock_get_streams.return_value = [
            {'id': 101, 'name': 'UK: BBC One HD', 'm3u_account_id': 1, 'is_custom': False},
            {'id': 201, 'name': 'UK: ITV HD', 'm3u_account_id': 2, 'is_custom': False},
        ]
        
        # Mock channels
        def fetch_side_effect(url):
            if url == 'http://test/api/channels/channels/':
                return [{'id': 1, 'name': 'UK Channels'}]
            elif url == 'http://test/api/channels/channels/1/streams/':
                return []
            return []
        
        mock_fetch.side_effect = fetch_side_effect
        
        mock_add_streams.return_value = 2
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager._get_base_url', return_value='http://test'):
                manager = AutomatedStreamManager()
                
                # Configure regex to match all UK streams
                patterns = {
                    'patterns': {
                        '1': {
                            'name': 'UK Channels',
                            'regex': [r'UK:'],
                            'enabled': True
                        }
                    },
                    'global_settings': {
                        'case_sensitive': False
                    }
                }
                manager.regex_matcher.channel_patterns = patterns
                # Save to file so reload_patterns() works
                manager.regex_matcher._save_patterns(patterns)
                
                # Empty list means all accounts enabled
                manager.config['enabled_m3u_accounts'] = []
                manager.config['enabled_features']['changelog_tracking'] = False
                
                # Run stream discovery
                result = manager.discover_and_assign_streams()
                
                # Verify streams from all accounts were added
                self.assertTrue(mock_add_streams.called)
                call_args = mock_add_streams.call_args[0]
                stream_ids = call_args[1]
                
                # Should include streams from both accounts
                self.assertEqual(set(stream_ids), {101, 201})


if __name__ == '__main__':
    unittest.main()
