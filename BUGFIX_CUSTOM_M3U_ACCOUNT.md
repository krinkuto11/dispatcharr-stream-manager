# Bug Fix: Custom M3U Playlist/Account Showing Up

## Problem Description
A "custom" M3U playlist/account was appearing in StreamFlow even though no custom M3U account had been added to Dispatcharr. This was confusing because it suggested there was a dummy or phantom M3U account.

## Root Cause
The M3U accounts endpoint (`/api/m3u-accounts`) was returning ALL M3U accounts from Dispatcharr, including a "custom" account placeholder that appears even when there are no custom streams. This "custom" account is used by Dispatcharr to manage user-created streams (streams with `is_custom=True`), but it shouldn't be shown in the UI when there are no actual custom streams.

## Solution
Modified the `/api/m3u-accounts` endpoint in `web_api.py` to conditionally filter out the "custom" M3U account:

- **If there are NO custom streams**: Filter out accounts named "custom" (case-insensitive) or accounts with both `server_url=None` and `file_path=None`
- **If there ARE custom streams**: Show all accounts including the "custom" account

### Implementation Details

The endpoint now:
1. Fetches all M3U accounts from Dispatcharr
2. Fetches all streams to check if any have `is_custom=True`
3. If no custom streams exist, filters out:
   - Accounts with name "custom" (case-insensitive)
   - Accounts with both `server_url=None` and `file_path=None` (placeholder accounts)
4. Returns the filtered list

## Changes Made

### Modified Files

**web_api.py:**
- Enhanced `/api/m3u-accounts` endpoint to conditionally filter the "custom" account
- Added logic to check for existence of custom streams
- Implemented filtering based on account properties

**Reverted Changes:**
- Reverted `api_utils.py` - removed `exclude_custom` parameter (not needed)
- Reverted `automated_stream_manager.py` - removed use of `exclude_custom` (not needed)

**Test Updates:**
- Removed `test_custom_stream_filtering.py` (no longer relevant)
- Created `test_m3u_accounts_endpoint.py` with 5 comprehensive tests
- Updated `test_m3u_account_filtering.py` to remove obsolete test

## Impact

### Fixes
✅ No more "custom" M3U playlist appearing when there are no custom streams  
✅ Custom streams remain visible when they exist  
✅ Users can still see and manage custom streams through the "custom" account  

### Maintained Functionality
✅ All existing M3U account operations work unchanged  
✅ Custom streams are still accessible when they exist  
✅ No changes to stream fetching or filtering logic  

## Testing

### Test Coverage
- **New tests in test_m3u_accounts_endpoint.py**: 5 tests
- **Existing tests**: 7 tests in test_m3u_account_filtering.py
- **Total**: 12/12 tests passing ✓

### Test Scenarios
1. ✓ Filters "custom" account when no custom streams exist
2. ✓ Keeps "custom" account when custom streams exist
3. ✓ Filters accounts with null URLs when no custom streams
4. ✓ Case-insensitive filtering of "custom" name
5. ✓ Returns all accounts when custom streams are present

## Code Quality

- **Minimal changes**: Only modified the M3U accounts endpoint
- **Surgical approach**: Targeted fix at the source of the issue
- **Well-tested**: Comprehensive test coverage
- **Backward compatible**: No breaking changes

## Comparison with Previous Approach

### Previous (Incorrect) Approach
- Filtered custom streams out of all stream operations
- Would have hidden custom streams from users
- Changed fundamental stream fetching behavior

### Current (Correct) Approach
- Only filters the "custom" M3U account from the accounts list when appropriate
- Preserves custom streams and their visibility
- Minimal changes to existing functionality
- Matches user's actual requirement: "only disable the 'custom' playlist if there are no custom streams present"
