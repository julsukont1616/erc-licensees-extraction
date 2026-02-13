import pandas as pd

df = pd.read_csv('erc_license_details_20260213_011253.csv', encoding='utf-8-sig')

print('='*70)
print('ENHANCED DATA VERIFICATION')
print('='*70)
print(f'Total records: {len(df)}')
print(f'Total columns: {len(df.columns)}')

# Check new fields
new_fields = [
    'ประเภทใบอนุญาต',
    'อายุใบอนุญาต_ปี',
    'เลขประจำตัวผู้เสียภาษี',
    'ที่อยู่สถานประกอบกิจการ',
    'GPS_N',
    'GPS_E',
    'เลขที่ใบคำขอ',
    'วันที่ยื่นคำขอ',
    'กำลังผลิตสูงสุด_kW'
]

print('\n' + '='*70)
print('NEW FIELDS VERIFICATION')
print('='*70)
for field in new_fields:
    if field in df.columns:
        non_empty = df[field].notna().sum()
        print(f'[OK] {field}: {non_empty}/{len(df)} records')
        if non_empty > 0:
            sample = df[field].dropna().iloc[0]
            print(f'  Sample: {str(sample)[:60]}...')
    else:
        print(f'[MISSING] {field}: NOT FOUND')

# Check nested tables
print('\n' + '='*70)
print('NESTED TABLES SUMMARY')
print('='*70)

plan_cols = [c for c in df.columns if 'แผนการผลิต' in c]
proc_cols = [c for c in df.columns if 'กระบวนการผลิต' in c]
machine_cols = [c for c in df.columns if 'เครื่องจักร' in c]

print(f'Production Plan fields: {len(plan_cols)}')
print(f'Production Process fields: {len(proc_cols)}')
print(f'Machine fields: {len(machine_cols)}')

# Data completeness
print('\n' + '='*70)
print('DATA COMPLETENESS BY PAGE')
print('='*70)

for page in [1, 2]:
    page_records = df[df['_page_number'] == page]
    avg_filled = 0
    for _, row in page_records.iterrows():
        non_empty = sum(1 for col in df.columns if pd.notna(row[col]) and str(row[col]).strip() != '')
        avg_filled += non_empty
    avg_filled = avg_filled / len(page_records) if len(page_records) > 0 else 0
    print(f'Page {page}: {len(page_records)} records, avg {avg_filled:.1f}/{len(df.columns)} fields filled ({avg_filled/len(df.columns)*100:.1f}%)')
