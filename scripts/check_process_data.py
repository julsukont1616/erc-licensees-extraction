import pandas as pd

# Read Excel to see all columns clearly
df = pd.read_excel('erc_license_details_20260213_004728.xlsx', sheet_name='License Details')

print('='*70)
print('CHECKING FOR PROCESS DATA')
print('='*70)
print(f'Total columns: {len(df.columns)}')

# List all columns
print('\nAll columns:')
for i, col in enumerate(df.columns, 1):
    print(f'{i}. {col}')

# Specifically check for process-related columns
print('\n' + '='*70)
proc_pattern = 'กระบวนการผลิต'
proc_cols = [c for c in df.columns if proc_pattern in c]
print(f'Process columns (with "{proc_pattern}"): {len(proc_cols)}')
if proc_cols:
    for col in proc_cols:
        print(f'  - {col}')
