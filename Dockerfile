# Simplified build for stream-checker application
# Frontend should be pre-built and copied to build context

FROM python:3.11-slim

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y curl ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create working directory for backend
WORKDIR /app

# Copy backend requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Copy backend application code
COPY backend/ ./

# Copy pre-built frontend to static directory
COPY frontend/build ./static

# Create necessary directories
# data directory will be mounted as volume for persistence
RUN mkdir -p csv logs data

# Set environment variable for config directory
ENV CONFIG_DIR=/app/data

# Set permissions for entrypoint
RUN chmod +x entrypoint.sh

# Create default configuration files in the data directory
RUN python3 create_default_configs.py

# Expose only the Flask port
EXPOSE 5000

# Health check for Flask only
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Use Python directly as entrypoint for simpler deployment
CMD ["python3", "web_api.py", "--host", "0.0.0.0", "--port", "5000"]

