#!/usr/bin/env python3
"""
Scrape only page 34 using the main scraper
Output will be saved as a separate file for manual merging
"""
from scrape_erc_licenses import ERCLicenseScraper
from datetime import datetime

def scrape_page_34_only():
    """Scrape only page 34 and save to separate file"""

    print("="*70)
    print("  ERC License Scraper - Page 34 Only")
    print("="*70)
    print("\nConfiguration:")
    print("  - Target: Page 34 only")
    print("  - Expected records: ~15")
    print("  - Output: Separate file (won't override merged files)")
    print()

    # Create scraper instance
    scraper = ERCLicenseScraper()

    # Create driver
    scraper.driver = scraper.create_driver()

    try:
        # Navigate to the listing page first
        print("[1] Loading listing page...")
        scraper.driver.get(scraper.base_url)
        import time
        time.sleep(5)

        # Scrape only page 34
        print("\n[2] Scraping page 34...")
        page_34_data = scraper.scrape_page(page_number=34, max_records=None)

        # Add to all_data
        scraper.all_data = page_34_data

        if scraper.all_data:
            # Save with specific filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_file = f"page_34_ONLY_{timestamp}.xlsx"
            csv_file = f"page_34_ONLY_{timestamp}.csv"

            print(f"\n[3] Saving {len(scraper.all_data)} records...")
            scraper.save_to_excel(excel_file)
            scraper.save_to_csv(csv_file)

            print("\n" + "="*70)
            print("  SUCCESS!")
            print("="*70)
            print(f"  Records extracted: {len(scraper.all_data)}")
            print(f"  Excel file: {excel_file}")
            print(f"  CSV file: {csv_file}")
            print("\n  These files are separate and won't override your merged data.")
            print("  You can manually merge them later.")
            print("="*70)
        else:
            print("\n[ERROR] No data extracted from page 34")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        print("\nClosing browser...")
        if scraper.driver:
            scraper.driver.quit()
        print("Done!")

if __name__ == '__main__':
    scrape_page_34_only()
