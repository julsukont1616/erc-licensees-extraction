"""
Pivot ERC Distribution License Data by Electricity Users
Transforms flattened data: one row per electricity user instead of one row per license
"""

import pandas as pd
import re
from datetime import datetime


def pivot_by_electricity_users(input_file):
    """
    Pivot distribution license data by electricity users.
    Each electricity user becomes a separate row with license info preserved.
    """
    print(f"\n{'='*70}")
    print(f"  ERC Distribution License Data Pivot by Electricity Users")
    print(f"{'='*70}\n")

    # Read the data
    print(f"[1/5] Reading input file: {input_file}")
    df = pd.read_excel(input_file)
    print(f"      Input: {len(df)} licenses, {len(df.columns)} columns")

    # Identify base columns (not electricity users)
    print(f"\n[2/5] Identifying columns...")
    user_pattern = re.compile(r'^ผู้ใช้ไฟฟ้า_(\d+)_(.+)$')

    base_columns = []
    user_columns = {}  # {user_number: [column_names]}

    for col in df.columns:
        match = user_pattern.match(col)
        if match:
            user_num = int(match.group(1))
            field_name = match.group(2)
            if user_num not in user_columns:
                user_columns[user_num] = []
            user_columns[user_num].append(col)
        else:
            base_columns.append(col)

    print(f"      Base columns: {len(base_columns)}")
    print(f"      Max electricity users per license: {len(user_columns)}")

    # Create pivoted records
    print(f"\n[3/5] Pivoting data...")
    pivoted_records = []

    for idx, row in df.iterrows():
        license_data = {col: row[col] for col in base_columns}

        # Extract each electricity user
        for user_num in sorted(user_columns.keys()):
            # Get user data
            user_data = {}
            has_data = False

            for col in user_columns[user_num]:
                # Extract field name without prefix
                field_name = col.replace(f'ผู้ใช้ไฟฟ้า_{user_num}_', '')
                value = row[col]
                user_data[field_name] = value

                # Check if this user has any actual data
                if pd.notna(value) and value != '':
                    has_data = True

            # Only add if user has data
            if has_data:
                # Combine license data with user data
                combined = {**license_data, **user_data}
                combined['_user_number'] = user_num  # Track which user number this was
                pivoted_records.append(combined)

        if (idx + 1) % 100 == 0:
            print(f"      Processed {idx + 1}/{len(df)} licenses...", end='\r')

    print(f"      Processed {len(df)}/{len(df)} licenses... Done!")

    # Create pivoted DataFrame
    print(f"\n[4/5] Creating pivoted DataFrame...")
    pivoted_df = pd.DataFrame(pivoted_records)

    # Reorder columns - put electricity user columns first after basic license info
    priority_cols = [
        '_record_number',
        '_page_number',
        '_row_on_page',
        '_worker_id',
        'ประเภทใบอนุญาต',
        'เลขทะเบียนใบอนุญาต',
        'ชื่อผู้รับใบอนุญาต',
        # Electricity user fields
        'ชื่อ_เลขที่สัญญา',
        'ชื่อคู่สัญญาผู้ใช้ไฟฟ้า',
        'ประเภทผู้ใช้ไฟฟ้า',
        'ระดับแรงดัน_kV',
        'ปริมาณสูงสุด_MW',
        'ปริมาณสูงสุด_kVA',
        'ปริมาณจำหน่ายไฟฟ้า_kWh_ปี',
        'อัตราค่าบริการไฟฟ้า',
        'SCOD',
        '_user_number',
    ]

    # Get remaining columns
    remaining_cols = [col for col in pivoted_df.columns if col not in priority_cols]

    # Reorder
    final_cols = [col for col in priority_cols if col in pivoted_df.columns] + remaining_cols
    pivoted_df = pivoted_df[final_cols]

    print(f"      Output: {len(pivoted_df)} electricity users (rows)")
    print(f"      Columns: {len(pivoted_df.columns)}")

    # Save results
    print(f"\n[5/5] Saving pivoted data...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    excel_file = f"ERC_DISTRIBUTION_PIVOTED_BY_USERS_{timestamp}.xlsx"
    csv_file = f"ERC_DISTRIBUTION_PIVOTED_BY_USERS_{timestamp}.csv"

    # Save to Excel
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        pivoted_df.to_excel(writer, sheet_name='Electricity Users', index=False)

        worksheet = writer.sheets['Electricity Users']

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass

            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    # Save to CSV
    pivoted_df.to_csv(csv_file, index=False, encoding='utf-8-sig')

    print(f"      [OK] Excel: {excel_file}")
    print(f"      [OK] CSV: {csv_file}")

    # Print summary statistics
    print(f"\n{'='*70}")
    print(f"  Summary Statistics")
    print(f"{'='*70}")
    print(f"  Original licenses: {len(df)}")
    print(f"  Electricity users (rows): {len(pivoted_df)}")
    print(f"  Average users per license: {len(pivoted_df)/len(df):.2f}")

    # Show top electricity users by contract count
    if 'ชื่อคู่สัญญาผู้ใช้ไฟฟ้า' in pivoted_df.columns:
        print(f"\n  Top 10 Electricity Users by Number of Contracts:")
        top_users = pivoted_df['ชื่อคู่สัญญาผู้ใช้ไฟฟ้า'].value_counts().head(10)
        for i, (user, count) in enumerate(top_users.items(), 1):
            print(f"    {i:2d}. {user}: {count} contracts")

    print(f"\n{'='*70}")
    print(f"  [SUCCESS] Pivot complete!")
    print(f"{'='*70}\n")

    return pivoted_df


def main():
    """Main execution"""
    import sys
    import glob

    # Find the most recent distribution parallel file
    pattern = "ERC_DISTRIBUTION_PARALLEL_V2_*.xlsx"
    files = glob.glob(pattern)

    if not files:
        print(f"\n[ERROR] No files matching pattern: {pattern}")
        print(f"Please provide the input file as an argument:")
        print(f"  python pivot_by_electricity_users.py <input_file.xlsx>")
        sys.exit(1)

    # Use most recent file or command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Sort by modification time, get most recent
        files.sort(key=lambda x: pd.Timestamp(x.split('_')[-1].replace('.xlsx', '')), reverse=True)
        input_file = files[0]
        print(f"\n[INFO] Using most recent file: {input_file}")

    try:
        pivoted_df = pivot_by_electricity_users(input_file)

        # Optional: Show sample of pivoted data
        print(f"\nSample of pivoted data (first 3 rows):")
        print("="*70)
        sample_cols = ['เลขทะเบียนใบอนุญาต', 'ชื่อผู้รับใบอนุญาต', 'ชื่อคู่สัญญาผู้ใช้ไฟฟ้า',
                       'ประเภทผู้ใช้ไฟฟ้า', 'ปริมาณสูงสุด_MW']
        available_cols = [col for col in sample_cols if col in pivoted_df.columns]
        if available_cols:
            print(pivoted_df[available_cols].head(3).to_string(index=False))

    except Exception as e:
        print(f"\n[ERROR] Failed to pivot data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
