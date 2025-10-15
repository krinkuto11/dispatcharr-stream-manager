# M3U Accounts Endpoint Performance Optimization

## Issue
The `/api/m3u-accounts` endpoint was experiencing slow load times when M3U playlists contained 3000+ streams. Users reported that the checkbox UI took a long time to show after reloading the page.

## Root Cause
The endpoint was calling `get_streams(log_result=False)` to fetch **all streams** from the Dispatcharr API just to check if any custom streams exist. With 3000+ streams and pagination at 100 streams per page, this resulted in ~30 API calls every time the endpoint was accessed.

```python
# Before (slow):
all_streams = get_streams(log_result=False)  # Fetches ALL 3000+ streams
has_custom_streams = any(s.get('is_custom', False) for s in all_streams)
```

## Solution
Implemented a new `has_custom_streams()` function that efficiently checks for custom streams without fetching all streams:

1. **First attempt**: Try API filtering with `?is_custom=true&page_size=1`
   - If supported by API, returns result in 1 call
   
2. **Fallback**: If filtering not supported, paginate with `page_size=100` and exit early
   - Stops as soon as a custom stream is found
   - Uses larger page size (100 vs 30) for fewer API calls

```python
# After (fast):
has_custom = has_custom_streams()  # 1-3 API calls instead of ~30
```

## Performance Impact

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| API filtering supported, custom streams exist | ~30 calls | 1 call | **30x faster** |
| API filtering not supported, custom stream in first page | ~30 calls | 2 calls | **15x faster** |
| No custom streams, all pages checked | ~30 calls | ~30 calls | Same (worst case) |

## Files Changed
- `backend/api_utils.py`: Added `has_custom_streams()` function
- `backend/web_api.py`: Updated `/api/m3u-accounts` endpoint to use new function
- `backend/tests/`: Updated 15 existing tests + added 5 new performance tests

## Benefits
1. **Faster UI loading**: Users with 3000+ streams will see checkboxes appear much faster
2. **Reduced API load**: Significantly fewer calls to Dispatcharr API
3. **Early exit optimization**: Stops searching as soon as custom stream found
4. **Backward compatible**: No changes to API contract or behavior

## Testing
All 20 tests pass, including:
- 7 tests for M3U accounts endpoint functionality
- 3 tests for disabled account edge cases
- 5 tests for non-active playlists filtering
- 5 new tests for performance optimization

Run tests:
```bash
cd backend
python -m unittest tests/test_m3u_accounts_endpoint.py \
                   tests/test_disabled_account_edge_case.py \
                   tests/test_non_active_playlists_filtering.py \
                   tests/test_has_custom_streams_performance.py -v
```

## Related Issues
This fix addresses the performance issue reported where UI checkbox loading was slow with 3000+ streams in M3U playlists.
