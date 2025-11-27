from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_scheduler() -> BackgroundScheduler:
    """
    Create and configure APScheduler instance.
    
    Returns:
        Configured BackgroundScheduler instance
    """
    # Configure job store (SQLite or PostgreSQL)
    jobstores = {
        'default': SQLAlchemyJobStore(url=settings.scheduler_database_url)
    }
    
    # Configure executors
    executors = {
        'default': ThreadPoolExecutor(max_workers=settings.TASK_MAX_INSTANCES)
    }
    
    # Configure job defaults
    job_defaults = {
        'coalesce': True,  # Combine multiple missed runs into one
        'max_instances': settings.TASK_MAX_INSTANCES,
        'misfire_grace_time': settings.TASK_MISFIRE_GRACE
    }
    
    # Create scheduler
    scheduler = BackgroundScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone=settings.TASK_TIMEZONE
    )
    
    logger.info(f"Scheduler created with timezone: {settings.TASK_TIMEZONE}")
    return scheduler


def register_jobs(scheduler: BackgroundScheduler) -> None:
    """
    Register all jobs (one-off and recurring) with the scheduler.
    
    Args:
        scheduler: APScheduler instance
    """
    from jobs.one_off import ONE_OFF_JOBS
    from jobs.recurring import RECURRING_JOBS
    
    # Register one-off jobs
    for job_spec in ONE_OFF_JOBS:
        try:
            scheduler.add_job(
                job_spec.func,
                'date',  # Run once at a specific date/time
                id=job_spec.job_id,
                name=job_spec.name,
                replace_existing=True
            )
            logger.info(f"Registered one-off job: {job_spec.name} (ID: {job_spec.job_id})")
        except Exception as e:
            logger.error(f"Failed to register one-off job {job_spec.name}: {e}")
    
    # Register recurring jobs
    for job_spec in RECURRING_JOBS:
        try:
            timezone = job_spec.timezone or settings.TASK_TIMEZONE
            scheduler.add_job(
                job_spec.func,
                'cron',
                id=job_spec.job_id,
                name=job_spec.name,
                replace_existing=True,
                timezone=timezone,
                **job_spec.cron_kwargs
            )
            logger.info(f"Registered recurring job: {job_spec.name} (ID: {job_spec.job_id}, Cron: {job_spec.cron_kwargs})")
        except Exception as e:
            logger.error(f"Failed to register recurring job {job_spec.name}: {e}")
    
    logger.info(f"Job registration complete: {len(ONE_OFF_JOBS)} one-off, {len(RECURRING_JOBS)} recurring")


def start_scheduler(scheduler: BackgroundScheduler) -> None:
    """
    Start the scheduler.
    
    Args:
        scheduler: APScheduler instance
    """
    scheduler.start()
    logger.info("Scheduler started successfully")


def shutdown_scheduler(scheduler: BackgroundScheduler) -> None:
    """
    Shutdown the scheduler gracefully.
    
    Args:
        scheduler: APScheduler instance
    """
    scheduler.shutdown(wait=True)
    logger.info("Scheduler shutdown complete")


# Global scheduler instance
_scheduler = None


def init_scheduler() -> BackgroundScheduler:
    """
    Initialize and start the scheduler with all registered jobs.
    
    Returns:
        Running scheduler instance
    """
    global _scheduler
    
    if _scheduler is not None:
        logger.warning("Scheduler already initialized")
        return _scheduler
    
    _scheduler = create_scheduler()
    register_jobs(_scheduler)
    start_scheduler(_scheduler)
    
    return _scheduler


def get_scheduler() -> BackgroundScheduler:
    """
    Get the global scheduler instance.
    
    Returns:
        Scheduler instance or None if not initialized
    """
    return _scheduler

