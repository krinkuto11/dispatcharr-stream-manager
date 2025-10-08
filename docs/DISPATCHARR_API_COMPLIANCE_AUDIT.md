# Dispatcharr API Compliance Audit Report

**Date**: 2024
**Audit Scope**: All functions accessing the Dispatcharr API
**Swagger Spec**: `/backend/swagger.json` (Swagger 2.0 / OpenAPI specification)

## Executive Summary

✅ **All API calls to Dispatcharr are COMPLIANT with the swagger.json specification.**

A comprehensive audit was conducted of all Python files that interact with the Dispatcharr API, checking for:
- Correct endpoint paths
- Proper HTTP methods (GET, POST, PATCH, DELETE)
- Correct request/response payloads
- Proper authentication mechanisms
- Support for pagination and query parameters

## Files Audited

The following files contain API calls to Dispatcharr:

1. **`backend/api_utils.py`** - Main API utilities module (9 API calls)
2. **`backend/channels_upload.py`** - Channel synchronization (5 API calls)
3. **`backend/groups_upload.py`** - Group management (4 API calls)
4. **`backend/automated_stream_manager.py`** - Stream automation (5 API calls)
5. **`backend/stream_checker_service.py`** - Stream validation (5 API calls)
6. **`backend/dispatcharr-stream-sorter.py`** - Stream sorting (3 API calls)
7. **`backend/web_api.py`** - Test connection endpoint (1 API call to Dispatcharr)

**Total**: 32 API calls analyzed

## Detailed Findings

### 1. Authentication (`/api/accounts/token/`)

**Swagger Specification**:
- Endpoint: `POST /api/accounts/token/`
- Required fields: `username` (string), `password` (string)
- Returns: `access` token

**Implementation Status**: ✅ COMPLIANT

All authentication implementations correctly use:
- POST method (not GET)
- Required fields: `username` and `password`
- Proper JSON payload format

**Files implementing login**:
- `api_utils.py` (line 83-92)
- `channels_upload.py` (line 100)
- `groups_upload.py` (line 88)
- `web_api.py` (line 671)

**Example (api_utils.py)**:
```python
login_url = f"{base_url}/api/accounts/token/"
resp = requests.post(
    login_url,
    headers={"Content-Type": "application/json"},
    json={"username": username, "password": password}
)
```

### 2. Channel Operations

#### 2.1 List Channels (`GET /api/channels/channels/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/channels/`
- Supported query parameters: `search`, `ordering`, `page`, `page_size`
- Returns: Paginated list of channels

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `api_utils.py` - Not directly, uses other functions
- `channels_upload.py` (line 196) - `fetch_data_from_url(f"{_get_base_url()}/api/channels/channels/")`
- `automated_stream_manager.py` (line 484, 514) - Channel fetching
- `web_api.py` (line 188) - Proxying to Dispatcharr

#### 2.2 Get/Update Single Channel (`/api/channels/channels/{id}/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/channels/{id}/`
- Methods: GET, PUT, PATCH, DELETE
- Path parameter: `id` (integer)

**Implementation Status**: ✅ COMPLIANT

**Note**: The code uses Python variable names like `channel_id` or `cid`, but these are mapped to the `{id}` path parameter correctly at runtime.

**Files using this endpoint**:
- `api_utils.py` (line 352) - PATCH to update channel
- `channels_upload.py` (line 228) - PATCH to update channel
- `stream_checker_service.py` (line 911, 1112) - GET channel data

#### 2.3 Get Channel Streams (`/api/channels/channels/{channel_id}/streams/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/channels/{channel_id}/streams/`
- Path parameter: `channel_id` (string)

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `api_utils.py` (line 330-332) - `fetch_channel_streams()` function
- `automated_stream_manager.py` (line 506, 567, 620) - Stream fetching

### 3. Stream Operations

#### 3.1 List Streams (`GET /api/channels/streams/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/streams/`
- Supported query parameters: `search`, `ordering`, `page`, `page_size`
- Returns: Paginated list of streams

**Implementation Status**: ✅ COMPLIANT

**Special Note**: The code correctly uses the `page_size` parameter to optimize pagination:

```python
url = f"{base_url}/api/channels/streams/?page_size=100"
```

**Files using this endpoint**:
- `api_utils.py` (line 437) - `get_streams()` function with pagination
- `dispatcharr-stream-sorter.py` - Stream listing

#### 3.2 Get/Update Single Stream (`/api/channels/streams/{id}/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/streams/{id}/`
- Methods: GET, PUT, PATCH, DELETE
- Path parameter: `id` (integer)

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `stream_checker_service.py` (line 861, 1015) - GET stream data
- `dispatcharr-stream-sorter.py` (line 1065) - Stream operations

#### 3.3 Create Channel from Stream (`POST /api/channels/channels/from-stream/`)

**Swagger Specification**:
- Endpoint: `POST /api/channels/channels/from-stream/`
- Required field: `stream_id` (integer)
- Optional fields: `channel_number`, `name`, `channel_profile_ids`

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `api_utils.py` (line 478-488) - `create_channel_from_stream()` function

```python
url = f"{_get_base_url()}/api/channels/channels/from-stream/"
data = {"stream_id": stream_id}
if channel_number is not None:
    data["channel_number"] = channel_number
# ... other optional fields
return post_request(url, data)
```

