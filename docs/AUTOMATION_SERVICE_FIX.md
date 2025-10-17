# Fix: Automation Service Auto-Start After Wizard Completion

## Problem
When users completed the setup wizard and selected a pipeline mode, the automation service and stream checker service did not start automatically. They would only start when the server was restarted, requiring users to manually restart the container or server.

## Root Cause
The auto-start logic in `web_api.py` only executed during server initialization (in the `if __name__ == '__main__'` block). When the wizard saved configuration changes via API endpoints during runtime, no auto-start logic was triggered.

## Solution
Enhanced the `update_stream_checker_config()` endpoint in `/backend/web_api.py` to:

1. Check if `pipeline_mode` is being updated
2. Verify wizard is complete using `check_wizard_complete()`
3. Auto-start both services if pipeline mode is active (not 'disabled')
4. Auto-stop both services if pipeline mode is switched to 'disabled'

## Implementation Details

### Modified Endpoint: `/api/stream-checker/config` (PUT)

```python
# Auto-start or stop services based on pipeline mode when wizard is complete
if 'pipeline_mode' in data and check_wizard_complete():
    pipeline_mode = data['pipeline_mode']
    manager = get_automation_manager()
    
    if pipeline_mode == 'disabled':
        # Stop services if pipeline is disabled
        if service.running:
            service.stop()
            logging.info("Stream checker service stopped (pipeline disabled)")
        if manager.running:
            manager.stop_automation()
            logging.info("Automation service stopped (pipeline disabled)")
    else:
        # Start services if pipeline is active and they're not already running
        if not service.running:
            service.start()
            logging.info(f"Stream checker service auto-started after config update (mode: {pipeline_mode})")
        if not manager.running:
            manager.start_automation()
            logging.info(f"Automation service auto-started after config update (mode: {pipeline_mode})")
```

### Key Features
- **Idempotent**: Only starts services if they're not already running
- **Smart Stop**: Stops services when switching to disabled mode
- **Wizard Guard**: Only auto-starts when wizard is complete
- **Clear Logging**: Logs when services start/stop for debugging

## Test Coverage

### Unit Tests (`test_wizard_autostart.py`)
- Services start when pipeline selected and wizard complete
- Services don't start when wizard incomplete
- Services don't start when pipeline disabled
- Wizard completion requires patterns

### Integration Tests (`test_wizard_autostart_api.py`)
- API endpoint correctly auto-starts services
- Services don't start when wizard incomplete
- Services don't start when pipeline is disabled
- Services are stopped when switching to disabled pipeline

All tests passing ✅

## User Experience Impact

### Before Fix
1. User completes setup wizard
2. User selects a pipeline mode (e.g., Pipeline 1.5)
3. Configuration is saved
4. **Services remain stopped** ❌
5. User must restart container/server manually

### After Fix
1. User completes setup wizard
2. User selects a pipeline mode (e.g., Pipeline 1.5)
3. Configuration is saved
4. **Services start automatically** ✅
5. User can immediately see automation working

## Compatibility
- Backward compatible with existing configurations
- No breaking changes to API contracts
- Works with all pipeline modes (1, 1.5, 2, 2.5, 3, disabled)
- Safe to deploy without migration

## Future Enhancements
Consider adding:
- UI notification when services start/stop
- Service status indicator in wizard completion screen
- Auto-refresh of dashboard status after wizard completion
