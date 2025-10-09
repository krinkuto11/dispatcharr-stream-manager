#!/usr/bin/env python3
"""
Unit test to verify that global check doesn't prematurely clear needs_check flags.

This test verifies that when a global check is initiated, channels that have
received updates (new streams) should still be marked as needing check even
after the global check is queued. The needs_check flag should only be cleared
when the channel is actually checked, not when it's queued.
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
)


class TestGlobalCheckPreservesNeedsCheck(unittest.TestCase):
    """Test that global check doesn't prematurely clear needs_check flags."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.tracker_file = Path(self.temp_dir) / 'test_tracker.json'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_global_check_preserves_needs_check_for_updated_channels(self):
        """Test that channels with new streams still need checking after global check is initiated."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker(self.tracker_file)
            
            # Simulate: Channel 1 was checked 1 hour ago with 3 streams
            one_hour_ago = datetime.now() - timedelta(hours=1)
            tracker.mark_channel_checked(
                channel_id=1,
                timestamp=one_hour_ago.isoformat(),
                stream_count=3,
                checked_stream_ids=[101, 102, 103]
            )
            
            # Simulate: 4 minutes ago, new streams were added to channel 1
            four_min_ago = datetime.now() - timedelta(minutes=4)
            tracker.mark_channel_updated(
                channel_id=1,
                timestamp=four_min_ago.isoformat(),
                stream_count=5  # 2 new streams added
            )
            
            # Verify channel needs checking due to new streams
            channels_before = tracker.get_channels_needing_check()
            self.assertEqual(len(channels_before), 1)
            self.assertIn(1, channels_before)
            
            # Now a global check is initiated
            # This should only update the timestamp, not clear needs_check flags
            tracker.mark_global_check()
            
            # CRITICAL: Channel 1 should STILL need checking because:
            # 1. It has new streams that haven't been analyzed yet
            # 2. It was only queued for checking, not actually checked
            # 3. The needs_check flag should only be cleared when actual checking completes
            channels_after = tracker.get_channels_needing_check()
            
            # This is the bug: currently mark_global_check clears ALL needs_check flags
            # It should NOT clear them - they should only be cleared when checked
            self.assertEqual(len(channels_after), 1, 
                           "Channel with new streams should still need checking after global check is initiated")
            self.assertIn(1, channels_after,
                        "Channel 1 with new streams should still be marked as needing check")
    
    def test_global_check_timestamp_updated_but_flags_preserved(self):
        """Test that mark_global_check updates timestamp but preserves needs_check flags."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker(self.tracker_file)
            
            # Mark multiple channels as needing check (simulating new streams)
            tracker.mark_channel_updated(1, stream_count=5)
            tracker.mark_channel_updated(2, stream_count=3)
            tracker.mark_channel_updated(3, stream_count=7)
            
            # Verify all need checking
            channels_before = tracker.get_channels_needing_check()
            self.assertEqual(len(channels_before), 3)
            
            # Get timestamp before global check
            last_global_before = tracker.get_last_global_check()
            self.assertIsNone(last_global_before)
            
            # Mark global check (simulating queue all channels)
            tracker.mark_global_check()
            
            # Verify timestamp was updated
            last_global_after = tracker.get_last_global_check()
            self.assertIsNotNone(last_global_after)
            
            # CRITICAL: Verify channels still need checking
            # They were queued but not yet actually checked
            channels_after = tracker.get_channels_needing_check()
            self.assertEqual(len(channels_after), 3,
                           "All channels should still need checking after global check is initiated")
            self.assertEqual(set(channels_after), set(channels_before),
                           "The same channels should still need checking")
    
    def test_needs_check_cleared_only_when_actually_checked(self):
        """Test that needs_check is only cleared when channel is actually checked."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            tracker = ChannelUpdateTracker(self.tracker_file)
            
            # Mark channel as needing check
            tracker.mark_channel_updated(1, stream_count=5)
            
            # Verify it needs checking
            self.assertEqual(len(tracker.get_channels_needing_check()), 1)
            
            # Global check is initiated (queued)
            tracker.mark_global_check()
            
            # Channel should STILL need checking (not yet processed from queue)
            self.assertEqual(len(tracker.get_channels_needing_check()), 1)
            
            # Now simulate the channel actually being checked
            tracker.mark_channel_checked(1, stream_count=5, checked_stream_ids=[101, 102, 103, 104, 105])
            
            # NOW the needs_check flag should be cleared
            self.assertEqual(len(tracker.get_channels_needing_check()), 0,
                           "Channel should not need checking after it was actually checked")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
