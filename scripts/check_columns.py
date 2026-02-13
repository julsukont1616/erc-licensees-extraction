import pandas as pd

df = pd.read_excel('ERC_Licenses_COMPLETE_ALL_PAGES_20260213_085640.xlsx')
print(f'Total columns: {len(df.columns)}')

# Column BC in Excel is column 55 (A=1, B=2, ..., BC=55)
print(f'\nColumn BC (position 54, 0-indexed):')
if len(df.columns) > 54:
    print(f'  {df.columns[54]}')

print(f'\nColumns around BC:')
for i in range(52, 58):
    if i < len(df.columns):
        print(f'  Column {i} (Excel: {chr(65 + i//26 - 1) if i >= 26 else ""}{chr(65 + i%26)}): {df.columns[i]}')

print(f'\nMachine-related columns:')
machine_cols = [col for col in df.columns if 'เครื่องจักร' in col]
print(f'  Found {len(machine_cols)} machine columns')
if machine_cols:
    print(f'\n  First 10:')
    for col in machine_cols[:10]:
        print(f'    - {col}')
