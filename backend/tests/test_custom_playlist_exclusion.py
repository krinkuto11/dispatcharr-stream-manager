#!/usr/bin/env python3
"""
Unit tests for custom playlist exclusion from automated updates.

This module tests that the "custom" M3U account is not refreshed
during automated playlist updates, as it contains locally added streams
and doesn't need to pull data from a remote server.
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automated_stream_manager import AutomatedStreamManager


class TestCustomPlaylistExclusion(unittest.TestCase):
    """Test that custom playlist is excluded from automated updates."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'automation_config.json'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_custom_account_excluded_from_refresh(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that account named 'custom' is excluded from refresh."""
        # Mock accounts including a custom one
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'IPTV Provider 1', 'server_url': 'http://example.com/playlist.m3u'},
            {'id': 2, 'name': 'custom', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'IPTV Provider 2', 'server_url': 'http://example.com/playlist2.m3u'}
        ]
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should refresh accounts 1 and 3, but NOT 2 (custom)
            expected_calls = [call(account_id=1), call(account_id=3)]
            mock_refresh.assert_has_calls(expected_calls, any_order=True)
            self.assertEqual(mock_refresh.call_count, 2)
            
            # Verify custom account was NOT refreshed
            for call_args in mock_refresh.call_args_list:
                args, kwargs = call_args
                if 'account_id' in kwargs:
                    self.assertNotEqual(kwargs['account_id'], 2, "Custom account should not be refreshed")
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_custom_case_insensitive(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that 'CUSTOM', 'Custom', 'custom' are all excluded."""
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Regular Account', 'server_url': 'http://example.com/playlist.m3u'},
            {'id': 2, 'name': 'CUSTOM', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'Custom', 'server_url': None, 'file_path': None},
        ]
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should only refresh account 1
            mock_refresh.assert_called_once_with(account_id=1)
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_null_url_accounts_not_excluded(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that accounts with null server_url and file_path are NOT excluded (bug fix).
        
        This test was updated to reflect the fix for the edge case where disabled/file-based
        accounts with null URLs were being incorrectly filtered out.
        """
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Valid Account', 'server_url': 'http://example.com/playlist.m3u'},
            {'id': 2, 'name': 'LocalAccount', 'server_url': None, 'file_path': None},
        ]
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should refresh both accounts (we no longer filter based on null URLs)
            self.assertEqual(mock_refresh.call_count, 2)
            mock_refresh.assert_any_call(account_id=1)
            mock_refresh.assert_any_call(account_id=2)
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_enabled_accounts_respects_custom_exclusion(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that custom accounts are excluded even when explicitly in enabled_accounts list."""
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Provider 1', 'server_url': 'http://example.com/playlist.m3u'},
            {'id': 2, 'name': 'custom', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'Provider 2', 'server_url': 'http://example.com/playlist2.m3u'}
        ]
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            # User explicitly enabled accounts 1, 2, 3
            manager.config['enabled_m3u_accounts'] = [1, 2, 3]
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should only refresh accounts 1 and 3, NOT 2 (custom)
            expected_calls = [call(account_id=1), call(account_id=3)]
            mock_refresh.assert_has_calls(expected_calls, any_order=True)
            self.assertEqual(mock_refresh.call_count, 2)
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_only_custom_accounts_no_refresh(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that if only custom accounts exist, no refresh occurs."""
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'custom', 'server_url': None, 'file_path': None},
        ]
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should not call refresh at all
            mock_refresh.assert_not_called()
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_fallback_when_accounts_unavailable(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test fallback behavior when get_m3u_accounts returns None."""
        mock_get_accounts.return_value = None
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should fall back to refreshing all (legacy behavior)
            mock_refresh.assert_called_once_with()


    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_inactive_accounts_excluded_from_refresh(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that accounts with is_active=False are excluded from refresh."""
        mock_get_streams.return_value = []
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Account', 'server_url': 'http://example.com', 'is_active': True},
            {'id': 2, 'name': 'Inactive Account', 'server_url': 'http://inactive.com', 'is_active': False},
            {'id': 3, 'name': 'Another Active', 'server_url': 'http://active2.com', 'is_active': True},
        ]
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should only refresh active accounts (ids 1 and 3)
            expected_calls = [call(account_id=1), call(account_id=3)]
            mock_refresh.assert_has_calls(expected_calls, any_order=True)
            self.assertEqual(mock_refresh.call_count, 2)
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_inactive_and_custom_accounts_excluded(self, mock_get_accounts, mock_get_streams, mock_refresh):
        """Test that both inactive and custom accounts are excluded from refresh."""
        mock_get_streams.return_value = []
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Account', 'server_url': 'http://example.com', 'is_active': True},
            {'id': 2, 'name': 'Inactive Account', 'server_url': 'http://inactive.com', 'is_active': False},
            {'id': 3, 'name': 'custom', 'server_url': None, 'is_active': True},
            {'id': 4, 'name': 'Another Active', 'server_url': 'http://active2.com', 'is_active': True},
        ]
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should only refresh active non-custom accounts (ids 1 and 4)
            expected_calls = [call(account_id=1), call(account_id=4)]
            mock_refresh.assert_has_calls(expected_calls, any_order=True)
            self.assertEqual(mock_refresh.call_count, 2)


if __name__ == '__main__':
    unittest.main()
