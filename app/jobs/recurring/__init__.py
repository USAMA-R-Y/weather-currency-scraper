from app.jobs.registry import RecurringJobSpec
from app.jobs.recurring.scrape_countries_cities import scrape_countries_cities_main
import random

# List of all recurring jobs
RECURRING_JOBS = [
    RecurringJobSpec(
        module="app.jobs.recurring.scrape_countries_cities",
        func=scrape_countries_cities_main,
        job_id="scrape_countries_cities",
        name="Scrape Countries and Cities",
        # Run on a random weekday (mon-fri) at a random hour between 13:00-19:00
        cron_kwargs={
            "day_of_week": str(random.randint(0, 4)),  # 0-4 = Monday-Friday
            "hour": str(random.randint(13, 19)),  # 13:00-19:00
            "minute": str(random.randint(0, 59))  # Random minute
        },
        timezone=None  # Uses default from settings
    ),
]
