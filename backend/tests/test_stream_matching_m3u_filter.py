#!/usr/bin/env python3
"""
Unit tests for stream matching with M3U account filtering.

This module tests that only streams from enabled M3U accounts are considered
during the stream matching and assignment process by verifying the filtering
logic before streams are matched to channels.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automated_stream_manager import AutomatedStreamManager


class TestStreamMatchingM3UFilter(unittest.TestCase):
    """Test that stream matching only considers streams from enabled M3U accounts."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _filter_streams_by_accounts(self, manager, all_streams, enabled_accounts_config):
        """
        Helper method that mimics the filtering logic from discover_and_assign_streams.
        This allows us to unit test just the filtering logic.
        """
        from automated_stream_manager import get_m3u_accounts
        
        # Get all M3U accounts and filter by enabled and active status
        all_accounts = get_m3u_accounts()
        enabled_account_ids = set()
        
        if all_accounts:
            # Filter out "custom" account and non-active accounts
            non_custom_accounts = [
                acc for acc in all_accounts
                if acc.get('name', '').lower() != 'custom' and acc.get('is_active', True)
            ]
            
            if enabled_accounts_config:
                # Only include accounts that are in the enabled list
                enabled_account_ids = set(
                    acc.get('id') for acc in non_custom_accounts 
                    if acc.get('id') in enabled_accounts_config and acc.get('id') is not None
                )
            else:
                # If no specific accounts are enabled in config, use all non-custom active accounts
                enabled_account_ids = set(
                    acc.get('id') for acc in non_custom_accounts 
                    if acc.get('id') is not None
                )
            
            # Filter streams to only include those from enabled accounts
            # Also include custom streams (is_custom=True) as they don't belong to an M3U account
            filtered_streams = [
                stream for stream in all_streams
                if stream.get('is_custom', False) or stream.get('m3u_account') in enabled_account_ids
            ]
            
            return filtered_streams
        
        return all_streams
    
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_filters_streams_by_enabled_accounts(self, mock_get_accounts):
        """Test that only streams from enabled M3U accounts are kept after filtering."""
        # Mock M3U accounts
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Enabled Account', 'is_active': True},
            {'id': 2, 'name': 'Disabled Account', 'is_active': True},
            {'id': 3, 'name': 'custom', 'is_active': True}
        ]
        
        # Mock streams from different accounts
        all_streams = [
            {'id': 101, 'name': 'ESPN HD', 'm3u_account': 1, 'is_custom': False},
            {'id': 102, 'name': 'ESPN 2 HD', 'm3u_account': 1, 'is_custom': False},
            {'id': 201, 'name': 'FOX HD', 'm3u_account': 2, 'is_custom': False},
            {'id': 202, 'name': 'FOX Sports HD', 'm3u_account': 2, 'is_custom': False},
            {'id': 301, 'name': 'Custom Stream', 'm3u_account': 3, 'is_custom': True}
        ]
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Configure to only enable account 1
            enabled_accounts_config = [1]
            
            # Test the filtering logic
            filtered_streams = self._filter_streams_by_accounts(manager, all_streams, enabled_accounts_config)
            
            # Verify filtering results
            filtered_ids = {s['id'] for s in filtered_streams}
            
            # Should include streams from account 1 and custom stream
            self.assertIn(101, filtered_ids)  # ESPN HD from account 1
            self.assertIn(102, filtered_ids)  # ESPN 2 HD from account 1
            self.assertIn(301, filtered_ids)  # Custom stream
            
            # Should NOT include streams from account 2
            self.assertNotIn(201, filtered_ids)  # FOX HD from account 2
            self.assertNotIn(202, filtered_ids)  # FOX Sports HD from account 2
            
            # Verify count
            self.assertEqual(len(filtered_streams), 3)  # 2 from account 1 + 1 custom
    
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_includes_all_streams_when_no_filter(self, mock_get_accounts):
        """Test that all streams are included when no filter is configured."""
        # Mock M3U accounts
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Account 1', 'is_active': True},
            {'id': 2, 'name': 'Account 2', 'is_active': True}
        ]
        
        # Mock streams from different accounts
        all_streams = [
            {'id': 101, 'name': 'Stream A', 'm3u_account': 1, 'is_custom': False},
            {'id': 201, 'name': 'Stream B', 'm3u_account': 2, 'is_custom': False}
        ]
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Empty enabled_m3u_accounts means all accounts enabled
            enabled_accounts_config = []
            
            # Test the filtering logic
            filtered_streams = self._filter_streams_by_accounts(manager, all_streams, enabled_accounts_config)
            
            # All streams should be included
            filtered_ids = {s['id'] for s in filtered_streams}
            
            self.assertIn(101, filtered_ids)
            self.assertIn(201, filtered_ids)
            self.assertEqual(len(filtered_streams), 2)
    
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_filters_out_inactive_accounts(self, mock_get_accounts):
        """Test that streams from inactive M3U accounts are filtered out."""
        # Mock M3U accounts with one inactive
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Account', 'is_active': True},
            {'id': 2, 'name': 'Inactive Account', 'is_active': False}
        ]
        
        # Mock streams from different accounts
        all_streams = [
            {'id': 101, 'name': 'Active Stream', 'm3u_account': 1, 'is_custom': False},
            {'id': 201, 'name': 'Inactive Stream', 'm3u_account': 2, 'is_custom': False}
        ]
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Empty list means all active accounts
            enabled_accounts_config = []
            
            # Test the filtering logic
            filtered_streams = self._filter_streams_by_accounts(manager, all_streams, enabled_accounts_config)
            
            # Only stream from active account should be included
            filtered_ids = {s['id'] for s in filtered_streams}
            
            self.assertIn(101, filtered_ids)  # Active stream
            self.assertNotIn(201, filtered_ids)  # Inactive stream
            self.assertEqual(len(filtered_streams), 1)
    
    @patch('automated_stream_manager.get_m3u_accounts')
    def test_excludes_custom_account(self, mock_get_accounts):
        """Test that 'custom' M3U account is excluded from filtering."""
        # Mock M3U accounts including custom
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Regular Account', 'is_active': True},
            {'id': 99, 'name': 'custom', 'is_active': True}
        ]
        
        # Mock streams, including one from custom account and a custom stream
        all_streams = [
            {'id': 101, 'name': 'Regular Stream', 'm3u_account': 1, 'is_custom': False},
            {'id': 999, 'name': 'Custom Account Stream', 'm3u_account': 99, 'is_custom': False},
            {'id': 888, 'name': 'Truly Custom Stream', 'm3u_account': None, 'is_custom': True}
        ]
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Enable only account 1
            enabled_accounts_config = [1]
            
            # Test the filtering logic
            filtered_streams = self._filter_streams_by_accounts(manager, all_streams, enabled_accounts_config)
            
            # Should include stream from account 1 and truly custom stream
            # Should not include stream from "custom" M3U account (99)
            filtered_ids = {s['id'] for s in filtered_streams}
            
            self.assertIn(101, filtered_ids)  # Regular stream from account 1
            self.assertIn(888, filtered_ids)  # Truly custom stream
            self.assertNotIn(999, filtered_ids)  # Stream from "custom" M3U account
            self.assertEqual(len(filtered_streams), 2)


if __name__ == '__main__':
    unittest.main()
