# Pipeline System Documentation

## Overview

The StreamFlow application now supports 5 different pipeline modes, each with different behaviors for updating M3U playlists, matching streams to channels, and checking stream quality. This provides flexibility for users with different needs and connection constraints.

## Pipeline Modes

### Pipeline 1: Update → Match → Check (with 2-hour immunity)

**Configuration:**
```json
{
  "pipeline_mode": "pipeline_1",
  "queue": {
    "check_on_update": true
  }
}
```

**Behavior:**
1. Every X minutes (configurable): Update M3U playlists
2. Match new streams to channels via regex patterns
3. Check channels that received new streams (respects 2-hour immunity)
   - Only checks streams that haven't been checked in the last 2 hours
   - Uses cached scores for recently checked streams

**Use Case:** Users with moderate connection limits who want automatic updates, matching, and quality checking with immunity to prevent excessive checking.

---

### Pipeline 1.5: Pipeline 1 + Scheduled Global Action

**Configuration:**
```json
{
  "pipeline_mode": "pipeline_1_5",
  "queue": {
    "check_on_update": true
  },
  "global_check_schedule": {
    "enabled": true,
    "frequency": "daily",  // or "monthly"
    "hour": 3,
    "minute": 0,
    "day_of_month": 1  // for monthly
  }
}
```

**Behavior:**
- All features of Pipeline 1
- **PLUS:** Scheduled Global Action (daily or monthly)
  - Updates all M3U playlists
  - Matches all streams
  - Checks ALL channels, bypassing 2-hour immunity
  - Typically scheduled during off-peak hours (e.g., 3 AM)

**Use Case:** Users who want automatic updates with immunity during the day, but want a complete check of all channels during off-peak hours.

---

### Pipeline 2: Update → Match only (no automatic checking)

**Configuration:**
```json
{
  "pipeline_mode": "pipeline_2",
  "queue": {
    "check_on_update": false
  }
}
```

**Behavior:**
1. Every X minutes: Update M3U playlists
2. Match new streams to channels via regex patterns
3. **NO automatic stream checking**

**Use Case:** Users with strict connection limits who only want to keep their channels populated with streams, but don't want automatic quality checking.

---

### Pipeline 2.5: Pipeline 2 + Scheduled Global Action

**Configuration:**
```json
{
  "pipeline_mode": "pipeline_2_5",
  "queue": {
    "check_on_update": false
  },
  "global_check_schedule": {
    "enabled": true,
    "frequency": "daily",
    "hour": 3,
    "minute": 0
  }
}
```

**Behavior:**
- All features of Pipeline 2
- **PLUS:** Scheduled Global Action (daily or monthly)
  - Updates all M3U playlists
  - Matches all streams
  - Checks ALL channels, bypassing immunity

**Use Case:** Users with connection limits who want to avoid checking during the day, but want a complete check during off-peak hours.

---

### Pipeline 3: Only Scheduled Global Action

**Configuration:**
```json
{
  "pipeline_mode": "pipeline_3",
  "queue": {
    "check_on_update": false
  },
  "global_check_schedule": {
    "enabled": true,
    "frequency": "daily",
    "hour": 3,
    "minute": 0
  }
}
```

**Behavior:**
- **NO automatic updates or matching**
- **ONLY:** Scheduled Global Action (daily or monthly)
  - Updates all M3U playlists
  - Matches all streams
  - Checks ALL channels

**Use Case:** Users who want complete control and only want the system to run once per day/month at a specific time.

---

## Global Action

### What is a Global Action?

A Global Action is a comprehensive operation that:
1. **Updates** all enabled M3U playlists
2. **Matches** all streams to channels via regex patterns
3. **Checks** ALL channels, bypassing the 2-hour immunity period

### When Does it Run?

Global Actions run:
- **Automatically:** Based on the scheduled time (for Pipeline 1.5, 2.5, and 3)
- **Manually:** Via the "Global Action" button in the UI or API call

