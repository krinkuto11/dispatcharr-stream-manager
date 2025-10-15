#!/usr/bin/env python3
"""
Unit tests for filtering non-active M3U playlists.

This module tests that non-active playlists (is_active=False) are filtered out
from the /api/m3u-accounts endpoint per the Dispatcharr API specification.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNonActivePlaylistsFiltering(unittest.TestCase):
    """Test that non-active playlists are filtered out from the API response."""
    
    @patch('api_utils.has_custom_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_filters_non_active_accounts(self, mock_get_accounts, mock_has_custom):
        """Test that accounts with is_active=False are filtered out."""
        from web_api import app
        
        # Mock M3U accounts with mixed active states
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Provider', 'server_url': 'http://example.com', 'is_active': True},
            {'id': 2, 'name': 'Inactive Provider', 'server_url': 'http://inactive.com', 'is_active': False},
            {'id': 3, 'name': 'Another Active', 'server_url': 'http://active.com', 'is_active': True},
        ]
        
        # Mock has_custom_streams (not relevant for this test but required by endpoint)
        mock_has_custom.return_value = False
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should only return the active accounts
            self.assertEqual(len(data), 2)
            account_ids = [acc['id'] for acc in data]
            self.assertIn(1, account_ids)
            self.assertIn(3, account_ids)
            self.assertNotIn(2, account_ids)
            
            # Verify inactive account is not in response
            account_names = [acc['name'] for acc in data]
            self.assertIn('Active Provider', account_names)
            self.assertIn('Another Active', account_names)
            self.assertNotIn('Inactive Provider', account_names)
    
    @patch('api_utils.has_custom_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_keeps_accounts_without_is_active_field(self, mock_get_accounts, mock_has_custom):
        """Test that accounts without is_active field are kept (default to active)."""
        from web_api import app
        
        # Mock M3U accounts where some don't have is_active field
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Provider', 'server_url': 'http://example.com', 'is_active': True},
            {'id': 2, 'name': 'No Active Field', 'server_url': 'http://nofield.com'},  # Missing is_active
            {'id': 3, 'name': 'Inactive Provider', 'server_url': 'http://inactive.com', 'is_active': False},
        ]
        
        # Mock has_custom_streams
        mock_has_custom.return_value = False
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return active and missing-field accounts, but not inactive
            self.assertEqual(len(data), 2)
            account_ids = [acc['id'] for acc in data]
            self.assertIn(1, account_ids)
            self.assertIn(2, account_ids)  # Should be kept (defaults to active)
            self.assertNotIn(3, account_ids)
    
    @patch('api_utils.has_custom_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_filters_non_active_and_custom_accounts(self, mock_get_accounts, mock_has_custom):
        """Test that both is_active=False and 'custom' name filtering work together."""
        from web_api import app
        
        # Mock M3U accounts with both inactive and custom accounts
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Provider', 'server_url': 'http://example.com', 'is_active': True},
            {'id': 2, 'name': 'Inactive Provider', 'server_url': 'http://inactive.com', 'is_active': False},
            {'id': 3, 'name': 'custom', 'server_url': None, 'is_active': True},
            {'id': 4, 'name': 'Another Active', 'server_url': 'http://active.com', 'is_active': True},
        ]
        
        # Mock has_custom_streams to return False (so "custom" account should be filtered)
        mock_has_custom.return_value = False
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should filter out both inactive (id=2) and custom (id=3) accounts
            self.assertEqual(len(data), 2)
            account_ids = [acc['id'] for acc in data]
            self.assertIn(1, account_ids)
            self.assertIn(4, account_ids)
            self.assertNotIn(2, account_ids)  # Filtered due to is_active=False
            self.assertNotIn(3, account_ids)  # Filtered due to name='custom' and no custom streams
    
    @patch('api_utils.has_custom_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_keeps_inactive_custom_account_when_custom_streams_exist(self, mock_get_accounts, mock_has_custom):
        """Test that even if 'custom' account is inactive, filtering by name still applies when custom streams exist."""
        from web_api import app
        
        # Mock accounts with inactive custom account
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Active Provider', 'server_url': 'http://example.com', 'is_active': True},
            {'id': 2, 'name': 'custom', 'server_url': None, 'is_active': False},
        ]
        
        # Mock has_custom_streams to return True
        mock_has_custom.return_value = True
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Even though custom streams exist, inactive custom account should be filtered
            # due to is_active=False (is_active filtering happens first)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['id'], 1)
            self.assertEqual(data[0]['name'], 'Active Provider')
    
    @patch('api_utils.has_custom_streams')
    @patch('api_utils.get_m3u_accounts')
    def test_all_accounts_inactive(self, mock_get_accounts, mock_has_custom):
        """Test edge case where all accounts are inactive."""
        from web_api import app
        
        # Mock all accounts as inactive
        mock_get_accounts.return_value = [
            {'id': 1, 'name': 'Inactive 1', 'server_url': 'http://example.com', 'is_active': False},
            {'id': 2, 'name': 'Inactive 2', 'server_url': 'http://inactive.com', 'is_active': False},
        ]
        
        # Mock has_custom_streams
        mock_has_custom.return_value = False
        
        with app.test_client() as client:
            response = client.get('/api/m3u-accounts')
            data = json.loads(response.data)
            
            # Should return empty list
            self.assertEqual(len(data), 0)


if __name__ == '__main__':
    unittest.main()
