# Features

## Stream Management

### Automated M3U Playlist Management
- Automatically refreshes playlists every 5 minutes (configurable)
- Detects playlist changes in real-time
- Updates channels immediately when M3U refreshes
- Tracks update history in changelog

### Intelligent Stream Quality Checking
Multi-factor analysis of stream quality:
- **Bitrate**: Average kbps measurement
- **Resolution**: Width × height detection
- **Frame Rate**: FPS analysis
- **Video Codec**: H.265/H.264 identification
- **Audio Codec**: Detection and validation
- **Error Detection**: Decode errors, discontinuities, timeouts
- **Interlacing**: Detection and penalty
- **Dropped Frames**: Tracking and penalty

### Automatic Stream Reordering
- Best quality streams automatically moved to top
- Quality score calculation (0.0-1.0 scale)
- Configurable scoring weights
- Preserves stream availability

### Stream Discovery
- Regex pattern matching for automatic assignment
- New stream detection on playlist refresh
- Automatic channel assignment based on patterns
- Pattern testing interface

## Quality Analysis

### Scoring Formula
**Total Score = (Bitrate × 0.30) + (Resolution × 0.25) + (FPS × 0.15) + (Codec × 0.10) + (Errors × 0.20)**

### Configurable Weights
```json
{
  "weights": {
    "bitrate": 0.30,      // Default: 30%
    "resolution": 0.25,   // Default: 25%
    "fps": 0.15,          // Default: 15%
    "codec": 0.10,        // Default: 10%
    "errors": 0.20        // Default: 20%
  }
}
```

### Codec Preferences
- H.265/HEVC preference: Higher score for modern codecs
- Interlaced penalty: Lower score for interlaced content
- Dropped frames penalty: Lower score for streams with frame drops

### Sequential Checking
- One channel at a time to avoid overload
- Protects streaming providers from concurrent requests
- Queue-based processing
- Real-time progress tracking

## User Interface

### Dashboard
- System status overview
- Recent activity display
- Quick action buttons (start/stop automation)
- Real-time statistics

### Stream Checker Dashboard
- Service status monitoring
- Queue visualization
- Progress tracking with details
- Quality score display
- Configuration interface

### Channel Configuration
- Visual regex pattern editor
- Pattern testing interface
- Live stream matching preview
- Enable/disable patterns

### Automation Settings
- Interval configuration
- Feature toggles
- Global check scheduling
- Quality analysis parameters

### Changelog
- Complete activity history
- Date range filtering
- Action categorization
- Detail expansion

### Setup Wizard
- Guided initial configuration
- Dispatcharr connection testing
- Configuration validation
- Quick start assistance

## Automation Features

### M3U Update Tracking
- Automatic detection of playlist updates
- Immediate channel queuing on update
- Update timestamp tracking
- Prevents duplicate checking

### Scheduled Global Checks
- Configurable off-peak checking (default: 3 AM)
- Full channel queue on schedule
- Manual global check trigger
- Schedule enable/disable toggle

### Queue Management
- Priority-based queue system
- Manual channel addition
- Queue clearing
- Duplicate prevention

### Real-Time Progress
- Current channel display
- Stream-by-stream progress
- Quality score updates
- Error reporting

## Data Management

### Changelog
- All automation actions logged
- Timestamps and details
- Persistent storage
- Filterable history

### Configuration Persistence
- All settings in JSON files
- Docker volume mounting
- Easy backup and restore
- Version-agnostic format

### Setup Wizard
- First-run configuration
- Connection validation
- Default settings
- Quick deployment

## API Integration

### REST API
- 30+ endpoints
- JSON request/response
- Authentication support
- Error handling

### Real-Time Updates
- Polling for status
- Progress tracking
- Queue monitoring
- Statistics updates

### Dispatcharr Integration
- Full API support
- Token-based authentication
- Channel management
- Stream operations

## Technical Features

### Docker Deployment
- Single container architecture
- Volume-based persistence
- Environment variable configuration
- Health checks

### Error Handling
- Automatic retry logic
- Error logging
- Graceful degradation
- User notifications

### Performance
- Sequential stream checking
- Efficient queue processing
- Minimal API calls
- Resource optimization

### Logging
- Comprehensive activity logs
- Error tracking
- Debug mode support
- Persistent changelog
