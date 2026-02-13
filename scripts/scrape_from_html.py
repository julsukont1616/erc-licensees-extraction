"""
Scrape ERC data from saved HTML file
Useful when the live site is not accessible
"""
import pandas as pd
from bs4 import BeautifulSoup


def clean_text(text):
    """Clean cell text"""
    if not text:
        return None
    text = text.replace('\xa0', '').replace('&nbsp;', '').strip()
    return text if text else None


def extract_from_html(html_file):
    """Extract data from saved HTML file"""

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Find main table
    table = soup.find('table', class_='rgMasterTable')
    if not table:
        print("ERROR: Table not found")
        print("Looking for alternative...")
        # Try by ID
        table = soup.find('table', {'id': lambda x: x and 'RadGrid' in x and 'ctl00' in x})

    if not table:
        print("ERROR: Could not find data table")
        return pd.DataFrame()

    print(f"✓ Table found: {table.get('id', 'no-id')}")

    # Find tbody
    tbody = table.find('tbody')
    if not tbody:
        print("ERROR: tbody not found")
        return pd.DataFrame()

    # Get data rows only
    rows = tbody.find_all('tr', class_=lambda x: x in ['rgRow', 'rgAltRow'])
    print(f"✓ Found {len(rows)} data rows")

    data = []

    for idx, row in enumerate(rows, 1):
        # Get direct td children only
        cells = [child for child in row.children if child.name == 'td']

        if len(cells) != 13:
            print(f"  Row {idx}: Skipped ({len(cells)} cells)")
            continue

        record = {
            'ลำดับ': clean_text(cells[0].get_text()),
            'ชื่อผู้รับใบอนุญาต': clean_text(cells[1].get_text()),
            'ชื่อสถานประกอบกิจการ': clean_text(cells[2].get_text()),
            'จังหวัด': clean_text(cells[3].get_text()),
            'สำนักงานประจำเขต': clean_text(cells[4].get_text()),
            'เลขทะเบียนใบอนุญาต': clean_text(cells[5].get_text()),
            'วันที่ออกใบอนุญาต': clean_text(cells[6].get_text()),
            'ชนิดเชื้อเพลิงหลัก': clean_text(cells[7].get_text()),
            'ชนิดเชื้อเพลิงเสริม': clean_text(cells[8].get_text()),
            'กำลังผลิต_MW': clean_text(cells[9].get_text()),
            'กำลังผลิต_kVA': clean_text(cells[10].get_text()),
            'วันที่_COD': clean_text(cells[11].get_text()),
        }

        if record['ชื่อผู้รับใบอนุญาต']:
            data.append(record)

    df = pd.DataFrame(data)

    # Convert numeric columns
    for col in ['กำลังผลิต_MW', 'กำลังผลิต_kVA']:
        if col in df.columns:
            df[col] = df[col].str.replace(',', '', regex=False) if df[col].dtype == 'object' else df[col]
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


if __name__ == "__main__":
    import sys

    # Check if HTML file is provided
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        print("Usage: python scrape_from_html.py <html_file>")
        print("\nExample:")
        print("  python scrape_from_html.py page.html")
        print("\nOr save the page HTML to 'page.html' and run without arguments")

        html_file = 'page.html'
        import os
        if not os.path.exists(html_file):
            print(f"\nERROR: {html_file} not found")
            print("\nTo use this scraper:")
            print("1. Save the ERC license page HTML to 'page.html'")
            print("2. Run: python scrape_from_html.py")
            sys.exit(1)

    print(f"Processing: {html_file}")
    print("="*80)

    df = extract_from_html(html_file)

    if not df.empty:
        # Save
        df.to_csv('erc_licenses.csv', index=False, encoding='utf-8-sig')
        df.to_excel('erc_licenses.xlsx', index=False)

        print(f"\n✓ Extracted {len(df)} records")
        print(f"\nColumns ({len(df.columns)}):")
        for col in df.columns:
            print(f"  - {col}")

        print("\n--- Sample Data ---")
        print(df[['ชื่อผู้รับใบอนุญาต', 'จังหวัด', 'กำลังผลิต_MW']].head().to_string(index=False))

        print("\n--- Data Quality ---")
        print(f"Records with MW: {df['กำลังผลิต_MW'].notna().sum()}/{len(df)}")
        print(f"Records with kVA: {df['กำลังผลิต_kVA'].notna().sum()}/{len(df)}")

        print("\n✓ Saved to:")
        print("  - erc_licenses.csv")
        print("  - erc_licenses.xlsx")
    else:
        print("\nERROR: No data extracted")
