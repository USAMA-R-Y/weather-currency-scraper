# Cities Weather Scraper

A background job that scrapes weather data for cities in user-preferred countries.

## Features

- Supports user-specific preferred countries
- Falls back to default countries (Pakistan, India, Afghanistan, Bangladesh)
- Reads city data from database or snapshots
- Saves weather data in datetime-based directories
- Graceful error handling with fallbacks

## Usage

### Command Line (Default Countries)

```bash
# Run with default countries
uv run python -m app.jobs.recurring.cities_weather.scrape_cities_weather

# Run with limit (for testing)
uv run python -m app.jobs.recurring.cities_weather.scrape_cities_weather --limit 2

# Run in headed mode (browser visible)
uv run python -m app.jobs.recurring.cities_weather.scrape_cities_weather --dry-run

# Store in database
uv run python -m app.jobs.recurring.cities_weather.scrape_cities_weather --db-store
```

### Programmatic Usage

#### Example 1: Default Countries

```python
from app.jobs.recurring.cities_weather.scrape_cities_weather import scrape_cities_weather_main

scrape_cities_weather_main(
    headless=True,
    limit=1,
    db_store=False,
    user_id=None  # Use default countries
)
```

#### Example 2: User's Preferred Countries

```python
scrape_cities_weather_main(
    headless=True,
    limit=None,
    db_store=True,
    user_id="user-123"  # Use this user's preferred countries
)
```

## Command-Line Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Run in headed mode (browser visible) for debugging |
| `--limit N` | Process only N countries (for testing) |
| `--db-store` | Store scraped data in database (default: snapshots only) |

## Output

Weather data is saved in datetime-based directories:

```
data/snapshots/scrape_cities_weather/
└── YYYY-MM-DD_HH-MM-SS/
    ├── weather_pakistan.json
    ├── weather_india.json
    ├── weather_afghanistan.json
    └── weather_bangladesh.json
```

Each file contains an array of cities with weather details:

```json
[
  {
    "city": "Karachi",
    "url": "https://www.weather-forecast.com/locations/Karachi/forecasts/latest",
    "scraped_at": "2025-11-28T18:39:12.340665",
    "weather": {}
  }
]
```

## User Preferred Countries

Users can have their own list of preferred countries stored in the database. The scraper fetches these preferences when a `user_id` is provided.

### How It Works

1. If `user_id` is provided, the scraper queries the database for the user's preferred countries
2. If the user has no preferences or doesn't exist, it falls back to default countries
3. If no `user_id` is provided, it uses default countries

### Database Schema

The relationship is defined via the `user_preferred_countries` association table:

```python
# User model
preferred_countries = relationship(
    "Country",
    secondary=user_preferred_countries,
    back_populates="preferred_by_users"
)
```

## Next Steps

The scraping logic is currently a placeholder. To complete the implementation:

1. Implement actual weather scraping in `scrape_weather_for_city()`
2. Uncomment the Playwright browser initialization code
3. Add weather data models for database storage (when using `--db-store`)
