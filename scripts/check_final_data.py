import pandas as pd

df = pd.read_csv('erc_license_details_20260213_010551.csv', encoding='utf-8-sig')

print('='*70)
print('FINAL DATA CHECK')
print('='*70)
print(f'Total columns: {len(df.columns)}')

# Check for process columns
proc_cols = [c for c in df.columns if 'กระบวนการผลิต' in c]
print(f'\nProcess columns: {len(proc_cols)}')
if proc_cols:
    print('\nProcess column names:')
    for col in proc_cols[:15]:
        print(f'  - {col}')

    # Check sample data
    rec1 = df.iloc[0]
    proc_data = {col: rec1[col] for col in proc_cols if pd.notna(rec1[col]) and str(rec1[col]).strip() != ''}
    print(f'\nSample process data from record 1: {len(proc_data)} fields')
    for k, v in list(proc_data.items())[:10]:
        print(f'  {k}: {v}')
else:
    print('  WARNING: No process columns found!')

# Check machine columns
machine_cols = [c for c in df.columns if 'เครื่องจักร' in c]
print(f'\nMachine columns: {len(machine_cols)}')

# Overall data completeness
print('\n' + '='*70)
print('DATA COMPLETENESS PER RECORD')
print('='*70)
for idx in range(len(df)):
    row = df.iloc[idx]
    non_empty = sum(1 for col in df.columns if pd.notna(row[col]) and str(row[col]).strip() != '')
    licensee = row['ชื่อผู้รับใบอนุญาต'][:25] if pd.notna(row['ชื่อผู้รับใบอนุญาต']) else 'N/A'
    print(f'Record {idx+1} ({licensee}...): {non_empty}/{len(df.columns)} fields')
