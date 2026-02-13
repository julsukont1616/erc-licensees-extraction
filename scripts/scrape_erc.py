import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

class ERCScraper:
    def __init__(self):
        self.url = "http://www.erc.or.th/eLicense/Licenser/06_Licensing/504_ListLicensing_Columns_New.aspx?LicenseType=1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_page(self):
        r = self.session.get(self.url, verify=False)
        r.encoding = 'utf-8'
        return BeautifulSoup(r.text, 'html.parser')

    def get_viewstate(self, soup):
        fields = {}
        for name in ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION']:
            inp = soup.find('input', {'name': name})
            if inp:
                fields[name] = inp.get('value', '')
        return fields

    def clean_text(self, text):
        """Clean cell text - remove &nbsp;, extra spaces, return None if empty"""
        if not text:
            return None
        text = text.replace('\xa0', '').replace('&nbsp;', '').strip()
        return text if text else None

    def get_direct_cells(self, row):
        """Get only direct <td> children, not nested ones"""
        cells = []
        for child in row.children:
            if child.name == 'td':
                cells.append(child)
        return cells

    def extract_data(self, soup):
        data = []
        table = soup.find('table', {'id': 'ctl00_MasterContentPlaceHolder_RadGrid_ctl00'})
        if not table:
            print("Warning: Main table not found")
            return data

        tbody = table.find('tbody')
        if not tbody:
            print("Warning: tbody not found")
            return data

        # Only get data rows (rgRow and rgAltRow), skip footer rows
        rows = tbody.find_all('tr', class_=lambda x: x in ['rgRow', 'rgAltRow'], recursive=False)

        for row in rows:
            # Get only direct td children to avoid nested tables
            cells = self.get_direct_cells(row)

            # Must have exactly 13 cells for a valid data row
            if len(cells) != 13:
                print(f"  Skipping row with {len(cells)} cells (expected 13)")
                continue

            # Extract and clean each cell - get text from direct content only
            def get_cell_text(cell):
                # Get direct text content, excluding nested tables
                texts = []
                for content in cell.children:
                    if isinstance(content, str):
                        texts.append(content)
                    elif content.name and content.name not in ['table', 'div']:
                        texts.append(content.get_text())
                return self.clean_text(' '.join(texts))

            record = {
                'ลำดับ': get_cell_text(cells[0]),
                'ชื่อผู้รับใบอนุญาต': get_cell_text(cells[1]),
                'ชื่อสถานประกอบกิจการ': get_cell_text(cells[2]),
                'จังหวัด': get_cell_text(cells[3]),
                'สำนักงานประจำเขต': get_cell_text(cells[4]),
                'เลขทะเบียนใบอนุญาต': get_cell_text(cells[5]),
                'วันที่ออกใบอนุญาต': get_cell_text(cells[6]),
                'ชนิดเชื้อเพลิงหลัก': get_cell_text(cells[7]),
                'ชนิดเชื้อเพลิงเสริม': get_cell_text(cells[8]),
                'กำลังผลิต_MW': get_cell_text(cells[9]),
                'กำลังผลิต_kVA': get_cell_text(cells[10]),
                'วันที่_COD': get_cell_text(cells[11]),
            }

            # Only add if we have key data (licensee name)
            if record['ชื่อผู้รับใบอนุญาต']:
                data.append(record)

        return data

    def next_page(self, page_num, viewstate):
        data = {
            **viewstate,
            '__EVENTTARGET': 'ctl00$MasterContentPlaceHolder$RadGrid$ctl00$ctl03$ctl01$RadGridPagingTemplate2$btnNext',
            '__EVENTARGUMENT': '',
            'ctl00$MasterContentPlaceHolder$RadGrid$ctl00$ctl03$ctl01$RadGridPagingTemplate2$RadNumericTextBox1': str(page_num),
        }

        r = self.session.post(self.url, data=data, verify=False)
        r.encoding = 'utf-8'
        return BeautifulSoup(r.text, 'html.parser')

    def get_total_pages(self, soup):
        text = soup.find(text=re.compile(r'of\s+\d+'))
        if text:
            match = re.search(r'of\s+(\d+)', text)
            if match:
                return int(match.group(1))
        return 1

    def scrape(self, max_pages=None):
        print("Starting scrape...")

        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        soup = self.get_page()
        total = self.get_total_pages(soup)

        if max_pages:
            total = min(total, max_pages)

        print(f"Total pages to scrape: {total}")

        all_data = []
        page = 1

        while page <= total:
            print(f"Page {page}/{total}...", end=' ')

            data = self.extract_data(soup)
            all_data.extend(data)
            print(f"{len(data)} records")

            if page < total:
                time.sleep(1)
                viewstate = self.get_viewstate(soup)
                soup = self.next_page(page + 1, viewstate)

            page += 1

        print(f"\nTotal extracted: {len(all_data)} records")

        if not all_data:
            print("ERROR: No data extracted! Check website structure.")
            return pd.DataFrame()

        df = pd.DataFrame(all_data)

        # Convert capacity columns to numeric
        for col in ['กำลังผลิต_MW', 'กำลังผลิต_kVA']:
            if col in df.columns:
                # Remove commas and convert
                df[col] = df[col].str.replace(',', '', regex=False) if df[col].dtype == 'object' else df[col]
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

if __name__ == "__main__":
    scraper = ERCScraper()

    # Test with 3 pages first
    df = scraper.scrape(max_pages=3)

    if not df.empty:
        # Save
        df.to_csv('erc_licenses.csv', index=False, encoding='utf-8-sig')
        df.to_excel('erc_licenses.xlsx', index=False)

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"Total records: {len(df)}")
        print(f"\nColumns ({len(df.columns)}):")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        print("\n--- Sample Data ---")
        sample_cols = ['ชื่อผู้รับใบอนุญาต', 'จังหวัด', 'กำลังผลิต_MW']
        print(df[sample_cols].head(5).to_string(index=False))

        print("\n--- Data Quality ---")
        print(f"Records with MW data: {df['กำลังผลิต_MW'].notna().sum()}/{len(df)}")
        print(f"Records with kVA data: {df['กำลังผลิต_kVA'].notna().sum()}/{len(df)}")

        missing = df[df['กำลังผลิต_MW'].isna()]
        if not missing.empty:
            print(f"\nRecords with missing MW: {len(missing)}")
            print(missing[['ชื่อผู้รับใบอนุญาต', 'กำลังผลิต_MW', 'กำลังผลิต_kVA']].head(3).to_string(index=False))

        print("\n" + "="*80)
        print("Files saved:")
        print("  ✓ erc_licenses.csv")
        print("  ✓ erc_licenses.xlsx")
        print("="*80)
    else:
        print("\nERROR: Failed to extract data")
