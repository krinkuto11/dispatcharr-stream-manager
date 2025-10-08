#!/usr/bin/env python3
"""
Unit tests for the has_custom_streams() performance optimization.

This module tests that has_custom_streams() is more efficient than get_streams()
when checking for the existence of custom streams.
"""

import unittest
from unittest.mock import Mock, patch, call
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestHasCustomStreamsPerformance(unittest.TestCase):
    """Test the performance optimization of has_custom_streams()."""
    
    @patch('api_utils.fetch_data_from_url')
    def test_returns_true_when_custom_stream_found_in_first_page(self, mock_fetch):
        """Test that has_custom_streams returns True immediately when custom stream is in first page."""
        from api_utils import has_custom_streams
        
        # Mock response with custom stream in first page (API filter works)
        mock_fetch.return_value = {
            'results': [
                {'id': 1, 'name': 'Custom Stream', 'is_custom': True}
            ],
            'next': None
        }
        
        result = has_custom_streams()
        
        # Should return True immediately after first call (filter works)
        self.assertTrue(result)
        # Should only call API once (filter query returns custom stream)
        self.assertEqual(mock_fetch.call_count, 1)
    
    @patch('api_utils.fetch_data_from_url')
    def test_returns_false_when_no_custom_streams(self, mock_fetch):
        """Test that has_custom_streams returns False after checking all pages."""
        from api_utils import has_custom_streams
        
        # Mock response with no custom streams
        def side_effect(url):
            if 'is_custom=true' in url:
                # First call with filter returns no results
                return {'results': [], 'next': None}
            else:
                # Fallback calls return non-custom streams
                return {
                    'results': [
                        {'id': 1, 'name': 'Stream 1', 'is_custom': False},
                        {'id': 2, 'name': 'Stream 2', 'is_custom': False}
                    ],
                    'next': None
                }
        
        mock_fetch.side_effect = side_effect
        
        result = has_custom_streams()
        
        # Should return False
        self.assertFalse(result)
    
    @patch('api_utils.fetch_data_from_url')
    def test_early_exit_when_custom_stream_found_in_middle_page(self, mock_fetch):
        """Test that has_custom_streams exits early when custom stream found in any page."""
        from api_utils import has_custom_streams
        
        call_count = [0]
        
        def side_effect(url):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call with filter returns no results but has 'results' key
                # This indicates filter worked and there are no custom streams
                # But we need to test early exit, so return None to trigger fallback
                return None
            elif call_count[0] == 2:
                # Second call: first page of fallback, no custom streams
                return {
                    'results': [
                        {'id': 1, 'name': 'Stream 1', 'is_custom': False},
                    ],
                    'next': 'http://api.example.com/streams/?page=2'
                }
            elif call_count[0] == 3:
                # Third call: second page has custom stream - should exit early
                return {
                    'results': [
                        {'id': 2, 'name': 'Custom Stream', 'is_custom': True},
                    ],
                    'next': 'http://api.example.com/streams/?page=3'
                }
            else:
                # Should never reach this - would be page 3
                self.fail("Should have exited early after finding custom stream")
        
        mock_fetch.side_effect = side_effect
        
        result = has_custom_streams()
        
        # Should return True
        self.assertTrue(result)
        # Should only call API 3 times (filter attempt + 2 pages), not continue to page 3
        self.assertEqual(mock_fetch.call_count, 3)
    
    @patch('api_utils.fetch_data_from_url')
    def test_uses_page_size_100_for_efficiency(self, mock_fetch):
        """Test that has_custom_streams uses page_size=100 for fallback to minimize API calls."""
        from api_utils import has_custom_streams
        
        def side_effect(url):
            if 'is_custom=true' in url:
                # Filter returns no results, triggering fallback
                return None
            else:
                # Fallback returns results
                return {
                    'results': [
                        {'id': 1, 'name': 'Stream 1', 'is_custom': False}
                    ],
                    'next': None
                }
        
        mock_fetch.side_effect = side_effect
        
        has_custom_streams()
        
        # Check that the fallback call uses page_size=100
        calls = mock_fetch.call_args_list
        # Second call should be the fallback with page_size=100
        self.assertIn('page_size=100', calls[1][0][0])
    
    @patch('api_utils.fetch_data_from_url')
    def test_tries_api_filtering_first(self, mock_fetch):
        """Test that has_custom_streams first tries API filtering with is_custom=true."""
        from api_utils import has_custom_streams
        
        mock_fetch.return_value = {
            'results': [],
            'next': None
        }
        
        has_custom_streams()
        
        # First call should attempt filtering
        first_call_url = mock_fetch.call_args_list[0][0][0]
        self.assertIn('is_custom=true', first_call_url)
        self.assertIn('page_size=1', first_call_url)


if __name__ == '__main__':
    unittest.main()
