# Job Scheduling System

This directory contains a comprehensive job scheduling system built with APScheduler, following the specifications from the job system prompt.

## Overview

The job system provides:
- **One-off jobs**: Run once with idempotency protection
- **Recurring jobs**: Scheduled with cron expressions
- **Database persistence**: Jobs survive application restarts
- **FastAPI integration**: API endpoints for job management
- **Async support**: Both sync and async job functions

## Structure

```
jobs/
├── __init__.py
├── README.md                    # This file
├── registry.py                  # Job registry with dataclasses
├── scheduler.py                 # Scheduler setup and job registration
├── one_off/                     # One-time jobs
│   ├── __init__.py             # Registers one-off jobs
│   └── import_crm_data.py      # CRM data import job
└── recurring/                   # Recurring jobs
    └── __init__.py             # Registers recurring jobs (empty for now)
```

## Features Implemented

### ✅ Core Components
- [x] TaskRun model for tracking job executions
- [x] Job registry system with dataclasses
- [x] Idempotency service for one-off jobs
- [x] APScheduler configuration with database persistence
- [x] FastAPI integration with lifecycle management

### ✅ CRM Data Import Job
- [x] Converted existing script to one-off job
- [x] Idempotency protection prevents duplicate imports
- [x] Batch processing for performance
- [x] Comprehensive logging and error handling
- [x] Duplicate detection using unique hashing

### ✅ Background Operation
- [x] Jobs run automatically in the background
- [x] No manual intervention required
- [x] Idempotency ensures one-off jobs run only once

## Usage

### Running the System

1. **Install dependencies** (already done):
   ```bash
   uv sync
   ```

2. **Run database migration**:
   ```bash
   alembic upgrade head
   ```

3. **Start the FastAPI application**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

4. **Jobs will run automatically** - the CRM import job will execute once when the application starts

### Adding New Jobs

#### One-off Job Example

1. Create job function in `jobs/one_off/my_job.py`:
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   def main() -> None:
       """Main function for my one-off job."""
       logger.info("Starting my job...")
       # Your job logic here
       logger.info("Job completed!")
   ```

2. Register in `jobs/one_off/__init__.py`:
   ```python
   from jobs.one_off.my_job import main as my_job_main
   
   ONE_OFF_JOBS.extend([
       OneOffJobSpec(
           module="jobs.one_off.my_job",
           func=my_job_main,
           job_id="my_job_v1",
           name="My One-off Job",
           idempotency_key="my_job_v1",
       ),
   ])
   ```

#### Recurring Job Example

1. Create job function in `jobs/recurring/daily_task.py`:
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   def daily_task():
       """Daily recurring task."""
       logger.info("Running daily task...")
       # Your job logic here
   ```

2. Register in `jobs/recurring/__init__.py`:
   ```python
   from jobs.recurring.daily_task import daily_task
   
   RECURRING_JOBS.extend([
       RecurringJobSpec(
           module="jobs.recurring.daily_task",
           func=daily_task,
           job_id="daily_task",
           name="Daily Task",
           cron_kwargs={"hour": "2", "minute": "0"},  # 2:00 AM daily
       ),
   ])
   ```

## Configuration

### Job System Settings

Job system settings in `app/core/config.py`:

```python
# Scheduler Configuration
TASK_TIMEZONE: str = "UTC"
TASK_MAX_INSTANCES: int = 1  # Max concurrent job instances
TASK_MISFIRE_GRACE: int = 300  # 5 minutes grace period
```

### Database URL Configuration

The system supports flexible database configuration:

**Option 1: Individual Environment Variables** (recommended)
```bash
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=crm_db
```

**Option 2: Direct Database URL**
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/crm_db
```

**Important**: The system automatically handles database URL scheme compatibility:
- **SQLAlchemy** uses `postgresql+psycopg://` for optimal performance
- **APScheduler** uses `postgresql://` for compatibility

This ensures both systems work correctly with the same database configuration.

## Database Schema

The system uses a `task_runs` table to track job executions:

```sql
CREATE TABLE task_runs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'processing',
    last_error TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE(name, idempotency_key)
);
```

## Idempotency

One-off jobs use the `idempotent_once` context manager to ensure they run only once:

```python
from app.utils.idempotency import idempotent_once

def my_job():
    with idempotent_once(name="my_job", idempotency_key="my_job_v1"):
        # Job logic here - will only run once
        pass
```

## Monitoring

- **Logs**: All job execution is logged with structured logging
- **Database**: Check `task_runs` table for execution history and status
- **Application Logs**: Monitor the FastAPI application logs for job execution details

## Current Jobs

### CRM Data Import Job
- **ID**: `import_crm_data_v1`
- **Type**: One-off
- **Purpose**: Import CRM data from Excel file to database
- **Features**:
  - Duplicate detection
  - Batch processing
  - Progress tracking
  - Error handling

### MOFA Embassy Monitoring Job
- **ID**: `mofa_monitoring`
- **Type**: Recurring
- **Schedule**: Daily at 3:00 AM
- **Purpose**: Monitor MOFA embassy data for changes
- **Features**:
  - Automated web scraping
  - Change detection
  - Database updates
  - Notification system integration

## Next Steps

1. **Add more jobs** as needed for your application
2. **Set up monitoring** alerts for failed jobs
3. **Configure job scheduling** based on your requirements
4. **Add job result storage** if needed for complex workflows

## Troubleshooting

### Common Issues

1. **Jobs not appearing**: Check that job modules are imported in `__init__.py` files
2. **Database errors**: Ensure migrations are run and database is accessible
3. **Scheduler not starting**: Check logs for configuration issues
4. **Jobs not running**: Verify cron expressions and timezone settings

### Debugging

Enable debug logging for APScheduler:
```python
import logging
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
```

## Dependencies

- `apscheduler>=3.10.1` - Job scheduling (replaces Celery + Redis)
- `sqlalchemy>=2.0.0` - Database ORM
- `fastapi` - Web framework integration
- `pandas` - Data processing (for CRM import)
- `beautifulsoup4` - Web scraping (for MOFA monitoring)
- `requests` - HTTP requests (for MOFA monitoring)
