# Implementation: Exclude Custom Playlist from Automated Updates

## Problem Description
The "custom" playlist in Dispatcharr is used for locally added streams and should not be updated the same way regular M3U playlists are. During automated playlist refresh cycles, the system was attempting to refresh the "custom" account, which doesn't need to pull new data from a remote server since it contains only manually added streams.

## Root Cause
The `refresh_playlists()` method in `AutomatedStreamManager` was refreshing all M3U accounts indiscriminately, including:
- Regular M3U accounts (with remote URLs that need periodic refresh)
- Custom accounts (with locally added streams that don't need remote refresh)

This was inefficient and could potentially cause errors when trying to refresh an account with no remote source.

## Solution
Modified the `refresh_playlists()` method to:
1. Fetch all M3U accounts using `get_m3u_accounts()`
2. Filter out "custom" accounts before refreshing
3. Only refresh non-custom M3U accounts
4. Log when custom accounts are skipped

### Custom Account Identification
An account is considered "custom" if:
- Its name is "custom" (case-insensitive), OR
- Both `server_url` and `file_path` are `None`

### Implementation Details

**Modified `automated_stream_manager.py`:**
```python
# Get all M3U accounts and filter out "custom" account
all_accounts = get_m3u_accounts()
if all_accounts:
    # Filter out "custom" account (it doesn't need refresh as it's for locally added streams)
    non_custom_accounts = [
        acc for acc in all_accounts
        if not (acc.get('name', '').lower() == 'custom' or 
               (acc.get('server_url') is None and acc.get('file_path') is None))
    ]
    
    # Refresh only non-custom accounts
    for account in non_custom_accounts:
        account_id = account.get('id')
        if account_id is not None:
            logging.info(f"Refreshing M3U account {account_id}")
            refresh_m3u_playlists(account_id=account_id)
```

## Changes Made

### Modified Files

**backend/automated_stream_manager.py:**
- Enhanced `refresh_playlists()` method to filter out custom accounts
- Added logic to fetch all M3U accounts before refreshing
- Implemented filtering based on account name and URL properties
- Added informative logging when accounts are skipped
- Maintained backward compatibility with `enabled_m3u_accounts` configuration
- Added fallback behavior if accounts cannot be fetched

**backend/tests/test_custom_playlist_exclusion.py (NEW):**
- Created comprehensive test suite with 6 tests
- Tests custom account exclusion by name
- Tests case-insensitive matching
- Tests exclusion by null URL/file_path
- Tests interaction with enabled_accounts configuration
- Tests edge cases and fallback behavior

**backend/tests/test_m3u_account_filtering.py:**
- Updated existing tests to mock `get_m3u_accounts()`
- Ensured all 7 existing tests continue to pass

## Impact

### Improvements
✅ Custom playlists no longer refreshed during automated cycles  
✅ More efficient - only refreshes accounts that need remote data  
✅ Reduced unnecessary API calls to Dispatcharr  
✅ Better logging - shows when accounts are skipped  

### Maintained Functionality
✅ Regular M3U accounts still refresh as expected  
✅ `enabled_m3u_accounts` configuration still works  
✅ Fallback behavior if accounts can't be fetched  
✅ All existing tests continue to pass  

## Testing

### Test Coverage
- **New tests**: 6 tests in `test_custom_playlist_exclusion.py`
- **Existing tests**: 7 tests in `test_m3u_account_filtering.py`
- **Total**: 13/13 tests passing ✓

### Test Scenarios
1. ✓ Custom account (by name) excluded from refresh
2. ✓ Case-insensitive matching ("custom", "Custom", "CUSTOM")
3. ✓ Accounts with null URLs excluded
4. ✓ Custom accounts excluded even when explicitly in enabled_accounts list
5. ✓ Only custom accounts present - no refresh occurs
6. ✓ Fallback behavior when accounts unavailable
7. ✓ Empty enabled_accounts still refreshes all non-custom accounts
8. ✓ Enabled_accounts respects custom exclusion
9. ✓ Changelog tracking still works

## Code Quality

- **Minimal changes**: Only modified the refresh logic, no breaking changes
- **Surgical approach**: Targeted fix that doesn't affect other functionality
- **Well-tested**: Comprehensive test coverage with edge cases
- **Backward compatible**: No breaking changes to existing functionality
- **Production-ready**: Includes fallback behavior and error handling

## Behavior Examples

### Before
```
Starting M3U playlist refresh...
Refreshing M3U account 1 (Provider 1)
Refreshing M3U account 2 (custom)      <- Unnecessary
Refreshing M3U account 3 (Provider 2)
```

### After
```
Starting M3U playlist refresh...
Refreshing M3U account 1 (Provider 1)
Refreshing M3U account 3 (Provider 2)
Skipped 1 'custom' account(s)          <- Informative logging
```

## Configuration Compatibility

The implementation respects the existing `enabled_m3u_accounts` configuration:

**When `enabled_m3u_accounts` is empty (default):**
- Refreshes all non-custom accounts

**When `enabled_m3u_accounts` has specific IDs:**
- Refreshes only the specified accounts
- Still excludes custom accounts even if listed
- Logs when accounts are skipped

## Edge Cases Handled

1. **Only custom accounts exist**: No refresh occurs (correct behavior)
2. **Accounts unavailable**: Falls back to legacy behavior (refresh all)
3. **Custom in enabled_accounts**: Excluded despite being explicitly listed
4. **Multiple custom accounts**: All are excluded
5. **Case variations**: "custom", "Custom", "CUSTOM" all excluded

## Future Considerations

This implementation provides a foundation for:
- More granular control over which accounts to refresh
- Potential UI toggle for manual custom account refresh (if ever needed)
- Better separation of concerns between local and remote data sources
