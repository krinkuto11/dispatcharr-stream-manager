"""Test regex pattern validation to prevent invalid patterns from being saved."""
import unittest
import sys
from pathlib import Path
import tempfile
import json

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from automated_stream_manager import RegexChannelMatcher


class TestRegexValidation(unittest.TestCase):
    """Test that invalid regex patterns are rejected before being saved."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_regex_config.json"
        
        # Create initial test configuration
        test_config = {
            "patterns": {},
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
    
    def test_valid_regex_patterns_accepted(self):
        """Test that valid regex patterns are accepted."""
        valid_patterns = [
            [".*CNN.*"],
            ["ESPN[0-9]+"],
            ["BBC (One|Two|Three)"],
            ["^FOX News$"],
            [r"ABC\s+XYZ"],
            ["CINEMAX(?:\\s[A-Z]+)?"],  # Fixed version of the problematic pattern
        ]
        
        for i, patterns in enumerate(valid_patterns):
            with self.subTest(patterns=patterns):
                try:
                    self.matcher.add_channel_pattern(
                        channel_id=f"test_{i}",
                        name=f"Test Channel {i}",
                        regex_patterns=patterns,
                        enabled=True
                    )
                except ValueError:
                    self.fail(f"Valid pattern {patterns} was rejected")
    
    def test_invalid_regex_unbalanced_parenthesis_rejected(self):
        """Test that regex with unbalanced parenthesis is rejected."""
        # This is the exact pattern from the bug report
        invalid_pattern = "CINEMAX(?:\\s[A-Z]+)).$"
        
        with self.assertRaises(ValueError) as context:
            self.matcher.add_channel_pattern(
                channel_id="test_1",
                name="Test Channel",
                regex_patterns=[invalid_pattern],
                enabled=True
            )
        
        error_msg = str(context.exception)
        self.assertIn("Invalid regex pattern", error_msg)
        self.assertIn(invalid_pattern, error_msg)
        self.assertIn("unbalanced parenthesis", error_msg.lower())
    
    def test_invalid_regex_unclosed_bracket_rejected(self):
        """Test that regex with unclosed bracket is rejected."""
        invalid_pattern = "ABC[0-9"
        
        with self.assertRaises(ValueError) as context:
            self.matcher.add_channel_pattern(
                channel_id="test_2",
                name="Test Channel",
                regex_patterns=[invalid_pattern],
                enabled=True
            )
        
        error_msg = str(context.exception)
        self.assertIn("Invalid regex pattern", error_msg)
        self.assertIn(invalid_pattern, error_msg)
    
    def test_invalid_regex_bad_escape_rejected(self):
        """Test that regex with invalid escape sequence is rejected."""
        invalid_pattern = "ABC\\k"  # \k is not a valid escape
        
        with self.assertRaises(ValueError) as context:
            self.matcher.add_channel_pattern(
                channel_id="test_3",
                name="Test Channel",
                regex_patterns=[invalid_pattern],
                enabled=True
            )
        
        error_msg = str(context.exception)
        self.assertIn("Invalid regex pattern", error_msg)
    
    def test_empty_pattern_list_rejected(self):
        """Test that empty pattern list is rejected."""
        with self.assertRaises(ValueError) as context:
            self.matcher.add_channel_pattern(
                channel_id="test_4",
                name="Test Channel",
                regex_patterns=[],
                enabled=True
            )
        
        error_msg = str(context.exception)
        self.assertIn("At least one regex pattern is required", error_msg)
    
    def test_empty_string_pattern_rejected(self):
        """Test that empty string pattern is rejected."""
        with self.assertRaises(ValueError) as context:
            self.matcher.add_channel_pattern(
                channel_id="test_5",
                name="Test Channel",
                regex_patterns=[""],
                enabled=True
            )
        
        error_msg = str(context.exception)
        self.assertIn("non-empty string", error_msg)
    
    def test_multiple_patterns_one_invalid_rejected(self):
        """Test that if one pattern in a list is invalid, the whole list is rejected."""
        patterns = [
            ".*CNN.*",  # Valid
            "ESPN[0-9",  # Invalid - unclosed bracket
            "BBC.*"     # Valid
        ]
        
        with self.assertRaises(ValueError) as context:
            self.matcher.add_channel_pattern(
                channel_id="test_6",
                name="Test Channel",
                regex_patterns=patterns,
                enabled=True
            )
        
        error_msg = str(context.exception)
        self.assertIn("Invalid regex pattern", error_msg)
        self.assertIn("ESPN[0-9", error_msg)
    
    def test_invalid_pattern_not_saved_to_file(self):
        """Test that invalid patterns are not saved to the config file."""
        invalid_pattern = "CINEMAX(?:\\s[A-Z]+)).$"
        
        # Try to add invalid pattern
        try:
            self.matcher.add_channel_pattern(
                channel_id="test_7",
                name="Test Channel",
                regex_patterns=[invalid_pattern],
                enabled=True
            )
        except ValueError:
            pass  # Expected
        
        # Reload patterns from file
        with open(self.config_file, 'r') as f:
            saved_config = json.load(f)
        
        # Verify the invalid pattern was not saved
        self.assertNotIn("test_7", saved_config.get("patterns", {}))
    
    def test_valid_pattern_saved_after_invalid_rejected(self):
        """Test that valid patterns can still be saved after an invalid one is rejected."""
        invalid_pattern = "ABC[0-9"
        valid_pattern = ".*CNN.*"
        
        # Try to add invalid pattern - should fail
        try:
            self.matcher.add_channel_pattern(
                channel_id="test_8",
                name="Invalid Channel",
                regex_patterns=[invalid_pattern],
                enabled=True
            )
        except ValueError:
            pass  # Expected
        
        # Add valid pattern - should succeed
        self.matcher.add_channel_pattern(
            channel_id="test_9",
            name="Valid Channel",
            regex_patterns=[valid_pattern],
            enabled=True
        )
        
        # Verify only valid pattern was saved
        with open(self.config_file, 'r') as f:
            saved_config = json.load(f)
        
        self.assertNotIn("test_8", saved_config.get("patterns", {}))
        self.assertIn("test_9", saved_config.get("patterns", {}))
    
    def test_validate_regex_patterns_method(self):
        """Test the validate_regex_patterns method directly."""
        # Valid patterns
        is_valid, error = self.matcher.validate_regex_patterns([".*CNN.*", "ESPN[0-9]+"])
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Invalid pattern - unbalanced parenthesis
        invalid_pattern = "ABC(DEF"
        is_valid, error = self.matcher.validate_regex_patterns([invalid_pattern])
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn("Invalid regex pattern", error)
        
        # Empty list
        is_valid, error = self.matcher.validate_regex_patterns([])
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        
        # Empty string
        is_valid, error = self.matcher.validate_regex_patterns([""])
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_complex_valid_patterns(self):
        """Test that complex but valid regex patterns are accepted."""
        complex_patterns = [
            r"^(?:US|UK|CA):\s*(?:HBO|Showtime)(?:\s+\d+)?(?:\s+(?:HD|FHD|4K))?$",
            r"(?i)(?:^|\s)SPORTS?(?:\s|$)",
            r"(?:ESPN|FOX\s+SPORTS|NBC\s+SPORTS)(?:\s+[0-9]+)?",
            r"^(?!.*(?:XXX|ADULT)).*NEWS.*$",  # Negative lookahead
        ]
        
        for i, pattern in enumerate(complex_patterns):
            with self.subTest(pattern=pattern):
                try:
                    self.matcher.add_channel_pattern(
                        channel_id=f"complex_{i}",
                        name=f"Complex Channel {i}",
                        regex_patterns=[pattern],
                        enabled=True
                    )
                except ValueError as e:
                    self.fail(f"Valid complex pattern {pattern} was rejected: {e}")


class TestRegexValidationPersistence(unittest.TestCase):
    """Test that validation prevents persistent error logs."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_regex_config.json"
        
        # Create initial empty configuration
        test_config = {
            "patterns": {},
            "global_settings": {
                "case_sensitive": False
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_invalid_pattern_does_not_cause_repeated_errors(self):
        """Test that rejected invalid patterns don't cause repeated error logs."""
        import logging
        from io import StringIO
        
        # Set up logging to capture log messages
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        logger = logging.getLogger()
        old_level = logger.level
        logger.setLevel(logging.WARNING)
        logger.addHandler(handler)
        
        try:
            matcher = RegexChannelMatcher(config_file=self.config_file)
            
            # Try to add invalid pattern - should be rejected
            invalid_pattern = "CINEMAX(?:\\s[A-Z]+)).$"
            try:
                matcher.add_channel_pattern(
                    channel_id="test_1",
                    name="Test Channel",
                    regex_patterns=[invalid_pattern],
                    enabled=True
                )
            except ValueError:
                pass  # Expected
            
            # Clear the log stream
            log_stream.truncate(0)
            log_stream.seek(0)
            
            # Now try to match streams multiple times
            # This should NOT produce repeated error logs about the invalid pattern
            for i in range(10):
                matcher.match_stream_to_channels(f"Test Stream {i}")
            
            # Check that no error logs were generated
            log_output = log_stream.getvalue()
            self.assertNotIn("Invalid regex pattern", log_output,
                           "Invalid pattern that was rejected should not cause error logs during matching")
            self.assertNotIn("CINEMAX", log_output,
                           "Rejected pattern should not appear in logs during matching")
        
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)


if __name__ == '__main__':
    unittest.main()
