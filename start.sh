#!/bin/bash
set -e

echo "=== Automated Weather Tracker Startup ==="

# Install dependencies
echo "Installing dependencies with uv..."
uv sync

# Wait for database (if using external DB, add connection check here)
echo "Checking database availability..."
if [ ! -d "data" ]; then
    mkdir -p data/logs
fi

# Run migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the server
echo "Starting FastAPI server..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
