#!/usr/bin/env python3
"""
Unit tests for autostart automation configuration.

This module tests:
- Default autostart_automation value
- Configuration persistence
- Config update functionality
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automated_stream_manager import AutomatedStreamManager


class TestAutostartConfiguration(unittest.TestCase):
    """Test autostart automation configuration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_default_autostart_is_false(self):
        """Test that default autostart_automation is False."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            self.assertEqual(manager.config.get('autostart_automation'), False)
    
    def test_autostart_config_persistence(self):
        """Test that autostart_automation config is saved and loaded correctly."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create manager and update config
            manager = AutomatedStreamManager()
            manager.update_config({'autostart_automation': True})
            
            # Verify it was saved
            self.assertEqual(manager.config['autostart_automation'], True)
            
            # Create new manager instance to test loading
            manager2 = AutomatedStreamManager()
            self.assertEqual(manager2.config['autostart_automation'], True)
    
    def test_autostart_can_be_disabled(self):
        """Test that autostart can be explicitly disabled."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            manager.update_config({'autostart_automation': True})
            
            # Now disable it
            manager.update_config({'autostart_automation': False})
            self.assertEqual(manager.config['autostart_automation'], False)
            
            # Verify persistence
            manager2 = AutomatedStreamManager()
            self.assertEqual(manager2.config['autostart_automation'], False)


if __name__ == '__main__':
    unittest.main()
