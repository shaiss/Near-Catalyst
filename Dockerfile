# NEAR Catalyst Framework - Multi-Agent Partnership Discovery System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data

# Set up benchmark configuration (copy example if main file doesn't exist)
RUN if [ ! -f "config/partnership_benchmarks.json" ]; then \
        cp config/partnership_benchmarks.example.json config/partnership_benchmarks.json; \
    fi

# Create a non-root user for security
RUN useradd -m -u 1000 catalyst && \
    chown -R catalyst:catalyst /app
USER catalyst

# Expose the Flask server port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health', timeout=5)" || exit 1

# Default command runs the Flask server
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "5000"] 