from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional


@dataclass
class OneOffJobSpec:
    """
    Specification for a one-time job.
    
    Attributes:
        module: Python module path (e.g., "jobs.one_off.import_data")
        func: Callable function to execute
        job_id: Unique identifier for the job
        name: Human-readable job name
        idempotency_key: Key to ensure job runs only once
    """
    module: str
    func: Callable
    job_id: str
    name: str
    idempotency_key: str


@dataclass
class RecurringJobSpec:
    """
    Specification for a recurring job.
    
    Attributes:
        module: Python module path (e.g., "jobs.recurring.daily_task")
        func: Callable function to execute
        job_id: Unique identifier for the job
        name: Human-readable job name
        cron_kwargs: Cron expression as kwargs (e.g., {"hour": "3", "minute": "0"})
        timezone: Optional timezone override (defaults to TASK_TIMEZONE from settings)
    """
    module: str
    func: Callable
    job_id: str
    name: str
    cron_kwargs: Dict[str, Any]
    timezone: Optional[str] = None
