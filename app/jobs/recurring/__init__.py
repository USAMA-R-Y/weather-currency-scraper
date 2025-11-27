from app.jobs.registry import RecurringJobSpec

# List of all recurring jobs
RECURRING_JOBS = [
    # Example:
    # RecurringJobSpec(
    #     module="jobs.recurring.example_job",
    #     func=example_job_function,
    #     job_id="example_job",
    #     name="Example Recurring Job",
    #     cron_kwargs={"hour": "3", "minute": "0"},  # Run at 3:00 AM daily
    #     timezone=None  # Uses default from settings
    # ),
]
