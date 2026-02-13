#!/usr/bin/env python3
"""
Special recovery script for Page 34
Uses manual navigation and robust error handling
"""
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime

# Import the main scraper class
from scrape_erc_licenses import ERCLicenseScraper

def recover_page_34_manual():
    """
    Manually navigate to page 34 and extract data with extra error handling
    """
    print("="*70)
    print("  PAGE 34 RECOVERY - Manual Approach")
    print("="*70)

    scraper = ERCLicenseScraper()

    # Use the scraper's driver creation method
    driver = scraper.create_driver()
    scraper.driver = driver

    try:
        print("\n[1] Loading initial page...")
        url = "https://www.erc.or.th/th/state/search-license"
        driver.get(url)
        time.sleep(5)

        print("[2] Clicking initial search button...")
        try:
            search_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "btn_search"))
            )
            driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(5)
        except Exception as e:
            print(f"  Warning: Could not click search button: {e}")
            print("  Please manually click the search button in the browser...")
            input("  Press Enter when you've clicked the search button and results are loaded...")

        # Navigate to page 34 manually with JavaScript
        print("\n[3] Navigating to page 34...")

        # Try multiple navigation methods
        methods_tried = 0
        success = False

        # Method 1: Direct page number input
        try:
            print("  Trying method 1: Direct page input...")
            page_input = driver.find_element(By.CSS_SELECTOR, "input.rgPageFirst + input[type='text']")
            page_input.clear()
            page_input.send_keys("34")
            # Find and click the page change button
            driver.find_element(By.CSS_SELECTOR, "input.rgPageFirst + input + input[type='button']").click()
            time.sleep(8)
            success = True
            print("  Success with method 1!")
        except Exception as e:
            print(f"  Method 1 failed: {e}")
            methods_tried += 1

        # Method 2: JavaScript navigation
        if not success:
            try:
                print("  Trying method 2: JavaScript...")
                driver.execute_script("""
                    var grid = $find('RadGrid1');
                    if (grid) {
                        grid.get_masterTableView().page(33); // 0-indexed
                    }
                """)
                time.sleep(8)
                success = True
                print("  Success with method 2!")
            except Exception as e:
                print(f"  Method 2 failed: {e}")
                methods_tried += 1

        # Method 3: Manual intervention
        if not success:
            print("\n  Automated navigation failed!")
            print("  Please manually navigate to page 34 in the browser...")
            input("  Press Enter when you're on page 34...")

        # Verify we're on page 34
        print("\n[4] Verifying page 34...")
        time.sleep(3)
        try:
            current_page_elem = driver.find_element(By.CSS_SELECTOR, "input.rgCurrentPage")
            current_page = current_page_elem.get_attribute("value")
            print(f"  Current page: {current_page}")
            if current_page != "34":
                print(f"  WARNING: Not on page 34! On page {current_page}")
                print("  Please navigate to page 34 manually...")
                input("  Press Enter when ready...")
        except Exception as e:
            print(f"  Could not verify page: {e}")

        # Now extract data from page 34
        print("\n[5] Extracting data from page 34...")
        page_34_data = []

        # Get all rows
        rows = driver.find_elements(By.CSS_SELECTOR, "table.rgMasterTable tbody tr[id]")
        print(f"  Found {len(rows)} records on page 34")

        for idx, row in enumerate(rows, start=1):
            try:
                record_num = (34 - 1) * 15 + idx
                print(f"    [{record_num}] Extracting details...", end=" ")

                # Click the detail button
                detail_btn = row.find_element(By.CSS_SELECTOR, "img[title='Detail']")
                driver.execute_script("arguments[0].scrollIntoView(true);", detail_btn)
                time.sleep(0.5)
                driver.execute_script("arguments[0].click();", detail_btn)
                time.sleep(3)

                # Extract data
                data = scraper.extract_detail_data(driver)
                if data:
                    page_34_data.append(data)
                    print("[OK]")
                else:
                    print("[EMPTY]")

                # Close popup
                scraper.close_popup(driver)
                time.sleep(1)

            except Exception as e:
                print(f"[ERROR: {str(e)[:50]}]")
                scraper.close_popup(driver)
                time.sleep(1)
                continue

        # Save data
        if page_34_data:
            print(f"\n[6] Saving {len(page_34_data)} records...")
            df = pd.DataFrame(page_34_data)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = f"page_34_recovered_{timestamp}.xlsx"
            csv_file = f"page_34_recovered_{timestamp}.csv"

            df.to_excel(excel_file, index=False, engine='openpyxl')
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')

            print(f"  [OK] Excel: {excel_file}")
            print(f"  [OK] CSV: {csv_file}")
            print("\n" + "="*70)
            print(f"  SUCCESS! Recovered {len(page_34_data)} records from page 34")
            print("="*70)

            return excel_file, csv_file
        else:
            print("\n[ERROR] No data extracted from page 34!")
            return None, None

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None, None

    finally:
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()

if __name__ == '__main__':
    recover_page_34_manual()
