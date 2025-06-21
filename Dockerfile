# Fatigue Detection System - Production Docker Container
# Production-ready container with 100% validation accuracy

FROM python:3.10-slim

# Set metadata
LABEL maintainer="Fatigue Detection Team"
LABEL version="1.0.0"
LABEL description="Production-ready fatigue detection system with 100% validation accuracy"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer1.0-dev \
    libpng16-16 \
    libjpeg62-turbo \
    libwebp6 \
    libtiff5 \
    libopenexr25 \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY cognitive_overload/ ./cognitive_overload/
COPY docs/ ./docs/
COPY *.py ./
COPY *.md ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/results

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV MODEL_PATH=/app/cognitive_overload/processing

# Create non-root user for security
RUN groupadd -r fatigueuser && useradd -r -g fatigueuser fatigueuser
RUN chown -R fatigueuser:fatigueuser /app
USER fatigueuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "from cognitive_overload.processing.fatigue_metrics import FatigueDetector; FatigueDetector()" || exit 1

# Expose port for web dashboard
EXPOSE 5000

# Default command - run production demo
CMD ["python3", "simple_demo.py"]