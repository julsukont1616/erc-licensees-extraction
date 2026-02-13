import pandas as pd

df = pd.read_csv('erc_license_details_20260213_003615.csv', encoding='utf-8-sig')

print('='*70)
print('DATA EXTRACTION SUMMARY')
print('='*70)
print(f'Total records: {len(df)}')
print(f'Total columns: {len(df.columns)}')

print('\n' + '='*70)
print('BASIC INFO (First Record)')
print('='*70)
rec1 = df.iloc[0]
print(f'License No: {rec1["เลขทะเบียนใบอนุญาต"]}')
print(f'Licensee: {rec1["ชื่อผู้รับใบอนุญาต"]}')
print(f'Power Plant: {rec1["ชื่อสถานประกอบกิจการ"]}')
print(f'Capacity MW: {rec1["กำลังผลิต_MW"]}')
print(f'Address: {rec1["ที่อยู่"][:80]}...')
print(f'Email: {rec1["Email"]}')

print('\n' + '='*70)
print('CHECKING NESTED TABLE EXTRACTION')
print('='*70)

# Check for production plan columns
plan_cols = [c for c in df.columns if 'แผนการผลิต' in c]
print(f'\nProduction Plan columns: {len(plan_cols)}')
if plan_cols:
    print(f'  {plan_cols}')
    # Check if first record has plan data
    plan_data = {col: rec1[col] for col in plan_cols if pd.notna(rec1[col]) and rec1[col] != ''}
    print(f'  Non-empty plan fields in record 1: {len(plan_data)}')
    for k, v in list(plan_data.items())[:3]:
        print(f'    {k}: {v}')

# Check for production process columns
proc_cols = [c for c in df.columns if 'กระบวนการผลิต' in c]
print(f'\nProduction Process columns: {len(proc_cols)}')
if proc_cols:
    print(f'  Sample: {proc_cols[:3]}')
    proc_data = {col: rec1[col] for col in proc_cols if pd.notna(rec1[col]) and rec1[col] != ''}
    print(f'  Non-empty process fields in record 1: {len(proc_data)}')
else:
    print('  WARNING: No production process data found!')

# Check for machine columns
machine_cols = [c for c in df.columns if 'เครื่องจักร' in c]
print(f'\nMachine columns: {len(machine_cols)}')
if machine_cols:
    print(f'  Sample: {machine_cols[:5]}')
    machine_data = {col: rec1[col] for col in machine_cols if pd.notna(rec1[col]) and rec1[col] != ''}
    print(f'  Non-empty machine fields in record 1: {len(machine_data)}')
    for k, v in list(machine_data.items())[:5]:
        print(f'    {k}: {v}')

print('\n' + '='*70)
print('ALL RECORDS - NON-EMPTY FIELD COUNT')
print('='*70)
for idx, row in df.iterrows():
    non_empty = sum(1 for col in df.columns if pd.notna(row[col]) and row[col] != '')
    print(f'Record {idx+1}: {non_empty} non-empty fields')
