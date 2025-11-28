#!/usr/bin/env python3
"""
Weather Forecast Countries & Cities Scraper

Usage:
    python scrape_countries_cities.py              # Runs in headless mode
    python scrape_countries_cities.py --dry-run    # Runs in headed mode for debugging
"""

import argparse
import sys
import time
import random
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from sqlalchemy.orm import Session

# Import your database models and session
from app.core.db import SessionLocal
from app.modules.weather.models import Country as CountryModel, City as CityModel


def wait_for_element_with_retry(page, xpath: str, retries: int = 5, wait_time: int = 3000):
    """
    Wait for an element to appear with retry mechanism.
    
    Args:
        page: Playwright page object
        xpath: XPath selector for the element
        retries: Number of retry attempts
        wait_time: Wait time in milliseconds for each attempt
    
    Returns:
        Element locator if found, None otherwise
    """
    for attempt in range(retries):
        try:
            element = page.locator(f"xpath={xpath}").first
            element.wait_for(state="visible", timeout=wait_time)
            return element
        except PlaywrightTimeoutError:
            if attempt < retries - 1:
                print(f"Waiting for element (retry {attempt + 2}/{retries})...")
                time.sleep(random.uniform(2, 4))
            else:
                print(f"Element not found after {retries} attempts")
                return None
    return None


def scrape_countries(page) -> List[Dict[str, str]]:
    """
    Scrape country names and URLs from weather-forecast.com
    
    Args:
        page: Playwright page object
    
    Returns:
        List of dictionaries with 'name' and 'url' keys
    """
    countries_data = []
    base_url = "https://www.weather-forecast.com"
    target_url = f"{base_url}/countries"
    
    print(f"\n{'='*60}")
    print("PHASE 1: SCRAPING COUNTRIES")
    print(f"{'='*60}\n")
    
    try:
        print(f"Navigating to: {target_url}")
        page.goto(target_url, wait_until="domcontentloaded")
        time.sleep(random.uniform(1, 4))
        
        divs_xpath = "//div[@class='mapctrytab-cont']"
        container_divs = wait_for_element_with_retry(page, divs_xpath, retries=5)
        
        if not container_divs:
            print("ERROR: Could not find country container divs")
            return countries_data
        
        time.sleep(random.uniform(2, 4))
        
            
        # Get all matching divs
        all_divs = page.locator(f"xpath={divs_xpath}").all()
        print(f"Found {len(all_divs)} country sections")
        
        for div_index, div in enumerate(all_divs, 1):
            
            ul_xpath = ".//ul"
            uls = div.locator(f"xpath={ul_xpath}").all()
            
            for ul_index, ul in enumerate(uls, 1):
                # Find all li elements within this ul
                li_xpath = ".//li"
                lis = ul.locator(f"xpath={li_xpath}").all()
                print(f"  Section {div_index}, List {ul_index}: {len(lis)} countries")
                
                for li_index, li in enumerate(lis, 1):
                    
                    try:
                        # Find anchor tag within li
                        anchor_xpath = ".//a"
                        anchor = li.locator(f"xpath={anchor_xpath}").first
                        
                        # Get href and text
                        href = anchor.get_attribute("href")
                        country_name = anchor.inner_text().strip()
                        
                        # Process URL
                        if href:
                            if href.startswith("http"):
                                full_url = href
                            else:
                                full_url = urljoin(base_url, href)
                        else:
                            full_url = None
                        
                        countries_data.append({
                            "name": country_name,
                            "url": full_url
                        })
                        
                    except Exception as e:
                        print(f"      [!] Error processing li {li_index}: {e}")
                        continue
            
            # Small delay between sections to mimic human behavior
            if div_index < len(all_divs):
                time.sleep(random.uniform(1, 4))
        
        print(f"\n{'='*60}")
        print(f"Successfully scraped {len(countries_data)} countries")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nERROR during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    return countries_data


