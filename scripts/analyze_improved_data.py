import pandas as pd

df = pd.read_csv('erc_license_details_20260213_004728.csv', encoding='utf-8-sig')

print('='*70)
print('IMPROVED DATA EXTRACTION ANALYSIS')
print('='*70)
print(f'Total records: {len(df)}')
print(f'Total columns: {len(df.columns)}')

print('\n' + '='*70)
print('SAMPLE RECORD (First Record)')
print('='*70)
rec1 = df.iloc[0]
print(f'License No: {rec1["เลขทะเบียนใบอนุญาต"]}')
print(f'Licensee: {rec1["ชื่อผู้รับใบอนุญาต"]}')
print(f'Capacity MW: {rec1["กำลังผลิต_MW"]}')

print('\n' + '='*70)
print('CHECKING NESTED TABLES')
print('='*70)

# Production Plan
plan_cols = [c for c in df.columns if 'แผนการผลิต' in c]
print(f'\nProduction Plan columns: {len(plan_cols)}')

# Production Process
proc_cols = [c for c in df.columns if 'กระบวนการผลิต' in c]
print(f'Production Process columns: {len(proc_cols)}')
if proc_cols:
    print(f'  Sample columns: {proc_cols[:5]}')
    # Check which records have process data
    records_with_proc = 0
    for idx, row in df.iterrows():
        has_proc = any(pd.notna(row[col]) and row[col] != '' for col in proc_cols)
        if has_proc:
            records_with_proc += 1
    print(f'  Records with process data: {records_with_proc}/{len(df)}')

    # Show sample process data from first record
    if records_with_proc > 0:
        proc_data = {col: rec1[col] for col in proc_cols if pd.notna(rec1[col]) and rec1[col] != ''}
        print(f'\n  Sample process data from record 1:')
        for k, v in list(proc_data.items())[:5]:
            print(f'    {k}: {v}')

# Machine
machine_cols = [c for c in df.columns if 'เครื่องจักร' in c]
print(f'\nMachine columns: {len(machine_cols)}')
if machine_cols:
    print(f'  Sample columns: {machine_cols[:7]}')
    # Check which records have machine data
    records_with_machines = 0
    for idx, row in df.iterrows():
        has_machine = any(pd.notna(row[col]) and row[col] != '' for col in machine_cols)
        if has_machine:
            records_with_machines += 1
    print(f'  Records with machine data: {records_with_machines}/{len(df)}')

    # Show sample machine data from first record
    if records_with_machines > 0:
        machine_data = {col: rec1[col] for col in machine_cols if pd.notna(rec1[col]) and rec1[col] != ''}
        print(f'\n  Sample machine data from record 1:')
        for k, v in list(machine_data.items())[:7]:
            print(f'    {k}: {v}')

print('\n' + '='*70)
print('DATA COMPLETENESS')
print('='*70)
for idx in range(min(5, len(df))):
    row = df.iloc[idx]
    non_empty = sum(1 for col in df.columns if pd.notna(row[col]) and row[col] != '')
    licensee = row['ชื่อผู้รับใบอนุญาต'][:30] if pd.notna(row['ชื่อผู้รับใบอนุญาต']) else 'N/A'
    print(f'Record {idx+1} ({licensee}...): {non_empty}/{len(df.columns)} fields')
