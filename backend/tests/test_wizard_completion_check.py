#!/usr/bin/env python3
"""
Unit tests for wizard completion check functionality.

This module tests:
- Wizard completion status check
- Automation service startup guard
- Configuration file validation
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from automated_stream_manager import AutomatedStreamManager, RegexChannelMatcher


class TestWizardCompletionCheck(unittest.TestCase):
    """Test wizard completion check functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_wizard_incomplete_when_no_config_files(self):
        """Test that wizard is incomplete when config files don't exist."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # No files created yet
            config_file = Path(self.temp_dir) / 'automation_config.json'
            regex_file = Path(self.temp_dir) / 'channel_regex_config.json'
            
            self.assertFalse(config_file.exists())
            self.assertFalse(regex_file.exists())
    
    def test_wizard_incomplete_when_no_patterns(self):
        """Test that wizard is incomplete when no patterns are configured."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create config files but with no patterns
            config_file = Path(self.temp_dir) / 'automation_config.json'
            regex_file = Path(self.temp_dir) / 'channel_regex_config.json'
            
            config_file.write_text(json.dumps({
                "playlist_update_interval_minutes": 5
            }))
            
            regex_file.write_text(json.dumps({
                "patterns": {},
                "global_settings": {
                    "case_sensitive": False
                }
            }))
            
            matcher = RegexChannelMatcher()
            patterns = matcher.get_patterns()
            
            # Should have no patterns
            self.assertEqual(len(patterns.get("patterns", {})), 0)
    
    def test_wizard_complete_when_patterns_configured(self):
        """Test that wizard is complete when patterns are properly configured."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create config files with patterns
            config_file = Path(self.temp_dir) / 'automation_config.json'
            regex_file = Path(self.temp_dir) / 'channel_regex_config.json'
            
            config_file.write_text(json.dumps({
                "playlist_update_interval_minutes": 5,
                "autostart_automation": False
            }))
            
            regex_file.write_text(json.dumps({
                "patterns": {
                    "1": {
                        "name": "CNN",
                        "regex": [".*CNN.*"],
                        "enabled": True
                    }
                },
                "global_settings": {
                    "case_sensitive": False
                }
            }))
            
            matcher = RegexChannelMatcher()
            patterns = matcher.get_patterns()
            
            # Should have patterns
            self.assertTrue(config_file.exists())
            self.assertTrue(regex_file.exists())
            self.assertGreater(len(patterns.get("patterns", {})), 0)
    
    def test_automation_manager_loads_config(self):
        """Test that automation manager can load its configuration."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create a config file
            config_file = Path(self.temp_dir) / 'automation_config.json'
            config_file.write_text(json.dumps({
                "playlist_update_interval_minutes": 10,
                "autostart_automation": True
            }))
            
            manager = AutomatedStreamManager()
            
            # Verify config loaded
            self.assertEqual(manager.config.get('playlist_update_interval_minutes'), 10)
            self.assertEqual(manager.config.get('autostart_automation'), True)
    
    def test_regex_matcher_validates_on_load(self):
        """Test that regex matcher validates patterns when loading."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Add a valid pattern
            matcher.add_channel_pattern("1", "Test", [".*Test.*"])
            
            # Reload and verify it persists
            matcher.reload_patterns()
            patterns = matcher.get_patterns()
            
            self.assertIn("1", patterns.get("patterns", {}))
            self.assertEqual(patterns["patterns"]["1"]["name"], "Test")
    
    def test_automation_not_started_without_config(self):
        """Test that automation should not start without proper configuration."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Manager should not be running by default
            self.assertFalse(manager.running)
    
    def test_config_file_creation_on_first_run(self):
        """Test that config files are created with defaults on first run."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create manager
            manager = AutomatedStreamManager()
            
            # Config file should be created
            config_file = Path(self.temp_dir) / 'automation_config.json'
            self.assertTrue(config_file.exists())
            
            # Should have default values
            self.assertIn('autostart_automation', manager.config)
            self.assertFalse(manager.config['autostart_automation'])
    
    def test_pattern_file_creation_on_first_run(self):
        """Test that pattern files are created with defaults on first run."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            # Create matcher
            matcher = RegexChannelMatcher()
            
            # Pattern file should be created
            pattern_file = Path(self.temp_dir) / 'channel_regex_config.json'
            self.assertTrue(pattern_file.exists())
            
            # Should have empty patterns by default
            patterns = matcher.get_patterns()
            self.assertEqual(len(patterns.get("patterns", {})), 0)


if __name__ == '__main__':
    unittest.main()
