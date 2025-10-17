#!/usr/bin/env python3
"""
Unit tests for regex pattern import functionality.

This module tests:
- JSON import endpoint validation
- Pattern structure validation
- Regex validation during import
- Error handling for invalid JSON
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

from automated_stream_manager import RegexChannelMatcher


class TestRegexPatternImport(unittest.TestCase):
    """Test regex pattern import functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_valid_pattern_import(self):
        """Test importing valid patterns."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Create valid pattern data
            patterns = {
                "patterns": {
                    "1": {
                        "name": "CNN",
                        "regex": [".*CNN.*"],
                        "enabled": True
                    },
                    "2": {
                        "name": "ESPN",
                        "regex": [".*ESPN.*"],
                        "enabled": True
                    }
                },
                "global_settings": {
                    "case_sensitive": False
                }
            }
            
            # Save patterns
            matcher._save_patterns(patterns)
            
            # Reload and verify
            matcher.reload_patterns()
            loaded_patterns = matcher.get_patterns()
            
            self.assertIn("patterns", loaded_patterns)
            self.assertEqual(len(loaded_patterns["patterns"]), 2)
            self.assertIn("1", loaded_patterns["patterns"])
            self.assertIn("2", loaded_patterns["patterns"])
    
    def test_invalid_regex_pattern_validation(self):
        """Test that invalid regex patterns are rejected."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Test with invalid regex
            invalid_patterns = ["[invalid("]
            is_valid, error_msg = matcher.validate_regex_patterns(invalid_patterns)
            
            self.assertFalse(is_valid)
            self.assertIsNotNone(error_msg)
            self.assertIn("Invalid regex pattern", error_msg)
    
    def test_empty_pattern_list_validation(self):
        """Test that empty pattern lists are rejected."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Test with empty list
            is_valid, error_msg = matcher.validate_regex_patterns([])
            
            self.assertFalse(is_valid)
            self.assertIn("At least one regex pattern is required", error_msg)
    
    def test_import_overwrites_existing_patterns(self):
        """Test that importing patterns overwrites existing ones."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Add initial pattern
            matcher.add_channel_pattern("1", "Initial", [".*Initial.*"])
            
            # Import new patterns
            new_patterns = {
                "patterns": {
                    "1": {
                        "name": "Updated",
                        "regex": [".*Updated.*"],
                        "enabled": True
                    }
                },
                "global_settings": {
                    "case_sensitive": False
                }
            }
            
            matcher._save_patterns(new_patterns)
            matcher.reload_patterns()
            
            loaded_patterns = matcher.get_patterns()
            self.assertEqual(loaded_patterns["patterns"]["1"]["name"], "Updated")
    
    def test_pattern_validation_with_special_characters(self):
        """Test validation of patterns with special regex characters."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Valid patterns with special characters
            valid_patterns = [
                ".*CNN.*",
                "^News.*",
                ".*Sports$",
                "ESPN|Fox Sports",
                "\\d+ News"
            ]
            
            is_valid, error_msg = matcher.validate_regex_patterns(valid_patterns)
            self.assertTrue(is_valid)
            self.assertIsNone(error_msg)
    
    def test_pattern_matching_after_import(self):
        """Test that patterns work correctly after import."""
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            matcher = RegexChannelMatcher()
            
            # Import patterns
            patterns = {
                "patterns": {
                    "1": {
                        "name": "News",
                        "regex": [".*CNN.*", ".*BBC.*"],
                        "enabled": True
                    }
                },
                "global_settings": {
                    "case_sensitive": False
                }
            }
            
            matcher._save_patterns(patterns)
            matcher.reload_patterns()
            
            # Test matching
            matches = matcher.match_stream_to_channels("CNN International")
            self.assertIn("1", matches)
            
            matches = matcher.match_stream_to_channels("BBC World News")
            self.assertIn("1", matches)
            
            matches = matcher.match_stream_to_channels("ESPN Sports")
            self.assertNotIn("1", matches)


if __name__ == '__main__':
    unittest.main()
