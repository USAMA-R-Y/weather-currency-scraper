# Automated Daily Scraper — Implementation Specification

**Project Type:** FastAPI-based automated scraper with APScheduler for daily randomized execution, SQLite persistence, and Git automation.

---

## 1. Project Overview

Build a modular FastAPI application that:
- Scrapes weather and currency data daily at randomized times
- Uses headless browsers (Playwright) for reliable data collection
- Stores data in SQLite database with Alembic migrations
- Auto-commits and pushes results to GitHub repository
- Uses APScheduler for job scheduling with idempotency

---

## 2. Tech Stack

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

## 3. Project Structure

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

## 4. Database Schema (SQLite)

### app/modules/weather/model.py
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base
from datetime import datetime

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime)
    status = Column(String(32), nullable=False, default="processing")  # success/failure/processing
    summary_json = Column(Text)  # JSON summary of results
    artifacts_path = Column(String(255))  # Path to snapshot file
    
    weather_points = relationship("WeatherPoint", back_populates="run")

class WeatherPoint(Base):
    __tablename__ = "weather_points"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("scrape_runs.id"))
    source = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    temp_c = Column(Float)
    humidity = Column(Float)
    wind_kph = Column(Float)
    observed_at = Column(DateTime, nullable=False)
    
    run = relationship("ScrapeRun", back_populates="weather_points")
```

### app/modules/currency/model.py
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from app.core.db import Base
from datetime import datetime

class CurrencyRate(Base):
    __tablename__ = "currency_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("scrape_runs.id"))
    source = Column(String(100), nullable=False)
    base_currency = Column(String(10), nullable=False)
    quote_currency = Column(String(10), nullable=False)
    rate = Column(Float, nullable=False)
    observed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
```

### app/modules/jobs/model.py
```python
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.db import Base
from datetime import datetime

class TaskRun(Base):
    __tablename__ = "task_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    idempotency_key = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False, default="processing")
    last_error = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        {"schema": None},
    )
```

---

## 5. Core Infrastructure Files

### app/core/db.py
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

Base = declarative_base()

is_sqlite = settings.effective_database_url.startswith("sqlite")
engine = create_engine(
    settings.effective_database_url,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/core/config.py
```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data/weather_tracker.db"
    
    # Scraper
    SCRAPE_WINDOW_START: str = "02:00"
    SCRAPE_WINDOW_END: str = "05:00"
    SCRAPER_LOCATIONS: str = "Karachi,London,New York"
    CURRENCIES: str = "USD,EUR,GBP,PKR"
    
    # Scheduler
    TASK_TIMEZONE: str = "UTC"
    TASK_MAX_INSTANCES: int = 1
    TASK_MISFIRE_GRACE: int = 300
    
    # Git
    GIT_USER_NAME: Optional[str] = None
    GIT_USER_EMAIL: Optional[str] = None
    GIT_PUSH_ENABLED: bool = True
    
    # Security
    ADMIN_TOKEN: Optional[str] = None
    
    @property
    def effective_database_url(self) -> str:
        return self.DATABASE_URL
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### app/core/logger.py
```python
import logging
import sys
from pathlib import Path

def setup_logging():
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data/logs/app.log")
        ]
    )
    
    return logging.getLogger(__name__)
```

---

## 6. APScheduler Job System

### jobs/registry.py
```python
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional

@dataclass
class OneOffJobSpec:
    module: str
    func: Callable
    job_id: str
    name: str
    idempotency_key: str

@dataclass
class RecurringJobSpec:
    module: str
    func: Callable
    job_id: str
    name: str
    cron_kwargs: Dict[str, Any]
    timezone: Optional[str] = None
```

### jobs/scheduler.py
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_scheduler():
    jobstores = {
        'default': SQLAlchemyJobStore(url=settings.effective_database_url)
    }
    
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        timezone=settings.TASK_TIMEZONE
    )
    
    return scheduler

def register_jobs(scheduler):
    from jobs.one_off import ONE_OFF_JOBS
    from jobs.recurring import RECURRING_JOBS
    
    # Register one-off jobs
    for job_spec in ONE_OFF_JOBS:
        scheduler.add_job(
            job_spec.func,
            'date',
            id=job_spec.job_id,
            name=job_spec.name,
            replace_existing=True
        )
    
    # Register recurring jobs
    for job_spec in RECURRING_JOBS:
        scheduler.add_job(
            job_spec.func,
            'cron',
            id=job_spec.job_id,
            name=job_spec.name,
            replace_existing=True,
            **job_spec.cron_kwargs
        )
    
    logger.info(f"Registered {len(ONE_OFF_JOBS)} one-off and {len(RECURRING_JOBS)} recurring jobs")
```

