# Release Guide

## Creating a Release

To publish a new version to GitHub Container Registry (GHCR), you need to create a GitHub release:

### Steps

1. **Create a Git Tag** (locally or via GitHub UI)
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

2. **Create a GitHub Release**
   - Go to the repository on GitHub
   - Navigate to "Releases" → "Create a new release"
   - Select or create a new tag (e.g., `v1.0.0`)
   - Fill in the release title and description
   - Click "Publish release"

3. **Automated Build and Push**
   - Once the release is published, GitHub Actions will automatically:
     - Build the frontend
     - Build the Docker image
     - Push to GHCR with multiple tags:
       - `ghcr.io/krinkuto11/streamflow:latest`
       - `ghcr.io/krinkuto11/streamflow:v1.0.0`
       - `ghcr.io/krinkuto11/streamflow:1.0`
       - `ghcr.io/krinkuto11/streamflow:1`

### Versioning

Use [Semantic Versioning](https://semver.org/):
- **Major version** (v1.0.0 → v2.0.0): Breaking changes
- **Minor version** (v1.0.0 → v1.1.0): New features, backwards compatible
- **Patch version** (v1.0.0 → v1.0.1): Bug fixes, backwards compatible

### Pull Request Testing

When you open a pull request:
- The workflow will build and test your changes
- Docker image will be built but **not pushed** to GHCR
- This ensures all changes are validated before merging

## Troubleshooting

### Release doesn't trigger workflow
- Ensure the release is set to "Published" (not draft)
- Check that the tag follows semantic versioning (e.g., v1.0.0)
- Verify GitHub Actions is enabled for the repository

### Docker push fails
- Ensure GITHUB_TOKEN has write permissions to packages
- Check that the repository name matches the workflow configuration
