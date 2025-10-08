#!/usr/bin/env python3
"""
Unit tests for check_on_update configuration in stream checker.

This module tests:
- Default check_on_update value
- Configuration persistence
- Config update functionality
"""

import unittest
import tempfile
from pathlib import Path
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import StreamCheckConfig


class TestCheckOnUpdateConfiguration(unittest.TestCase):
    """Test check_on_update configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp(prefix='test_check_on_update_')
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_check_on_update_is_true(self):
        """Test that default check_on_update is True."""
        config_file = Path(self.temp_dir) / "test_default_config.json"
        config = StreamCheckConfig(config_file=config_file)
        self.assertEqual(config.get('queue.check_on_update'), True)
    
    def test_check_on_update_config_persistence(self):
        """Test that check_on_update config is saved and loaded correctly."""
        config_file = Path(self.temp_dir) / "test_persistence_config.json"
        # Create config and update
        config = StreamCheckConfig(config_file=config_file)
        config.update({'queue': {'check_on_update': False}})
        
        # Verify it was saved
        self.assertEqual(config.get('queue.check_on_update'), False)
        
        # Create new config instance to test loading
        config2 = StreamCheckConfig(config_file=config_file)
        self.assertEqual(config2.get('queue.check_on_update'), False)
    
    def test_check_on_update_can_be_reenabled(self):
        """Test that check_on_update can be re-enabled after being disabled."""
        config_file = Path(self.temp_dir) / "test_reenable_config.json"
        config = StreamCheckConfig(config_file=config_file)
        config.update({'queue': {'check_on_update': False}})
        
        # Now enable it
        config.update({'queue': {'check_on_update': True}})
        self.assertEqual(config.get('queue.check_on_update'), True)
        
        # Verify persistence
        config2 = StreamCheckConfig(config_file=config_file)
        self.assertEqual(config2.get('queue.check_on_update'), True)
    
    def test_nested_config_update(self):
        """Test that nested queue configuration updates properly."""
        config_file = Path(self.temp_dir) / "test_nested_config.json"
        config = StreamCheckConfig(config_file=config_file)
        
        # Update multiple queue settings
        config.update({
            'queue': {
                'check_on_update': False,
                'max_channels_per_run': 100
            }
        })
        
        self.assertEqual(config.get('queue.check_on_update'), False)
        self.assertEqual(config.get('queue.max_channels_per_run'), 100)
        
        # Verify only max_size remains at default (wasn't updated)
        self.assertEqual(config.get('queue.max_size'), 1000)


if __name__ == '__main__':
    unittest.main()
