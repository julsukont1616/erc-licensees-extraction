#!/usr/bin/env python3
"""
Split the เครื่องจักร_ขนาดพิกัด_Rated_Capacity column into:
- Numeric value
- Unit of measurement
"""
import pandas as pd
import re
from datetime import datetime

def split_capacity_column():
    """Extract number and unit from capacity column"""

    print("="*70)
    print("  Splitting Capacity Column into Number and Unit")
    print("="*70)

    # Read the pivoted file
    input_file = "ERC_Licenses_PIVOTED_BY_MACHINES_20260213_090442.xlsx"
    print(f"\n[1] Reading input file...")
    print(f"  File: {input_file}")

    df = pd.read_excel(input_file)
    print(f"  - Records: {len(df):,}")
    print(f"  - Columns: {len(df.columns):,}")

    capacity_col = 'เครื่องจักร_ขนาดพิกัด_Rated_Capacity'

    # Function to extract number and unit
    def extract_number_and_unit(value):
        """
        Extract the first number and its unit from capacity string
        Returns: (number, unit)
        """
        if pd.isna(value):
            return None, None

        value_str = str(value).strip()

        # Pattern to match: optional number with comma/decimal, optional space, optional unit
        # Units: W, kW, MW, GW, kVA, MVA, Wp, kWp, MWp, t/h, etc.
        pattern = r'^([0-9,]+\.?[0-9]*)\s*([A-Za-z/]+)?'

        match = re.match(pattern, value_str)

        if match:
            number_str = match.group(1)
            unit = match.group(2) if match.group(2) else None

            # Remove commas from number
            try:
                number = float(number_str.replace(',', ''))
            except:
                number = None

            return number, unit
        else:
            # If no match, return None for both
            return None, None

    print(f"\n[2] Extracting numbers and units from '{capacity_col}'...")

    # Apply extraction
    df[['เครื่องจักร_ขนาดพิกัด_ตัวเลข', 'เครื่องจักร_ขนาดพิกัด_หน่วย']] = df[capacity_col].apply(
        lambda x: pd.Series(extract_number_and_unit(x))
    )

    # Count results
    total_rows = len(df)
    extracted_numbers = df['เครื่องจักร_ขนาดพิกัด_ตัวเลข'].notna().sum()
    extracted_units = df['เครื่องจักร_ขนาดพิกัด_หน่วย'].notna().sum()

    print(f"  - Total rows: {total_rows:,}")
    print(f"  - Numbers extracted: {extracted_numbers:,} ({extracted_numbers/total_rows*100:.1f}%)")
    print(f"  - Units extracted: {extracted_units:,} ({extracted_units/total_rows*100:.1f}%)")

    # Show unit distribution
    print(f"\n[3] Unit distribution:")
    unit_counts = df['เครื่องจักร_ขนาดพิกัด_หน่วย'].value_counts()
    print(f"  Found {len(unit_counts)} unique units:")
    for unit, count in unit_counts.head(15).items():
        print(f"    {unit}: {count:,} ({count/total_rows*100:.1f}%)")
    if len(unit_counts) > 15:
        print(f"    ... and {len(unit_counts) - 15} more units")

    # Reorder columns: put new columns right after the original capacity column
    print(f"\n[4] Reordering columns...")
    cols = df.columns.tolist()
    capacity_idx = cols.index(capacity_col)

    # Insert new columns right after the capacity column
    new_order = (cols[:capacity_idx + 1] +
                ['เครื่องจักร_ขนาดพิกัด_ตัวเลข', 'เครื่องจักร_ขนาดพิกัด_หน่วย'] +
                [col for col in cols[capacity_idx + 1:] if col not in ['เครื่องจักร_ขนาดพิกัด_ตัวเลข', 'เครื่องจักร_ขนาดพิกัด_หน่วย']])

    df = df[new_order]

    # Save enhanced file
    print(f"\n[5] Saving enhanced dataset...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_excel = f"ERC_Licenses_MACHINES_WITH_CAPACITY_SPLIT_{timestamp}.xlsx"
    output_csv = f"ERC_Licenses_MACHINES_WITH_CAPACITY_SPLIT_{timestamp}.csv"

    df.to_excel(output_excel, index=False, engine='openpyxl')
    print(f"  [OK] Excel: {output_excel}")

    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"  [OK] CSV: {output_csv}")

    # Show examples
    print(f"\n{'='*70}")
    print(f"  EXTRACTION COMPLETE!")
    print(f"{'='*70}")
    print(f"\nSample of extracted data:")
    sample_cols = [capacity_col, 'เครื่องจักร_ขนาดพิกัด_ตัวเลข', 'เครื่องจักร_ขนาดพิกัด_หน่วย']
    sample = df[sample_cols].dropna(subset=['เครื่องจักร_ขนาดพิกัด_ตัวเลข']).head(20)
    print(sample.to_string())

    print(f"\n{'='*70}")
    print(f"  Output files:")
    print(f"    - {output_excel}")
    print(f"    - {output_csv}")
    print(f"\n  New columns added:")
    print(f"    - เครื่องจักร_ขนาดพิกัด_ตัวเลข (numeric capacity)")
    print(f"    - เครื่องจักร_ขนาดพิกัด_หน่วย (unit)")
    print(f"{'='*70}\n")

    return output_excel, output_csv

if __name__ == '__main__':
    split_capacity_column()
