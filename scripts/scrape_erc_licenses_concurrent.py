"""
ERC Energy License Scraper - Concurrent Version
Uses multiple Chrome instances to scrape pages in parallel
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import sys
import os

# Import the main scraper class
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_erc_licenses import ERCLicenseScraper


class ConcurrentERCScraper:
    """Concurrent scraper using multiple Chrome instances"""

    def __init__(self, num_workers=2):
        """
        Initialize concurrent scraper

        Args:
            num_workers: Number of parallel Chrome instances (default: 2)
                        Recommended: 2-3 workers for stability
        """
        self.num_workers = num_workers
        self.base_url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"
        self.all_data = []
        self.data_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        self.total_extracted = 0

    def worker_scrape_page(self, worker_id, page_number, max_records=None):
        """
        Worker function to scrape a single page

        Args:
            worker_id: ID of the worker (for logging)
            page_number: Page number to scrape
            max_records: Max records to extract from page

        Returns:
            tuple: (page_number, list of extracted records)
        """
        # Small delay to stagger worker starts
        time.sleep((worker_id - 1) * 2)

        # Create a scraper instance for this worker
        scraper = ERCLicenseScraper()

        try:
            scraper.driver = scraper.create_driver()
        except Exception as e:
            print(f"[Worker-{worker_id}] [ERROR] Could not create driver for page {page_number}: {e}")
            return (page_number, [])

        print(f"[Worker-{worker_id}] Starting page {page_number}")

        try:
            # Scrape the page
            page_data = scraper.scrape_page(page_number, max_records=max_records)

            with self.progress_lock:
                self.total_extracted += len(page_data)
                print(f"[Worker-{worker_id}] [OK] Page {page_number} done: {len(page_data)} records (Total: {self.total_extracted})")

            return (page_number, page_data)

        except Exception as e:
            print(f"[Worker-{worker_id}] [FAIL] Page {page_number} error: {str(e)[:50]}")
            return (page_number, [])

        finally:
            # Always close the driver
            if scraper.driver:
                try:
                    scraper.driver.quit()
                    time.sleep(1)  # Give time for cleanup
                except:
                    pass

    def scrape_concurrent(self, max_pages=None, max_records_per_page=None):
        """
        Scrape pages concurrently using multiple workers

        Args:
            max_pages: Maximum number of pages to scrape (None for all)
            max_records_per_page: Max records per page (None for all)
        """
        print(f"\n{'='*70}")
        print(f"  ERC Energy License Scraper - CONCURRENT MODE")
        print(f"  Workers: {self.num_workers}")
        print(f"{'='*70}")

        # First, get total pages using a temporary driver
        print("\n[INIT] Detecting total pages...")
        temp_scraper = ERCLicenseScraper()
        temp_scraper.driver = temp_scraper.create_driver()

        try:
            temp_scraper.driver.get(self.base_url)
            time.sleep(3)
            detected_pages = temp_scraper.get_total_pages(temp_scraper.driver)
        finally:
            temp_scraper.driver.quit()

        total_pages = min(max_pages, detected_pages) if max_pages else detected_pages

        print(f"\n[CONFIG] Scraping Configuration:")
        print(f"   Total pages detected: {detected_pages}")
        print(f"   Pages to scrape: {total_pages}")
        print(f"   Workers: {self.num_workers}")
        if max_records_per_page:
            print(f"   Max records per page: {max_records_per_page}")
        print()

        # Create list of pages to scrape
        pages_to_scrape = list(range(1, total_pages + 1))

        print(f"[START] Scraping {total_pages} pages with {self.num_workers} workers...")
        print(f"{'='*70}\n")

        start_time = time.time()

        # Use ThreadPoolExecutor to manage workers
        results = {}
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all pages to workers
            future_to_page = {}
            for page_num in pages_to_scrape:
                # Assign worker ID based on page (for logging)
                worker_id = ((page_num - 1) % self.num_workers) + 1
                future = executor.submit(
                    self.worker_scrape_page,
                    worker_id,
                    page_num,
                    max_records_per_page
                )
                future_to_page[future] = page_num

            # Collect results as they complete
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_number, page_data = future.result()
                    results[page_number] = page_data
                except Exception as e:
                    print(f"[ERROR] Page {page_num} raised exception: {e}")
                    results[page_num] = []

        # Collect all data in page order
        for page_num in sorted(results.keys()):
            self.all_data.extend(results[page_num])

        elapsed_time = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"[COMPLETE] Scraping finished!")
        print(f"   Total records extracted: {len(self.all_data)}")
        print(f"   Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"   Average: {elapsed_time/total_pages:.1f} sec/page")
        print(f"   Speed boost: ~{self.num_workers}x faster than sequential")
        print(f"{'='*70}\n")

    def save_to_excel(self, filename=None):
        """Save data to Excel with formatting"""
        if not self.all_data:
            print("No data to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erc_license_details_concurrent_{timestamp}.xlsx"

        print(f"[SAVE] Saving data to Excel: {filename}")

        # Flatten nested data for Excel
        flattened_data = []
        for record in self.all_data:
            flat_record = {}

            # Copy basic fields
            for key, value in record.items():
                if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                    flat_record[key] = value

            # Flatten production plans
            plans = record.get('แผนการผลิต', [])
            if plans:
                for i, plan in enumerate(plans, 1):
                    for k, v in plan.items():
                        flat_record[f'แผนการผลิต_{i}_{k}'] = v

            # Flatten processes
            processes = record.get('กระบวนการผลิต', [])
            if processes:
                for i, proc in enumerate(processes, 1):
                    for k, v in proc.items():
                        flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

            # Flatten machines
            machines = record.get('เครื่องจักร', [])
            if machines:
                for i, machine in enumerate(machines, 1):
                    for k, v in machine.items():
                        flat_record[f'เครื่องจักร_{i}_{k}'] = v

            flattened_data.append(flat_record)

        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)

        # Sort by record number
        if '_record_number' in df.columns:
            df = df.sort_values('_record_number')

        # Save to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='License Details', index=False)

            # Get worksheet
            worksheet = writer.sheets['License Details']

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"[OK] Data saved successfully!")
        print(f"   File: {filename}")
        print(f"   Records: {len(df)}")
        print(f"   Columns: {len(df.columns)}")

    def save_to_csv(self, filename=None):
        """Save data to CSV"""
        if not self.all_data:
            print("No data to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erc_license_details_concurrent_{timestamp}.csv"

        # Flatten data same as Excel
        flattened_data = []
        for record in self.all_data:
            flat_record = {}
            for key, value in record.items():
                if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                    flat_record[key] = value

            plans = record.get('แผนการผลิต', [])
            if plans:
                for i, plan in enumerate(plans, 1):
                    for k, v in plan.items():
                        flat_record[f'แผนการผลิต_{i}_{k}'] = v

            processes = record.get('กระบวนการผลิต', [])
            if processes:
                for i, proc in enumerate(processes, 1):
                    for k, v in proc.items():
                        flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

            machines = record.get('เครื่องจักร', [])
            if machines:
                for i, machine in enumerate(machines, 1):
                    for k, v in machine.items():
                        flat_record[f'เครื่องจักร_{i}_{k}'] = v

            flattened_data.append(flat_record)

        df = pd.DataFrame(flattened_data)
        if '_record_number' in df.columns:
            df = df.sort_values('_record_number')

        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"[OK] CSV saved: {filename}")


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("  ERC Energy License Detail Scraper - CONCURRENT VERSION")
    print("  Multiple Chrome instances for faster scraping")
    print("="*70)

    # Configuration
    NUM_WORKERS = 2         # Number of parallel Chrome instances (2-3 recommended)
    MAX_PAGES = 5           # Number of pages to scrape (None for all 133)
    MAX_RECORDS = None      # Max records per page (None for all ~15)

    print(f"\n[CONFIG] Using {NUM_WORKERS} concurrent workers")
    print(f"         Scraping {MAX_PAGES if MAX_PAGES else 'ALL'} pages")
    print(f"         {MAX_RECORDS if MAX_RECORDS else 'ALL'} records per page")

    # Create concurrent scraper
    scraper = ConcurrentERCScraper(num_workers=NUM_WORKERS)

    try:
        # Scrape data
        scraper.scrape_concurrent(
            max_pages=MAX_PAGES,
            max_records_per_page=MAX_RECORDS
        )

        # Save to Excel
        scraper.save_to_excel()

        # Also save to CSV
        scraper.save_to_csv()

        print("\n" + "="*70)
        print("  [SUCCESS] Concurrent scraping completed successfully!")
        print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n[WARNING] Scraping interrupted by user")
        print(f"   Partial data collected: {len(scraper.all_data)} records")
        if scraper.all_data:
            save = input("\n   Save partial data? (y/n): ")
            if save.lower() == 'y':
                scraper.save_to_excel()
                scraper.save_to_csv()

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
