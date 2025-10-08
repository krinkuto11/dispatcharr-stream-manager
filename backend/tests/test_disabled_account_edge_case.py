#!/usr/bin/env python3
"""
Unit tests for the disabled account edge case fix.

This module documents and tests the edge case where accounts with null URLs
were being incorrectly filtered out, causing legitimate disabled or file-based
accounts to disappear from the UI.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDisabledAccountEdgeCase(unittest.TestCase):
    """Test the edge case fix for disabled accounts with null URLs."""
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_edge_case_disabled_account_still_shown(self, mock_get_accounts, mock_get_streams):
        """
        Test the edge case that was fixed:
        
        SCENARIO:
        1. User has accounts: Account A, Account B, Custom
        2. Account B gets disabled in Dispatcharr (server_url and file_path become None)
        3. Before fix: Account B would be filtered out (thinking it's a placeholder)
        4. After fix: Account B remains visible (only "custom" is filtered by name)
        """
        from web_api import app
        
        # Mock accounts including a disabled one with null URLs
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Account A', 'server_url': 'http://example.com/playlist.m3u'},
            {'id': 2, 'name': 'Account B', 'server_url': None, 'file_path': None},  # Disabled
            {'id': 3, 'name': 'custom', 'server_url': None, 'file_path': None},  # Should be filtered
        ]
        
        # No custom streams
        mock_get_streams.return_value = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
        ]
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return Account A and Account B (not "custom")
            self.assertEqual(len(data), 2)
            account_names = [acc['name'] for acc in data]
            self.assertIn('Account A', account_names)
            self.assertIn('Account B', account_names)  # Disabled account is kept!
            self.assertNotIn('custom', account_names)  # Only "custom" is filtered
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_file_based_account_with_null_server_url_shown(self, mock_get_accounts, mock_get_streams):
        """
        Test that file-based accounts with null server_url are kept.
        
        SCENARIO:
        1. Account uses a local file (file_path set, server_url is None)
        2. This is a legitimate account configuration
        3. Should NOT be filtered out
        """
        from web_api import app
        
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Online Provider', 'server_url': 'http://example.com'},
            {'id': 2, 'name': 'Local File', 'server_url': None, 'file_path': '/path/to/playlist.m3u'},
            {'id': 3, 'name': 'custom', 'server_url': None, 'file_path': None},
        ]
        
        mock_get_streams.return_value = []
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return both Online Provider and Local File (not "custom")
            self.assertEqual(len(data), 2)
            account_names = [acc['name'] for acc in data]
            self.assertIn('Online Provider', account_names)
            self.assertIn('Local File', account_names)
            self.assertNotIn('custom', account_names)
    
    @patch('api_utils.get_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_all_accounts_disabled_except_custom(self, mock_get_accounts, mock_get_streams):
        """
        Test edge case where all real accounts are disabled, only custom remains.
        
        SCENARIO:
        1. All accounts get disabled (null URLs)
        2. Only "custom" account remains with null URLs
        3. No custom streams exist
        4. Result: Should filter out "custom", show the disabled accounts
        """
        from web_api import app
        
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Disabled A', 'server_url': None, 'file_path': None},
            {'id': 2, 'name': 'Disabled B', 'server_url': None, 'file_path': None},
            {'id': 3, 'name': 'custom', 'server_url': None, 'file_path': None},
        ]
        
        mock_get_streams.return_value = []
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return both disabled accounts (not "custom")
            self.assertEqual(len(data), 2)
            account_names = [acc['name'] for acc in data]
            self.assertIn('Disabled A', account_names)
            self.assertIn('Disabled B', account_names)
            self.assertNotIn('custom', account_names)


if __name__ == '__main__':
    unittest.main()
