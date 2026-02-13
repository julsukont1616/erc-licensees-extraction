#!/usr/bin/env python3
"""
Merge the main dataset with page 34 data
Handles column differences automatically
"""
import pandas as pd
from datetime import datetime

def merge_with_page34():
    """Merge the complete dataset with page 34 recovery"""

    print("="*70)
    print("  Merging Complete Dataset with Page 34")
    print("="*70)

    # File paths
    main_file = "ERC_Licenses_MERGED_ALL_PAGES_20260213_084009.xlsx"
    page34_file = "page_34_ONLY_20260213_085356.xlsx"

    print(f"\n[1] Reading files...")
    print(f"  Main file: {main_file}")

    # Read main file
    df_main = pd.read_excel(main_file)
    print(f"  - Records: {len(df_main)}")
    print(f"  - Columns: {len(df_main.columns)}")

    print(f"\n  Page 34 file: {page34_file}")

    # Read page 34 file
    df_page34 = pd.read_excel(page34_file)
    print(f"  - Records: {len(df_page34)}")
    print(f"  - Columns: {len(df_page34.columns)}")

    # Combine dataframes (pandas will handle column differences automatically)
    print(f"\n[2] Merging dataframes...")
    print(f"  - Combining all columns from both files")
    print(f"  - Missing columns will be filled with NaN")

    # Concatenate (this automatically aligns columns and fills missing with NaN)
    df_combined = pd.concat([df_main, df_page34], ignore_index=True)

    print(f"  - Combined records: {len(df_combined)}")
    print(f"  - Combined columns: {len(df_combined.columns)}")

    # Sort by record number to get correct order
    print(f"\n[3] Sorting by record number...")
    if '_record_number' in df_combined.columns:
        df_combined = df_combined.sort_values('_record_number')
        print(f"  - Sorted by _record_number")
    else:
        print(f"  - Warning: No _record_number column found")

    # Reset index
    df_combined = df_combined.reset_index(drop=True)

    # Verify record numbers are sequential
    print(f"\n[4] Verifying data integrity...")
    if '_record_number' in df_combined.columns:
        record_nums = df_combined['_record_number'].dropna().astype(int).tolist()
        expected = list(range(1, len(df_combined) + 1))

        # Check for duplicates
        duplicates = df_combined['_record_number'].duplicated().sum()
        if duplicates > 0:
            print(f"  - Warning: {duplicates} duplicate record numbers found")
        else:
            print(f"  - No duplicate records found")

        # Check for gaps
        record_set = set(record_nums)
        expected_set = set(expected)
        missing = expected_set - record_set
        if missing:
            print(f"  - Warning: Missing record numbers: {sorted(missing)}")
        else:
            print(f"  - All record numbers present (1 to {len(df_combined)})")

    # Save merged file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel = f"ERC_Licenses_COMPLETE_ALL_PAGES_{timestamp}.xlsx"
    output_csv = f"ERC_Licenses_COMPLETE_ALL_PAGES_{timestamp}.csv"

    print(f"\n[5] Saving complete dataset...")

    # Save Excel
    df_combined.to_excel(output_excel, index=False, engine='openpyxl')
    print(f"  [OK] Excel: {output_excel}")

    # Save CSV
    df_combined.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  [OK] CSV: {output_csv}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  MERGE COMPLETE!")
    print(f"{'='*70}")
    print(f"  Total Records: {len(df_combined):,}")
    print(f"  Total Columns: {len(df_combined.columns):,}")
    print(f"  File Size: {df_combined.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB (in memory)")
    print(f"\n  Output Files:")
    print(f"  - {output_excel}")
    print(f"  - {output_csv}")
    print(f"{'='*70}")

    # Show sample of page 34 records
    if '_record_number' in df_combined.columns:
        print(f"\n  Page 34 records (496-510) verification:")
        page34_records = df_combined[
            (df_combined['_record_number'] >= 496) &
            (df_combined['_record_number'] <= 510)
        ]
        if len(page34_records) == 15:
            print(f"  [OK] All 15 page 34 records are present!")
            print(f"\n  Record numbers: {sorted(page34_records['_record_number'].tolist())}")
        else:
            print(f"  [WARNING] Expected 15 records, found {len(page34_records)}")

    print(f"\n{'='*70}\n")

    return output_excel, output_csv

if __name__ == '__main__':
    merge_with_page34()
