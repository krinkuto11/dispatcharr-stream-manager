"""Test regex pattern matching with various whitespace scenarios."""
import unittest
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from automated_stream_manager import RegexChannelMatcher
import tempfile
import json


class TestRegexWhitespaceMatching(unittest.TestCase):
    """Test that regex patterns handle different whitespace characters correctly."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_regex_config.json"
        
        # Create test configuration with a pattern
        test_config = {
            "patterns": {
                "1": {
                    "name": "TVP 1 Channel",
                    "regex": ["TVP 1"],
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False,
                "require_exact_match": False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        self.matcher = RegexChannelMatcher(config_file=self.config_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_normal_space_matching(self):
        """Test that patterns with normal spaces match streams with normal spaces."""
        stream_names = [
            "PL| TVP 1 FHD",
            "PL: TVP 1 HD",
            "PL: TVP 1 4K",
            "PL VIP: TVP 1 RAW"
        ]
        
        for stream_name in stream_names:
            with self.subTest(stream_name=stream_name):
                matches = self.matcher.match_stream_to_channels(stream_name)
                self.assertIn("1", matches, 
                             f"Stream '{stream_name}' should match channel 1")
    
    def test_non_breaking_space_in_stream(self):
        """Test that patterns match streams with non-breaking spaces."""
        # Non-breaking space (U+00A0) instead of regular space
        stream_name = "PL: TVP\u00a01 HD"
        matches = self.matcher.match_stream_to_channels(stream_name)
        self.assertIn("1", matches, 
                     f"Stream '{stream_name}' with non-breaking space should match")
    
    def test_double_space_in_stream(self):
        """Test that patterns match streams with double spaces."""
        stream_name = "PL: TVP  1 HD"  # Double space between TVP and 1
        matches = self.matcher.match_stream_to_channels(stream_name)
        self.assertIn("1", matches, 
                     f"Stream '{stream_name}' with double space should match")
    
    def test_tab_character_in_stream(self):
        """Test that patterns match streams with tab characters."""
        stream_name = "PL: TVP\t1 HD"  # Tab instead of space
        matches = self.matcher.match_stream_to_channels(stream_name)
        self.assertIn("1", matches, 
                     f"Stream '{stream_name}' with tab should match")
    
    def test_en_space_in_stream(self):
        """Test that patterns match streams with en spaces."""
        # En space (U+2002)
        stream_name = "PL: TVP\u20021 HD"
        matches = self.matcher.match_stream_to_channels(stream_name)
        self.assertIn("1", matches, 
                     f"Stream '{stream_name}' with en space should match")
    
    def test_no_match_when_text_different(self):
        """Test that patterns don't match unrelated streams."""
        stream_names = [
            "ESPN HD",
            "CNN International",
            "BBC One"
        ]
        
        for stream_name in stream_names:
            with self.subTest(stream_name=stream_name):
                matches = self.matcher.match_stream_to_channels(stream_name)
                self.assertNotIn("1", matches, 
                                f"Stream '{stream_name}' should not match channel 1")
    
    def test_multiple_whitespace_variations(self):
        """Test pattern with multiple spaces handles various whitespace."""
        # Update pattern to have multiple spaces
        test_config = {
            "patterns": {
                "2": {
                    "name": "Test Channel",
                    "regex": ["FOO BAR BAZ"],
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        matcher = RegexChannelMatcher(config_file=self.config_file)
        
        # These should all match
        test_streams = [
            "FOO BAR BAZ",           # Normal spaces
            "FOO  BAR  BAZ",         # Double spaces
            "FOO\u00a0BAR\u00a0BAZ", # Non-breaking spaces
            "FOO\tBAR\tBAZ",         # Tabs
            "PREFIX FOO BAR BAZ SUFFIX",  # Pattern in middle
        ]
        
        for stream_name in test_streams:
            with self.subTest(stream_name=stream_name):
                matches = matcher.match_stream_to_channels(stream_name)
                self.assertIn("2", matches, 
                             f"Stream '{stream_name}' should match channel 2")
    
    def test_reported_tvp_issue(self):
        """Test the specific TVP 1 issue reported by the tester.
        
        Channel name: "TVP 1"
        Stream that worked: "PL| TVP 1 FHD"
        Streams that didn't work: "PL: TVP 1 HD", "PL: TVP 1 4K", "PL VIP: TVP 1 RAW"
        Regex pattern: "TVP 1"
        
        This test simulates the exact scenario where streams with potentially different
        whitespace characters should all match the pattern.
        """
        test_config = {
            "patterns": {
                "tvp1": {
                    "name": "TVP 1",
                    "regex": ["TVP 1"],
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        matcher = RegexChannelMatcher(config_file=self.config_file)
        
        # All of these should match
        all_streams = [
            "PL| TVP 1 FHD",        # Original working stream
            "PL: TVP 1 HD",         # Reported as not working
            "PL: TVP 1 4K",         # Reported as not working  
            "PL VIP: TVP 1 RAW",    # Reported as not working
        ]
        
        for stream_name in all_streams:
            with self.subTest(stream_name=stream_name):
                matches = matcher.match_stream_to_channels(stream_name)
                self.assertIn("tvp1", matches, 
                             f"Stream '{stream_name}' should match TVP 1 channel")
        
        # Also test with various whitespace scenarios that might occur in real data
        whitespace_variants = [
            "PL: TVP\u00a01 HD",     # Non-breaking space
            "PL: TVP  1 4K",         # Double space
            "PL: TVP\t1 RAW",        # Tab character
        ]
        
        for stream_name in whitespace_variants:
            with self.subTest(stream_name=stream_name):
                matches = matcher.match_stream_to_channels(stream_name)
                self.assertIn("tvp1", matches, 
                             f"Stream '{stream_name}' with special whitespace should match TVP 1 channel")


    def test_regex_patterns_still_work(self):
        """Test that actual regex patterns (not just literal text) still work correctly."""
        test_config = {
            "patterns": {
                "3": {
                    "name": "Regex Test",
                    "regex": [
                        ".*CNN.*",           # Wildcard pattern
                        "ESPN[0-9]+",        # Character class
                        "BBC (One|Two|Three)"  # Alternation
                    ],
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        matcher = RegexChannelMatcher(config_file=self.config_file)
        
        # These should match
        matching_streams = [
            "HD CNN International",   # Matches .*CNN.*
            "US: CNN HD",            # Matches .*CNN.*
            "ESPN2 HD",              # Matches ESPN[0-9]+
            "UK: BBC One HD",        # Matches BBC (One|Two|Three)
            "BBC Two",               # Matches BBC (One|Two|Three)
        ]
        
        for stream_name in matching_streams:
            with self.subTest(stream_name=stream_name):
                matches = matcher.match_stream_to_channels(stream_name)
                self.assertIn("3", matches, 
                             f"Stream '{stream_name}' should match channel 3")
        
        # These should NOT match
        non_matching_streams = [
            "FOX News",              # Doesn't match any pattern
            "ESPN HD",               # ESPN without number doesn't match ESPN[0-9]+
            "BBC Four",              # Not One, Two, or Three
        ]
        
        for stream_name in non_matching_streams:
            with self.subTest(stream_name=stream_name):
                matches = matcher.match_stream_to_channels(stream_name)
                self.assertNotIn("3", matches, 
                                f"Stream '{stream_name}' should NOT match channel 3")
    
    def test_pattern_with_existing_regex_whitespace(self):
        """Test that patterns already using \\s+ work correctly."""
        test_config = {
            "patterns": {
                "4": {
                    "name": "Regex Whitespace",
                    "regex": [r"ABC\s+XYZ"],  # Pattern already using \s+
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        matcher = RegexChannelMatcher(config_file=self.config_file)
        
        # All should match
        matching_streams = [
            "ABC XYZ",
            "ABC  XYZ",
            "ABC\tXYZ",
            "ABC\u00a0XYZ",
        ]
        
        for stream_name in matching_streams:
            with self.subTest(stream_name=stream_name):
                matches = matcher.match_stream_to_channels(stream_name)
                self.assertIn("4", matches, 
                             f"Stream '{stream_name}' should match channel 4")


if __name__ == '__main__':
    unittest.main()
