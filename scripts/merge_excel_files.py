#!/usr/bin/env python3
"""
Merge all batch Excel files into one master file
"""
import pandas as pd
import glob
from datetime import datetime

def merge_excel_files():
    """Merge all batch Excel files into one master file"""

    # Find all batch Excel files
    excel_files = sorted(glob.glob('batch_pages_*_to_*.xlsx'))

    if not excel_files:
        print("No Excel files found to merge!")
        return

    print(f"\nFound {len(excel_files)} files to merge:")
    for f in excel_files:
        print(f"  - {f}")

    # Read and combine all dataframes
    all_data = []
    total_records = 0

    for excel_file in excel_files:
        print(f"\nReading {excel_file}...")
        df = pd.read_excel(excel_file)
        records = len(df)
        total_records += records
        print(f"  Records: {records}")
        all_data.append(df)

    # Concatenate all dataframes
    print(f"\n{'='*70}")
    print("Merging all data...")
    merged_df = pd.concat(all_data, ignore_index=True)

    # Sort by page number if available (assuming there's a page column or we can infer)
    # The records should already be in order since we're concatenating in order

    print(f"Total records in merged file: {len(merged_df)}")
    print(f"Total columns: {len(merged_df.columns)}")

    # Save merged file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel = f"ERC_Licenses_MERGED_ALL_PAGES_{timestamp}.xlsx"
    output_csv = f"ERC_Licenses_MERGED_ALL_PAGES_{timestamp}.csv"

    print(f"\n{'='*70}")
    print("Saving merged files...")

    # Save as Excel
    merged_df.to_excel(output_excel, index=False, engine='openpyxl')
    print(f"[OK] Excel saved: {output_excel}")

    # Save as CSV
    merged_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"[OK] CSV saved: {output_csv}")

    print(f"\n{'='*70}")
    print("MERGE COMPLETE!")
    print(f"{'='*70}")
    print(f"Master file: {output_excel}")
    print(f"Total records: {len(merged_df):,}")
    print(f"Total columns: {len(merged_df.columns)}")
    print(f"\nNote: Page 34 data missing (15 records) due to ChromeDriver crash")
    print(f"{'='*70}\n")

    return output_excel, output_csv

if __name__ == '__main__':
    merge_excel_files()
