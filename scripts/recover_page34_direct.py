#!/usr/bin/env python3
"""
Page 34 Recovery using direct URL provided by user
No manual intervention needed
"""
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from datetime import datetime
from scrape_erc_licenses import ERCLicenseScraper

def recover_page_34_direct():
    """
    Navigate directly to the listing page and go to page 34
    """
    print("="*70)
    print("  PAGE 34 RECOVERY - Direct URL Method")
    print("="*70)

    scraper = ERCLicenseScraper()
    driver = scraper.create_driver()
    scraper.driver = driver

    try:
        # Go directly to the listing page
        print("\n[1] Loading listing page directly...")
        url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"
        driver.get(url)
        time.sleep(8)

        print("[2] Navigating to page 34...")

        # Try JavaScript navigation first
        try:
            driver.execute_script("""
                var grid = $find('RadGrid1');
                if (grid && grid.get_masterTableView()) {
                    grid.get_masterTableView().page(33); // 0-indexed, so page 34 is index 33
                }
            """)
            time.sleep(8)
            print("  Navigated via JavaScript")
        except Exception as e:
            print(f"  JavaScript navigation failed: {e}")

            # Try page input method
            try:
                page_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input.rgPageFirst + input[type='text']"))
                )
                page_input.clear()
                page_input.send_keys("34")

                # Click page change button
                page_btn = driver.find_element(By.CSS_SELECTOR, "input.rgPageFirst + input + input[type='button']")
                driver.execute_script("arguments[0].click();", page_btn)
                time.sleep(8)
                print("  Navigated via page input")
            except Exception as e2:
                print(f"  Page input failed: {e2}")
                print("  ERROR: Could not navigate to page 34")
                return None, None

        # Verify page 34
        print("\n[3] Verifying we're on page 34...")
        try:
            current_page_elem = driver.find_element(By.CSS_SELECTOR, "input.rgCurrentPage")
            current_page = current_page_elem.get_attribute("value")
            print(f"  Current page: {current_page}")

            if current_page != "34":
                print(f"  WARNING: Not on page 34! We're on page {current_page}")
                return None, None
        except Exception as e:
            print(f"  Could not verify page number: {e}")

        # Extract data
        print("\n[4] Extracting records from page 34...")
        page_34_data = []

        rows = driver.find_elements(By.CSS_SELECTOR, "table.rgMasterTable tbody tr[id]")
        print(f"  Found {len(rows)} records")

        for idx, row in enumerate(rows, start=1):
            try:
                record_num = 496 + idx - 1  # Page 34 starts at record 496
                print(f"    [{record_num}] Extracting...", end=" ", flush=True)

                # Click detail button
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
                print(f"[ERROR: {str(e)[:40]}]")
                try:
                    scraper.close_popup(driver)
                except:
                    pass
                time.sleep(1)
                continue

        # Save data
        if page_34_data:
            print(f"\n[5] Saving {len(page_34_data)} records...")
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
            print("\n[ERROR] No data extracted!")
            return None, None

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None, None

    finally:
        print("\nClosing browser...")
        time.sleep(3)
        driver.quit()

if __name__ == '__main__':
    excel_file, csv_file = recover_page_34_direct()
    if excel_file:
        print(f"\nRecovered files:")
        print(f"  - {excel_file}")
        print(f"  - {csv_file}")
    else:
        print("\nRecovery failed!")
