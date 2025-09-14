# Use minimal Python image with pre-installed ML libraries
FROM python:3.11-slim

WORKDIR /app

# Install only essential system dependencies
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy and install requirements in one step
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm -rf ~/.cache/pip

# Copy app
COPY app.py .

# Expose port
EXPOSE 5000

# Run app
CMD ["python", "app.py"]