FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 9000

# Set environment variables
ENV WHISPER_MODEL_SIZE=base
ENV WHISPER_LANGUAGE=en
ENV WHISPER_TASK=transcribe

# Run the application
CMD ["python", "main.py"] 