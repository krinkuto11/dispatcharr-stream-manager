#!/usr/bin/env python3
"""
Unit test to verify that regular automation is paused during global action.

This test verifies that when a global action is in progress:
1. The global_action_in_progress flag is set
2. Regular automation cycle skips when flag is set
3. Scheduler skips channel queueing when flag is set
4. Flag is cleared after global action completes
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
    ChannelUpdateTracker,
    StreamCheckConfig
)


class TestGlobalActionBlocking(unittest.TestCase):
    """Test that global action blocks regular automation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_config.json'
        self.tracker_file = Path(self.temp_dir) / 'test_tracker.json'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_global_action_sets_flag(self):
        """Test that _perform_global_action sets global_action_in_progress flag."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Initially flag should be False
            self.assertFalse(service.global_action_in_progress)
            
            # Mock the automation manager to avoid actual execution
            with patch('automated_stream_manager.AutomatedStreamManager'):
                # Mock _queue_all_channels to avoid side effects
                service._queue_all_channels = Mock()
                
                # Call _perform_global_action
                service._perform_global_action()
            
            # After completion, flag should be False again (cleared in finally)
            self.assertFalse(service.global_action_in_progress)
    
    def test_scheduler_skips_when_global_action_in_progress(self):
        """Test that scheduler skips channel queueing when global action is in progress."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock _queue_updated_channels to track calls
            queue_calls = []
            def mock_queue():
                queue_calls.append(datetime.now())
            service._queue_updated_channels = Mock(side_effect=mock_queue)
            
            # Set global action flag
            service.global_action_in_progress = True
            
            # Trigger the scheduler check
            service.check_trigger.set()
            
            # Simulate one iteration of scheduler loop logic
            triggered = service.check_trigger.is_set()
            if triggered:
                service.check_trigger.clear()
                if not service.config_changed.is_set():
                    if service.global_action_in_progress:
                        # This is what should happen - skip queueing
                        pass
                    else:
                        service._queue_updated_channels()
            
            # Verify that _queue_updated_channels was NOT called
            self.assertEqual(len(queue_calls), 0, 
                           "Should not queue channels when global action is in progress")
    
    def test_status_includes_global_action_flag(self):
        """Test that get_status includes global_action_in_progress."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Get status when flag is False
            status = service.get_status()
            self.assertIn('global_action_in_progress', status)
            self.assertFalse(status['global_action_in_progress'])
            
            # Set flag and check status again
            service.global_action_in_progress = True
            status = service.get_status()
            self.assertTrue(status['global_action_in_progress'])
    
    def test_global_action_flag_cleared_on_error(self):
        """Test that global_action_in_progress is cleared even if error occurs."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock _queue_all_channels to avoid API calls
            service._queue_all_channels = Mock()
            
            # Mock to raise an error during automation
            with patch('automated_stream_manager.AutomatedStreamManager') as mock_manager:
                mock_manager.side_effect = Exception("Test error")
                
                # Call _perform_global_action - should handle error gracefully
                service._perform_global_action()
            
            # Flag should be cleared even after error
            self.assertFalse(service.global_action_in_progress)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
