#!/usr/bin/env python3
"""
Unit tests for pipeline mode functionality.

Tests the different pipeline modes and their behaviors:
- Pipeline 1: Update → Match → Check (with 2hr immunity)
- Pipeline 1.5: Pipeline 1 + Scheduled Global Action
- Pipeline 2: Update → Match only (no checking)
- Pipeline 2.5: Pipeline 2 + Scheduled Global Action
- Pipeline 3: Only Scheduled Global Action
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


class TestPipelineModes(unittest.TestCase):
    """Test different pipeline mode behaviors."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_pipeline_mode_in_default_config(self):
        """Test that pipeline_mode is in default configuration."""
        config = StreamCheckConfig.DEFAULT_CONFIG
        self.assertIn('pipeline_mode', config)
        self.assertEqual(config['pipeline_mode'], 'pipeline_1_5')
    
    def test_pipeline_1_checks_on_update(self):
        """Test that Pipeline 1 checks channels on M3U update."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_1'})
            
            # Mock the queue and tracker
            service.check_queue.add_channels = Mock(return_value=2)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            
            # Trigger check for updated channels
            service._queue_updated_channels()
            
            # Verify channels were queued (Pipeline 1 checks on update)
            service.update_tracker.get_and_clear_channels_needing_check.assert_called_once()
            service.check_queue.add_channels.assert_called_once()
    
    def test_pipeline_2_skips_check_on_update(self):
        """Test that Pipeline 2 skips checking on M3U update."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_2'})
            
            # Mock the queue and tracker
            service.check_queue.add_channels = Mock(return_value=2)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            
            # Trigger check for updated channels
            service._queue_updated_channels()
            
            # Verify channels were NOT queued (Pipeline 2 skips checking)
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_pipeline_3_skips_check_on_update(self):
        """Test that Pipeline 3 skips checking on M3U update."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_3'})
            
            # Mock the queue and tracker
            service.check_queue.add_channels = Mock(return_value=2)
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            
            # Trigger check for updated channels
            service._queue_updated_channels()
            
            # Verify channels were NOT queued (Pipeline 3 only does scheduled checks)
            service.update_tracker.get_and_clear_channels_needing_check.assert_not_called()
            service.check_queue.add_channels.assert_not_called()
    
    def test_pipeline_1_5_has_scheduled_checks(self):
        """Test that Pipeline 1.5 runs scheduled global checks."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'pipeline_1_5'})
            
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
            
            # Verify global action was triggered
            service._perform_global_action.assert_called_once()
    
    def test_pipeline_1_no_scheduled_checks(self):
        """Test that Pipeline 1 (without .5) does NOT run scheduled checks."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
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
            
            # Set last check to yesterday
            service.update_tracker.updates['last_global_check'] = (now - timedelta(days=1)).isoformat()
            
            # Trigger global check schedule
            service._check_global_schedule()
            
            # Verify global action was NOT triggered (Pipeline 1 doesn't have scheduled checks)
            service._perform_global_action.assert_not_called()


class TestForceCheckBehavior(unittest.TestCase):
    """Test force_check flag behavior."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_force_check_flag_set_and_retrieved(self):
        """Test that force_check flag can be set and retrieved."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker()
            
            # Set force check for channel 1
            tracker.mark_channel_for_force_check(1)
            
            # Verify flag is set
            self.assertTrue(tracker.should_force_check(1))
            
            # Verify other channels don't have the flag
            self.assertFalse(tracker.should_force_check(2))
    
    def test_force_check_flag_cleared(self):
        """Test that force_check flag can be cleared."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker()
            
            # Set and then clear force check
            tracker.mark_channel_for_force_check(1)
            self.assertTrue(tracker.should_force_check(1))
            
            tracker.clear_force_check(1)
            self.assertFalse(tracker.should_force_check(1))
    
    def test_global_action_sets_force_check(self):
        """Test that queueing all channels with force_check sets the flag."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock fetch_data_from_url to return channels
            with patch('stream_checker_service.fetch_data_from_url') as mock_fetch:
                mock_fetch.return_value = [
                    {'id': 1, 'name': 'Channel 1'},
                    {'id': 2, 'name': 'Channel 2'}
                ]
                
                # Mock _get_base_url
                with patch('stream_checker_service._get_base_url', return_value='http://test:8000'):
                    # Queue all channels with force check
                    service._queue_all_channels(force_check=True)
                    
                    # Verify force check flags were set
                    self.assertTrue(service.update_tracker.should_force_check(1))
                    self.assertTrue(service.update_tracker.should_force_check(2))


class TestGlobalAction(unittest.TestCase):
    """Test global action functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_perform_global_action_calls_all_steps(self):
        """Test that _perform_global_action calls update, match, and queue steps."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock AutomatedStreamManager
            with patch('automated_stream_manager.AutomatedStreamManager') as MockManager:
                mock_manager = Mock()
                mock_manager.refresh_playlists.return_value = True
                mock_manager.discover_and_assign_streams.return_value = {'1': 5}
                MockManager.return_value = mock_manager
                
                # Mock _queue_all_channels
                service._queue_all_channels = Mock()
                
                # Perform global action
                service._perform_global_action()
                
                # Verify all steps were called
                mock_manager.refresh_playlists.assert_called_once()
                mock_manager.discover_and_assign_streams.assert_called_once()
                service._queue_all_channels.assert_called_once_with(force_check=True)
    
    def test_trigger_global_action_marks_timestamp(self):
        """Test that triggering global action marks the timestamp."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Mock _perform_global_action
            service._perform_global_action = Mock()
            
            # Get timestamp before trigger
            before = datetime.now()
            
            # Trigger global action
            success = service.trigger_global_action()
            
            # Get timestamp after trigger
            after = datetime.now()
            
            # Verify success
            self.assertTrue(success)
            
            # Verify global check was marked
            last_check = service.update_tracker.get_last_global_check()
            self.assertIsNotNone(last_check)
            
            # Verify timestamp is recent
            last_check_time = datetime.fromisoformat(last_check)
            self.assertGreaterEqual(last_check_time, before)
            self.assertLessEqual(last_check_time, after)


if __name__ == '__main__':
    unittest.main()
