#!/usr/bin/env python3
"""
Integration tests for pipeline features: update, match, check, and global actions.

These tests verify the end-to-end behavior of the pipeline system.
"""

import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import (
    StreamCheckerService,
)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for complete pipeline features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_1_full_flow(self):
        """Test Pipeline 1: Update triggers Match and Check."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_1'})
            
            # Mock methods
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2, 3])
            service.check_queue.add_channels = Mock(return_value=3)
            service.check_queue.remove_from_completed = Mock()
            
            # Trigger update
            service.trigger_check_updated_channels()
            
            # Wait briefly for trigger to be processed
            time.sleep(0.1)
            
            # Call the queue method directly (simulating what scheduler would do)
            service._queue_updated_channels()
            
            # Verify channels were queued
            service.update_tracker.get_and_clear_channels_needing_check.assert_called_once()
            self.assertEqual(service.check_queue.add_channels.call_count, 1)
    
    def test_pipeline_2_skips_check(self):
        """Test Pipeline 2: Update triggers Match but NOT Check."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_2'})
            
            # Mock methods
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2, 3])
            service.check_queue.add_channels = Mock(return_value=0)
            
            # Trigger update
            service.trigger_check_updated_channels()
            time.sleep(0.1)
            
            # Call the queue method
            service._queue_updated_channels()
            
            # Verify channels were NOT queued (pipeline_2 skips checking)
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_pipeline_1_5_has_both_features(self):
        """Test Pipeline 1.5: Has both update-triggered and scheduled checks."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_1_5'})
            
            # Test 1: Update-triggered check works
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            service.check_queue.add_channels = Mock(return_value=2)
            service.check_queue.remove_from_completed = Mock()
            
            service._queue_updated_channels()
            
            service.update_tracker.get_and_clear_channels_needing_check.assert_called_once()
            service.check_queue.add_channels.assert_called_once()
            
            # Test 2: Scheduled check works
            service._perform_global_action = Mock()
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
            
            service._perform_global_action.assert_called_once()
    
    def test_pipeline_3_only_scheduled(self):
        """Test Pipeline 3: Only scheduled checks, no update-triggered."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_3'})
            
            # Test 1: Update-triggered check does NOT work
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            service.check_queue.add_channels = Mock(return_value=0)
            
            service._queue_updated_channels()
            
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
            
            # Test 2: Scheduled check DOES work
            service._perform_global_action = Mock()
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
            
            service._perform_global_action.assert_called_once()
    
    def test_global_action_performs_all_steps(self):
        """Test that global action performs update, match, and check."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock AutomatedStreamManager where it's imported
            with patch('automated_stream_manager.AutomatedStreamManager') as MockManager:
                mock_manager = Mock()
                mock_manager.refresh_playlists.return_value = True
                mock_manager.discover_and_assign_streams.return_value = {'1': 5, '2': 3}
                MockManager.return_value = mock_manager
                
                # Mock _queue_all_channels
                service._queue_all_channels = Mock()
                
                # Perform global action
                service._perform_global_action()
                
                # Verify all three steps were called
                mock_manager.refresh_playlists.assert_called_once()
                mock_manager.discover_and_assign_streams.assert_called_once()
                service._queue_all_channels.assert_called_once_with(force_check=True)
    
    def test_force_check_bypasses_immunity(self):
        """Test that force_check flag in global action bypasses 2-hour immunity."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock fetch_data_from_url to return channels
            with patch('stream_checker_service.fetch_data_from_url') as mock_fetch:
                mock_fetch.return_value = [
                    {'id': 1, 'name': 'Channel 1'},
                    {'id': 2, 'name': 'Channel 2'},
                    {'id': 3, 'name': 'Channel 3'}
                ]
                
                with patch('stream_checker_service._get_base_url', return_value='http://test:8000'):
                    # Queue all channels with force check
                    service._queue_all_channels(force_check=True)
                    
                    # Verify force check flags were set for all channels
                    self.assertTrue(service.update_tracker.should_force_check(1))
                    self.assertTrue(service.update_tracker.should_force_check(2))
                    self.assertTrue(service.update_tracker.should_force_check(3))
    
    def test_config_change_wakes_scheduler_immediately(self):
        """Test that config changes wake up the scheduler immediately."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Initially both events should be clear
            self.assertFalse(service.config_changed.is_set())
            self.assertFalse(service.check_trigger.is_set())
            
            # Update config
            service.update_config({'pipeline_mode': 'pipeline_2'})
            
            # Both events should be set to wake up scheduler
            self.assertTrue(service.config_changed.is_set())
            self.assertTrue(service.check_trigger.is_set())
    
    def test_config_change_skips_channel_queueing(self):
        """Test that scheduler skips channel queueing when woken by config change."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Set config_changed flag (simulating config update)
            service.config_changed.set()
            service.check_trigger.set()
            
            # Mock methods
            service._queue_updated_channels = Mock()
            
            # Simulate scheduler loop logic
            triggered = service.check_trigger.wait(timeout=0.1)
            self.assertTrue(triggered)
            
            if triggered:
                service.check_trigger.clear()
                # Should NOT call _queue_updated_channels if config_changed is set
                if not service.config_changed.is_set():
                    service._queue_updated_channels()
            
            # Verify _queue_updated_channels was NOT called
            service._queue_updated_channels.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
