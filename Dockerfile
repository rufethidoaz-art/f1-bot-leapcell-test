# Use Python 3.11 slim image for Leapcell deployment
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright and Python packages
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium && playwright install-deps

# Copy application code
COPY leapcell_f1_bot.py .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (for health checks)
EXPOSE 8080

# Run the bot
CMD ["python", "leapcell_f1_bot.py"]