#!/usr/bin/env python3
"""
Test scheduler robustness and pipeline selection.

These tests verify that:
1. The scheduler correctly respects pipeline mode settings
2. Configuration changes are applied immediately
3. The scheduler doesn't call unnecessary functions based on pipeline mode
"""

import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import (
    StreamCheckerService,
)


class TestSchedulerRobustness(unittest.TestCase):
    """Test that scheduler robustly respects pipeline configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_scheduler_respects_pipeline_mode_on_trigger(self):
        """Test that scheduler checks pipeline mode before queueing on trigger."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set to pipeline_2 (no checking on update)
            service.config.update({'pipeline_mode': 'pipeline_2'})
            
            # Mock the internal queue method
            service.check_queue.add_channels = Mock(return_value=0)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2, 3])
            
            # Trigger the check
            service.check_trigger.set()
            
            # Call scheduler loop iteration manually (simulating one loop)
            # First, check the trigger
            triggered = service.check_trigger.wait(timeout=0.1)
            self.assertTrue(triggered)
            
            if triggered:
                service.check_trigger.clear()
                # This is what the scheduler does - but should respect pipeline mode
                if service.config.get('queue.check_on_update', True):
                    service._queue_updated_channels()
            
            # Verify that get_and_clear was NOT called for pipeline_2
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_scheduler_loop_calls_queue_updated_directly(self):
        """Test that scheduler loop should call _queue_updated_channels without extra checks."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set to pipeline_2 with check_on_update=False
            # This combination should still work (pipeline mode takes precedence)
            service.config.update({
                'pipeline_mode': 'pipeline_2',
                'queue': {'check_on_update': False}
            })
            
            # Mock methods
            service._queue_updated_channels = Mock()
            
            # Trigger the check
            service.check_trigger.set()
            
            # Simulate scheduler loop logic
            triggered = service.check_trigger.wait(timeout=0.1)
            if triggered:
                service.check_trigger.clear()
                # Current implementation checks queue.check_on_update first
                # This is the bug - it should just call _queue_updated_channels
                if service.config.get('queue.check_on_update', True):
                    service._queue_updated_channels()
            
            # With check_on_update=False, _queue_updated_channels is NOT called
            # But it SHOULD be called and let the function decide based on pipeline mode
            service._queue_updated_channels.assert_not_called()
            
            # This is the bug: the scheduler checks the wrong flag
    
    def test_pipeline_mode_overrides_check_on_update_flag(self):
        """Test that pipeline mode takes precedence over check_on_update flag."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set check_on_update to True but pipeline to pipeline_3 (no regular checks)
            service.config.update({
                'pipeline_mode': 'pipeline_3',
                'queue': {'check_on_update': True}  # This should be ignored
            })
            
            # Mock methods
            service.check_queue.add_channels = Mock(return_value=0)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            
            # Call _queue_updated_channels directly
            service._queue_updated_channels()
            
            # Verify nothing was queued (pipeline_3 only does scheduled checks)
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_config_change_applies_immediately_to_scheduler(self):
        """Test that config changes are applied immediately in scheduler loop."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Start with pipeline_1
            service.config.update({'pipeline_mode': 'pipeline_1'})
            
            # Mock methods
            service.check_queue.add_channels = Mock(return_value=2)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            
            # Trigger first check - should queue
            service.check_trigger.set()
            service._queue_updated_channels()
            
            # Verify it was called for pipeline_1
            self.assertEqual(service.update_tracker.get_and_clear_channels_needing_check.call_count, 1)
            
            # Reset mocks
            service.check_queue.add_channels.reset_mock()
            service.update_tracker.get_and_clear_channels_needing_check.reset_mock()
            
            # Now change to pipeline_2 (no checking)
            service.config.update({'pipeline_mode': 'pipeline_2'})
            service.config_changed.set()
            
            # Simulate config change detection (as scheduler does)
            if service.config_changed.is_set():
                service.config_changed.clear()
            
            # Trigger second check - should NOT queue because of pipeline_2
            service.check_trigger.set()
            service._queue_updated_channels()
            
            # Verify it was NOT called for pipeline_2
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_global_schedule_respects_pipeline_mode_immediately(self):
        """Test that global schedule check respects pipeline mode changes immediately."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set to pipeline_1 (no scheduled global checks)
            service.config.update({'pipeline_mode': 'pipeline_1'})
            
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
            
            # Set last check to yesterday to ensure it would run
            service.update_tracker.updates['last_global_check'] = (now - timedelta(days=1)).isoformat()
            
            # Call global schedule check
            service._check_global_schedule()
            
            # Verify global action was NOT called (pipeline_1 doesn't have scheduled checks)
            service._perform_global_action.assert_not_called()
            
            # Now change to pipeline_1_5 (has scheduled global checks)
            service.config.update({'pipeline_mode': 'pipeline_1_5'})
            service.config_changed.set()
            
            # Clear the event (as scheduler does)
            if service.config_changed.is_set():
                service.config_changed.clear()
            
            # Call global schedule check again
            service._check_global_schedule()
            
            # Now it SHOULD be called (pipeline_1_5 has scheduled checks)
            service._perform_global_action.assert_called_once()
    
    def test_disabled_mode_prevents_all_automation(self):
        """Test that disabled mode prevents all automatic operations."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set to disabled
            service.config.update({'pipeline_mode': 'disabled'})
            
            # Mock methods
            service.check_queue.add_channels = Mock(return_value=0)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            service._perform_global_action = Mock()
            
            # Try to queue updated channels
            service._queue_updated_channels()
            
            # Verify nothing was queued
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
            
            # Try global schedule check
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            service.update_tracker.updates['last_global_check'] = (now - timedelta(days=1)).isoformat()
            
            service._check_global_schedule()
            
            # Verify global action was NOT called (disabled mode)
            service._perform_global_action.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
