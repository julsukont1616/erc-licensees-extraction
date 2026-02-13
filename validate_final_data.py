"""
Validate the final scraped data - check for detail rows and data quality
"""

import pandas as pd
import re

print("\n" + "="*70)
print("  Final Data Quality Validation")
print("="*70)

# Load the data
df = pd.read_excel('ERC_DISTRIBUTION_PARALLEL_V2_20260213_223654.xlsx')

print(f"\n[1/5] Basic Statistics")
print(f"      Total licenses: {len(df)}")
print(f"      Total columns: {len(df.columns)}")

# Check for bad electricity user rows
print(f"\n[2/5] Checking for detail rows in electricity users...")
bad_users = 0
total_users = 0

for idx, row in df.iterrows():
    # Check all electricity user columns
    user_cols = [c for c in df.columns if 'ผู้ใช้ไฟฟ้า_' in c and '_ชื่อ_เลขที่สัญญา' in c]

    for col in user_cols:
        contract = str(row[col])
        if contract and contract != 'nan':
            total_users += 1
            # Check if this looks like a detail row
            if re.match(r'^\d+\.\d+(\s+[\d,]+\.\d+)?$', contract):
                bad_users += 1
                if bad_users <= 5:  # Show first 5 examples
                    print(f"      [BAD] License {row['เลขทะเบียนใบอนุญาต']}: {contract}")

print(f"\n      Total users found: {total_users}")
print(f"      Bad detail rows: {bad_users}")

if bad_users == 0:
    print(f"      OK PASSED - No detail rows found!")
else:
    print(f"      FAIL FAILED - Found {bad_users} detail rows!")

# Sample validation
print(f"\n[3/5] Sample Data Quality Check")
print("      First 5 licenses with users:")
print("      " + "-"*66)

sample_cols = ['เลขทะเบียนใบอนุญาต', 'ชื่อผู้รับใบอนุญาต', 'ผู้ใช้ไฟฟ้า_1_ชื่อคู่สัญญาผู้ใช้ไฟฟ้า', 'ผู้ใช้ไฟฟ้า_2_ชื่อคู่สัญญาผู้ใช้ไฟฟ้า']
for i in range(min(5, len(df))):
    print(f"\n      License {i+1}: {df.iloc[i]['เลขทะเบียนใบอนุญาต']}")
    user1 = df.iloc[i].get('ผู้ใช้ไฟฟ้า_1_ชื่อคู่สัญญาผู้ใช้ไฟฟ้า', 'N/A')
    user2 = df.iloc[i].get('ผู้ใช้ไฟฟ้า_2_ชื่อคู่สัญญาผู้ใช้ไฟฟ้า', 'N/A')
    print(f"        User 1: {user1}")
    if str(user2) != 'nan' and str(user2) != 'N/A':
        print(f"        User 2: {user2}")

# Count total actual users
print(f"\n[4/5] User Statistics")
user_count = 0
for idx, row in df.iterrows():
    user_cols = [c for c in df.columns if 'ผู้ใช้ไฟฟ้า_' in c and '_ชื่อคู่สัญญาผู้ใช้ไฟฟ้า' in c]
    for col in user_cols:
        val = row[col]
        if pd.notna(val) and str(val) != '':
            user_count += 1

print(f"      Total electricity users: {user_count}")
print(f"      Average users per license: {user_count/len(df):.2f}")
print(f"      Expected (if fix worked): ~650-700 users")

# Final verdict
print(f"\n[5/5] Final Verdict")
print("      " + "="*66)
if bad_users == 0 and user_count < 800:
    print(f"      OK VALIDATION PASSED")
    print(f"      - No detail rows found")
    print(f"      - User count looks correct ({user_count} users)")
    print(f"      - Data is clean and ready to use!")
else:
    if bad_users > 0:
        print(f"      FAIL VALIDATION FAILED")
        print(f"      - Found {bad_users} detail rows")
    if user_count >= 800:
        print(f"      WARNING WARNING: User count seems high ({user_count})")
        print(f"      - May still have detail rows")

print("\n" + "="*70)
