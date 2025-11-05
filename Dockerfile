# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit google-api-python-client google-auth

# Copy application code
COPY simple_ace_app.py .
COPY assets/ ./assets/
COPY data/ ./data/
COPY examples/ ./examples/

# Create directory for potential .env file
RUN mkdir -p /app/config

# Expose Streamlit port
EXPOSE 8520

# Health check - check if Streamlit is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8520/ || exit 1

# Set environment variables with defaults
ENV STREAMLIT_SERVER_PORT=8520
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Run the application
CMD ["streamlit", "run", "simple_ace_app.py", "--server.port", "8520", "--server.address", "0.0.0.0"]
