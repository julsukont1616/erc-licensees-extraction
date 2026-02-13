#!/usr/bin/env python3
"""
Transform dataset to have one row per machine
Each machine gets its own row with all license info preserved
"""
import pandas as pd
import numpy as np
from datetime import datetime
import re

def pivot_by_machines():
    """Transform data so each row represents one machine"""

    print("="*70)
    print("  Pivoting Data by Machines")
    print("  One row per machine instead of one row per license")
    print("="*70)

    # Read the complete dataset
    input_file = "ERC_Licenses_COMPLETE_ALL_PAGES_20260213_085640.xlsx"
    print(f"\n[1] Reading input file...")
    print(f"  File: {input_file}")

    df = pd.read_excel(input_file)
    print(f"  - Records: {len(df):,}")
    print(f"  - Columns: {len(df.columns):,}")

    # Identify machine columns
    print(f"\n[2] Identifying machine columns...")
    machine_cols = [col for col in df.columns if 'เครื่องจักร_' in col]
    print(f"  - Found {len(machine_cols)} machine columns")

    # Extract machine numbers and field names
    machine_pattern = re.compile(r'เครื่องจักร_(\d+)_(.+)')
    machine_fields = {}
    max_machine_num = 0

    for col in machine_cols:
        match = machine_pattern.match(col)
        if match:
            machine_num = int(match.group(1))
            field_name = match.group(2)
            max_machine_num = max(max_machine_num, machine_num)

            if field_name not in machine_fields:
                machine_fields[field_name] = []
            machine_fields[field_name].append(machine_num)

    print(f"  - Maximum machines per record: {max_machine_num}")
    print(f"  - Machine fields: {list(machine_fields.keys())}")

    # Identify base columns (non-machine, non-process, non-plan columns)
    print(f"\n[3] Identifying base information columns...")
    base_cols = [col for col in df.columns
                 if not col.startswith('เครื่องจักร_')
                 and not col.startswith('กระบวนการผลิต_')
                 and not col.startswith('แผนการผลิต_')]

    print(f"  - Base columns: {len(base_cols)}")

    # Create expanded dataframe
    print(f"\n[4] Creating expanded dataset (one row per machine)...")
    expanded_rows = []
    total_machines = 0

    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"  - Processing record {idx+1}/{len(df)}...", end='\r')

        # Get base data for this record
        base_data = {col: row[col] for col in base_cols}

        # For each machine number, create a separate row
        for machine_num in range(1, max_machine_num + 1):
            # Check if this machine exists for this record
            machine_col_name = f'เครื่องจักร_{machine_num}_รายการเครื่องจักร'

            # Skip if machine doesn't exist or is empty
            if machine_col_name not in df.columns or pd.isna(row[machine_col_name]):
                continue

            # Create new row with base data
            new_row = base_data.copy()

            # Add machine number
            new_row['เครื่องจักร_ลำดับที่'] = machine_num

            # Add all machine fields
            for field_name in machine_fields.keys():
                machine_col = f'เครื่องจักร_{machine_num}_{field_name}'
                if machine_col in df.columns:
                    new_row[f'เครื่องจักร_{field_name}'] = row[machine_col]
                else:
                    new_row[f'เครื่องจักร_{field_name}'] = None

            expanded_rows.append(new_row)
            total_machines += 1

    print(f"\n  - Created {total_machines:,} machine rows from {len(df):,} license records")

    # Create new dataframe
    print(f"\n[5] Building final dataframe...")
    df_expanded = pd.DataFrame(expanded_rows)

    print(f"  - Total rows: {len(df_expanded):,}")
    print(f"  - Total columns: {len(df_expanded.columns):,}")

    # Reorder columns: base info first, then machine fields
    machine_only_cols = [col for col in df_expanded.columns if col.startswith('เครื่องจักร_')]
    other_cols = [col for col in df_expanded.columns if not col.startswith('เครื่องจักร_')]

    # Put machine sequence number first, then base info, then machine details
    if 'เครื่องจักร_ลำดับที่' in df_expanded.columns:
        ordered_cols = ['_record_number', '_page_number', 'เครื่องจักร_ลำดับที่'] + \
                      [col for col in other_cols if col not in ['_record_number', '_page_number']] + \
                      [col for col in machine_only_cols if col != 'เครื่องจักร_ลำดับที่']
        # Filter to only existing columns
        ordered_cols = [col for col in ordered_cols if col in df_expanded.columns]
        df_expanded = df_expanded[ordered_cols]

    # Save to Excel
    print(f"\n[6] Saving pivoted data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel = f"ERC_Licenses_PIVOTED_BY_MACHINES_{timestamp}.xlsx"
    output_csv = f"ERC_Licenses_PIVOTED_BY_MACHINES_{timestamp}.csv"

    df_expanded.to_excel(output_excel, index=False, engine='openpyxl')
    print(f"  [OK] Excel: {output_excel}")

    df_expanded.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  [OK] CSV: {output_csv}")

    # Summary statistics
    print(f"\n{'='*70}")
    print(f"  PIVOT COMPLETE!")
    print(f"{'='*70}")
    print(f"  Original dataset:")
    print(f"    - {len(df):,} rows (licenses)")
    print(f"    - {len(df.columns):,} columns")
    print(f"\n  Pivoted dataset:")
    print(f"    - {len(df_expanded):,} rows (machines)")
    print(f"    - {len(df_expanded.columns):,} columns")
    print(f"\n  Expansion factor: {len(df_expanded) / len(df):.2f}x")
    print(f"  Average machines per license: {len(df_expanded) / len(df):.2f}")
    print(f"\n  Output files:")
    print(f"    - {output_excel}")
    print(f"    - {output_csv}")
    print(f"{'='*70}\n")

    # Show sample
    print(f"Sample of first few rows:")
    display_cols = ['_record_number', 'เครื่องจักร_ลำดับที่', 'เครื่องจักร_หน่วยการผลิตที่',
                   'เครื่องจักร_รายการเครื่องจักร', 'เครื่องจักร_ประเภทเครื่องจักร']
    display_cols = [col for col in display_cols if col in df_expanded.columns]
    print(df_expanded[display_cols].head(10).to_string())
    print()

    return output_excel, output_csv

if __name__ == '__main__':
    pivot_by_machines()
