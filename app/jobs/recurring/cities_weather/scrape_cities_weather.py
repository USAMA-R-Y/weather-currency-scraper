#!/usr/bin/env python3
"""
Cities Weather Scraper

Scrapes weather data for cities in user-preferred countries.
Reads city data from database (if available) or latest snapshots.

Usage:
    python scrape_cities_weather.py              # Runs in headless mode
    python scrape_cities_weather.py --dry-run    # Runs in headed mode for debugging
    python scrape_cities_weather.py --limit 2    # Process only 2 countries
"""

import argparse
import sys
import time
import random
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from sqlalchemy.orm import Session

# Import database models and session
from app.core.db import SessionLocal
from app.modules.weather.models import Country as CountryModel, City as CityModel


# Default countries to process if no user preferences found
DEFAULT_COUNTRIES = ["Pakistan", "India"]


def get_project_root() -> Path:
    """Get the project root directory (5 levels up from this script)"""
    return Path(__file__).resolve().parent.parent.parent.parent.parent


def get_cities_from_db(country_name: str) -> List[Dict[str, str]]:
    """
    Get cities for a country from the database
    
    Args:
        country_name: Name of the country
    
    Returns:
        List of dictionaries with 'name' and 'url' keys
    """
    db: Session = SessionLocal()
    cities_data = []
    
    try:
        # Import here to catch model errors
        from sqlalchemy.exc import InvalidRequestError
        
        # Find the country
        country = db.query(CountryModel).filter(
            CountryModel.name == country_name
        ).first()
        
        if not country:
            print(f"  ⚠ Country '{country_name}' not found in database")
            return cities_data
        
        # Get all cities for this country
        cities = db.query(CityModel).filter(
            CityModel.country_id == country.id
        ).all()
        
        for city in cities:
            cities_data.append({
                "name": city.name,
                "url": city.url
            })
        
        print(f"  ✓ Loaded {len(cities_data)} cities from database for {country_name}")
        
    except Exception as e:
        error_msg = str(e)
        # Check if it's the user_preferred_countries model error
        if "user_preferred_countries" in error_msg:
            print(f"  ⚠ Database model issue (user_preferred_countries table not defined)")
        else:
            print(f"  [!] Error reading from database for {country_name}: {e}")
        
    finally:
        db.close()
    
    return cities_data


def get_cities_from_snapshot(country_name: str) -> List[Dict[str, str]]:
    """
    Get cities for a country from the latest snapshot file
    
    Args:
        country_name: Name of the country
    
    Returns:
        List of dictionaries with 'name' and 'url' keys
    """
    cities_data = []
    
    try:
        project_root = get_project_root()
        snapshot_dir = project_root / "data" / "snapshots" / "scrape_countries_cities"
        
        if not snapshot_dir.exists():
            print(f"  ⚠ Snapshot directory not found: {snapshot_dir}")
            return cities_data
        
        # Find the latest snapshot file
        snapshot_files = sorted(snapshot_dir.glob("*.json"), reverse=True)
        
        if not snapshot_files:
            print(f"  ⚠ No snapshot files found in {snapshot_dir}")
            return cities_data
        
        latest_snapshot = snapshot_files[0]
        print(f"  → Reading from snapshot: {latest_snapshot.name}")
        
        with open(latest_snapshot, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)
        
        # Find the country in the snapshot
        for country_obj in snapshot_data:
            if country_obj.get("country") == country_name:
                cities_data = country_obj.get("cities", [])
                print(f"  ✓ Loaded {len(cities_data)} cities from snapshot for {country_name}")
                break
        
        if not cities_data:
            print(f"  ⚠ Country '{country_name}' not found in snapshot")
        
    except Exception as e:
        print(f"  [!] Error reading from snapshot for {country_name}: {e}")
        import traceback
        traceback.print_exc()
    
    return cities_data


