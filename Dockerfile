FROM python:3.11-alpine

WORKDIR /app

# Install minimal system dependencies for alpine
RUN apk add --no-cache \
    git \
    ffmpeg \
    gcc \
    musl-dev \
    linux-headers

# Copy and install requirements with cache
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