import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Try different URL variations
urls = [
    "http://app04.erc.or.th/elicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1",
    "http://app04.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1",
    "http://portal.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1",
    "https://portal.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1",
    "http://www.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1",
]

session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0'})

for url in urls:
    try:
        print(f"\nTrying: {url}")
        r = session.get(url, verify=False, timeout=10)
        print(f"  Status: {r.status_code}")

        if r.status_code == 200 and len(r.text) > 10000:
            print(f"  Length: {len(r.text)} - LOOKS GOOD!")
            r.encoding = 'utf-8'
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            title = soup.find('title')
            print(f"  Title: {title.get_text()[:80] if title else 'None'}")

            table = soup.find('table', {'id': 'ctl00_MasterContentPlaceHolder_RadGrid_ctl00'})
            if table:
                print(f"  ✓✓✓ MAIN TABLE FOUND! This is the correct URL!")
                print(f"\n  CORRECT URL: {url}")
                break
        else:
            print(f"  Length: {len(r.text)}")

    except Exception as e:
        print(f"  Error: {type(e).__name__}")