def scrape_cities_for_country(page, country_url: str, country_name: str) -> List[Dict[str, str]]:
    """
    Scrape cities for a specific country
    
    Args:
        page: Playwright page object
        country_url: URL of the country page
        country_name: Name of the country (for logging)
    
    Returns:
        List of dictionaries with 'name' and 'url' keys
    """
    cities_data = []
    base_url = "https://www.weather-forecast.com"
    
    print(f"Navigating to: {country_name}")
    page.goto(country_url, wait_until="domcontentloaded")
    time.sleep(random.uniform(1, 4))
    
    letter_nav_xpath = "//div[@class='letter_nav']"
    letter_nav = wait_for_element_with_retry(page, letter_nav_xpath, retries=3, wait_time=2000)
    
    # If no letter_nav found, scrape cities directly from b-wrapper
    if not letter_nav:
        print(f"  → No letter navigation found, scraping cities directly")
        
        b_wrapper_xpath = "//section[@class='b-wrapper']"
        b_wrapper = wait_for_element_with_retry(page, b_wrapper_xpath, retries=3, wait_time=2000)
        
        if not b_wrapper:
            print(f"  ⚠ No cities found for {country_name}")
            return cities_data
        
        time.sleep(random.uniform(1, 4))
        
        # Get all li items with class 'b-list-table__item'
        li_xpath = "//section[@class='b-wrapper']//ul//li[@class='b-list-table__item']"
        lis = page.locator(f"xpath={li_xpath}").all()
        
        print(f"  → Found {len(lis)} cities")
        
        for li_index, li in enumerate(lis, 1):
            try:
                # Find span with class 'b-list-table__item-name' and then anchor tag
                anchor_xpath = ".//span[@class='b-list-table__item-name']//a"
                anchor = li.locator(f"xpath={anchor_xpath}").first
                
                # Get href and text
                href = anchor.get_attribute("href")
                city_name = anchor.inner_text().strip()
                
                # Process URL
                if href:
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = urljoin(base_url, href)
                else:
                    full_url = None
                
                cities_data.append({
                    "name": city_name,
                    "url": full_url
                })
                
            except Exception as e:
                print(f"    [!] Error processing city {li_index}: {e}")
                continue
        
        print(f"Scraped {len(cities_data)} cities for {country_name}")
        return cities_data
    
    # Letter navigation exists - process with filters
    time.sleep(random.uniform(1, 4))
    
    lower_tr_xpath = "//div[@class='letter_nav']//tr[@class='lower']"
    lower_trs = page.locator(f"xpath={lower_tr_xpath}").all()
    
    # Collect all city letter links first
    all_city_letter_links = []
    
    for tr_index, tr in enumerate(lower_trs, 1):
        
        try:
            # Get the second td (skip first td with class 'left_part')
            td_xpath = ".//td[not(@class='left_part')]"
            tds = tr.locator(f"xpath={td_xpath}").all()
            
            if not tds:
                continue
            
            # Get the second td (or first non-left_part td)
            target_td = tds[0] if len(tds) > 0 else None
            
            if not target_td:
                continue
            
            anchor_xpath = ".//a"
            anchors = target_td.locator(f"xpath={anchor_xpath}").all()
            
            for anchor in anchors:
                href = anchor.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = urljoin(base_url, href)
                    all_city_letter_links.append(full_url)
            
        except Exception as e:
            print(f"    [!] Error processing letter section {tr_index}: {e}")
            continue
    
    print(f"Processing {len(all_city_letter_links)} city letter links")
    
    for link_index, city_letter_url in enumerate(all_city_letter_links, 1):
        print(f"\n[{link_index}/{len(all_city_letter_links)}] Navigating to: {city_letter_url}")
        # Delay between navigations
        if link_index > 1:
            time.sleep(random.uniform(1, 3))
        
        page.goto(city_letter_url, wait_until="domcontentloaded")
        time.sleep(random.uniform(1, 4))
        
        b_wrapper_xpath = "//section[@class='b-wrapper']"
        b_wrapper = wait_for_element_with_retry(page, b_wrapper_xpath, retries=3, wait_time=2000)
        
        if not b_wrapper:
            continue
        
        time.sleep(random.uniform(2, 4))
        
        li_xpath = "//section[@class='b-wrapper']//ul//li[@class='b-list-table__item']"
        lis = page.locator(f"xpath={li_xpath}").all()
        
        for li_index, li in enumerate(lis, 1):
            
            try:
                # Find span with class 'b-list-table__item-name' and then anchor tag
                anchor_xpath = ".//span[@class='b-list-table__item-name']//a"
                anchor = li.locator(f"xpath={anchor_xpath}").first
                
                # Get href and text
                href = anchor.get_attribute("href")
                city_name = anchor.inner_text().strip()
                
                # Process URL
                if href:
                    if href.startswith("http"):
                        full_url = href
                    else:
                        full_url = urljoin(base_url, href)
                else:
                    full_url = None
                
                cities_data.append({
                    "name": city_name,
                    "url": full_url
                })
                
            except Exception as e:
                print(f"        [!] Error processing city {li_index}: {e}")
                continue
        
        # Small delay between letter links
        if link_index < len(all_city_letter_links):
            time.sleep(random.uniform(1, 4))
    
    print(f"Scraped {len(cities_data)} cities for {country_name}")
    
    return cities_data


