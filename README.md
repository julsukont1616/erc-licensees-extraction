# ERC License Scraper

## Usage

```bash
python scrape_erc.py
```

## Configuration

Edit `scrape_erc.py` line 122:

```python
# Test mode (3 pages ~45 records)
df = scraper.scrape(max_pages=3)

# Full scrape (all pages ~1,994 records)
df = scraper.scrape(max_pages=None)
```

## Output Files

- `erc_licenses.csv` - UTF-8 with BOM (Excel-compatible)
- `erc_licenses.xlsx` - Excel format

## Columns

| Column | Description |
|--------|-------------|
| ลำดับ | Row number |
| ชื่อผู้รับใบอนุญาต | Licensee name |
| ชื่อสถานประกอบกิจการ | Plant/facility name |
| จังหวัด | Province |
| สำนักงานประจำเขต | Regional office |
| เลขทะเบียนใบอนุญาต | License number |
| วันที่ออกใบอนุญาต | Issue date |
| ชนิดเชื้อเพลิงหลัก | Primary fuel type |
| ชนิดเชื้อเพลิงเสริม | Secondary fuel type |
| กำลังผลิต_MW | Capacity in MW (numeric) |
| กำลังผลิต_kVA | Capacity in kVA (numeric) |
| วันที่_COD | Commercial operation date |

## Notes

- Empty cells are stored as `None` (null in CSV/Excel)
- Some records may have null capacity (not reported on website)
- Capacity columns are automatically converted to numeric
- Thai text encoding is handled automatically

## Troubleshooting

**SSL Error:**
The scraper uses `verify=False` to handle SSL certificate issues.

**No data extracted:**
Check if the website structure has changed.

**Column named '1' or weird columns:**
Fixed in latest version - only valid 13-cell rows are processed.
