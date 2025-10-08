#!/usr/bin/env python3
"""
Unit tests for M3U accounts endpoint filtering.

This module tests:
- Filtering out "custom" M3U account when no custom streams exist
- Keeping "custom" M3U account when custom streams exist
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestM3UAccountsEndpoint(unittest.TestCase):
    """Test M3U accounts endpoint filtering."""
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_filters_custom_account_when_no_custom_streams(self, mock_get_accounts, mock_get_streams):
        """Test that 'custom' M3U account is filtered out when there are no custom streams."""
        from web_api import app
        
        # Mock M3U accounts including a "custom" account
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'IPTV Provider', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'custom', 'server_url': None, 'file_path': None},
        ]
        
        # Mock streams with NO custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
            {'id': 2, 'name': 'Stream 2', 'is_custom': False, 'm3u_account': 1},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should only return the non-custom account
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['id'], 1)
            self.assertEqual(data[0]['name'], 'IPTV Provider')
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_keeps_custom_account_when_custom_streams_exist(self, mock_get_accounts, mock_get_streams):
        """Test that 'custom' M3U account is kept when custom streams exist."""
        from web_api import app
        
        # Mock M3U accounts including a "custom" account
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'IPTV Provider', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'custom', 'server_url': None, 'file_path': None},
        ]
        
        # Mock streams with custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
            {'id': 2, 'name': 'My Custom Stream', 'is_custom': True, 'm3u_account': None},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return both accounts since custom streams exist
            self.assertEqual(len(data), 2)
            account_names = [acc['name'] for acc in data]
            self.assertIn('IPTV Provider', account_names)
            self.assertIn('custom', account_names)
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_keeps_account_with_null_urls_when_no_custom_streams(self, mock_get_accounts, mock_get_streams):
        """Test that accounts with null server_url and file_path are kept (not filtered) when no custom streams.
        
        This ensures legitimate disabled or file-based accounts aren't incorrectly filtered out.
        """
        from web_api import app
        
        # Mock M3U accounts with different configurations
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'IPTV Provider', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'Placeholder', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'File Source', 'server_url': None, 'file_path': '/path/to/file.m3u'},
        ]
        
        # Mock streams with NO custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return all 3 accounts - we no longer filter based on null URLs
            # Only filter by name matching "custom" (case-insensitive)
            self.assertEqual(len(data), 3)
            account_ids = [acc['id'] for acc in data]
            self.assertIn(1, account_ids)
            self.assertIn(2, account_ids)
            self.assertIn(3, account_ids)
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_case_insensitive_custom_name_filter(self, mock_get_accounts, mock_get_streams):
        """Test that 'custom' name filtering is case-insensitive."""
        from web_api import app
        
        # Mock M3U accounts with different case variations of "custom"
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'IPTV Provider', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'Custom', 'server_url': None},
            {'id': 3, 'name': 'CUSTOM', 'server_url': None},
            {'id': 4, 'name': 'CuStOm', 'server_url': None},
        ]
        
        # Mock streams with NO custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should only return the non-custom account (all variations of "custom" filtered)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['id'], 1)
            self.assertEqual(data[0]['name'], 'IPTV Provider')
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_returns_all_accounts_when_custom_streams_present(self, mock_get_accounts, mock_get_streams):
        """Test that all accounts are returned when custom streams are present."""
        from web_api import app
        
        # Mock various M3U accounts
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'IPTV Provider', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'custom', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'Another Provider', 'server_url': 'http://another.com'},
        ]
        
        # Mock streams with custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
            {'id': 2, 'name': 'My Custom', 'is_custom': True, 'm3u_account': None},
            {'id': 3, 'name': 'Another Custom', 'is_custom': True, 'm3u_account': None},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return all 3 accounts since custom streams exist
            self.assertEqual(len(data), 3)
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_disabled_accounts_with_null_urls_are_not_filtered(self, mock_get_accounts, mock_get_streams):
        """Test edge case: disabled accounts with null URLs should not be filtered out.
        
        This was the bug - accounts with null server_url and file_path were being filtered
        even if they were legitimate disabled accounts, not just placeholders.
        """
        from web_api import app
        
        # Mock accounts where some might be disabled with null URLs
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Account', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'Disabled Account', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'custom', 'server_url': None, 'file_path': None},
        ]
        
        # No custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return Active and Disabled accounts, but filter out "custom"
            self.assertEqual(len(data), 2)
            account_names = [acc['name'] for acc in data]
            self.assertIn('Active Account', account_names)
            self.assertIn('Disabled Account', account_names)
            self.assertNotIn('custom', account_names)


if __name__ == '__main__':
    unittest.main()