### 4. Group Operations

#### 4.1 List Groups (`GET /api/channels/groups/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/groups/`
- Returns: List of channel groups

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `groups_upload.py` (line 169) - `fetch_existing_groups()`
- `dispatcharr-stream-sorter.py` - Group listing

#### 4.2 Get/Update Single Group (`/api/channels/groups/{id}/`)

**Swagger Specification**:
- Endpoint: `GET /api/channels/groups/{id}/`
- Methods: GET, PUT, PATCH, DELETE
- Path parameter: `id` (integer)

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `groups_upload.py` (line 211) - PATCH to update group

### 5. M3U Account Operations

#### 5.1 List M3U Accounts (`GET /api/m3u/accounts/`)

**Swagger Specification**:
- Endpoint: `GET /api/m3u/accounts/`
- Returns: List of M3U accounts

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `api_utils.py` (line 418) - `get_m3u_accounts()` function
- `web_api.py` (line 490) - Via `api_utils.get_m3u_accounts()`

#### 5.2 Refresh M3U Playlists (`POST /api/m3u/refresh/`)

**Swagger Specification**:
- Endpoint: `POST /api/m3u/refresh/` - Refresh all accounts
- Endpoint: `POST /api/m3u/refresh/{account_id}/` - Refresh specific account
- Path parameter: `account_id` (integer)

**Implementation Status**: ✅ COMPLIANT

**Files using this endpoint**:
- `api_utils.py` (line 397-402) - `refresh_m3u_playlists()` function

```python
if account_id:
    url = f"{base_url}/api/m3u/refresh/{account_id}/"
else:
    url = f"{base_url}/api/m3u/refresh/"
resp = post_request(url, {})
```

## Code Quality Observations

### Strengths

1. **Consistent Error Handling**: All API calls use try-except blocks with appropriate error logging
2. **Token Management**: Proper token validation and refresh logic in `api_utils.py`
3. **Pagination Support**: Correctly implements pagination with `page_size` parameter
4. **Retry Logic**: 401 errors trigger automatic token refresh and retry
5. **Type Hints**: Most functions include proper type hints for parameters and return values

### Best Practices Followed

1. **Centralized API Functions**: Core API operations are centralized in `api_utils.py`
2. **DRY Principle**: Reusable functions like `fetch_data_from_url()`, `patch_request()`, `post_request()`
3. **Proper HTTP Methods**: Correct use of GET, POST, PATCH for different operations
4. **Query Parameters**: Properly formatted query strings for pagination
5. **Authorization Headers**: Consistent use of Bearer token authentication

## Parameter Naming Clarification

**Important Note**: The swagger spec uses `{id}` as the path parameter name in many endpoints (e.g., `/api/channels/channels/{id}/`), while the Python code often uses descriptive variable names like `channel_id`, `stream_id`, or `cid`.

**This is COMPLIANT**: The parameter names in the swagger spec refer to the REST API path structure, not the Python variable names. When the code constructs URLs like:

```python
url = f"{base_url}/api/channels/channels/{channel_id}/"
```

The Python variable `channel_id` is correctly substituted into the `{id}` position in the API path.

## Endpoints Not Used

The following Dispatcharr API endpoints are defined in the swagger spec but not currently used in the codebase:

- `/api/accounts/auth/login/` - Alternative login endpoint
- `/api/accounts/auth/logout/` - Logout endpoint
- `/api/accounts/token/refresh/` - Token refresh endpoint
- `/api/channels/channels/assign/` - Auto-assign channel numbers
- `/api/channels/channels/bulk-delete/` - Bulk delete channels
- `/api/channels/logos/*` - Logo management endpoints
- Various EPG-related endpoints
- VOD-related endpoints

**Recommendation**: These are not issues. They represent Dispatcharr features that StreamFlow doesn't currently need to use.

## Conclusion

✅ **All 32 API calls to Dispatcharr are fully compliant with the swagger.json specification.**

The codebase demonstrates:
- Correct endpoint usage
- Proper HTTP methods
- Valid request payloads
- Appropriate authentication
- Good error handling practices

**No changes are required.** The implementation correctly follows the Dispatcharr API specification.

## Recommendations for Future Development

1. **Token Refresh**: Consider implementing the `/api/accounts/token/refresh/` endpoint for more efficient token management
2. **Bulk Operations**: Consider using bulk endpoints like `/api/channels/channels/bulk-delete/` for better performance
3. **Error Response Handling**: Document expected error responses from Dispatcharr for each endpoint
4. **API Version Tracking**: Add version checking to ensure compatibility with future Dispatcharr API changes

## Audit Methodology

This audit was conducted through:

1. **Swagger Specification Analysis**: Parsed and analyzed the complete swagger.json file
2. **Code Review**: Manual inspection of all Python files making Dispatcharr API calls
3. **Endpoint Mapping**: Verified each API call against the swagger specification
4. **Method Verification**: Confirmed correct HTTP methods (GET, POST, PATCH, DELETE)
5. **Payload Validation**: Verified request payloads match schema definitions
6. **Parameter Analysis**: Confirmed correct use of path and query parameters

---

**Auditor Notes**: This audit confirms that the StreamFlow application correctly implements all Dispatcharr API interactions according to the provided swagger specification. No compliance issues were found.
