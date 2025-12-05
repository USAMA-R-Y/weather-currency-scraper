# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # uv config
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Playwright config
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Install system dependencies required for Playwright
# We do this first to leverage layer caching
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
# We copy only what's needed for installation first
COPY pyproject.toml uv.lock ./
COPY requirements.txt ./

# Install project dependencies
# --mount=type=cache allows sharing the UV cache across builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Install Playwright browsers and dependencies
# We install dependencies for chromium only to keep image size down
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run playwright install chromium --with-deps

# Copy application code
COPY . .

# Install the project itself (if applicable, otherwise this just ensures the environment is ready)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Create necessary directories
RUN mkdir -p data/logs data/snapshots

# Expose port
EXPOSE 8000

# Make start script executable
RUN chmod +x start.sh

# Run the application
CMD ["./start.sh"]
