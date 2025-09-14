## Use minimal Python image with pre-installed ML libraries
#FROM python:3.11-slim
#
#WORKDIR /app
#
## Install only essential system dependencies
#RUN apt-get update && apt-get install -y \
#    git \
#    ffmpeg \
#    build-essential \
#    && rm -rf /var/lib/apt/lists/* \
#    && apt-get clean
#
## Copy and install requirements in one step
#COPY requirements.txt .
#RUN pip install --upgrade pip && \
#    pip install -r requirements.txt && \
#    rm -rf ~/.cache/pip
#
## Copy app
#COPY app.py .
#
## Expose port
#EXPOSE 5000
#
## Run app
#CMD ["python", "app.py"]

# -------- build stage --------
FROM python:3.11-slim AS builder
WORKDIR /app

# Install system deps needed for building wheels
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install deps
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# -------- runtime stage --------
FROM python:3.11-slim
WORKDIR /app

# Only keep what’s needed at runtime (ffmpeg for whisper)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy Python environment from builder
COPY --from=builder /usr/local /usr/local

# Copy application code
COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]
