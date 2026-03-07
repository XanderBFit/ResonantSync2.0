FROM python:3.11-slim

WORKDIR /app

# Install ffmpeg for audio processing fallback if needed
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Command to run the application using uvicorn directly
# Defaulting to 8080 to support Cloud Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
