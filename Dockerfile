FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code and data assets
COPY backend /app/backend
COPY data /app/data
COPY results.json /app/results.json
COPY .env.example /app/.env.example

# Set environment
ENV PYTHONPATH=/app/backend
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

# Start FastAPI application
CMD exec uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port ${PORT:-8000}

