# Native ARM Runner Setup

## Overview

This repository now uses native ARM runners for building Docker images, providing faster and more reliable ARM64 builds compared to the previous QEMU emulation approach.

## What Changed

### Before
- Single job running on `ubuntu-latest` (x86_64)
- Used Docker Buildx with QEMU emulation to build ARM64 images
- Both architectures built sequentially using emulation
- Slower build times for ARM64 (3-5x slower than native)

### After
- Matrix strategy with platform-specific native runners:
  - `ubuntu-latest` for linux/amd64 (x86_64)
  - `ubuntu-22.04-arm` for linux/arm64 (ARM64)
- Each architecture builds on its native hardware
- Parallel builds for both architectures
- Significantly faster ARM64 builds
- Separate merge job combines both into multi-arch manifest

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Build Job (Matrix Strategy)                                 │
├─────────────────────────────────┬───────────────────────────┤
│ ubuntu-latest                   │ ubuntu-22.04-arm          │
│ Platform: linux/amd64           │ Platform: linux/arm64     │
├─────────────────────────────────┼───────────────────────────┤
│ 1. Checkout code                │ 1. Checkout code          │
│ 2. Setup Node.js                │ 2. Setup Node.js          │
│ 3. Build frontend               │ 3. Build frontend         │
│ 4. Setup Docker Buildx          │ 4. Setup Docker Buildx    │
│ 5. Build & push by digest       │ 5. Build & push by digest │
│ 6. Upload digest artifact       │ 6. Upload digest artifact │
└─────────────────────────────────┴───────────────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Merge Job             │
                  │ (ubuntu-latest)       │
                  ├───────────────────────┤
                  │ 1. Download digests   │
                  │ 2. Create manifest    │
                  │ 3. Push final tags    │
                  └───────────────────────┘
```

## Benefits

1. **Faster Builds**: Native ARM64 compilation is 3-5x faster than emulation
2. **Better Reliability**: No QEMU emulation issues or quirks
3. **Accurate Testing**: Builds run on the same architecture as deployment
4. **Parallel Execution**: Both architectures build simultaneously
5. **Resource Efficiency**: Native builds use less memory and CPU

## Technical Details

### Build Process

Each platform job:
1. Builds the Docker image for its native architecture
2. Pushes the image by digest (not by tag)
3. Uploads the image digest as an artifact

The merge job:
1. Downloads digests from both platform builds
2. Uses `docker buildx imagetools create` to combine them
3. Creates a multi-arch manifest with proper tags
4. Pushes the final tagged manifest to GHCR

### Tags Created

On release:
- `ghcr.io/krinkuto11/streamflow:latest`
- `ghcr.io/krinkuto11/streamflow:<version>` (e.g., v1.0.0)
- `ghcr.io/krinkuto11/streamflow:<major>.<minor>` (e.g., 1.0)
- `ghcr.io/krinkuto11/streamflow:<major>` (e.g., 1)

On merged PR to dev:
- `ghcr.io/krinkuto11/streamflow:pr-test`

### Cache Strategy

Each architecture maintains its own build cache:
- Key includes both OS and architecture: `${{ runner.os }}-${{ runner.arch }}-buildx-${{ github.sha }}`
- Prevents cache conflicts between different architectures
- Improves cache hit rates for incremental builds

## Requirements

- GitHub Actions must have access to `ubuntu-22.04-arm` runners
- For GitHub-hosted runners, this is available on GitHub Enterprise or with larger runner plans
- For self-hosted runners, you need to set up ARM64 machines with the `ubuntu-22.04-arm` label

## Troubleshooting

### ARM Runner Not Available
**Error**: `No runner matching 'ubuntu-22.04-arm' found`

**Solutions**:
1. Verify your GitHub plan includes ARM runners
2. Set up self-hosted ARM64 runners with the correct label
3. Temporarily fall back to emulation by changing `ubuntu-22.04-arm` to `ubuntu-latest` and using QEMU

### Build Failures on One Platform
If one platform fails, the merge job won't run. Check:
1. Platform-specific build logs
2. Architecture-specific dependency issues
3. Cross-compilation requirements in Dockerfile

### Manifest Creation Fails
**Error**: `failed to resolve source metadata`

**Solutions**:
1. Ensure both build jobs completed successfully
2. Verify digests were uploaded correctly
3. Check GHCR authentication is valid

## Migration Notes

If you need to revert to the old emulation-based approach:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      # ... existing steps ...
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          platforms: linux/amd64,linux/arm64
          # ... other options ...
```

## References

- [GitHub Actions: About larger runners](https://docs.github.com/en/actions/using-github-hosted-runners/about-larger-runners)
- [Docker Buildx: Multi-platform builds](https://docs.docker.com/build/building/multi-platform/)
- [Docker Buildx Imagetools](https://docs.docker.com/engine/reference/commandline/buildx_imagetools/)
