#!/usr/bin/env python3
"""
Validation tests for the specific requirements in the problem statement.

These tests explicitly verify:
1. Scheduler respects pipeline selection
2. Configuration changes work without restart
3. Pipeline features (update, match, check, global) are correctly performed
4. Configuration changes apply immediately
"""

import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import StreamCheckerService


class TestRequirementsValidation(unittest.TestCase):
    """Validation of explicit requirements from problem statement."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_requirement_1_scheduler_respects_pipeline_selection(self):
        """
        REQUIREMENT: "doesn't respect the pipeline selection"
        
        Verify that the scheduler properly respects all pipeline modes:
        - Pipeline 1: Checks on update
        - Pipeline 2: No checking on update
        - Pipeline 3: Only scheduled checks
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Test Pipeline 1: Should check on update
            service.config.update({'pipeline_mode': 'pipeline_1'})
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            service.check_queue.add_channels = Mock(return_value=2)
            service.check_queue.remove_from_completed = Mock()
            
            service._queue_updated_channels()
            self.assertTrue(service.update_tracker.get_and_clear_channels_needing_check.called,
                          "Pipeline 1 should queue channels on update")
            
            # Reset mocks
            service.update_tracker.get_and_clear_channels_needing_check.reset_mock()
            service.check_queue.add_channels.reset_mock()
            
            # Test Pipeline 2: Should NOT check on update
            service.config.update({'pipeline_mode': 'pipeline_2'})
            service._queue_updated_channels()
            self.assertFalse(service.update_tracker.get_and_clear_channels_needing_check.called,
                           "Pipeline 2 should NOT queue channels on update")
            
            # Test Pipeline 3: Should NOT check on update
            service.config.update({'pipeline_mode': 'pipeline_3'})
            service._queue_updated_channels()
            self.assertFalse(service.update_tracker.get_and_clear_channels_needing_check.called,
                           "Pipeline 3 should NOT queue channels on update")
    
    def test_requirement_2_config_changes_without_restart(self):
        """
        REQUIREMENT: "doesn't respect configuration changes through the UI without a restart"
        
        Verify that configuration changes work without restarting the service.
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True  # Simulate running service
            
            # Change pipeline mode while running
            initial_mode = service.config.get('pipeline_mode')
            new_mode = 'pipeline_2' if initial_mode != 'pipeline_2' else 'pipeline_1'
            
            service.update_config({'pipeline_mode': new_mode})
            
            # Verify config was updated in memory
            self.assertEqual(service.config.get('pipeline_mode'), new_mode,
                           "Config should update without restart")
            
            # Verify config_changed event was set
            self.assertTrue(service.config_changed.is_set(),
                          "config_changed event should be set")
    
    def test_requirement_3_pipeline_features_update_match_check(self):
        """
        REQUIREMENT: "pipelines' features: update, match and check ... are correctly performed"
        
        Verify that all pipeline features work correctly:
        - Update: M3U playlist refresh
        - Match: Stream to channel matching
        - Check: Channel stream quality checking
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Test that _perform_global_action calls all three features
            with patch('automated_stream_manager.AutomatedStreamManager') as MockManager:
                mock_manager = Mock()
                mock_manager.refresh_playlists.return_value = True  # UPDATE
                mock_manager.discover_and_assign_streams.return_value = {'1': 2}  # MATCH
                MockManager.return_value = mock_manager
                
                service._queue_all_channels = Mock()  # CHECK
                
                service._perform_global_action()
                
                # Verify UPDATE was called
                mock_manager.refresh_playlists.assert_called_once()
                
                # Verify MATCH was called
                mock_manager.discover_and_assign_streams.assert_called_once()
                
                # Verify CHECK was called (via _queue_all_channels)
                service._queue_all_channels.assert_called_once()
    
    def test_requirement_4_global_variant_features(self):
        """
        REQUIREMENT: "(and the global variant) are correctly performed"
        
        Verify that global action performs complete update, match, and check cycle.
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            with patch('automated_stream_manager.AutomatedStreamManager') as MockManager:
                mock_manager = Mock()
                mock_manager.refresh_playlists.return_value = True
                mock_manager.discover_and_assign_streams.return_value = {'1': 5}
                MockManager.return_value = mock_manager
                
                service._queue_all_channels = Mock()
                
                # Perform global action
                service._perform_global_action()
                
                # Verify all three steps of global action
                mock_manager.refresh_playlists.assert_called_once()
                mock_manager.discover_and_assign_streams.assert_called_once()
                service._queue_all_channels.assert_called_once_with(force_check=True)
    
    def test_requirement_5_config_changes_apply_immediately(self):
        """
        REQUIREMENT: "effects of that change are applied immediately"
        
        Verify that configuration changes are applied immediately,
        not on the next service restart.
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Update config
            service.update_config({'pipeline_mode': 'pipeline_3'})
            
            # Verify scheduler is woken up immediately
            self.assertTrue(service.check_trigger.is_set(),
                          "check_trigger should be set to wake scheduler")
            
            # Simulate scheduler waking up and checking config
            service.check_trigger.wait(timeout=0.1)
            
            # Config should already be applied
            self.assertEqual(service.config.get('pipeline_mode'), 'pipeline_3',
                           "Config should be applied immediately")
    
    def test_requirement_6_scheduler_reset_on_config_change(self):
        """
        REQUIREMENT: "configuration changes reset the scheduler"
        
        Verify that the scheduler properly resets/responds when config changes.
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Initially, events should be clear
            self.assertFalse(service.config_changed.is_set())
            
            # Update config
            service.update_config({'pipeline_mode': 'pipeline_2'})
            
            # Scheduler should be signaled to reset/wake up
            self.assertTrue(service.config_changed.is_set(),
                          "config_changed should signal scheduler")
            self.assertTrue(service.check_trigger.is_set(),
                          "check_trigger should wake scheduler immediately")
    
    def test_requirement_complete_workflow(self):
        """
        Complete workflow test: Change pipeline mode and verify it takes effect immediately.
        
        This test validates the entire requirement chain:
        1. Config changes work without restart
        2. Scheduler respects new pipeline mode
        3. Changes apply immediately
        """
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.running = True
            
            # Start with pipeline_1 (checks on update)
            service.config.update({'pipeline_mode': 'pipeline_1'})
            
            # Mock methods
            service.update_tracker.get_and_clear_channels_needing_check = Mock(return_value=[1, 2])
            service.check_queue.add_channels = Mock(return_value=2)
            service.check_queue.remove_from_completed = Mock()
            
            # Verify pipeline_1 queues channels
            service._queue_updated_channels()
            self.assertTrue(service.update_tracker.get_and_clear_channels_needing_check.called)
            
            # Reset mocks
            service.update_tracker.get_and_clear_channels_needing_check.reset_mock()
            service.check_queue.add_channels.reset_mock()
            
            # NOW: Change to pipeline_2 (no checking on update) WITHOUT RESTART
            service.update_config({'pipeline_mode': 'pipeline_2'})
            
            # Clear the events (simulating scheduler processing them)
            service.config_changed.clear()
            service.check_trigger.clear()
            
            # Verify pipeline_2 does NOT queue channels (immediate effect)
            service._queue_updated_channels()
            self.assertFalse(service.update_tracker.get_and_clear_channels_needing_check.called,
                           "Pipeline 2 should NOT queue (immediate effect of config change)")


if __name__ == '__main__':
    unittest.main(verbosity=2)
