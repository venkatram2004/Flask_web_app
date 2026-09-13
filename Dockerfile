# Simple Dockerfile for the Finance Tracker Flask app
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (better Docker layer caching —
# this layer only rebuilds when requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Flask's default port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]