### Force Check Behavior

During a Global Action, all channels are marked for "force check" which:
- Bypasses the 2-hour immunity period
- Analyzes ALL streams in every channel (not just new ones)
- Updates all stream quality scores
- Re-ranks all channels based on fresh analysis

---

## API Endpoints

### Trigger Manual Global Action

```
POST /api/stream-checker/global-action
```

**Response:**
```json
{
  "message": "Global action triggered successfully",
  "status": "in_progress",
  "description": "Update, Match, and Check all channels in progress"
}
```

### Get Stream Checker Status

```
GET /api/stream-checker/status
```

**Response includes:**
```json
{
  "running": true,
  "config": {
    "pipeline_mode": "pipeline_1_5",
    "global_check_schedule": {
      "enabled": true,
      "frequency": "daily",
      "hour": 3,
      "minute": 0
    }
  },
  "last_global_check": "2025-10-13T03:00:15.123Z"
}
```

---

## Technical Implementation

### Key Classes and Methods

#### StreamCheckerService

**New Methods:**
- `_perform_global_action()`: Executes complete Update→Match→Check cycle
- `trigger_global_action()`: Manually triggers a global action
- `_queue_updated_channels()`: Now respects pipeline mode

**Updated Methods:**
- `_check_global_schedule()`: Checks pipeline mode before running
- `_queue_all_channels(force_check=False)`: Supports force checking

#### ChannelUpdateTracker

**New Methods:**
- `mark_channel_for_force_check(channel_id)`: Sets force check flag
- `should_force_check(channel_id)`: Checks if channel should be force checked
- `clear_force_check(channel_id)`: Clears force check flag

### Queue Management

The queue system prevents:
- Duplicate channel checking
- Race conditions during M3U updates
- Checking channels that are already queued or in progress
- Global actions from stacking up

### 2-Hour Immunity System

Streams are tracked per channel:
- Each stream's last check timestamp is stored
- When checking a channel, only unchecked streams (or those not checked in 2 hours) are analyzed
- Recently checked streams use cached quality scores
- Force check bypasses this immunity

---

## Configuration Examples

### For Users Without Connection Limits
```json
{
  "pipeline_mode": "pipeline_1",
  "queue": {
    "check_on_update": true,
    "max_channels_per_run": 50
  }
}
```

### For Users With Moderate Limits
```json
{
  "pipeline_mode": "pipeline_1_5",
  "queue": {
    "check_on_update": true,
    "max_channels_per_run": 20
  },
  "global_check_schedule": {
    "enabled": true,
    "frequency": "daily",
    "hour": 3,
    "minute": 0
  }
}
```

### For Users With Strict Limits
```json
{
  "pipeline_mode": "pipeline_3",
  "global_check_schedule": {
    "enabled": true,
    "frequency": "daily",
    "hour": 3,
    "minute": 0
  }
}
```

---

## Migration Guide

Existing installations will automatically use Pipeline 1.5 (the default). To change:

1. Via API:
```bash
curl -X PUT http://localhost:3000/api/stream-checker/config \
  -H "Content-Type: application/json" \
  -d '{"pipeline_mode": "pipeline_2_5"}'
```

2. Via Configuration File:
Edit `/app/data/stream_checker_config.json`:
```json
{
  "pipeline_mode": "pipeline_2_5"
}
```

3. Restart the service for changes to take effect.

---

## Testing

All pipeline modes are thoroughly tested:
- 146 total tests pass
- 11 tests specifically for pipeline modes
- Tests cover:
  - Pipeline mode selection
  - Force check behavior
  - Global action functionality
  - Queue management
  - Scheduled checks

---

## Future Enhancements

Potential future improvements:
- UI for selecting pipeline mode
- Per-channel pipeline overrides
- Custom pipeline schedules per channel
- Analytics dashboard showing check frequency and patterns
- Dynamic pipeline adjustment based on connection speed
