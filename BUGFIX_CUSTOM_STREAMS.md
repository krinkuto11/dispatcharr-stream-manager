# Bug Fix: Custom M3U Playlist/Account Showing Up

## Problem Description
When using StreamFlow, a "custom" M3U playlist/account was appearing in the UI even though no custom M3U account had been added to Dispatcharr. This was confusing because it suggested there was a dummy or phantom M3U account.

## Root Cause
The issue was caused by `get_streams()` fetching ALL streams from Dispatcharr, including:
1. Streams from M3U accounts (is_custom=False)
2. User-created custom streams (is_custom=True)

Custom streams are streams that users create directly in Dispatcharr without being part of any M3U account. These streams have:
- `is_custom=True`
- `m3u_account=None`

When StreamFlow performed M3U-related operations (like playlist refresh or stream discovery), it was including these custom streams in its results. This could make it appear as if there was a "custom" M3U account when streams were grouped or displayed.

## Solution
Added a new optional parameter `exclude_custom` to the `get_streams()` function in `api_utils.py`:

```python
def get_streams(log_result: bool = True, exclude_custom: bool = False) -> List[Dict[str, Any]]:
```

When `exclude_custom=True`, the function filters out any streams where `is_custom=True`.

## Changes Made

### 1. Updated `api_utils.py`
- Added `exclude_custom` parameter to `get_streams()` function
- Implemented filtering logic to exclude custom streams when requested
- Updated function documentation

### 2. Updated `automated_stream_manager.py`
Modified three key operations to exclude custom streams:

**a) Playlist Refresh (refresh_playlists method)**
- Now calls `get_streams(log_result=False, exclude_custom=True)` before refresh
- Calls `get_streams(log_result=True, exclude_custom=True)` after refresh
- This ensures changelog tracking only counts M3U account streams

**b) Stream Discovery (discover_and_assign_streams method)**
- Now calls `get_streams(log_result=False, exclude_custom=True)`
- Ensures only M3U account streams are assigned to channels via regex patterns

### 3. Added Tests
Created comprehensive test coverage:

**test_custom_stream_filtering.py**
- Tests that custom streams are included by default (backward compatibility)
- Tests that custom streams are excluded when `exclude_custom=True`
- Tests handling of missing `is_custom` field
- Tests pagination with filtering
- Tests edge case where all streams are custom

**test_m3u_account_filtering.py**
- Added test to verify custom streams are excluded during playlist refresh
- Ensures `exclude_custom=True` is passed in all refresh operations

## Impact
- **No Breaking Changes**: The default behavior remains unchanged (custom streams are included by default)
- **Backward Compatible**: Existing code continues to work without modification
- **Targeted Fix**: Only M3U-related operations now exclude custom streams
- **Better Accuracy**: Changelog tracking and stream discovery now only count M3U account streams

## Testing Results
All tests pass successfully:
- 5/5 custom stream filtering tests ✓
- 8/8 M3U account filtering tests ✓

## Use Cases

### When to Exclude Custom Streams
1. **M3U Playlist Refresh**: Only track changes to M3U account streams
2. **Stream Discovery**: Only auto-assign M3U account streams to channels
3. **Changelog Tracking**: Only report additions/removals from M3U accounts

### When to Include Custom Streams
1. **Testing Regex Patterns**: Users may want to test patterns against all streams
2. **Manual Operations**: Users manually selecting streams should see all options
3. **General Stream Queries**: Default behavior for backward compatibility

## Future Considerations
If needed, additional filtering options could be added:
- Filter by specific M3U account ID
- Filter by M3U account type (STD vs XC)
- Combine multiple filter criteria
