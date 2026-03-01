FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories for storing data
RUN mkdir -p cough_samples eye_images palm_captures fingernail_images xray_images medgemma_reports

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Copy startup script and make executable
COPY start_services.sh /app/start_services.sh
RUN chmod +x /app/start_services.sh

# Run both services
CMD ["/app/start_services.sh"]
