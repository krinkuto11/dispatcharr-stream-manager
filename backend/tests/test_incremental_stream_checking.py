#!/usr/bin/env python3
"""
Unit test to verify incremental stream checking for channels with new streams.

This test verifies that when new streams are added to a recently-checked channel,
only the new streams are analyzed while previously-checked streams use cached scores.
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
    ChannelUpdateTracker,
)


class TestIncrementalStreamChecking(unittest.TestCase):
    """Test incremental stream checking for channels with new streams."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.tracker_file = Path(self.temp_dir) / 'test_tracker.json'
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_channel_stores_checked_stream_ids(self):
        """Test that mark_channel_checked stores the list of checked stream IDs."""
        tracker = ChannelUpdateTracker(self.tracker_file)
        
        # Mark channel as checked with specific stream IDs
        checked_stream_ids = [101, 102, 103]
        tracker.mark_channel_checked(
            channel_id=1,
            stream_count=3,
            checked_stream_ids=checked_stream_ids
        )
        
        # Verify the stream IDs were stored
        retrieved_ids = tracker.get_checked_stream_ids(1)
        self.assertEqual(retrieved_ids, checked_stream_ids)
    
    def test_new_streams_mark_channel_for_recheck(self):
        """Test that adding new streams marks channel for recheck even within invulnerability period."""
        tracker = ChannelUpdateTracker(self.tracker_file)
        
        # Mark channel as checked with 3 streams
        now = datetime.now()
        tracker.mark_channel_checked(
            channel_id=1,
            timestamp=now.isoformat(),
            stream_count=3,
            checked_stream_ids=[101, 102, 103]
        )
        
        # Verify channel doesn't need checking
        channels_needing_check = tracker.get_channels_needing_check()
        self.assertEqual(len(channels_needing_check), 0)
        
        # Simulate new streams being added (10 minutes later, within 2-hour period)
        later = now + timedelta(minutes=10)
        tracker.mark_channel_updated(
            channel_id=1,
            timestamp=later.isoformat(),
            stream_count=5  # 2 new streams added
        )
        
        # Verify channel now needs checking despite being within invulnerability period
        channels_needing_check = tracker.get_channels_needing_check()
        self.assertEqual(len(channels_needing_check), 1)
        self.assertIn(1, channels_needing_check)
        
        # Verify previously checked stream IDs are preserved
        checked_ids = tracker.get_checked_stream_ids(1)
        self.assertEqual(checked_ids, [101, 102, 103])
    
    def test_checked_stream_ids_preserved_on_update(self):
        """Test that checked_stream_ids are preserved when marking channel updated."""
        tracker = ChannelUpdateTracker(self.tracker_file)
        
        # Initial check with 3 streams
        tracker.mark_channel_checked(
            channel_id=1,
            stream_count=3,
            checked_stream_ids=[101, 102, 103]
        )
        
        # Mark channel updated (e.g., new streams added)
        tracker.mark_channel_updated(
            channel_id=1,
            stream_count=5
        )
        
        # Verify the old checked stream IDs are still there
        checked_ids = tracker.get_checked_stream_ids(1)
        self.assertEqual(checked_ids, [101, 102, 103])
    
    def test_mark_channels_updated_preserves_checked_stream_ids(self):
        """Test that mark_channels_updated preserves checked_stream_ids."""
        tracker = ChannelUpdateTracker(self.tracker_file)
        
        # Mark multiple channels as checked with stream IDs
        tracker.mark_channel_checked(1, stream_count=3, checked_stream_ids=[101, 102, 103])
        tracker.mark_channel_checked(2, stream_count=2, checked_stream_ids=[201, 202])
        
        # Mark channels updated (batch update)
        tracker.mark_channels_updated(
            channel_ids=[1, 2],
            stream_counts={1: 5, 2: 4}
        )
        
        # Verify checked stream IDs are preserved
        self.assertEqual(tracker.get_checked_stream_ids(1), [101, 102, 103])
        self.assertEqual(tracker.get_checked_stream_ids(2), [201, 202])
        
        # Verify channels need checking
        channels_needing_check = tracker.get_channels_needing_check()
        self.assertEqual(len(channels_needing_check), 2)
    
    def test_get_checked_stream_ids_returns_empty_for_new_channel(self):
        """Test that get_checked_stream_ids returns empty list for new/untracked channels."""
        tracker = ChannelUpdateTracker(self.tracker_file)
        
        # Query a channel that was never checked
        checked_ids = tracker.get_checked_stream_ids(999)
        self.assertEqual(checked_ids, [])
    
    def test_incremental_check_updates_checked_stream_ids(self):
        """Test that after incremental check, all streams are marked as checked."""
        tracker = ChannelUpdateTracker(self.tracker_file)
        
        # Initial check with 3 streams
        tracker.mark_channel_checked(
            channel_id=1,
            stream_count=3,
            checked_stream_ids=[101, 102, 103]
        )
        
        # New streams added
        tracker.mark_channel_updated(channel_id=1, stream_count=5)
        
        # Simulate incremental check completing (now all 5 streams checked)
        tracker.mark_channel_checked(
            channel_id=1,
            stream_count=5,
            checked_stream_ids=[101, 102, 103, 104, 105]
        )
        
        # Verify all streams are now tracked as checked
        checked_ids = tracker.get_checked_stream_ids(1)
        self.assertEqual(checked_ids, [101, 102, 103, 104, 105])
        
        # Verify channel doesn't need checking
        channels_needing_check = tracker.get_channels_needing_check()
        self.assertEqual(len(channels_needing_check), 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
