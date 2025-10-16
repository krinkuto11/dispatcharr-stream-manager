"""
Test that configuration changes are applied immediately without restart.
"""

import unittest
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestImmediateConfigUpdate(unittest.TestCase):
    """Test immediate application of configuration changes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        import os
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_stream_checker_config_change_signals_event(self):
        """Test that updating stream checker config signals the config_changed event."""
        import stream_checker_service
        
        with patch.object(stream_checker_service, 'CONFIG_DIR', Path(self.temp_dir)):
            from stream_checker_service import StreamCheckerService
            
            service = StreamCheckerService()
            
            # Start the service
            service.start()
            
            try:
                # Ensure config_changed event is not set initially
                self.assertFalse(service.config_changed.is_set())
                
                # Update configuration
                updates = {
                    'pipeline_mode': 'pipeline_2',
                    'global_check_schedule': {
                        'hour': 10,
                        'minute': 15
                    }
                }
                service.update_config(updates)
                
                # Config should be updated
                self.assertEqual(service.config.get('pipeline_mode'), 'pipeline_2')
                self.assertEqual(service.config.get('global_check_schedule.hour'), 10)
                self.assertEqual(service.config.get('global_check_schedule.minute'), 15)
                
                # Event should be set to signal scheduler
                self.assertTrue(service.config_changed.is_set())
                
            finally:
                service.stop()
    
    def test_automation_config_update_logs_changes(self):
        """Test that automation config updates are logged properly."""
        from automated_stream_manager import AutomatedStreamManager
        
        with patch('automated_stream_manager.CONFIG_DIR', Path(self.temp_dir)):
            manager = AutomatedStreamManager()
            
            # Update configuration with logging
            updates = {
                'playlist_update_interval_minutes': 10,
                'enabled_features': {
                    'auto_playlist_update': True,
                    'auto_stream_discovery': False
                }
            }
            
            with self.assertLogs(level='INFO') as log_context:
                manager.update_config(updates)
            
            # Check that config was updated
            self.assertEqual(manager.config['playlist_update_interval_minutes'], 10)
            self.assertEqual(manager.config['enabled_features']['auto_stream_discovery'], False)
            
            # Check that update was logged
            log_messages = ' '.join(log_context.output)
            self.assertIn('updated', log_messages.lower())
    
    def test_pipeline_mode_change_logged(self):
        """Test that pipeline mode changes are logged with old and new values."""
        import stream_checker_service
        
        with patch.object(stream_checker_service, 'CONFIG_DIR', Path(self.temp_dir)):
            from stream_checker_service import StreamCheckerService
            
            service = StreamCheckerService()
            service.start()
            
            try:
                # Change pipeline mode
                with self.assertLogs(level='INFO') as log_context:
                    service.update_config({'pipeline_mode': 'pipeline_3'})
                
                log_messages = ' '.join(log_context.output)
                self.assertIn('pipeline_3', log_messages.lower())
                self.assertIn('configuration updated', log_messages.lower())
                
            finally:
                service.stop()
    
    def test_schedule_time_change_logged(self):
        """Test that schedule time changes are logged with old and new values."""
        import stream_checker_service
        
        with patch.object(stream_checker_service, 'CONFIG_DIR', Path(self.temp_dir)):
            from stream_checker_service import StreamCheckerService
            
            service = StreamCheckerService()
            service.start()
            
            try:
                # Change schedule time
                updates = {
                    'global_check_schedule': {
                        'hour': 14,
                        'minute': 30
                    }
                }
                
                with self.assertLogs(level='INFO') as log_context:
                    service.update_config(updates)
                
                log_messages = ' '.join(log_context.output)
                self.assertIn('14:30', log_messages)
                self.assertIn('configuration', log_messages.lower())
                
            finally:
                service.stop()
    
    def test_config_persisted_to_file(self):
        """Test that config changes are persisted to file."""
        from stream_checker_service import StreamCheckConfig
        
        config_file = Path(self.temp_dir) / "test_config.json"
        
        with patch('stream_checker_service.CONFIG_DIR', Path(self.temp_dir)):
            config = StreamCheckConfig(str(config_file))
            
            # Update config
            config.update({
                'pipeline_mode': 'pipeline_2_5',
                'global_check_schedule': {
                    'hour': 12,
                    'minute': 0
                }
            })
            
            # Verify file was updated
            self.assertTrue(config_file.exists())
            
            # Load config from file
            with open(config_file, 'r') as f:
                saved_config = json.load(f)
            
            self.assertEqual(saved_config['pipeline_mode'], 'pipeline_2_5')
            self.assertEqual(saved_config['global_check_schedule']['hour'], 12)


if __name__ == '__main__':
    unittest.main()
