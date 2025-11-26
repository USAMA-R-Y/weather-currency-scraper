# Automated Weather Tracker

**Project Type:** FastAPI-based automated scraper with APScheduler for daily randomized execution, SQLite persistence, and Git automation.

---

## Project Overview

A modular FastAPI application that:
- Scrapes weather and currency data daily at randomized times
- Uses headless browsers (Playwright) for reliable data collection
- Stores data in SQLite database with Alembic migrations
- Auto-commits and pushes results to GitHub repository
- Uses APScheduler for job scheduling with idempotency

---

## Tech Stack

- **Python 3.11+**
- **uv** - Fast Python package manager (replaces pip)
- **FastAPI** - Web framework with async support
- **Playwright** - Headless browser automation
- **SQLite** - Local database via SQLAlchemy
- **Alembic** - Database migrations (required)
- **APScheduler** - Job scheduling
- **GitPython** - Git automation
- **Pydantic** - Data validation and settings

---

## Project Structure

```
automated-weather-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app entry point
│   ├── core/                            # Core infrastructure
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings with Pydantic
│   │   ├── db.py                        # Database setup (engine, SessionLocal, Base, get_db)
│   │   ├── logger.py                    # Logging configuration
│   │   └── security.py                  # Auth tokens, security utilities
│   ├── modules/                         # Application modules
│   │   ├── __init__.py
│   │   ├── weather/                     # Weather scraper module
│   │   │   ├── __init__.py
│   │   │   ├── model.py                 # WeatherPoint, ScrapeRun models
│   │   │   ├── repository.py            # DB operations for weather
│   │   │   ├── router.py                # FastAPI routes (/health, /last-run, /data/latest)
│   │   │   ├── schemas.py               # Pydantic schemas
│   │   │   ├── service.py               # Business logic orchestration
│   │   │   └── scripts/                 # Weather-specific scripts
│   │   │       └── weather.py           # Weather scraping logic
│   │   ├── currency/                    # Currency scraper module
│   │   │   ├── __init__.py
│   │   │   ├── model.py                 # CurrencyRate model
│   │   │   ├── repository.py            # DB operations for currency
│   │   │   ├── router.py                # Currency API routes
│   │   │   ├── schemas.py               # Pydantic schemas
│   │   │   ├── service.py               # Business logic
│   │   │   └── scripts/                 # Currency-specific scripts
│   │   │       └── currency.py          # Currency scraping logic
│   │   └── jobs/                        # Jobs tracking module
│   │       ├── __init__.py
│   │       └── model.py                 # TaskRun model for job execution tracking
│   └── utils/                           # Shared utilities
│       ├── __init__.py
│       ├── git_sync.py                  # Git commit & push automation
│       └── idempotency.py               # Idempotency context manager
├── jobs/                                # APScheduler jobs
│   ├── __init__.py
│   ├── registry.py                      # Job dataclasses (OneOffJobSpec, RecurringJobSpec)
│   ├── scheduler.py                     # Scheduler initialization & registration
│   ├── one_off/                         # One-time jobs
│   │   └── __init__.py
│   └── recurring/                       # Recurring jobs
│       ├── __init__.py
│       └── daily_scraper.py             # Main daily scraping job
├── alembic/                             # Database migrations
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── data/
│   ├── logs/                            # Application logs
│   └── weather_tracker.db               # SQLite database
├── tests/
│   ├── test_scraper.py
│   └── test_currency.py
├── start.sh                             # Startup script
├── pyproject.toml                       # uv project config
├── .env.example                         # Environment variables template
└── README.md
```

---

## Environment Variables (.env.example)

```bash
# Database
DATABASE_URL=sqlite:///./data/weather_tracker.db

# Scraper Configuration
SCRAPE_WINDOW_START=02:00
SCRAPE_WINDOW_END=05:00
SCRAPER_LOCATIONS=Karachi,London,New York
CURRENCIES=USD,EUR,GBP,PKR

# Scheduler
TASK_TIMEZONE=UTC
TASK_MAX_INSTANCES=1
TASK_MISFIRE_GRACE=300

# Git Configuration
GIT_USER_NAME=Your Name
GIT_USER_EMAIL=your.email@example.com
GIT_PUSH_ENABLED=true

# Security
ADMIN_TOKEN=your-secret-token
```

---

## Installation & Usage

```bash
# Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone <your-repo>
cd automated-weather-tracker

# Create .env file
cp .env.example .env

# Make start script executable
chmod +x start.sh

# Run the application
./start.sh
```

---

## Key Features

1. **SQLite Database**: All data stored in `data/weather_tracker.db`
2. **Alembic Migrations**: Schema management and version control
3. **Modular Architecture**: Separate modules for weather, currency, and jobs
4. **APScheduler**: Automated job scheduling with cron expressions
5. **Idempotency**: Prevents duplicate job executions
6. **Git Automation**: Optional automatic commits and pushes
7. **uv Package Manager**: Fast, modern Python package management