def get_user_preferred_countries(user_id: Optional[str] = None) -> List[str]:
    """
    Get list of user-preferred countries from database
    
    Args:
        user_id: Optional user ID to fetch preferences for
    
    Returns:
        List of country names (defaults to DEFAULT_COUNTRIES if no user_id or user not found)
    """
    # If no user_id provided, return default countries
    if not user_id:
        print(f"No user_id provided. Using default countries: {', '.join(DEFAULT_COUNTRIES)}")
        return DEFAULT_COUNTRIES
    
    # Try to fetch user's preferred countries from database
    db: Session = SessionLocal()
    try:
        from app.modules.auth.service import get_user_preferred_countries as get_prefs
        
        preferred = get_prefs(db, user_id)
        
        if preferred:
            print(f"Loaded {len(preferred)} preferred countries for user {user_id}: {', '.join(preferred)}")
            return preferred
        else:
            print(f"No preferred countries found for user {user_id}. Using default countries: {', '.join(DEFAULT_COUNTRIES)}")
            return DEFAULT_COUNTRIES
            
    except Exception as e:
        print(f"Error fetching user preferences: {e}")
        print(f"Falling back to default countries: {', '.join(DEFAULT_COUNTRIES)}")
        return DEFAULT_COUNTRIES
        
    finally:
        db.close()


def scrape_weather_for_city(page, city_url: str, city_name: str) -> Dict:
    """
    Scrape weather data for a specific city
    
    Args:
        page: Playwright page object
        city_url: URL of the city weather page
        city_name: Name of the city (for logging)
    
    Returns:
        Dictionary with weather data (placeholder for now)
    """
    # TODO: Implement actual weather scraping logic
    # For now, return a placeholder structure
    
    print(f"    → Scraping weather for: {city_name}")
    
    # Navigate to city page (commented out for now)
    # page.goto(city_url, wait_until="domcontentloaded")
    # time.sleep(random.uniform(1, 3))
    
    # Placeholder weather data structure
    weather_data = {
        "city": city_name,
        "url": city_url,
        "scraped_at": datetime.now().isoformat(),
        "weather": {
            # TODO: Add actual weather fields here
            # "temperature": None,
            # "condition": None,
            # "humidity": None,
            # etc.
        }
    }
    
    return weather_data


def save_country_weather_data(country_name: str, cities_weather: List[Dict], snapshot_dir: Path):
    """
    Save weather data for a country to JSON file in datetime directory
    
    Args:
        country_name: Name of the country
        cities_weather: List of weather data dictionaries for cities
        snapshot_dir: Directory path for this scraping session (datetime-based)
    """
    try:
        # Create filename: weather_{country}.json
        filename = f"weather_{country_name.lower().replace(' ', '_')}.json"
        file_path = snapshot_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cities_weather, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Saved weather data to: {file_path}")
        
    except Exception as e:
        print(f"  [!] Error saving weather data for {country_name}: {e}")
        import traceback
        traceback.print_exc()


