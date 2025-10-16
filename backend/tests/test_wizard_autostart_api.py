#!/usr/bin/env python3
"""
Integration tests for automation service auto-start via API endpoint.

This module tests:
- API endpoint auto-starts services when pipeline mode is updated
- Services start only when wizard is complete
- Services don't start when pipeline is disabled
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

from web_api import app, get_automation_manager, get_stream_checker_service


class TestWizardAutostartAPI(unittest.TestCase):
    """Test automation service auto-start via API endpoint."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.app = app.test_client()
        self.app.testing = True
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Stop any running services
        try:
            manager = get_automation_manager()
            if manager.running:
                manager.stop_automation()
        except:
            pass
        
        try:
            service = get_stream_checker_service()
            if service.running:
                service.stop()
        except:
            pass
    
    def _create_complete_wizard_config(self):
        """Helper to create a complete wizard configuration."""
        config_file = Path(self.temp_dir) / 'automation_config.json'
        regex_file = Path(self.temp_dir) / 'channel_regex_config.json'
        stream_checker_file = Path(self.temp_dir) / 'stream_checker_config.json'
        
        config_file.write_text(json.dumps({
            "playlist_update_interval_minutes": 5,
            "autostart_automation": False
        }))
        
        regex_file.write_text(json.dumps({
            "patterns": {
                "1": {
                    "name": "Test Channel",
                    "regex": [".*Test.*"],
                    "enabled": True
                }
            },
            "global_settings": {
                "case_sensitive": False
            }
        }))
        
        stream_checker_file.write_text(json.dumps({
            "pipeline_mode": "disabled",
            "enabled": True
        }))
    
    def test_endpoint_starts_services_when_wizard_complete(self):
        """Test that API endpoint auto-starts services when wizard is complete."""
        with patch('web_api.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
                with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
                    # Setup complete wizard configuration
                    self._create_complete_wizard_config()
                    
                    # Update stream checker config via API with a pipeline mode
                    response = self.app.put(
                        '/api/stream-checker/config',
                        data=json.dumps({
                            'pipeline_mode': 'pipeline_1_5'
                        }),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify services are running
                    service = get_stream_checker_service()
                    manager = get_automation_manager()
                    
                    self.assertTrue(service.running, "Stream checker service should be running")
                    self.assertTrue(manager.running, "Automation service should be running")
                    
                    # Cleanup
                    service.stop()
                    manager.stop_automation()
    
    def test_endpoint_doesnt_start_when_wizard_incomplete(self):
        """Test that API endpoint doesn't auto-start when wizard is incomplete."""
        with patch('web_api.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
                with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
                    # Don't create complete wizard config (missing patterns)
                    config_file = Path(self.temp_dir) / 'automation_config.json'
                    config_file.write_text(json.dumps({
                        "playlist_update_interval_minutes": 5
                    }))
                    
                    # Update stream checker config via API
                    response = self.app.put(
                        '/api/stream-checker/config',
                        data=json.dumps({
                            'pipeline_mode': 'pipeline_1_5'
                        }),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify services are NOT running (wizard incomplete)
                    service = get_stream_checker_service()
                    manager = get_automation_manager()
                    
                    self.assertFalse(service.running, "Stream checker service should not be running")
                    self.assertFalse(manager.running, "Automation service should not be running")
    
    def test_endpoint_doesnt_start_when_pipeline_disabled(self):
        """Test that API endpoint doesn't auto-start when pipeline is disabled."""
        with patch('web_api.CONFIG_DIR', Path(self.temp_dir)):
            with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
                with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
                    # Setup complete wizard configuration
                    self._create_complete_wizard_config()
                    
                    # Update stream checker config via API with disabled pipeline
                    response = self.app.put(
                        '/api/stream-checker/config',
                        data=json.dumps({
                            'pipeline_mode': 'disabled'
                        }),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Verify services are NOT running (pipeline disabled)
                    service = get_stream_checker_service()
                    manager = get_automation_manager()
                    
                    self.assertFalse(service.running, "Stream checker service should not be running")
                    self.assertFalse(manager.running, "Automation service should not be running")


if __name__ == '__main__':
    unittest.main()
