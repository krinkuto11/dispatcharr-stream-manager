# StreamFlow for Dispatcharr

Automated stream management system for Dispatcharr IPTV services with intelligent quality checking and automatic stream reordering.
1. Updates playlists.
2. Adds Streams to channels via Regex
3. Checks streams
4. Reorders the streams to ensure the best ones are first

## Quick Deployment

```bash
git clone https://github.com/krinkuto11/streamflow.git
cd streamflow
cp .env.template .env
# Edit .env with your Dispatcharr instance details
docker compose up -d
```

**Access**: http://localhost:3000

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## Features

- **Automated M3U Playlist Management**: Refresh playlists every 5 minutes (configurable)
- **Stream Quality Checking**: Analyze streams for bitrate, resolution, FPS, codec quality, and errors
- **Automatic Stream Reordering**: Best quality streams moved to the top
- **Stream Discovery**: Regex patterns for automatic stream-to-channel assignment
- **Web Interface**: React-based UI for monitoring and configuration
- **REST API**: Full API access for all operations

## Architecture

Single Docker container with:
- Flask backend (Python) serving REST API
- React frontend for web interface
- Persistent configuration storage via Docker volumes
- Single port (3000) for all access
- Multi-platform support: linux/amd64, linux/arm64

## Configuration

All configuration stored in JSON files in `/app/data` (Docker volume):
- `automation_config.json` - Automation settings (intervals, features)
- `stream_checker_config.json` - Stream checking parameters and scoring weights
- `channel_regex_config.json` - Regex patterns for stream assignment
- `channel_updates.json` - Channel update tracking
- `changelog.json` - Activity history

## Project Structure

```
backend/
  ├── automated_stream_manager.py    # Core automation engine
  ├── stream_checker_service.py      # Stream quality checking
  ├── web_api.py                      # Flask REST API
  ├── api_utils.py                    # Dispatcharr API utilities
  └── ...
frontend/
  └── src/
      ├── components/                 # React components
      └── services/                   # API client
docs/
  ├── DEPLOYMENT.md                   # Detailed deployment guide
  ├── API.md                          # API documentation
  └── FEATURES.md                     # Feature details
```

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Installation and deployment instructions
- [API Documentation](docs/API.md) - REST API endpoints and usage
- [Features](docs/FEATURES.md) - Detailed feature descriptions

## Requirements

- Docker and Docker Compose
- Dispatcharr instance with API access

## License

See [LICENSE](LICENSE) file for details.
