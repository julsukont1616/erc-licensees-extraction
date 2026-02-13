import pandas as pd

df = pd.read_excel('ERC_Licenses_PIVOTED_BY_MACHINES_20260213_090442.xlsx')

# Check the capacity column
capacity_col = 'เครื่องจักร_ขนาดพิกัด_Rated_Capacity'

print(f"Sample values from {capacity_col}:\n")
print(df[capacity_col].dropna().head(30).to_string())

print(f"\n\nUnique value patterns (first 50):")
unique_vals = df[capacity_col].dropna().unique()[:50]
for val in unique_vals:
    print(f"  '{val}'")
