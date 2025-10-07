# Regex Pattern Whitespace Handling

## Overview

The regex pattern matching system now automatically handles different types of whitespace characters in stream names. This ensures that patterns like "TVP 1" will match streams regardless of whether they use regular spaces, non-breaking spaces, tabs, or double spaces.

## Problem

Previously, if you configured a regex pattern like `TVP 1` (with a regular space), it would only match streams that had exactly the same type of space character. Streams with non-breaking spaces, tabs, or multiple spaces would not match, even though they appeared visually similar.

### Example of the Issue

**Pattern:** `TVP 1`

**Streams:**
- ✅ `PL| TVP 1 FHD` - **Worked** (regular space)
- ❌ `PL: TVP 1 HD` - **Didn't work** (non-breaking space)
- ❌ `PL: TVP 1 4K` - **Didn't work** (double space)
- ❌ `PL VIP: TVP 1 RAW` - **Didn't work** (tab character)

## Solution

The system now automatically converts literal spaces in your patterns to flexible whitespace matching. When you enter `TVP 1`, the system internally converts it to match any whitespace characters:

- Regular space (` `)
- Non-breaking space (`\u00a0`)
- Tab character (`\t`)
- Multiple consecutive spaces
- En space, em space, and other Unicode whitespace

## How It Works

When you configure a pattern with spaces, the system:

1. Takes your pattern (e.g., `TVP 1`)
2. Converts literal spaces to the regex pattern `\s+` (which matches one or more whitespace characters)
3. Matches against stream names using the flexible pattern

### Technical Details

The conversion happens in three places:
- `automated_stream_manager.py` - During automated stream discovery
- `web_api.py` - In the pattern testing endpoints

The transformation uses: `re.sub(r' +', r'\\s+', pattern)`

This replaces one or more consecutive spaces with `\s+`, which matches any whitespace.

## Impact on Existing Patterns

### Simple Text Patterns
**Before and After:** Work the same way, but now more flexible

Example: `CNN HD`
- Still matches: `CNN HD`, `US: CNN HD Premium`
- Now also matches: `CNN  HD` (double space), `CNN\tHD` (tab)

### Regex Patterns
**Before and After:** Continue to work as expected

Example: `.*ESPN.*`, `BBC (One|Two|Three)`, `ESPN[0-9]+`
- All regex features continue to work
- Space handling is improved within these patterns too

### Patterns Already Using `\s+`
**Before and After:** Work identically

Example: `FOO\s+BAR`
- No change in behavior
- Already handled whitespace flexibly

## Best Practices

### For Simple Channel Names
Just enter the text as you see it:
- `TVP 1` - Works great!
- `BBC One` - Perfect!
- `CNN International` - Excellent!

### For Advanced Patterns
You can still use regex features:
- `.*ESPN.*` - Matches anything containing ESPN
- `HBO (HD|FHD|4K)` - Matches HBO with different quality labels
- `^US:.*` - Matches streams starting with "US:"

### For Exact Matching
If you need to match exact text without flexibility, use word boundaries:
- `\bTVP 1\b` - Matches "TVP 1" but not "TVP 10" or "TVP 1A"
- `\bCNN\b` - Matches "CNN" but not "CNN2" or "CNNE"

## Testing Your Patterns

Use the built-in pattern tester in the Channel Configuration interface:

1. Enter your pattern (e.g., `TVP 1`)
2. Click "Test Patterns Against Live Streams"
3. See which streams match
4. Verify the results are what you expect

The tester uses the same matching logic as the automated stream assignment system.

## Migration Notes

### Existing Configurations
No changes needed! Your existing patterns will automatically benefit from the improved whitespace handling.

### If You Experience Issues
If a pattern starts matching too many streams after this update:

1. Use more specific patterns: `TVP 1 HD` instead of `TVP 1`
2. Use word boundaries: `\bTVP 1\b` for exact matching
3. Use anchors: `^TVP 1 ` to match only at the start

## Examples

### Example 1: Polish TV Channels
```
Pattern: TVP 1
Matches:
  ✓ PL| TVP 1 FHD
  ✓ PL: TVP 1 HD  
  ✓ PL: TVP 1 4K
  ✓ PL VIP: TVP 1 RAW
```

### Example 2: Sports Channels
```
Pattern: ESPN HD
Matches:
  ✓ ESPN HD
  ✓ US: ESPN HD
  ✓ ESPN  HD (double space)
  ✓ ESPN	HD (tab character)
```

### Example 3: Multiple Regex Patterns
```
Patterns: 
  - .*CNN.*
  - CNN International
  - CNN (HD|FHD|4K)

All patterns benefit from flexible whitespace matching
```

## Summary

This improvement makes pattern matching more robust and user-friendly. You can now rely on patterns working consistently regardless of the whitespace characters used in stream names, while still maintaining full regex functionality for advanced use cases.
