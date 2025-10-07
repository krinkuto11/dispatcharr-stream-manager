#!/usr/bin/env python3
"""
Unit tests for M3U account filtering functionality.

This module tests:
- M3U account selection configuration
- Refresh behavior with filtered accounts
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


class TestM3UAccountFiltering(unittest.TestCase):
    """Test M3U account filtering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'automation_config.json'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config_includes_empty_enabled_accounts(self):
        """Test that default configuration includes empty enabled_m3u_accounts list."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Check default config has enabled_m3u_accounts
            self.assertIn('enabled_m3u_accounts', manager.config)
            self.assertEqual(manager.config['enabled_m3u_accounts'], [])
    
    def test_config_persistence_with_enabled_accounts(self):
        """Test that enabled_m3u_accounts is saved and loaded correctly."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create manager and update config with enabled accounts
            manager = AutomatedStreamManager()
            test_accounts = [1, 2, 3]
            manager.update_config({'enabled_m3u_accounts': test_accounts})
            
            # Create new manager instance to test loading
            manager2 = AutomatedStreamManager()
            self.assertEqual(manager2.config['enabled_m3u_accounts'], test_accounts)
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    def test_refresh_all_accounts_when_none_selected(self, mock_get_streams, mock_refresh):
        """Test that all accounts are refreshed when enabled_m3u_accounts is empty."""
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should call refresh without account_id (refresh all)
            mock_refresh.assert_called_once_with()
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    def test_refresh_only_enabled_accounts(self, mock_get_streams, mock_refresh):
        """Test that only enabled accounts are refreshed when some are selected."""
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            enabled_accounts = [1, 3, 5]
            manager.config['enabled_m3u_accounts'] = enabled_accounts
            manager.config['enabled_features']['changelog_tracking'] = False
            manager.refresh_playlists()
            
            # Should call refresh for each enabled account
            expected_calls = [call(account_id=acc_id) for acc_id in enabled_accounts]
            mock_refresh.assert_has_calls(expected_calls)
            self.assertEqual(mock_refresh.call_count, len(enabled_accounts))
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    def test_refresh_with_changelog_disabled(self, mock_get_streams, mock_refresh):
        """Test that refresh works correctly when changelog tracking is disabled."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = [1, 2]
            manager.config['enabled_features']['changelog_tracking'] = False
            
            manager.refresh_playlists()
            
            # Should still call refresh for enabled accounts
            self.assertEqual(mock_refresh.call_count, 2)
            # get_streams should not be called when changelog is disabled
            mock_get_streams.assert_not_called()
    
    @patch('automated_stream_manager.refresh_m3u_playlists')
    @patch('automated_stream_manager.get_streams')
    def test_refresh_excludes_custom_streams(self, mock_get_streams, mock_refresh):
        """Test that custom streams are excluded when fetching streams during refresh."""
        mock_get_streams.return_value = []
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.config['enabled_m3u_accounts'] = []
            manager.config['enabled_features']['changelog_tracking'] = True
            manager.refresh_playlists()
            
            # Verify get_streams was called with exclude_custom=True
            # It should be called twice: before and after refresh
            self.assertEqual(mock_get_streams.call_count, 2)
            for call_obj in mock_get_streams.call_args_list:
                # Check that exclude_custom=True was passed
                self.assertIn('exclude_custom', call_obj.kwargs)
                self.assertTrue(call_obj.kwargs['exclude_custom'])


class TestM3UAccountConfiguration(unittest.TestCase):
    """Test M3U account configuration updates."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_enabled_accounts(self):
        """Test updating enabled M3U accounts via update_config."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Update with new account selection
            new_accounts = [2, 4, 6]
            manager.update_config({'enabled_m3u_accounts': new_accounts})
            
            # Verify config was updated
            self.assertEqual(manager.config['enabled_m3u_accounts'], new_accounts)
            
            # Verify it persisted
            manager2 = AutomatedStreamManager()
            self.assertEqual(manager2.config['enabled_m3u_accounts'], new_accounts)
    
    def test_empty_accounts_list(self):
        """Test that empty list means all accounts enabled."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.update_config({'enabled_m3u_accounts': []})
            
            # Empty list should be stored correctly
            self.assertEqual(manager.config['enabled_m3u_accounts'], [])


if __name__ == '__main__':
    unittest.main()
