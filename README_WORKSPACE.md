# ERC License Scraper - Organized Workspace

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
