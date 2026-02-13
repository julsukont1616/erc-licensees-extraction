"""
ERC License Batch Scraper
Easy way to scrape specific page ranges for manual parallelization
"""

from scrape_erc_licenses import ERCLicenseScraper
from datetime import datetime
import sys


def scrape_page_range(start_page, end_page, max_records_per_page=None):
    """
    Scrape a specific range of pages

    Args:
        start_page: First page to scrape (inclusive)
        end_page: Last page to scrape (inclusive)
        max_records_per_page: Max records per page (None for all ~15)

    Example:
        scrape_page_range(1, 30)     # Scrape pages 1-30
        scrape_page_range(31, 60)    # Scrape pages 31-60
    """
    print(f"\n{'='*70}")
    print(f"  BATCH SCRAPER: Pages {start_page}-{end_page}")
    print(f"{'='*70}\n")

    scraper = ERCLicenseScraper()
    scraper.driver = scraper.create_driver()

    try:
        total_pages = end_page - start_page + 1
        print(f"[CONFIG] Scraping {total_pages} pages ({start_page} to {end_page})")
        if max_records_per_page:
            print(f"         Max {max_records_per_page} records per page")
        print()

        # Scrape each page in the range
        for page_num in range(start_page, end_page + 1):
            print(f"\n[Progress] Page {page_num}/{end_page} ({page_num-start_page+1}/{total_pages} in this batch)")
            page_data = scraper.scrape_page(page_num, max_records=max_records_per_page)
            scraper.all_data.extend(page_data)

        print(f"\n[COMPLETE] Batch scraping finished!")
        print(f"   Pages scraped: {start_page}-{end_page}")
        print(f"   Total records: {len(scraper.all_data)}")

        # Save with descriptive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"batch_pages_{start_page}_to_{end_page}_{timestamp}"

        scraper.all_data_backup = scraper.all_data  # Backup before flattening
        scraper.save_to_excel(f"{base_name}.xlsx")
        scraper.all_data = scraper.all_data_backup
        scraper.save_to_csv(f"{base_name}.csv")

        print(f"\n{'='*70}")
        print(f"  [SUCCESS] Batch {start_page}-{end_page} completed!")
        print(f"{'='*70}\n")

    except KeyboardInterrupt:
        print(f"\n\n[WARNING] Interrupted!")
        print(f"   Partial data: {len(scraper.all_data)} records")
        if scraper.all_data and input("Save partial data? (y/n): ").lower() == 'y':
            scraper.save_to_excel(f"partial_pages_{start_page}_to_{end_page}.xlsx")
            scraper.save_to_csv(f"partial_pages_{start_page}_to_{end_page}.csv")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        if scraper.driver:
            scraper.driver.quit()


def main():
    """Main function with example batches"""
    print("\n" + "="*70)
    print("  ERC License Batch Scraper")
    print("  Scrape specific page ranges for manual parallelization")
    print("="*70)

    if len(sys.argv) >= 3:
        # Command line arguments: python batch_scraper.py <start> <end>
        start = int(sys.argv[1])
        end = int(sys.argv[2])
        max_records = int(sys.argv[3]) if len(sys.argv) > 3 else None

        scrape_page_range(start, end, max_records)

    else:
        # Interactive mode
        print("\n[INTERACTIVE MODE]")
        print("\nFull dataset is 133 pages (~1,995 records)")
        print("Recommended batch sizes:")
        print("  - Small:  20-30 pages (~300-450 records, 30-45 min)")
        print("  - Medium: 40-50 pages (~600-750 records, 1-1.5 hours)")
        print("  - Large:  60-70 pages (~900-1050 records, 1.5-2 hours)")

        print("\n[SUGGESTED BATCHES for Full Scrape]")
        print("  Batch 1: Pages 1-30")
        print("  Batch 2: Pages 31-60")
        print("  Batch 3: Pages 61-90")
        print("  Batch 4: Pages 91-120")
        print("  Batch 5: Pages 121-133")

        print("\nYou can run these in parallel in different terminals!")

        print("\n" + "-"*70)
        start = int(input("\nEnter start page (1-133): "))
        end = int(input("Enter end page (1-133): "))
        max_rec = input("Max records per page (Enter for all ~15): ").strip()
        max_records = int(max_rec) if max_rec else None

        scrape_page_range(start, end, max_records)


if __name__ == "__main__":
    main()