### jobs/recurring/daily_scraper.py
```python
import logging
from datetime import datetime
from app.utils.idempotency import idempotent_once
from app.modules.scraper.service import ScraperService
from app.modules.currency.service import CurrencyService
from app.utils.git_sync import commit_and_push

logger = logging.getLogger(__name__)

def daily_scraping_job():
    """Main daily scraping job - runs weather and currency scrapers"""
    logger.info("Starting daily scraping job")
    
    try:
        # Run weather scraper
        weather_service = WeatherService()
        weather_results = weather_service.run_scraping()
        
        # Run currency scraper
        currency_service = CurrencyService()
        currency_results = currency_service.run_scraping()
        
        # All data is stored in the database
        logger.info(f"Scraped {len(weather_results)} weather points and {len(currency_results)} currency rates")
        logger.info("Daily scraping job completed successfully")
    except Exception as e:
        logger.error(f"Daily scraping job failed: {e}", exc_info=True)
        raise
```

### jobs/recurring/__init__.py
```python
from jobs.registry import RecurringJobSpec
from jobs.recurring.daily_scraper import daily_scraping_job

RECURRING_JOBS = [
    RecurringJobSpec(
        module="jobs.recurring.daily_scraper",
        func=daily_scraping_job,
        job_id="daily_scraper",
        name="Daily Weather & Currency Scraper",
        cron_kwargs={"hour": "3", "minute": "0"}  # 3:00 AM daily
    ),
]
```

---

## 7. Startup Script (start.sh)

```bash
#!/bin/bash
set -e

echo "=== Automated Weather Tracker Startup ==="

# Install dependencies
echo "Installing dependencies with uv..."
uv sync

# Wait for database (if using external DB, add connection check here)
echo "Checking database availability..."
if [ ! -d "data" ]; then
    mkdir -p data/snapshots data/logs
fi

# Run migrations
echo "Running database migrations..."
uv run alembic upgrade head

# Start the server
echo "Starting FastAPI server..."
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 8. FastAPI Main Application

### app/main.py
```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.logger import setup_logging
from jobs.scheduler import create_scheduler, register_jobs
import logging

logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    scheduler = create_scheduler()
    register_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()

app = FastAPI(title="Automated Weather Tracker", lifespan=lifespan)

# Include routers
from app.modules.weather.router import router as weather_router
from app.modules.currency.router import router as currency_router

app.include_router(weather_router, prefix="/weather", tags=["weather"])
app.include_router(currency_router, prefix="/currency", tags=["currency"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "automated-weather-tracker"}
```

---

## 9. Module Implementation Examples

### app/modules/weather/service.py
```python
from playwright.sync_api import sync_playwright
from app.modules.weather.scripts.weather import fetch_weather_data
from app.modules.weather.repository import WeatherRepository
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class WeatherService:
    def __init__(self):
        self.repository = WeatherRepository()
    
    def run_scraping(self):
        locations = settings.SCRAPER_LOCATIONS.split(",")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            results = []
            for location in locations:
                data = fetch_weather_data(page, location.strip())
                results.append(data)
            
            browser.close()
        
        # Save to database
        run_id = self.repository.create_scrape_run()
        for data in results:
            self.repository.save_weather_point(run_id, data)
        
        return results
```

### app/modules/weather/scripts/weather.py
```python
from playwright.sync_api import Page
import logging

logger = logging.getLogger(__name__)

def fetch_weather_data(page: Page, location: str) -> dict:
    """Fetch weather data for a location using Playwright"""
    logger.info(f"Fetching weather for {location}")
    
    # Example: scrape from a weather website
    # Replace with actual scraping logic
    url = f"https://example-weather-site.com/{location}"
    page.goto(url)
    
    # Extract data (example)
    data = {
        "location": location,
        "temp_c": 25.0,  # Parse from page
        "humidity": 60.0,
        "wind_kph": 15.0,
        "source": "example-weather-site"
    }
    
    return data
```

---

## 10. Git Automation (Optional)

### app/utils/git_sync.py
```python
import subprocess
import logging
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

def commit_and_push():
    """Commit and push database changes to repository (optional)"""
    if not settings.GIT_PUSH_ENABLED:
        logger.info("Git push disabled")
        return
    
    try:
        # Add database file
        subprocess.run(["git", "add", "data/weather_tracker.db"], check=True)
        
        # Commit
        from datetime import datetime
        message = f"chore(scrape): update data {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        subprocess.run(["git", "commit", "-m", message], check=True)
        
        # Push
        subprocess.run(["git", "push", "origin", "main"], check=True)
        logger.info("Successfully pushed database updates")
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        raise
```

---

## 11. Environment Variables (.env.example)

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

## 12. Installation & Usage

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

## 13. Key Implementation Notes

1. **SQLite Database**: All data stored in `data/weather_tracker.db` (no JSON/CSV snapshots needed)
2. **Alembic Migrations**: Required for schema management
3. **Module Structure**: Each module (weather, currency) has its own models, repository, router, schemas, service, and scripts
4. **APScheduler**: Jobs defined in `jobs/` folder with registry pattern
5. **Idempotency**: One-off jobs use `idempotent_once` context manager
6. **Git Automation**: Optional - can commit database file to track changes over time
7. **uv Package Manager**: Fast, modern Python package management

This specification is complete and ready for AI implementation.
