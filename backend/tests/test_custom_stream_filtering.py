#!/usr/bin/env python3
"""
Unit tests for custom stream filtering functionality.

This module tests:
- Filtering custom streams from get_streams() calls
- Ensuring custom streams (is_custom=True) are excluded when requested
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_utils import get_streams


class TestCustomStreamFiltering(unittest.TestCase):
    """Test custom stream filtering functionality."""
    
    @patch('api_utils.fetch_data_from_url')
    def test_get_streams_includes_custom_by_default(self, mock_fetch):
        """Test that custom streams are included by default."""
        # Mock response with both custom and M3U account streams
        mock_streams = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
            {'id': 2, 'name': 'Custom Stream', 'is_custom': True, 'm3u_account': None},
            {'id': 3, 'name': 'Stream 3', 'is_custom': False, 'm3u_account': 1},
        ]
        mock_fetch.return_value = {
            'results': mock_streams,
            'next': None
        }
        
        streams = get_streams(log_result=False, exclude_custom=False)
        
        # All streams should be included
        self.assertEqual(len(streams), 3)
        self.assertEqual(streams, mock_streams)
    
    @patch('api_utils.fetch_data_from_url')
    def test_get_streams_excludes_custom_when_requested(self, mock_fetch):
        """Test that custom streams are excluded when exclude_custom=True."""
        # Mock response with both custom and M3U account streams
        mock_streams = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False, 'm3u_account': 1},
            {'id': 2, 'name': 'Custom Stream', 'is_custom': True, 'm3u_account': None},
            {'id': 3, 'name': 'Stream 3', 'is_custom': False, 'm3u_account': 1},
        ]
        mock_fetch.return_value = {
            'results': mock_streams,
            'next': None
        }
        
        streams = get_streams(log_result=False, exclude_custom=True)
        
        # Only non-custom streams should be included
        self.assertEqual(len(streams), 2)
        self.assertEqual(streams[0]['id'], 1)
        self.assertEqual(streams[1]['id'], 3)
        # Verify no custom streams in result
        for stream in streams:
            self.assertFalse(stream.get('is_custom', False))
    
    @patch('api_utils.fetch_data_from_url')
    def test_get_streams_handles_missing_is_custom_field(self, mock_fetch):
        """Test that streams without is_custom field are not filtered out."""
        # Mock response where some streams don't have is_custom field
        mock_streams = [
            {'id': 1, 'name': 'Stream 1', 'm3u_account': 1},  # Missing is_custom
            {'id': 2, 'name': 'Custom Stream', 'is_custom': True},
            {'id': 3, 'name': 'Stream 3', 'is_custom': False},
        ]
        mock_fetch.return_value = {
            'results': mock_streams,
            'next': None
        }
        
        streams = get_streams(log_result=False, exclude_custom=True)
        
        # Streams 1 and 3 should be included (2 is custom)
        self.assertEqual(len(streams), 2)
        self.assertIn(1, [s['id'] for s in streams])
        self.assertIn(3, [s['id'] for s in streams])
        self.assertNotIn(2, [s['id'] for s in streams])
    
    @patch('api_utils.fetch_data_from_url')
    def test_get_streams_with_pagination_excludes_custom(self, mock_fetch):
        """Test that custom stream filtering works with pagination."""
        # Mock paginated response
        page1_streams = [
            {'id': 1, 'name': 'Stream 1', 'is_custom': False},
            {'id': 2, 'name': 'Custom Stream 1', 'is_custom': True},
        ]
        page2_streams = [
            {'id': 3, 'name': 'Stream 3', 'is_custom': False},
            {'id': 4, 'name': 'Custom Stream 2', 'is_custom': True},
        ]
        
        def mock_fetch_side_effect(url):
            if 'page=2' in url or url.endswith('page=2'):
                return {
                    'results': page2_streams,
                    'next': None
                }
            else:
                return {
                    'results': page1_streams,
                    'next': 'http://example.com/api/streams/?page=2'
                }
        
        mock_fetch.side_effect = mock_fetch_side_effect
        
        streams = get_streams(log_result=False, exclude_custom=True)
        
        # Only non-custom streams should be included
        self.assertEqual(len(streams), 2)
        self.assertEqual(streams[0]['id'], 1)
        self.assertEqual(streams[1]['id'], 3)
        # Verify no custom streams in result
        for stream in streams:
            self.assertFalse(stream.get('is_custom', False))
    
    @patch('api_utils.fetch_data_from_url')
    def test_get_streams_all_custom_returns_empty(self, mock_fetch):
        """Test that if all streams are custom, empty list is returned."""
        # Mock response with only custom streams
        mock_streams = [
            {'id': 1, 'name': 'Custom Stream 1', 'is_custom': True},
            {'id': 2, 'name': 'Custom Stream 2', 'is_custom': True},
        ]
        mock_fetch.return_value = {
            'results': mock_streams,
            'next': None
        }
        
        streams = get_streams(log_result=False, exclude_custom=True)
        
        # Should return empty list
        self.assertEqual(len(streams), 0)


if __name__ == '__main__':
    unittest.main()
