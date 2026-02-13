#!/usr/bin/env python3
"""
Clean up and organize the workspace folder
"""
import os
import shutil
from pathlib import Path

def cleanup_workspace():
    """Organize all files into proper folders"""

    base_dir = Path(".")

    # Create organization folders
    folders = {
        'archive': base_dir / 'archive',
        'logs': base_dir / 'logs',
        'output_files': base_dir / 'output_files',
        'scripts': base_dir / 'scripts',
        'docs': base_dir / 'docs'
    }

    print("Creating organization folders...")
    for name, folder in folders.items():
        folder.mkdir(exist_ok=True)
        print(f"  - {folder}")

    print("\n" + "="*70)
    print("Organizing files...")
    print("="*70)

    # Move batch output files (keep merged files in root for easy access)
    batch_files = list(base_dir.glob('batch_pages_*.xlsx')) + list(base_dir.glob('batch_pages_*.csv'))
    if batch_files:
        print(f"\nMoving {len(batch_files)} batch output files to archive/...")
        for f in batch_files:
            dest = folders['archive'] / f.name
            shutil.move(str(f), str(dest))
            print(f"  - {f.name}")

    # Move log files
    log_files = list(base_dir.glob('*.log')) + list(base_dir.glob('batch_*.log'))
    if log_files:
        print(f"\nMoving {len(log_files)} log files to logs/...")
        for f in log_files:
            if f.exists():  # Check if not already moved
                dest = folders['logs'] / f.name
                shutil.move(str(f), str(dest))
                print(f"  - {f.name}")

    # Move old/test scripts
    old_scripts = [
        'scrape_erc_licenses_concurrent.py',
        'scrape_erc_licenses_parallel.py',
        'scrape_erc_licenses_V0.5.py',
        'start_staggered_workers.py',
        'monitor_progress.py',
        'batch_scraper.py',
        'merge_excel_files.py'
    ]

    print(f"\nMoving scripts to scripts/...")
    for script in old_scripts:
        script_path = base_dir / script
        if script_path.exists():
            dest = folders['scripts'] / script
            shutil.move(str(script_path), str(dest))
            print(f"  - {script}")

    # Move documentation files
    doc_files = [
        'OVERNIGHT_SCRAPING_STATUS.md',
        'CONCURRENT_SCRAPING_GUIDE.md'
    ]

    print(f"\nMoving documentation to docs/...")
    for doc in doc_files:
        doc_path = base_dir / doc
        if doc_path.exists():
            dest = folders['docs'] / doc
            shutil.move(str(doc_path), str(dest))
            print(f"  - {doc}")

    # Create README for the organized workspace
    readme_content = """# ERC License Scraper - Organized Workspace

## 📁 Folder Structure

### Main Files (Root Directory)
- `scrape_erc_licenses.py` - Main production scraper
- `ERC_Licenses_MERGED_ALL_PAGES_*.xlsx` - Final merged dataset
- `ERC_Licenses_MERGED_ALL_PAGES_*.csv` - Final merged dataset (CSV)

### archive/
Batch output files from parallel scraping (4 workers)

### logs/
All scraping log files and progress monitoring logs

### scripts/
Helper scripts:
- `batch_scraper.py` - Batch scraping for page ranges
- `merge_excel_files.py` - Merge multiple Excel files
- `monitor_progress.py` - Progress monitoring
- Old/experimental scripts

### docs/
Documentation and status reports

## 📊 Dataset Summary

**Total Records:** 1,979 (out of ~1,995 expected)
**Missing:** Page 34 (15 records) - ChromeDriver crash issue
**Columns:** 632 (dynamic based on nested data)

## 🚀 Quick Start

To scrape more pages:
```bash
python scrape_erc_licenses.py
```

To scrape specific page ranges:
```bash
cd scripts
python batch_scraper.py START_PAGE END_PAGE
```
"""

    readme_path = base_dir / 'README_WORKSPACE.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"\n[OK] Created README_WORKSPACE.md")

    print("\n" + "="*70)
    print("CLEANUP COMPLETE!")
    print("="*70)
    print("\nWorkspace is now organized:")
    print("  [OK] Main scraper: scrape_erc_licenses.py")
    print("  [OK] Merged data: ERC_Licenses_MERGED_ALL_PAGES_*.xlsx")
    print("  [OK] Batch files: archive/")
    print("  [OK] Logs: logs/")
    print("  [OK] Scripts: scripts/")
    print("  [OK] Docs: docs/")
    print("\nYour workspace is clean and organized!\n")

if __name__ == '__main__':
    cleanup_workspace()
