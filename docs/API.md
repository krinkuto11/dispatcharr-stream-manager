# API Documentation

All API endpoints are accessible at `http://localhost:3000/api/`

## Stream Checker Endpoints

### Get Status
```
GET /api/stream-checker/status
```
Returns service status, statistics, and queue information.

**Response:**
```json
{
  "running": true,
  "current_channel": "Channel Name",
  "queue_size": 5,
  "statistics": {
    "total_checked": 150,
    "total_failed": 3,
    "total_improved": 120
  }
}
```

### Start Service
```
POST /api/stream-checker/start
```
Starts the stream checking service.

### Stop Service
```
POST /api/stream-checker/stop
```
Stops the stream checking service.

### Get Queue
```
GET /api/stream-checker/queue
```
Returns current queue of channels pending check.

### Add to Queue
```
POST /api/stream-checker/queue/add
Content-Type: application/json

{
  "channel_ids": [1, 2, 3]
}
```
Adds specific channels to the checking queue.

### Clear Queue
```
POST /api/stream-checker/queue/clear
```
Removes all pending checks from the queue.

### Get Configuration
```
GET /api/stream-checker/config
```
Returns current stream checker configuration.

### Update Configuration
```
PUT /api/stream-checker/config
Content-Type: application/json

{
  "enabled": true,
  "check_interval": 300,
  "scoring": {
    "weights": {
      "bitrate": 0.30,
      "resolution": 0.25,
      "fps": 0.15,
      "codec": 0.10,
      "errors": 0.20
    }
  }
}
```
Updates stream checker configuration.

### Get Progress
```
GET /api/stream-checker/progress
```
Returns real-time progress of current check operation.

### Check Channel
```
POST /api/stream-checker/check-channel
Content-Type: application/json

{
  "channel_id": 123
}
```
Immediately checks a specific channel.

### Mark Updated
```
POST /api/stream-checker/mark-updated
Content-Type: application/json

{
  "channel_ids": [1, 2, 3]
}
```
Marks channels as updated and needing check.

## Automation Endpoints

### Get Automation Status
```
GET /api/automation/status
```
Returns automation service status and configuration.

### Start Automation
```
POST /api/automation/start
```
Starts the automation service.

### Stop Automation
```
POST /api/automation/stop
```
Stops the automation service.

### Get Configuration
```
GET /api/automation/config
```
Returns automation configuration.

### Update Configuration
```
PUT /api/automation/config
Content-Type: application/json

{
  "check_interval": 300,
  "enabled_features": {
    "playlist_refresh": true,
    "stream_discovery": true
  }
}
```
Updates automation configuration.

### Discover Streams
```
POST /api/automation/discover-streams
```
Manually triggers stream discovery cycle.

## Channel Endpoints

### Get Channels
```
GET /api/channels
```
Returns list of all channels.

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Results per page (default: 50)

### Get Channel Details
```
GET /api/channels/{channel_id}
```
Returns details for a specific channel.

### Get Channel Streams
```
GET /api/channels/{channel_id}/streams
```
Returns all streams for a specific channel.

## Regex Pattern Endpoints

### Get Patterns
```
GET /api/regex-patterns
```
Returns all configured regex patterns.

### Add Pattern
```
POST /api/regex-patterns
Content-Type: application/json

{
  "pattern": "^HD.*Sports$",
  "channel_id": 123,
  "enabled": true
}
```
Adds a new regex pattern.

### Update Pattern
```
PUT /api/regex-patterns/{pattern_id}
Content-Type: application/json

{
  "pattern": "^HD.*Sports$",
  "channel_id": 123,
  "enabled": true
}
```
Updates an existing pattern.

### Delete Pattern
```
DELETE /api/regex-patterns/{pattern_id}
```
Deletes a regex pattern.

### Test Pattern
```
POST /api/regex-patterns/test
Content-Type: application/json

{
  "pattern": "^HD.*Sports$"
}
```
Tests a regex pattern against available streams.

## Changelog Endpoints

### Get Changelog
```
GET /api/changelog
```
Returns activity history.

**Query Parameters:**
- `start_date` - Filter by start date (ISO format)
- `end_date` - Filter by end date (ISO format)
- `page` - Page number
- `per_page` - Results per page

### Clear Changelog
```
POST /api/changelog/clear
```
Clears the activity history.

## Health Check

### Health Status
```
GET /api/health
```
Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "automation": "running",
    "stream_checker": "running"
  }
}
```
