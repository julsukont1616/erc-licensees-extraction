"""
ERC Energy License Scraper - Process-Based Parallel Version
Uses multiprocessing for better isolation and stability
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
from datetime import datetime
from multiprocessing import Pool, Manager, cpu_count
import sys
import os

# Import the main scraper class
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scrape_erc_licenses import ERCLicenseScraper


def scrape_single_page(args):
    """
    Worker function to scrape a single page (runs in separate process)

    Args:
        args: tuple of (page_number, max_records, worker_id)

    Returns:
        tuple: (page_number, list of extracted records, error_msg)
    """
    page_number, max_records, worker_id = args

    print(f"[Worker-{worker_id}] [Page {page_number}] Starting...")

    try:
        # Create a scraper instance for this process
        scraper = ERCLicenseScraper()
        scraper.driver = scraper.create_driver()

        # Scrape the page
        page_data = scraper.scrape_page(page_number, max_records=max_records)

        # Close driver
        scraper.driver.quit()

        print(f"[Worker-{worker_id}] [Page {page_number}] OK - {len(page_data)} records")
        return (page_number, page_data, None)

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:100]}"
        print(f"[Worker-{worker_id}] [Page {page_number}] FAILED - {error_msg}")
        return (page_number, [], error_msg)


class ParallelERCScraper:
    """Process-based parallel scraper for better stability"""

    def __init__(self, num_workers=2):
        """
        Initialize parallel scraper

        Args:
            num_workers: Number of parallel processes (default: 2)
                        Max recommended: cpu_count() or 3, whichever is lower
        """
        max_workers = min(cpu_count(), 3)
        self.num_workers = min(num_workers, max_workers)
        self.base_url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"
        self.all_data = []

    def scrape_parallel(self, max_pages=None, max_records_per_page=None, batch_size=None):
        """
        Scrape pages in parallel using multiprocessing

        Args:
            max_pages: Maximum number of pages to scrape (None for all)
            max_records_per_page: Max records per page (None for all)
            batch_size: Process pages in batches (default: None = all at once)
                       Recommended: 5-10 for large scrapes
        """
        print(f"\n{'='*70}")
        print(f"  ERC Energy License Scraper - PARALLEL MODE")
        print(f"  Workers: {self.num_workers} processes")
        print(f"{'='*70}")

        # Get total pages
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
        print(f"   Parallel workers: {self.num_workers}")
        if max_records_per_page:
            print(f"   Max records per page: {max_records_per_page}")
        if batch_size:
            print(f"   Batch size: {batch_size} pages")
        print()

        # Create list of pages to scrape
        pages_to_scrape = list(range(1, total_pages + 1))

        # Process in batches if specified
        if batch_size:
            batches = [pages_to_scrape[i:i+batch_size] for i in range(0, len(pages_to_scrape), batch_size)]
            print(f"[INFO] Processing {len(batches)} batches of up to {batch_size} pages each\n")
        else:
            batches = [pages_to_scrape]
            print(f"[INFO] Processing all {len(pages_to_scrape)} pages in one batch\n")

        start_time = time.time()
        results = {}
        total_processed = 0

        # Process each batch
        for batch_num, batch_pages in enumerate(batches, 1):
            if len(batches) > 1:
                print(f"\n{'='*70}")
                print(f"  BATCH {batch_num}/{len(batches)} - Pages {batch_pages[0]} to {batch_pages[-1]}")
                print(f"{'='*70}\n")

            # Prepare arguments for each page in this batch
            batch_args = [(page_num, max_records_per_page, (page_num % self.num_workers) + 1)
                         for page_num in batch_pages]

            # Use multiprocessing Pool
            with Pool(processes=self.num_workers) as pool:
                batch_results = pool.map(scrape_single_page, batch_args)

            # Collect batch results
            for page_number, page_data, error_msg in batch_results:
                results[page_number] = page_data
                total_processed += 1
                if error_msg:
                    print(f"[WARNING] Page {page_number} had errors: {error_msg}")

            # Show batch progress
            batch_records = sum(len(data) for _, data, _ in batch_results)
            print(f"\n[BATCH {batch_num} COMPLETE] {len(batch_pages)} pages, {batch_records} records")

        # Collect all data in page order
        for page_num in sorted(results.keys()):
            self.all_data.extend(results[page_num])

        elapsed_time = time.time() - start_time

        print(f"\n{'='*70}")
        print(f"[COMPLETE] Parallel scraping finished!")
        print(f"   Total pages processed: {total_processed}")
        print(f"   Total records extracted: {len(self.all_data)}")
        print(f"   Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time/60:.1f} minutes)")
        print(f"   Average: {elapsed_time/total_processed:.1f} sec/page")
        if self.num_workers > 1:
            print(f"   Speedup: ~{self.num_workers}x faster than sequential")
        print(f"{'='*70}\n")

    def save_to_excel(self, filename=None):
        """Save data to Excel"""
        if not self.all_data:
            print("No data to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erc_license_details_parallel_{timestamp}.xlsx"

        print(f"[SAVE] Saving to Excel: {filename}")

        # Flatten nested data
        flattened_data = []
        for record in self.all_data:
            flat_record = {}
            for key, value in record.items():
                if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                    flat_record[key] = value

            for i, plan in enumerate(record.get('แผนการผลิต', []), 1):
                for k, v in plan.items():
                    flat_record[f'แผนการผลิต_{i}_{k}'] = v

            for i, proc in enumerate(record.get('กระบวนการผลิต', []), 1):
                for k, v in proc.items():
                    flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

            for i, machine in enumerate(record.get('เครื่องจักร', []), 1):
                for k, v in machine.items():
                    flat_record[f'เครื่องจักร_{i}_{k}'] = v

            flattened_data.append(flat_record)

        df = pd.DataFrame(flattened_data)
        if '_record_number' in df.columns:
            df = df.sort_values('_record_number')

        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='License Details', index=False)
            worksheet = writer.sheets['License Details']
            for column in worksheet.columns:
                max_length = max(len(str(cell.value)) for cell in column)
                worksheet.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)

        print(f"[OK] Excel saved: {filename}")
        print(f"     Records: {len(df)}, Columns: {len(df.columns)}")

    def save_to_csv(self, filename=None):
        """Save data to CSV"""
        if not self.all_data:
            print("No data to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erc_license_details_parallel_{timestamp}.csv"

        # Flatten data
        flattened_data = []
        for record in self.all_data:
            flat_record = {}
            for key, value in record.items():
                if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                    flat_record[key] = value

            for i, plan in enumerate(record.get('แผนการผลิต', []), 1):
                for k, v in plan.items():
                    flat_record[f'แผนการผลิต_{i}_{k}'] = v

            for i, proc in enumerate(record.get('กระบวนการผลิต', []), 1):
                for k, v in proc.items():
                    flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

            for i, machine in enumerate(record.get('เครื่องจักร', []), 1):
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
    print("  ERC Energy License Scraper - PARALLEL VERSION")
    print("  Uses multiprocessing for better stability")
    print("="*70)

    # Configuration
    NUM_WORKERS = 2         # Number of parallel processes (2-3 recommended)
    MAX_PAGES = 10          # Number of pages to scrape (None for all 133)
    MAX_RECORDS = None      # Max records per page (None for all ~15)
    BATCH_SIZE = 5          # Process pages in batches (None = all at once)

    print(f"\n[CONFIG] Using {NUM_WORKERS} parallel processes")
    print(f"         Scraping {MAX_PAGES if MAX_PAGES else 'ALL'} pages")
    print(f"         Batch size: {BATCH_SIZE if BATCH_SIZE else 'ALL'} pages")

    # Create parallel scraper
    scraper = ParallelERCScraper(num_workers=NUM_WORKERS)

    try:
        # Scrape data
        scraper.scrape_parallel(
            max_pages=MAX_PAGES,
            max_records_per_page=MAX_RECORDS,
            batch_size=BATCH_SIZE
        )

        # Save results
        scraper.save_to_excel()
        scraper.save_to_csv()

        print("\n" + "="*70)
        print("  [SUCCESS] Parallel scraping completed!")
        print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n[WARNING] Interrupted by user")
        print(f"   Partial data: {len(scraper.all_data)} records")
        if scraper.all_data:
            save = input("\n   Save partial data? (y/n): ")
            if save.lower() == 'y':
                scraper.save_to_excel()
                scraper.save_to_csv()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
