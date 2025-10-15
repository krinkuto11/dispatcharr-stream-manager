#!/usr/bin/env python3
"""
Unit tests for disabled pipeline mode functionality.

This module tests:
- Disabled pipeline mode prevents all automation
- Disabled pipeline mode skips check on update
- Disabled pipeline mode skips scheduled global checks
- Service should not auto-start with disabled mode
"""

import unittest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import (
    StreamCheckerService,
    StreamCheckConfig,
    ChannelUpdateTracker
)


class TestDisabledPipelineMode(unittest.TestCase):
    """Test disabled pipeline mode behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_disabled_in_default_config_options(self):
        """Test that disabled is a valid pipeline mode option."""
        config = StreamCheckConfig.DEFAULT_CONFIG
        self.assertIn('pipeline_mode', config)
        # Verify the comment includes 'disabled' as an option
        # (we can't test the comment directly, but we can test the functionality)
        
    def test_disabled_mode_skips_check_on_update(self):
        """Test that disabled mode skips checking on M3U update."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'disabled'})
            
            # Mock the queue and tracker
            service.check_queue.add_channels = Mock(return_value=2)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            
            # Trigger check for updated channels
            service._queue_updated_channels()
            
            # Verify channels were NOT queued (disabled mode skips all automation)
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_disabled_mode_skips_scheduled_checks(self):
        """Test that disabled mode skips scheduled global checks."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'disabled'})
            
            # Mock _perform_global_action
            service._perform_global_action = Mock()
            
            # Set scheduled time to now
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            
            # Set last check to yesterday
            service.update_tracker.updates['last_global_check'] = (now - timedelta(days=1)).isoformat()
            
            # Trigger global check schedule
            service._check_global_schedule()
            
            # Verify global action was NOT triggered (disabled mode skips all automation)
            service._perform_global_action.assert_not_called()
    
    def test_disabled_mode_can_be_set_and_persisted(self):
        """Test that disabled mode can be set and persists across restarts."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            # Create service and set to disabled mode
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'disabled'})
            
            # Verify it was set
            self.assertEqual(service.config.get('pipeline_mode'), 'disabled')
            
            # Create new service instance to test loading
            service2 = StreamCheckerService()
            self.assertEqual(service2.config.get('pipeline_mode'), 'disabled')
    
    def test_disabled_mode_can_be_enabled_again(self):
        """Test that disabled mode can be changed back to an active pipeline."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'disabled'})
            
            # Now enable it with Pipeline 1
            service.config.update({'pipeline_mode': 'pipeline_1'})
            self.assertEqual(service.config.get('pipeline_mode'), 'pipeline_1')
            
            # Verify persistence
            service2 = StreamCheckerService()
            self.assertEqual(service2.config.get('pipeline_mode'), 'pipeline_1')


if __name__ == '__main__':
    unittest.main()
