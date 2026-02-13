import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try the correct eLicense URL
url = "http://app04.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1"

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

print(f"Testing URL: {url}")
print("Fetching page...")

r = session.get(url, verify=False)
r.encoding = 'utf-8'

print(f"Status: {r.status_code}")
print(f"Final URL: {r.url}")
print(f"Content length: {len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')

# Check title
title = soup.find('title')
print(f"Title: {title.get_text() if title else 'Not found'}")

# Check for main table
table = soup.find('table', {'id': 'ctl00_MasterContentPlaceHolder_RadGrid_ctl00'})
print(f"\nMain table: {'FOUND ✓' if table else 'NOT FOUND'}")

if table:
    # Count rows
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr', class_=lambda x: x in ['rgRow', 'rgAltRow'])
        print(f"Data rows: {len(rows)}")

        if rows:
            print("\nFirst row cells:")
            first_row = rows[0]
            cells = []
            for child in first_row.children:
                if child.name == 'td':
                    cells.append(child)

            print(f"Total cells: {len(cells)}")
            for i, cell in enumerate(cells[:5]):
                text = cell.get_text(strip=True)[:50]
                print(f"  Cell {i}: {text}")
