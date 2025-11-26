from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.db import SessionLocal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@contextmanager
def idempotent_once(name: str, idempotency_key: str):
    """
    Context manager to ensure a job runs only once based on idempotency key.
    
    Usage:
        with idempotent_once(name="import_data", idempotency_key="import_v1"):
            # Job logic here - will only run once
            process_data()
    
    Args:
        name: Name of the job/task
        idempotency_key: Unique key to identify this specific run
    
    Raises:
        Exception: If job has already completed successfully
    """
    from app.modules.jobs.model import TaskRun
    
    db: Session = SessionLocal()
    task_run = None
    
    try:
        # Check if task has already been completed
        existing_run = db.query(TaskRun).filter(
            TaskRun.name == name,
            TaskRun.idempotency_key == idempotency_key,
            TaskRun.status == "success"
        ).first()
        
        if existing_run:
            logger.info(f"Task '{name}' with key '{idempotency_key}' already completed. Skipping.")
            db.close()
            return
        
        # Create or update task run record
        task_run = db.query(TaskRun).filter(
            TaskRun.name == name,
            TaskRun.idempotency_key == idempotency_key
        ).first()
        
        if not task_run:
            task_run = TaskRun(
                name=name,
                idempotency_key=idempotency_key,
                status="processing",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(task_run)
        else:
            task_run.status = "processing"
            task_run.updated_at = datetime.utcnow()
            task_run.last_error = None
        
        db.commit()
        logger.info(f"Starting task '{name}' with key '{idempotency_key}'")
        
        # Yield control to the job
        yield
        
        # Mark as successful
        task_run.status = "success"
        task_run.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Task '{name}' completed successfully")
        
    except Exception as e:
        # Mark as failed
        if task_run:
            task_run.status = "failed"
            task_run.last_error = str(e)
            task_run.updated_at = datetime.utcnow()
            db.commit()
        
        logger.error(f"Task '{name}' failed: {e}", exc_info=True)
        raise
    
    finally:
        db.close()


def check_idempotency(name: str, idempotency_key: str) -> bool:
    """
    Check if a task has already been completed successfully.
    
    Args:
        name: Name of the job/task
        idempotency_key: Unique key to identify this specific run
    
    Returns:
        True if task has been completed, False otherwise
    """
    from app.modules.jobs.model import TaskRun
    
    db: Session = SessionLocal()
    try:
        existing_run = db.query(TaskRun).filter(
            TaskRun.name == name,
            TaskRun.idempotency_key == idempotency_key,
            TaskRun.status == "success"
        ).first()
        
        return existing_run is not None
    finally:
        db.close()
