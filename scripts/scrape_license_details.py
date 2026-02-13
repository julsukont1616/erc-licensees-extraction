#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to scrape additional license details from the ERC website.
Extracts data from popup windows that aren't in the exported CSV.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import re

def setup_driver():
    """Setup Chrome driver with appropriate options."""
    options = Options()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Uncomment to run headless (without opening browser window)
    # options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    return driver

def extract_popup_data(driver, main_window):
    """Extract all data from the popup window."""
    try:
        # Switch to the popup window
        for handle in driver.window_handles:
            if handle != main_window:
                driver.switch_to.window(handle)
                break

        # Wait for popup to load
        time.sleep(2)

        # Extract all data from the popup
        popup_data = {}

        # Try to find all table rows or labeled data
        # This will depend on the popup structure - we'll extract everything we can find
        try:
            # Look for tables with data
            tables = driver.find_elements(By.TAG_NAME, 'table')
            for table_idx, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, 'td')
                    if len(cells) >= 2:
                        # Assume first cell is label, second is value
                        label = cells[0].text.strip()
                        value = cells[1].text.strip()
                        if label and label != '':
                            popup_data[label] = value

            # Also try to get the entire page text as backup
            body = driver.find_element(By.TAG_NAME, 'body')
            popup_data['_full_text'] = body.text

        except Exception as e:
            print(f"    Error extracting popup data: {e}")
            popup_data['_error'] = str(e)

        # Close popup and switch back
        driver.close()
        driver.switch_to.window(main_window)

        return popup_data

    except Exception as e:
        print(f"    Error handling popup: {e}")
        driver.switch_to.window(main_window)
        return {'_error': str(e)}

def scrape_license_data(url, max_rows=10):
    """
    Scrape license data from the website.

    Args:
        url: The URL to scrape
        max_rows: Maximum number of rows to process (for testing)
    """
    print("="*100)
    print("ERC LICENSE DETAIL SCRAPER")
    print("="*100)
    print(f"\nTarget URL: {url}")
    print(f"Max rows to process: {max_rows}\n")

    driver = setup_driver()
    all_data = []

    try:
        print("Loading main page...")
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 20)

        # Wait for the table to appear
        print("Waiting for table to load...")
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))

        time.sleep(3)  # Additional wait for dynamic content

        print("Finding all data rows...")

        # Find all rows in the table
        rows = driver.find_elements(By.XPATH, "//table//tr[td]")
        total_rows = len(rows)

        print(f"Found {total_rows} data rows")
        print(f"Processing first {min(max_rows, total_rows)} rows...\n")

        main_window = driver.current_window_handle

        # Process each row
        for idx in range(min(max_rows, total_rows)):
            try:
                # Re-find the rows (in case page changed)
                rows = driver.find_elements(By.XPATH, "//table//tr[td]")
                row = rows[idx]

                print(f"Row {idx + 1}/{min(max_rows, total_rows)}:")

                # Extract visible data from the row
                cells = row.find_elements(By.TAG_NAME, 'td')
                row_data = {}

                for cell_idx, cell in enumerate(cells):
                    row_data[f'col_{cell_idx}'] = cell.text.strip()

                print(f"  Visible data: {row_data.get('col_1', 'N/A')[:50]}...")

                # Look for the detail icon/link (รายละเอียด column)
                # Try to find a clickable element (link or icon)
                detail_links = row.find_elements(By.XPATH, ".//a[contains(@href, 'javascript:')]")

                if detail_links:
                    print(f"  Found {len(detail_links)} clickable elements, clicking first...")

                    # Click the detail link
                    detail_links[0].click()

                    # Wait for popup
                    time.sleep(2)

                    # Check if popup window opened
                    if len(driver.window_handles) > 1:
                        print("  Popup opened, extracting data...")
                        popup_data = extract_popup_data(driver, main_window)
                        row_data['popup_data'] = popup_data
                        print(f"  Extracted {len(popup_data)} fields from popup")
                    else:
                        print("  No popup window detected")
                        row_data['popup_data'] = {'_note': 'No popup opened'}
                else:
                    print("  No detail link found in this row")
                    row_data['popup_data'] = {'_note': 'No detail link'}

                all_data.append(row_data)
                print()

            except Exception as e:
                print(f"  Error processing row {idx + 1}: {e}")
                print()
                continue

        print("\n" + "="*100)
        print(f"COMPLETED: Processed {len(all_data)} rows")
        print("="*100)

    except Exception as e:
        print(f"\nError during scraping: {e}")

    finally:
        print("\nClosing browser...")
        driver.quit()

    return all_data

def save_results(data, output_file='license_details_scraped.xlsx'):
    """Save scraped data to Excel file."""
    if not data:
        print("No data to save!")
        return

    print(f"\nSaving {len(data)} records to {output_file}...")

    # Flatten the data structure
    flattened_data = []
    for row in data:
        flat_row = {}

        # Add regular columns
        for key, value in row.items():
            if key != 'popup_data':
                flat_row[key] = value

        # Add popup data with prefix
        if 'popup_data' in row:
            for popup_key, popup_value in row['popup_data'].items():
                flat_row[f'detail_{popup_key}'] = popup_value

        flattened_data.append(flat_row)

    # Create DataFrame and save
    df = pd.DataFrame(flattened_data)
    df.to_excel(output_file, index=False)

    print(f"Saved successfully!")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  File: {output_file}")

def main():
    url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"

    # Start with just 5 rows for testing
    print("\n" + "="*100)
    print("TESTING MODE: Processing first 5 rows")
    print("="*100)
    print("Once verified, you can increase max_rows to process all data")
    print("="*100 + "\n")

    data = scrape_license_data(url, max_rows=5)

    if data:
        save_results(data)

        # Show sample of what was extracted
        print("\n" + "="*100)
        print("SAMPLE OF EXTRACTED DATA")
        print("="*100)
        for idx, row in enumerate(data[:2], 1):
            print(f"\nRow {idx}:")
            print(f"  Visible columns: {len([k for k in row.keys() if k != 'popup_data'])}")
            if 'popup_data' in row:
                print(f"  Popup fields: {len(row['popup_data'])}")
                print(f"  Popup keys: {list(row['popup_data'].keys())[:5]}...")
    else:
        print("\nNo data was extracted. Please check:")
        print("1. Website is accessible")
        print("2. Chrome driver is installed")
        print("3. Website structure hasn't changed")

if __name__ == '__main__':
    main()
