# Countries & Cities Scraper

Scrapes country and city data from weather-forecast.com and stores it in the database.

## Usage

### Command Line

```bash
# Run in headless mode (default)
python -m app.jobs.recurring.scrape_countries_cities.scraper

# Run with browser visible (for debugging)
python -m app.jobs.recurring.scrape_countries_cities.scraper --dry-run

# Limit to first N countries (for testing)
python -m app.jobs.recurring.scrape_countries_cities.scraper --limit 5

# Save snapshots of scraped data
python -m app.jobs.recurring.scrape_countries_cities.scraper --snapshots

# Combine options
python -m app.jobs.recurring.scrape_countries_cities.scraper --dry-run --limit 10 --snapshots
```

### Programmatic Usage

```python
from app.jobs.recurring.scrape_countries_cities import scrape_countries_cities_main

# Run with default settings (headless, all countries, no snapshots)
scrape_countries_cities_main()

# Run with custom settings
scrape_countries_cities_main(
    headless=True,      # Run in headless mode
    limit=10,           # Process only 10 countries
    snapshots=True      # Save snapshots
)
```

## Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--dry-run` | flag | `False` | Run in headed mode (browser visible) for debugging |
| `--limit` | int | `None` | Limit number of countries to process (useful for testing) |
| `--snapshots` | flag | `False` | Save snapshots of scraped data as JSON files |

## Features

- **Automatic retry logic**: Restarts browser if it crashes
- **Incremental saving**: Saves each country's cities immediately after scraping
- **Smart delays**: Random delays (1-4 seconds) between navigations to appear human-like
- **Snapshot support**: Optionally saves daily snapshots to `data/snapshots/scrape_countries_cities/`
- **Minimal logging**: Only logs essential progress and errors

## Snapshots

When `--snapshots` is enabled:
- Saves to: `data/snapshots/scrape_countries_cities/{YYYY-MM-DD}_countries_cities.json`
- Deletes previous snapshot from the same day before creating a new one
- Only keeps snapshot if script completes successfully
- Deletes snapshot if script fails or is interrupted

## Database

Data is stored in two tables:
- `countries`: Country name and URL
- `cities`: City name, URL, and foreign key to country

The script performs upsert operations (insert if new, update if exists).
