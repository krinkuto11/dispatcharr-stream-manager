#!/usr/bin/env python3
"""
Unit test to verify that global channel checks don't stack up multiple times.

This test verifies that the fix for the global check stacking issue works correctly
by ensuring that mark_global_check() is called after queueing channels.
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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stream_checker_service import (
    StreamCheckerService,
    ChannelUpdateTracker,
    StreamCheckConfig
)


class TestGlobalCheckNoStacking(unittest.TestCase):
    """Test that global checks don't stack up multiple times."""
    
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
    
    def test_mark_global_check_called_after_queueing(self):
        """Test that mark_global_check() is called after _queue_all_channels()."""
        # Create service with test config
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock the _queue_all_channels method
            service._queue_all_channels = Mock()
            
            # Set the scheduled time to current time
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            
            # Ensure last global check is old (more than a day ago)
            old_timestamp = (now - timedelta(days=2)).isoformat()
            service.update_tracker.updates['last_global_check'] = old_timestamp
            
            # Call _check_global_schedule
            service._check_global_schedule()
            
            # Verify _queue_all_channels was called
            service._queue_all_channels.assert_called_once()
            
            # Verify mark_global_check was called (last_global_check should be updated)
            last_check = service.update_tracker.get_last_global_check()
            self.assertIsNotNone(last_check)
            
            # Verify the timestamp is recent (within last minute)
            last_check_time = datetime.fromisoformat(last_check)
            time_diff = abs((now - last_check_time).total_seconds())
            self.assertLess(time_diff, 60, "mark_global_check should have been called with current timestamp")
    
    def test_no_duplicate_queueing_in_time_window(self):
        """Test that channels are not queued multiple times within the time window."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock the _queue_all_channels method to track calls
            queue_all_calls = []
            original_queue_all = service._queue_all_channels
            
            def mock_queue_all():
                queue_all_calls.append(datetime.now())
                # Don't actually queue, just mark
                service.update_tracker.mark_global_check()
            
            service._queue_all_channels = Mock(side_effect=mock_queue_all)
            
            # Set the scheduled time to current time
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            
            # Ensure last global check is old
            old_timestamp = (now - timedelta(days=2)).isoformat()
            service.update_tracker.updates['last_global_check'] = old_timestamp
            
            # Call _check_global_schedule multiple times (simulating scheduler loop)
            for i in range(5):
                service._check_global_schedule()
            
            # Verify _queue_all_channels was called only ONCE
            self.assertEqual(len(queue_all_calls), 1, 
                           f"Expected 1 call to _queue_all_channels, got {len(queue_all_calls)}")
    
    def test_global_check_respects_daily_limit(self):
        """Test that global check only runs once per day."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock the _queue_all_channels method
            service._queue_all_channels = Mock()
            
            # Set the scheduled time to current time
            now = datetime.now()
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'hour': now.hour,
                    'minute': now.minute
                }
            })
            
            # Set last global check to 12 hours ago (same day)
            recent_timestamp = (now - timedelta(hours=12)).isoformat()
            service.update_tracker.updates['last_global_check'] = recent_timestamp
            
            # Call _check_global_schedule
            service._check_global_schedule()
            
            # Verify _queue_all_channels was NOT called (too recent)
            service._queue_all_channels.assert_not_called()
    
    def test_tracker_mark_global_check_updates_timestamp(self):
        """Test that ChannelUpdateTracker.mark_global_check updates the timestamp."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker(self.tracker_file)
            
            # Get timestamp before marking
            before_time = datetime.now()
            
            # Mark global check
            tracker.mark_global_check()
            
            # Get timestamp after marking
            last_check = tracker.get_last_global_check()
            self.assertIsNotNone(last_check)
            
            # Verify timestamp is recent
            last_check_time = datetime.fromisoformat(last_check)
            time_diff = abs((before_time - last_check_time).total_seconds())
            self.assertLess(time_diff, 5, "Timestamp should be within 5 seconds of now")
    
    def test_tracker_mark_global_check_preserves_needs_check_flags(self):
        """Test that mark_global_check preserves needs_check flags (only updates timestamp)."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker(self.tracker_file)
            
            # Mark some channels as needing check
            tracker.mark_channel_updated(1)
            tracker.mark_channel_updated(2)
            tracker.mark_channel_updated(3)
            
            # Verify they need checking
            channels_needing_check = tracker.get_channels_needing_check()
            self.assertEqual(len(channels_needing_check), 3)
            
            # Mark global check (this just updates the timestamp, doesn't clear flags)
            tracker.mark_global_check()
            
            # Verify needs_check flags are preserved (channels queued but not yet checked)
            channels_needing_check = tracker.get_channels_needing_check()
            self.assertEqual(len(channels_needing_check), 3, 
                           "needs_check flags should be preserved after global check is initiated")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
