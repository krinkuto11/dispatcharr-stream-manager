#!/usr/bin/env python3
"""
Unit test to verify token validation and caching improvements.

This test verifies that the token validation mechanism works correctly
and reduces unnecessary login attempts.
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestTokenValidation(unittest.TestCase):
    """Test token validation and caching functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('api_utils.requests.get')
    @patch('api_utils.os.getenv')
    def test_validate_token_with_valid_token(self, mock_getenv, mock_get):
        """Test that _validate_token returns True for valid tokens."""
        from api_utils import _validate_token
        
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'DISPATCHARR_BASE_URL': 'http://test.com'
        }.get(key)
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = _validate_token('valid_token_123')
        self.assertTrue(result)
        
        # Verify the API was called with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('test.com/api/channels/channels/', call_args[0][0])
        self.assertIn('Authorization', call_args[1]['headers'])
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer valid_token_123')
    
    @patch('api_utils.requests.get')
    @patch('api_utils.os.getenv')
    def test_validate_token_with_invalid_token(self, mock_getenv, mock_get):
        """Test that _validate_token returns False for invalid tokens."""
        from api_utils import _validate_token
        
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'DISPATCHARR_BASE_URL': 'http://test.com'
        }.get(key)
        
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = _validate_token('invalid_token')
        self.assertFalse(result)
    
    @patch('api_utils.requests.get')
    @patch('api_utils.os.getenv')
    def test_validate_token_with_connection_error(self, mock_getenv, mock_get):
        """Test that _validate_token returns False on connection error."""
        from api_utils import _validate_token
        
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'DISPATCHARR_BASE_URL': 'http://test.com'
        }.get(key)
        
        # Mock connection error
        mock_get.side_effect = Exception("Connection failed")
        
        result = _validate_token('some_token')
        self.assertFalse(result)
    
    @patch('api_utils._validate_token')
    @patch('api_utils.login')
    @patch('api_utils.os.getenv')
    def test_get_auth_headers_uses_valid_token(self, mock_getenv, mock_login, mock_validate):
        """Test that _get_auth_headers uses existing valid token without logging in."""
        from api_utils import _get_auth_headers
        
        # Mock that we have a valid token
        mock_getenv.return_value = 'valid_token_123'
        mock_validate.return_value = True
        
        headers = _get_auth_headers()
        
        # Verify token is used
        self.assertEqual(headers['Authorization'], 'Bearer valid_token_123')
        
        # Verify login was NOT called
        mock_login.assert_not_called()
        
        # Verify validate was called once
        mock_validate.assert_called_once_with('valid_token_123')
    
    @patch('api_utils._validate_token')
    @patch('api_utils.login')
    @patch('api_utils.load_dotenv')
    @patch('api_utils.env_path')
    @patch('api_utils.os.getenv')
    def test_get_auth_headers_refreshes_invalid_token(self, mock_getenv, mock_env_path, 
                                                       mock_load_dotenv, mock_login, mock_validate):
        """Test that _get_auth_headers logs in when token is invalid."""
        from api_utils import _get_auth_headers
        
        # Mock environment: first call has invalid token, second call has new token
        token_calls = ['invalid_token_old', 'new_valid_token']
        mock_getenv.side_effect = token_calls
        
        # Mock validation: first call returns False (invalid), validate is not called again
        mock_validate.return_value = False
        
        # Mock successful login
        mock_login.return_value = True
        
        # Mock that .env file exists
        mock_env_path.exists.return_value = True
        
        headers = _get_auth_headers()
        
        # Verify login WAS called
        mock_login.assert_called_once()
        
        # Verify validation was called once for the invalid token
        mock_validate.assert_called_once_with('invalid_token_old')
        
        # Verify new token is used
        self.assertEqual(headers['Authorization'], 'Bearer new_valid_token')


class TestProgressTracking(unittest.TestCase):
    """Test detailed progress tracking functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.progress_file = Path(self.temp_dir) / 'test_progress.json'
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_progress_update_with_steps(self):
        """Test that progress update includes step information."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            from stream_checker_service import StreamCheckerProgress
            
            progress = StreamCheckerProgress(self.progress_file)
            
            # Update with step information
            progress.update(
                channel_id=1,
                channel_name='Test Channel',
                current=5,
                total=10,
                current_stream='Stream 5',
                status='analyzing',
                step='Analyzing stream quality',
                step_detail='Checking bitrate, resolution, codec (5/10)'
            )
            
            # Read back the progress
            progress_data = progress.get()
            
            # Verify all fields are present
            self.assertEqual(progress_data['channel_id'], 1)
            self.assertEqual(progress_data['channel_name'], 'Test Channel')
            self.assertEqual(progress_data['current_stream'], 5)
            self.assertEqual(progress_data['total_streams'], 10)
            self.assertEqual(progress_data['percentage'], 50.0)
            self.assertEqual(progress_data['current_stream_name'], 'Stream 5')
            self.assertEqual(progress_data['status'], 'analyzing')
            self.assertEqual(progress_data['step'], 'Analyzing stream quality')
            self.assertEqual(progress_data['step_detail'], 'Checking bitrate, resolution, codec (5/10)')
    
    def test_progress_update_without_steps(self):
        """Test that progress update works without step information (backward compatibility)."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            from stream_checker_service import StreamCheckerProgress
            
            progress = StreamCheckerProgress(self.progress_file)
            
            # Update without step information
            progress.update(
                channel_id=1,
                channel_name='Test Channel',
                current=5,
                total=10,
                current_stream='Stream 5',
                status='checking'
            )
            
            # Read back the progress
            progress_data = progress.get()
            
            # Verify basic fields are present
            self.assertEqual(progress_data['channel_id'], 1)
            self.assertEqual(progress_data['status'], 'checking')
            # Step fields should be empty strings
            self.assertEqual(progress_data['step'], '')
            self.assertEqual(progress_data['step_detail'], '')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
