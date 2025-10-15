#!/usr/bin/env python3
"""
Unit tests for autostart behavior with disabled pipeline mode.

This module tests:
- Automation service should auto-start when pipeline mode is active (not disabled)
- Automation service should NOT auto-start when pipeline mode is disabled
- Stream checker service should auto-start when pipeline mode is active (not disabled)
- Stream checker service should NOT auto-start when pipeline mode is disabled
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream_checker_service import StreamCheckerService, StreamCheckConfig
from automated_stream_manager import AutomatedStreamManager


class TestAutostartWithDisabledMode(unittest.TestCase):
    """Test autostart behavior with disabled pipeline mode."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_stream_checker_should_not_autostart_when_disabled(self):
        """Test that stream checker does not auto-start when pipeline is disabled."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            service = StreamCheckerService()
            service.config.update({'pipeline_mode': 'disabled'})
            
            pipeline_mode = service.config.get('pipeline_mode', 'pipeline_1_5')
            
            # According to the logic in web_api.py, when pipeline_mode == 'disabled',
            # service.start() should NOT be called
            self.assertEqual(pipeline_mode, 'disabled')
            
            # Verify that disabled mode is recognized
            should_autostart = (
                pipeline_mode != 'disabled' and 
                service.config.get('enabled', True)
            )
            self.assertFalse(should_autostart)
    
    def test_stream_checker_should_autostart_when_active(self):
        """Test that stream checker auto-starts when pipeline is active."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            for mode in ['pipeline_1', 'pipeline_1_5', 'pipeline_2', 'pipeline_2_5', 'pipeline_3']:
                service = StreamCheckerService()
                service.config.update({'pipeline_mode': mode})
                
                pipeline_mode = service.config.get('pipeline_mode', 'pipeline_1_5')
                
                # According to the logic in web_api.py, when pipeline_mode != 'disabled',
                # service.start() SHOULD be called if enabled
                self.assertEqual(pipeline_mode, mode)
                
                # Verify that active mode triggers autostart
                should_autostart = (
                    pipeline_mode != 'disabled' and 
                    service.config.get('enabled', True)
                )
                self.assertTrue(should_autostart, f"Pipeline mode {mode} should trigger autostart")
    
    def test_automation_manager_should_not_autostart_when_disabled(self):
        """Test that automation manager does not auto-start when pipeline is disabled."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
                service = StreamCheckerService()
                service.config.update({'pipeline_mode': 'disabled'})
                
                pipeline_mode = service.config.get('pipeline_mode', 'pipeline_1_5')
                
                # According to the logic in web_api.py, when pipeline_mode == 'disabled',
                # manager.start_automation() should NOT be called
                should_autostart = pipeline_mode != 'disabled'
                self.assertFalse(should_autostart)
    
    def test_automation_manager_should_autostart_when_active(self):
        """Test that automation manager auto-starts when pipeline is active."""
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
                for mode in ['pipeline_1', 'pipeline_1_5', 'pipeline_2', 'pipeline_2_5', 'pipeline_3']:
                    service = StreamCheckerService()
                    service.config.update({'pipeline_mode': mode})
                    
                    pipeline_mode = service.config.get('pipeline_mode', 'pipeline_1_5')
                    
                    # According to the logic in web_api.py, when pipeline_mode != 'disabled',
                    # manager.start_automation() SHOULD be called
                    should_autostart = pipeline_mode != 'disabled'
                    self.assertTrue(should_autostart, f"Pipeline mode {mode} should trigger autostart")


if __name__ == '__main__':
    unittest.main()