def scrape_cities_weather_main(headless: bool = True, limit: Optional[int] = None, db_store: bool = False, user_id: Optional[str] = None):
    """
    Main execution function
    
    Args:
        headless: Run browser in headless mode (default: True)
        limit: Limit number of countries to process (default: None = all countries)
        db_store: Store data in database (default: False, snapshots only)
        user_id: Optional user ID to fetch preferred countries for
    """
    print(f"\n{'='*60}")
    print(f"CITIES WEATHER SCRAPER")
    print(f"{'='*60}\n")
    
    start_time = datetime.now()
    print(f"Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Snapshot configuration (always enabled by default)
    snapshot_enabled = True
    snapshot_success = False
    
    # Create snapshot directory with datetime
    project_root = get_project_root()
    base_snapshot_dir = project_root / "data" / "snapshots" / "scrape_cities_weather"
    base_snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate directory name with current datetime
    current_datetime = start_time.strftime("%Y-%m-%d_%H-%M-%S")
    snapshot_dir = base_snapshot_dir / current_datetime
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Snapshots enabled. Will save to: {snapshot_dir}\n")
    
    # Get user-preferred countries
    preferred_countries = get_user_preferred_countries(user_id)
    
    # Apply limit if specified
    countries_to_process = preferred_countries[:limit] if limit else preferred_countries
    total_countries = len(countries_to_process)
    
    if limit:
        print(f"⚠ Processing limited to {limit} countries (testing mode)\n")
    
    print(f"Countries to process: {', '.join(countries_to_process)}\n")
    
    if db_store:
        print("Database storage enabled (--db-store flag provided)\n")
    else:
        print("Database storage disabled (default behavior). Use --db-store to enable.\n")
    
    print(f"Running in {'HEADLESS' if headless else 'HEADED'} mode\n")
    
    # Process each country
    for country_index, country_name in enumerate(countries_to_process, 1):
        print(f"\n{'='*60}")
        print(f"[{country_index}/{total_countries}] Processing: {country_name}")
        print(f"{'='*60}\n")
        
        # Get cities data for this country
        cities_data = []
        
        # Try database first
        cities_data = get_cities_from_db(country_name)
        
        # Fallback to snapshot if database is empty or has errors
        if not cities_data:
            print(f"  → Falling back to snapshot for {country_name}")
            cities_data = get_cities_from_snapshot(country_name)
        
        if not cities_data:
            print(f"  ✗ No cities data found for {country_name}, skipping...")
            continue
        
        print(f"\n  Processing {len(cities_data)} cities for {country_name}...\n")
        
        # Scrape weather for each city (placeholder for now)
        cities_weather = []
        
        # TODO: Uncomment when implementing actual scraping
        # with sync_playwright() as p:
        #     browser = p.chromium.launch(headless=headless)
        #     context = browser.new_context(
        #         viewport={'width': 1920, 'height': 1080},
        #         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        #     )
        #     page = context.new_page()
        #     
        #     try:
        #         for city_index, city in enumerate(cities_data, 1):
        #             city_name = city["name"]
        #             city_url = city["url"]
        #             
        #             print(f"  [{city_index}/{len(cities_data)}] {city_name}")
        #             
        #             weather_data = scrape_weather_for_city(page, city_url, city_name)
        #             cities_weather.append(weather_data)
        #             
        #             # Small delay between cities
        #             if city_index < len(cities_data):
        #                 time.sleep(random.uniform(1, 3))
        #     
        #     finally:
        #         browser.close()
        
        # For now, create placeholder data for each city
        for city_index, city in enumerate(cities_data, 1):
            city_name = city["name"]
            city_url = city["url"]
            
            print(f"  [{city_index}/{len(cities_data)}] {city_name} (placeholder)")
            
            cities_weather.append({
                "city": city_name,
                "url": city_url,
                "scraped_at": datetime.now().isoformat(),
                "weather": {
                    # TODO: Add actual weather fields
                }
            })
        
        # Save weather data for this country to snapshot
        save_country_weather_data(country_name, cities_weather, snapshot_dir)
        
        # Delay between countries
        if country_index < total_countries:
            print(f"\n  → Waiting before next country...")
            time.sleep(random.uniform(2, 4))
    
    # Script completion
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Mark snapshot as successful
    snapshot_success = True
    
    print(f"\n{'='*60}")
    print(f"✓ SCRIPT COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"Started at:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:    {duration}")
    print(f"{'='*60}\n")
    
    # Cleanup: Delete snapshot directory if script failed
    if snapshot_enabled and not snapshot_success and snapshot_dir.exists():
        try:
            import shutil
            shutil.rmtree(snapshot_dir)
            print(f"⚠ Snapshot deleted due to script failure: {snapshot_dir}\n")
        except Exception as e:
            print(f"⚠ Failed to delete snapshot directory: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape weather data for cities in preferred countries")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in headed mode for debugging (browser visible)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of countries to process (for testing)"
    )
    parser.add_argument(
        "--db-store",
        action="store_true",
        help="Store scraped data in database (default: snapshots only)"
    )
    
    args = parser.parse_args()
    
    # Determine parameters from arguments
    headless = not args.dry_run
    limit = args.limit
    db_store = args.db_store
    
    # For now, user_id is None (can be passed programmatically when calling this function)
    # In the future, this could be read from environment variable or config
    user_id = None
    
    scrape_cities_weather_main(headless=headless, limit=limit, db_store=db_store, user_id=user_id)
