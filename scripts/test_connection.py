import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "http://www.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1"

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

print("Fetching page...")
r = session.get(url, verify=False)
r.encoding = 'utf-8'

print(f"Status: {r.status_code}")
print(f"URL: {r.url}")
print(f"Content length: {len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')

# Check title
title = soup.find('title')
print(f"Title: {title.get_text() if title else 'Not found'}")

# Check for main table
table = soup.find('table', {'id': 'ctl00_MasterContentPlaceHolder_RadGrid_ctl00'})
print(f"\nMain table found: {table is not None}")

if not table:
    # Try to find any tables
    all_tables = soup.find_all('table')
    print(f"Total tables found: {len(all_tables)}")

    if all_tables:
        print("\nTable IDs:")
        for i, t in enumerate(all_tables[:10]):
            tid = t.get('id', 'no-id')
            tclass = t.get('class', 'no-class')
            print(f"  {i+1}. ID: {tid}, Class: {tclass}")

# Save HTML for inspection
with open('page_source.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
print("\nSaved HTML to page_source.html")
