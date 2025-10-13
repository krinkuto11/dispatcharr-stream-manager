#!/usr/bin/env python3
"""
Unit test to verify that global check schedule runs once per day after scheduled time.

This test verifies that the global check runs automatically when:
1. The service starts after the scheduled time
2. The check hasn't run today yet
3. The check doesn't run multiple times in the same day
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import (
    StreamCheckerService,
    ChannelUpdateTracker
)


class TestGlobalCheckRunsDaily(unittest.TestCase):
    """Test that global check runs once per day after scheduled time."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker_file = Path(self.temp_dir) / 'channel_updates.json'
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_runs_after_scheduled_time_on_same_day(self):
        """Test that check runs when current time is after scheduled time and hasn't run today."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service._perform_global_action = Mock()
            
            # Set schedule to earlier today (e.g., 9:00 AM)
            now = datetime.now()
            earlier_hour = max(0, now.hour - 2)  # 2 hours ago
            
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'frequency': 'daily',
                    'hour': earlier_hour,
                    'minute': 0
                }
            })
            
            # Ensure no check has run today
            service.update_tracker.updates['last_global_check'] = None
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was called since we're past scheduled time
            service._perform_global_action.assert_called_once()
    
    def test_does_not_run_before_scheduled_time(self):
        """Test that check does NOT run when current time is before scheduled time."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service._perform_global_action = Mock()
            
            # Set schedule to later today (e.g., 23:59)
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'frequency': 'daily',
                    'hour': 23,
                    'minute': 59
                }
            })
            
            # Ensure no check has run today
            service.update_tracker.updates['last_global_check'] = None
            
            # Call check (should not run since we're before scheduled time)
            service._check_global_schedule()
            
            # Verify queue was NOT called
            service._perform_global_action.assert_not_called()
    
    def test_does_not_run_twice_same_day(self):
        """Test that check does NOT run twice on the same day."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service._perform_global_action = Mock()
            
            # Set schedule to earlier today
            now = datetime.now()
            earlier_hour = max(0, now.hour - 2)
            
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'frequency': 'daily',
                    'hour': earlier_hour,
                    'minute': 0
                }
            })
            
            # Mark that check already ran today
            service.update_tracker.updates['last_global_check'] = now.isoformat()
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was NOT called (already ran today)
            service._perform_global_action.assert_not_called()
    
    def test_runs_if_last_check_was_yesterday(self):
        """Test that check runs if last check was yesterday."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service._perform_global_action = Mock()
            
            # Set schedule to earlier today
            now = datetime.now()
            earlier_hour = max(0, now.hour - 2)
            
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'frequency': 'daily',
                    'hour': earlier_hour,
                    'minute': 0
                }
            })
            
            # Mark that check ran yesterday
            yesterday = now - timedelta(days=1)
            service.update_tracker.updates['last_global_check'] = yesterday.isoformat()
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was called (new day)
            service._perform_global_action.assert_called_once()
    
    def test_monthly_check_runs_on_correct_day(self):
        """Test that monthly check runs on the correct day of month."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service._perform_global_action = Mock()
            
            # Set schedule to monthly on current day
            now = datetime.now()
            earlier_hour = max(0, now.hour - 2)
            
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'frequency': 'monthly',
                    'hour': earlier_hour,
                    'minute': 0,
                    'day_of_month': now.day
                }
            })
            
            # Mark that check ran last month
            last_month = now - timedelta(days=35)
            service.update_tracker.updates['last_global_check'] = last_month.isoformat()
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was called
            service._perform_global_action.assert_called_once()
    
    def test_monthly_check_does_not_run_on_wrong_day(self):
        """Test that monthly check does NOT run on wrong day of month."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service._perform_global_action = Mock()
            
            # Set schedule to monthly on a different day
            now = datetime.now()
            earlier_hour = max(0, now.hour - 2)
            different_day = 1 if now.day != 1 else 2
            
            service.config.update({
                'global_check_schedule': {
                    'enabled': True,
                    'frequency': 'monthly',
                    'hour': earlier_hour,
                    'minute': 0,
                    'day_of_month': different_day
                }
            })
            
            # Mark that check ran last month
            last_month = now - timedelta(days=35)
            service.update_tracker.updates['last_global_check'] = last_month.isoformat()
            
            # Call check
            service._check_global_schedule()
            
            # Verify queue was NOT called (wrong day)
            service._perform_global_action.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