def upsert_countries_to_db(countries_data: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Insert or update countries in the database
    
    Args:
        countries_data: List of dictionaries with 'name' and 'url' keys
    
    Returns:
        Dictionary mapping country names to country IDs
    """
    db: Session = SessionLocal()
    country_name_to_id = {}
    
    try:
        print(f"\n{'='*60}")
        print("DATABASE: Upserting countries...")
        print(f"{'='*60}\n")
        
        inserted_count = 0
        updated_count = 0
        
        for country_data in countries_data:
            country_name = country_data["name"]
            country_url = country_data["url"]
            
            # Skip Israel
            if country_name == "Israel":
                continue
            
            # Check if country already exists
            existing_country = db.query(CountryModel).filter(
                CountryModel.name == country_name
            ).first()
            
            if existing_country:
                # Update existing country
                if existing_country.url != country_url:
                    existing_country.url = country_url
                    updated_count += 1
                country_name_to_id[country_name] = existing_country.id
            else:
                # Insert new country
                new_country = CountryModel(
                    name=country_name,
                    url=country_url
                )
                db.add(new_country)
                db.flush()  # Get the ID immediately
                inserted_count += 1
                country_name_to_id[country_name] = new_country.id
        
        # Commit all changes
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"Countries DB operations completed:")
        print(f"  - Total Processed: {len(countries_data)}")
        print(f"  - New Inserted: {inserted_count}")
        print(f"  - Updated: {updated_count}")
        print(f"  - Already Existed: {len(countries_data) - inserted_count - updated_count}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        db.rollback()
        print(f"\nERROR during country database operations: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()
    
    return country_name_to_id


def upsert_cities_to_db(cities_data: List[Dict[str, str]], country_id: str, country_name: str):
    """
    Insert or update cities in the database for a specific country
    
    Args:
        cities_data: List of dictionaries with 'name' and 'url' keys
        country_id: ID of the country these cities belong to
        country_name: Name of the country (for logging)
    """
    db: Session = SessionLocal()
    
    try:
        inserted_count = 0
        updated_count = 0
        skipped_count = 0
        
        for city_data in cities_data:
            city_name = city_data["name"]
            city_url = city_data["url"]
            
            # Check if city already exists for this country
            existing_city = db.query(CityModel).filter(
                CityModel.name == city_name,
                CityModel.country_id == country_id
            ).first()
            
            if existing_city:
                # Update existing city
                if existing_city.url != city_url:
                    existing_city.url = city_url
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Insert new city
                new_city = CityModel(
                    name=city_name,
                    url=city_url,
                    country_id=country_id
                )
                db.add(new_city)
                inserted_count += 1
        
        # Commit all changes
        db.commit()
        
        print(f"    ✓ Cities DB for {country_name}: Total={len(cities_data)}, New={inserted_count}, Updated={updated_count}, Existing={skipped_count}")
        
    except Exception as e:
        db.rollback()
        print(f"    [!] ERROR during city database operations for {country_name}: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


def scrape_countries_cities_main(headless: bool = True, limit: Optional[int] = None, db_store: bool = False):
    """
    Main execution function
    
    Args:
        headless: Run browser in headless mode (default: True)
        limit: Limit number of countries to process (default: None = all countries)
        db_store: Store data in database (default: False)
    """
    # If called from command line, parse arguments
    if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Scrape countries and cities from weather-forecast.com")
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
        
        # Override parameters with command line arguments
        headless = not args.dry_run
        limit = args.limit
        db_store = args.db_store
    
    # Snapshot configuration (always enabled by default)
    snapshot_enabled = True
    snapshot_data = []
    snapshot_file_path = None
    snapshot_success = False
    
    # Define snapshot directory and file path using pathlib
    from pathlib import Path
    
    # Get project root (4 levels up from this script)
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    snapshot_dir = project_root / "data" / "snapshots" / "scrape_countries_cities"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Check if snapshot for today already exists and delete it
    existing_snapshots = list(snapshot_dir.glob(f"{current_date}*"))
    for existing_path in existing_snapshots:
        print(f"Removing existing snapshot: {existing_path}")
        existing_path.unlink()
    
    # Create new snapshot file path
    snapshot_file_path = snapshot_dir / f"{current_date}_countries_cities.json"
    print(f"Snapshots enabled. Will save to: {snapshot_file_path}\n")
    
    if db_store:
        print("Database storage enabled (--db-store flag provided)\n")
    else:
        print("Database storage disabled (default behavior). Use --db-store to enable.\n")
    
    # Determine headless mode (default: True, unless --dry-run is specified)
    
    print(f"\n{'='*60}")
    print(f"Starting scraper in {'HEADLESS' if headless else 'HEADED'} mode")
    print(f"{'='*60}\n")
    
    with sync_playwright() as p:
        # Launch browser function
        def launch_browser():
            print("Launching browser...")
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            return browser, context, page

        browser, context, page = launch_browser()
        
        try:
            # PHASE 1: Scrape countries
            try:
                countries_data = scrape_countries(page)
            except Exception as e:
                print(f"Error during country scraping: {e}")
                # Try one restart for countries
                print("Restarting browser and retrying countries scraping...")
                browser.close()
                browser, context, page = launch_browser()
                countries_data = scrape_countries(page)
            
            if not countries_data:
                print("\n⚠ No countries data scraped. Exiting.")
                sys.exit(1)
            
            # Upsert countries to database and get country IDs (only if DB store enabled)
            country_name_to_id = {}
            if db_store:
                country_name_to_id = upsert_countries_to_db(countries_data)
            
            # Initialize snapshot data if enabled
            if snapshot_enabled:
                for country in countries_data:
                    snapshot_data.append({
                        "country": country["name"],
                        "url": country["url"],
                        "cities": []
                    })
            
            # PHASE 2: Scrape cities for each country
            print(f"\n{'='*60}")
            print("PHASE 2: SCRAPING CITIES FOR EACH COUNTRY")
            print(f"{'='*60}\n")
            
            # Apply limit if specified
            countries_to_process = countries_data[:limit] if limit else countries_data
            total_countries = len(countries_to_process)
            
            if limit:
                print(f"⚠ Processing limited to {limit} countries (testing mode)\n")
            
            for country_index, country in enumerate(countries_to_process, 1):
                country_name = country["name"]
                country_url = country["url"]
                
                # Only check for ID if DB store is enabled
                country_id = None
                if db_store:
                    country_id = country_name_to_id.get(country_name)
                    if not country_id:
                        print(f"[{country_index}/{total_countries}] ⚠ Skipping {country_name} - no ID found")
                        continue
                
                if not country_url:
                    print(f"[{country_index}/{total_countries}] ⚠ Skipping {country_name} - no URL")
                    continue
                
                print(f"\n{'='*60}")
                print(f"[{country_index}/{total_countries}] Processing: {country_name}")
                print(f"{'='*60}")
                
                # Scrape cities for this country with retry logic
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        cities_data = scrape_cities_for_country(page, country_url, country_name)
                        
                        if cities_data:
                            # Upsert cities to database (only if enabled)
                            if db_store and country_id:
                                upsert_cities_to_db(cities_data, country_id, country_name)
                            
                            # Add cities to snapshot data if enabled
                            if snapshot_enabled:
                                # Find the country object in snapshot_data array
                                for country_obj in snapshot_data:
                                    if country_obj["country"] == country_name:
                                        country_obj["cities"] = cities_data
                                        break
                                
                                # Save snapshot incrementally after each country
                                try:
                                    with open(snapshot_file_path, 'w', encoding='utf-8') as f:
                                        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
                                except Exception as e:
                                    print(f"  ⚠ Warning: Failed to save incremental snapshot: {e}")
                        else:
                            print(f"  ⚠ No cities found for {country_name}")
                        
                        # Break retry loop if successful
                        break
                        
                    except Exception as e:
                        print(f"  [!] Error processing {country_name} (Attempt {attempt+1}/{max_retries}): {e}")
                        
                        # Check if it's a browser crash/closed error
                        error_str = str(e).lower()
                        if "closed" in error_str or "crash" in error_str or "detached" in error_str:
                            print("  ⚠ Browser appears to have crashed/closed. Restarting...")
                            try:
                                browser.close()
                            except:
                                pass
                            browser, context, page = launch_browser()
                        
                        if attempt == max_retries - 1:
                            print(f"  ✗ Failed to process {country_name} after {max_retries} attempts")
                
                # Delay between countries to mimic human behavior
                if country_index < total_countries:
                    print(f"\n  → Waiting before next country...")
                    time.sleep(random.uniform(4, 7))
            
            print(f"\n{'='*60}")
            print("✓ Script completed successfully!")
            print(f"{'='*60}\n")
            
            # Mark snapshot as successful
            snapshot_success = True
            
        except Exception as e:
            print(f"\nERROR during execution: {e}")
            import traceback
            traceback.print_exc()
            snapshot_success = False
            sys.exit(1)
        
        finally:
            # Save snapshot if enabled and successful
            if snapshot_enabled and snapshot_success and snapshot_file_path:
                try:
                    with open(snapshot_file_path, 'w', encoding='utf-8') as f:
                        json.dump(snapshot_data, f, indent=2, ensure_ascii=False)
                    print(f"✓ Snapshot saved successfully: {snapshot_file_path}\n")
                except Exception as e:
                    print(f"⚠ Failed to save snapshot: {e}\n")
            elif snapshot_enabled and not snapshot_success and snapshot_file_path:
                # Delete snapshot file if script failed
                if snapshot_file_path.exists():
                    try:
                        snapshot_file_path.unlink()
                        print(f"⚠ Snapshot deleted due to script failure: {snapshot_file_path}\n")
                    except Exception as e:
                        print(f"⚠ Failed to delete snapshot: {e}\n")
            
            # Close browser
            print("Closing browser...")
            try:
                browser.close()
            except:
                pass


if __name__ == "__main__":
    scrape_countries_cities_main()