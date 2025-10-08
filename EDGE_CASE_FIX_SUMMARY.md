# Edge Case Fix: Disabled Accounts with Null URLs

## Summary
Fixed an edge case where M3U accounts with null `server_url` and `file_path` were being incorrectly filtered out from the UI, even when they were legitimate disabled or file-based accounts.

## The Problem

### Original Filtering Logic
The filtering logic was checking two conditions:
```python
if not (acc.get('name', '').lower() == 'custom' or 
       (acc.get('server_url') is None and acc.get('file_path') is None))
```

This filtered out accounts that:
1. Had name "custom" (case-insensitive), **OR**
2. Had **both** `server_url=None` **AND** `file_path=None`

### Why This Was Problematic

The assumption was that accounts with both null URLs were "placeholders" that should be hidden. However, this assumption was flawed because:

1. **Disabled accounts**: When an account is disabled in Dispatcharr, it might have null URL values
2. **File-based accounts**: Some accounts might have null `server_url` while having a valid `file_path`
3. **Temporary states**: Accounts might temporarily have null values during configuration
4. **API behavior**: Dispatcharr might return accounts with null values for various legitimate reasons

## The Edge Case Scenario

### Before Fix
1. User has accounts: "Account A", "Account B", "Custom"
2. Account B gets disabled in Dispatcharr
3. Dispatcharr API returns Account B with `server_url=None` and `file_path=None`
4. StreamFlow filtering logic incorrectly filters out Account B (thinking it's a placeholder)
5. **Result**: Account B disappears from UI, confusing the user

### After Fix
1. User has accounts: "Account A", "Account B", "Custom"
2. Account B gets disabled in Dispatcharr
3. Dispatcharr API returns Account B with `server_url=None` and `file_path=None`
4. StreamFlow keeps Account B (only filters by name="custom")
5. **Result**: Account B remains visible in UI, user can manage it properly

## The Solution

### Updated Filtering Logic
```python
if acc.get('name', '').lower() != 'custom'
```

Now the filtering **only** checks the account name, not the URL values. This ensures:

1. **Only "custom" accounts are filtered**: When no custom streams exist
2. **All other accounts are preserved**: Regardless of their URL values
3. **Consistency**: Same logic applied in both `web_api.py` and `automated_stream_manager.py`

### Modified Files
- `backend/web_api.py`: Updated `/api/m3u-accounts` endpoint
- `backend/automated_stream_manager.py`: Updated `refresh_playlists()` method

## Test Coverage

### New Tests
1. `test_disabled_accounts_with_null_urls_are_not_filtered` - Ensures disabled accounts aren't filtered
2. `test_edge_case_disabled_account_still_shown` - Documents the specific edge case
3. `test_file_based_account_with_null_server_url_shown` - Tests file-based accounts
4. `test_all_accounts_disabled_except_custom` - Tests extreme edge case

### Updated Tests
1. `test_keeps_account_with_null_urls_when_no_custom_streams` - Renamed and updated expectations
2. `test_null_url_accounts_not_excluded` - Updated to reflect new behavior

### Test Results
- **22 tests** total in M3U-related test suites
- **All 22 passing** ✓

## Impact

### Fixes
✅ Disabled accounts with null URLs no longer disappear from UI  
✅ File-based accounts with null `server_url` remain visible  
✅ Consistent filtering logic between API and automation manager  
✅ Only "custom" account is filtered based on custom streams existence  

### No Breaking Changes
✅ All existing functionality maintained  
✅ Custom account filtering still works as expected  
✅ Backward compatible with existing configurations  
✅ No changes to API response structure  

## Related Documentation
- `BUGFIX_CUSTOM_M3U_ACCOUNT.md` - Original bug fix and edge case details
- `test_disabled_account_edge_case.py` - Comprehensive edge case tests
- `test_m3u_accounts_endpoint.py` - API endpoint tests
- `test_custom_playlist_exclusion.py` - Automation manager tests
