FROM mcr.microsoft.com/devcontainers/python:3.11

# Non-interactive apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libatspi2.0-0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libcairo2 libpango-1.0-0 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Playwright with all dependencies
RUN playwright install --with-deps chromium
