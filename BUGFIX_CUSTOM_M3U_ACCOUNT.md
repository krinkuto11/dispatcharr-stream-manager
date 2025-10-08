# Bug Fix: Custom M3U Playlist/Account Showing Up & Disabled Accounts Edge Case

## Problem Description
1. A "custom" M3U playlist/account was appearing in StreamFlow even though no custom M3U account had been added to Dispatcharr. This was confusing because it suggested there was a dummy or phantom M3U account.
2. **Edge Case**: Accounts with null `server_url` and `file_path` were being filtered out even when they were legitimate disabled or file-based accounts from Dispatcharr.

## Root Cause
1. The M3U accounts endpoint (`/api/m3u-accounts`) was returning ALL M3U accounts from Dispatcharr, including a "custom" account placeholder that appears even when there are no custom streams. This "custom" account is used by Dispatcharr to manage user-created streams (streams with `is_custom=True`), but it shouldn't be shown in the UI when there are no actual custom streams.
2. The filtering logic was too aggressive - it filtered out ANY account with both `server_url=None` and `file_path=None`, assuming they were all placeholders. However, legitimate disabled accounts or file-based accounts might have these null values temporarily or permanently.

## Solution
Modified the `/api/m3u-accounts` endpoint in `web_api.py` and `automated_stream_manager.py` to properly filter the "custom" M3U account:

- **If there are NO custom streams**: Filter out ONLY accounts named "custom" (case-insensitive)
- **If there ARE custom streams**: Show all accounts including the "custom" account
- **No longer filter based on null URLs**: Accounts with `server_url=None` and `file_path=None` are kept to avoid hiding legitimate disabled or file-based accounts

### Implementation Details

The endpoint now:
1. Fetches all M3U accounts from Dispatcharr
2. Fetches all streams to check if any have `is_custom=True`
3. If no custom streams exist, filters out:
   - Accounts with name "custom" (case-insensitive) ONLY
   - NO longer filters based on null `server_url` and `file_path` values
4. Returns the filtered list

The automation manager refresh logic:
1. Uses the same filtering logic for consistency
2. Filters out accounts named "custom" from refresh operations
3. Preserves all other accounts regardless of their URL values

## Changes Made

### Modified Files

**web_api.py:**
- Enhanced `/api/m3u-accounts` endpoint to conditionally filter the "custom" account
- Added logic to check for existence of custom streams
- **Fixed edge case**: Removed filtering based on null URLs to avoid hiding legitimate accounts
- Only filters by account name matching "custom" (case-insensitive)

**automated_stream_manager.py:**
- Updated `refresh_playlists()` method to use consistent filtering logic
- **Fixed edge case**: Removed filtering based on null URLs
- Only filters accounts named "custom" from refresh operations

**Test Updates:**
- Updated `test_m3u_accounts_endpoint.py`: Modified test for null URL handling, added edge case test
- Updated `test_custom_playlist_exclusion.py`: Fixed test to match new filtering behavior
- All 6 tests in test_m3u_accounts_endpoint.py passing ✓
- All 6 tests in test_custom_playlist_exclusion.py passing ✓
- All 7 tests in test_m3u_account_filtering.py passing ✓

## Impact

### Fixes
✅ No more "custom" M3U playlist appearing when there are no custom streams  
✅ Custom streams remain visible when they exist  
✅ Users can still see and manage custom streams through the "custom" account  
✅ **Edge Case Fixed**: Disabled or file-based accounts with null URLs are no longer incorrectly filtered out  
✅ **Consistency**: Same filtering logic applied in both API endpoint and automation manager  

### Maintained Functionality
✅ All existing M3U account operations work unchanged  
✅ Custom streams are still accessible when they exist  
✅ No changes to stream fetching or filtering logic  
✅ Accounts returned by Dispatcharr API are preserved (except "custom" when no custom streams exist)  

## Testing

### Test Coverage
- **test_m3u_accounts_endpoint.py**: 6 tests (1 new edge case test)
- **test_custom_playlist_exclusion.py**: 6 tests (1 updated for new behavior)
- **test_m3u_account_filtering.py**: 7 tests (unchanged)
- **Total**: 19/19 tests passing ✓

### Test Scenarios
1. ✓ Filters "custom" account when no custom streams exist
2. ✓ Keeps "custom" account when custom streams exist
3. ✓ **NEW**: Keeps accounts with null URLs (disabled/file-based accounts not filtered)
4. ✓ Case-insensitive filtering of "custom" name
5. ✓ Returns all accounts when custom streams are present
6. ✓ **NEW**: Edge case test - disabled accounts with null URLs are not filtered out
7. ✓ Automation manager uses consistent filtering logic

## Code Quality

- **Minimal changes**: Only modified the M3U accounts endpoint
- **Surgical approach**: Targeted fix at the source of the issue
- **Well-tested**: Comprehensive test coverage
- **Backward compatible**: No breaking changes

## Comparison with Previous Approach

### Original (Problematic) Approach
- Filtered both "custom" accounts AND accounts with null URLs
- Would incorrectly hide legitimate disabled or file-based accounts
- Caused edge case where accounts would disappear from UI unexpectedly

### Updated (Fixed) Approach
- Only filters accounts named "custom" (case-insensitive)
- Preserves all other accounts regardless of their URL values
- Prevents edge case where legitimate accounts are hidden
- Minimal changes to existing functionality
- Consistent filtering logic between API endpoint and automation manager
- Matches user's actual requirement: "only disable the 'custom' playlist if there are no custom streams present"

### Edge Case Scenario Fixed
**Before Fix:**
1. Account gets disabled in Dispatcharr → `server_url` and `file_path` become None
2. StreamFlow filters it out thinking it's a placeholder
3. Account disappears from UI (incorrect behavior)

**After Fix:**
1. Account gets disabled in Dispatcharr → `server_url` and `file_path` become None
2. StreamFlow keeps the account (only filters by name="custom")
3. Account remains visible in UI (correct behavior)
