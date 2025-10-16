#!/usr/bin/env python3
"""
Unit test to verify that queue logging accurately reports the number of channels added.

This test verifies the fix for the logging inconsistency where:
- "Added X/Y channels to checking queue" (from add_channels)
- "Queued Y channels for global check" (from _queue_all_channels)

The second log should report the actual number added, not the total attempted.
"""

import unittest
import tempfile
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import (
    StreamCheckerService,
    StreamCheckQueue
)


class TestQueueLoggingAccuracy(unittest.TestCase):
    """Test that queue logging accurately reports channels added."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_channels_returns_actual_count(self):
        """Test that add_channels returns the actual number of channels added."""
        queue = StreamCheckQueue(max_size=10)
        
        # Add 5 channels
        channel_ids = [1, 2, 3, 4, 5]
        added = queue.add_channels(channel_ids, priority=5)
        
        # Should add all 5
        self.assertEqual(added, 5)
        
        # Try to add the same channels again
        added_again = queue.add_channels(channel_ids, priority=5)
        
        # Should add 0 since they're already in queue or completed
        self.assertEqual(added_again, 0)
    
    def test_add_channels_skips_already_queued(self):
        """Test that add_channels correctly skips already queued channels."""
        queue = StreamCheckQueue(max_size=10)
        
        # Add initial set of channels
        initial_channels = [1, 2, 3, 4, 5]
        added_first = queue.add_channels(initial_channels, priority=5)
        self.assertEqual(added_first, 5)
        
        # Try to add overlapping set (3 already queued, 2 new)
        overlapping_channels = [4, 5, 6, 7]
        added_second = queue.add_channels(overlapping_channels, priority=5)
        
        # Should only add the 2 new channels (6, 7)
        self.assertEqual(added_second, 2)
    
    def test_queue_all_channels_logs_actual_count(self):
        """Test that _queue_all_channels logs the actual number of channels added."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock the API calls
            mock_channels = [
                {'id': 1, 'name': 'Channel 1'},
                {'id': 2, 'name': 'Channel 2'},
                {'id': 3, 'name': 'Channel 3'}
            ]
            
            with patch('stream_checker_service.fetch_data_from_url', return_value=mock_channels):
                # Pre-queue one channel to simulate it being already in queue
                service.check_queue.add_channel(1, priority=5)
                
                # Capture log output (use root logger since stream_checker_service uses logging.basicConfig)
                with self.assertLogs(level='INFO') as log_context:
                    service._queue_all_channels(force_check=False)
                
                # Find the log message about queueing
                queue_log = None
                for log_msg in log_context.output:
                    if 'Queued' in log_msg and 'channels for global check' in log_msg:
                        queue_log = log_msg
                        break
                
                self.assertIsNotNone(queue_log, "Should have a log message about queueing channels")
                
                # The log should say "Queued 2/3 channels" (since 1 was already queued)
                # or similar format showing actual vs total
                self.assertIn('/3 channels for global check', queue_log,
                            "Log should show actual added count vs total count")
                self.assertIn('Queued 2/3', queue_log,
                            "Should show 2 channels added out of 3 total")
    
    def test_queue_all_channels_batching_tracks_total(self):
        """Test that _queue_all_channels correctly tracks total across batches."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Set max_channels_per_run to 2 to force batching
            service.config.config['queue']['max_channels_per_run'] = 2
            
            # Mock 5 channels (will be processed in 3 batches: 2, 2, 1)
            mock_channels = [
                {'id': i, 'name': f'Channel {i}'} for i in range(1, 6)
            ]
            
            with patch('stream_checker_service.fetch_data_from_url', return_value=mock_channels):
                # Pre-queue channel 3 to test that it's skipped in batch 2
                service.check_queue.add_channel(3, priority=5)
                
                # Capture log output (use root logger since stream_checker_service uses logging.basicConfig)
                with self.assertLogs(level='INFO') as log_context:
                    service._queue_all_channels(force_check=False)
                
                # Find the summary log (last one about queueing)
                queue_log = None
                for log_msg in reversed(log_context.output):
                    if 'Queued' in log_msg and 'channels for global check' in log_msg:
                        queue_log = log_msg
                        break
                
                self.assertIsNotNone(queue_log, "Should have a summary log about queueing channels")
                
                # Should show 4/5 (skipped channel 3 which was already queued)
                self.assertIn('Queued 4/5', queue_log,
                            "Should track total across all batches and show 4 added out of 5")
    
    def test_queue_all_channels_removes_from_completed_set(self):
        """Test that _queue_all_channels removes channels from completed set before queueing."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            
            # Mock 3 channels
            mock_channels = [
                {'id': i, 'name': f'Channel {i}'} for i in range(1, 4)
            ]
            
            with patch('stream_checker_service.fetch_data_from_url', return_value=mock_channels):
                # Simulate channels being completed (fully processed through the queue)
                for ch_id in [1, 2, 3]:
                    # Add to queue
                    service.check_queue.add_channel(ch_id, priority=5)
                    # Get from queue (moves to in_progress)
                    service.check_queue.get_next_channel()
                    # Mark as completed
                    service.check_queue.mark_completed(ch_id)
                
                # Verify they're in completed set
                self.assertIn(1, service.check_queue.completed)
                self.assertIn(2, service.check_queue.completed)
                self.assertIn(3, service.check_queue.completed)
                
                # Capture log output
                with self.assertLogs(level='INFO') as log_context:
                    service._queue_all_channels(force_check=True)
                
                # Find the summary log
                queue_log = None
                for log_msg in reversed(log_context.output):
                    if 'Queued' in log_msg and 'channels for global check' in log_msg:
                        queue_log = log_msg
                        break
                
                self.assertIsNotNone(queue_log, "Should have a summary log about queueing channels")
                
                # Should show 3/3 (all channels should be queued after removing from completed set)
                self.assertIn('Queued 3/3', queue_log,
                            "Should queue all 3 channels after removing them from completed set")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
