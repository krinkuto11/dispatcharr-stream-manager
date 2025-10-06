#!/usr/bin/env python3
"""
Unit test to verify that global check schedule configuration can be properly saved and loaded.

This test verifies that users can configure the time (hour and minute) when the global
channel check runs, and that the configuration is properly persisted and loaded.
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import (
    StreamCheckerService,
    StreamCheckConfig
)


class TestGlobalCheckScheduleConfig(unittest.TestCase):
    """Test that global check schedule configuration is properly saved and loaded."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'stream_checker_config.json'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_config_has_schedule(self):
        """Test that default config includes global_check_schedule."""
        config = StreamCheckConfig.DEFAULT_CONFIG
        
        self.assertIn('global_check_schedule', config)
        self.assertIn('enabled', config['global_check_schedule'])
        self.assertIn('hour', config['global_check_schedule'])
        self.assertIn('minute', config['global_check_schedule'])
        
        # Check default values exist and are valid
        self.assertTrue(config['global_check_schedule']['enabled'])
        self.assertIsInstance(config['global_check_schedule']['hour'], int)
        self.assertGreaterEqual(config['global_check_schedule']['hour'], 0)
        self.assertLessEqual(config['global_check_schedule']['hour'], 23)
        self.assertIsInstance(config['global_check_schedule']['minute'], int)
        self.assertGreaterEqual(config['global_check_schedule']['minute'], 0)
        self.assertLessEqual(config['global_check_schedule']['minute'], 59)
    
    def test_custom_schedule_time_is_saved(self):
        """Test that custom schedule time is properly saved to config file."""
        # Create config with custom schedule
        custom_config = {
            'global_check_schedule': {
                'enabled': True,
                'hour': 14,  # 2 PM
                'minute': 30
            }
        }
        
        # Save to file
        with open(self.config_file, 'w') as f:
            json.dump(custom_config, f)
        
        # Load config
        config = StreamCheckConfig(config_file=self.config_file)
        
        # Verify custom values are loaded
        self.assertEqual(config.get('global_check_schedule.hour'), 14)
        self.assertEqual(config.get('global_check_schedule.minute'), 30)
        self.assertTrue(config.get('global_check_schedule.enabled'))
    
    def test_schedule_can_be_disabled(self):
        """Test that scheduled global check can be disabled."""
        custom_config = {
            'global_check_schedule': {
                'enabled': False,
                'hour': 3,
                'minute': 0
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(custom_config, f)
        
        config = StreamCheckConfig(config_file=self.config_file)
        
        self.assertFalse(config.get('global_check_schedule.enabled'))
    
    def test_update_schedule_via_update_config(self):
        """Test that schedule can be updated via update_config method."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Update schedule to different time
            updates = {
                'global_check_schedule': {
                    'enabled': True,
                    'hour': 22,  # 10 PM
                    'minute': 15
                }
            }
            
            service.update_config(updates)
            
            # Verify update was applied
            self.assertEqual(service.config.get('global_check_schedule.hour'), 22)
            self.assertEqual(service.config.get('global_check_schedule.minute'), 15)
    
    def test_schedule_time_respected_in_check(self):
        """Test that _check_global_schedule respects configured time."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock _queue_all_channels
            service._queue_all_channels = Mock()
            
            # Set schedule to current time
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            
            # Ensure no recent global check
            service.update_tracker.updates['last_global_check'] = None
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was called
            service._queue_all_channels.assert_called_once()
    
    def test_schedule_disabled_prevents_check(self):
        """Test that disabling schedule prevents automatic global check."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock _queue_all_channels
            service._queue_all_channels = Mock()
            
            # Set schedule to current time but disabled
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': False,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was NOT called (disabled)
            service._queue_all_channels.assert_not_called()
    
    def test_get_status_includes_schedule_config(self):
        """Test that get_status includes global_check_schedule configuration."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set custom schedule
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': 15,
                    'minute': 45
                }
            })
            
            # Get status
            status = service.get_status()
            
            # Verify schedule is included in config
            self.assertIn('config', status)
            self.assertIn('global_check_schedule', status['config'])
            self.assertEqual(status['config']['global_check_schedule']['hour'], 15)
            self.assertEqual(status['config']['global_check_schedule']['minute'], 45)
            self.assertTrue(status['config']['global_check_schedule']['enabled'])


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
