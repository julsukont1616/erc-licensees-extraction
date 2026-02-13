"""
Monitor scraping progress and report completion
"""
import time
import os
from datetime import datetime

workers = [
    ("batch_1_33.log", 1, 33, 495),
    ("batch_34_66.log", 34, 66, 495),
    ("batch_67_99.log", 67, 99, 495),
    ("batch_100_133.log", 100, 133, 510)
]

print("\n" + "="*70)
print("  SCRAPING PROGRESS MONITOR")
print("="*70)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

completed = set()
last_progress = {}

while len(completed) < 4:
    time.sleep(60)  # Check every minute

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Progress Update:")
    print("-" * 70)

    for log_file, start_page, end_page, expected_records in workers:
        worker_num = workers.index((log_file, start_page, end_page, expected_records)) + 1

        if log_file in completed:
            print(f"Worker {worker_num} (Pages {start_page}-{end_page}): COMPLETE ✓")
            continue

        try:
            # Count records extracted
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                extracted_count = content.count('[OK]')

            # Check if completed
            if 'COMPLETE' in content or 'SUCCESS' in content:
                completed.add(log_file)
                print(f"Worker {worker_num} (Pages {start_page}-{end_page}): COMPLETE ✓ ({extracted_count} records)")
                continue

            # Calculate progress
            progress_pct = (extracted_count / expected_records * 100) if expected_records > 0 else 0
            current_page = start_page + (extracted_count // 15)

            # Show progress
            status = f"{extracted_count}/{expected_records} records ({progress_pct:.1f}%)"
            print(f"Worker {worker_num} (Pages {start_page}-{end_page}): Page ~{current_page} - {status}")

            # Check if stalled
            if log_file in last_progress and last_progress[log_file] == extracted_count:
                print(f"         WARNING: No progress in last minute!")

            last_progress[log_file] = extracted_count

        except FileNotFoundError:
            print(f"Worker {worker_num} (Pages {start_page}-{end_page}): NOT STARTED")
        except Exception as e:
            print(f"Worker {worker_num} (Pages {start_page}-{end_page}): ERROR - {e}")

    if len(completed) > 0:
        print(f"\nCompleted: {len(completed)}/4 workers")

print("\n" + "="*70)
print("  ALL WORKERS COMPLETE!")
print(f"  Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# List output files
print("\nOutput files:")
for f in os.listdir('.'):
    if f.startswith('batch_pages_') and (f.endswith('.xlsx') or f.endswith('.csv')):
        size = os.path.getsize(f) / 1024 / 1024  # MB
        print(f"  {f} ({size:.2f} MB)")

print("\nAll data extracted successfully!")
print("You can now merge the Excel files if needed.\n")
