import requests
import pandas as pd
import json

def scrape_erc_rooftop_pv():
    """
    Scrape the ERC Rooftop PV System license table.
    All data is returned in a single POST request to the API endpoint.
    """

    url = "http://app04.erc.or.th/ElicenseRooftop/Data/PV/get_list_importdata.ashx"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "http://app04.erc.or.th/ElicenseRooftop/PV/Public/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    print("Fetching data from ERC Rooftop PV API...")
    response = requests.post(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    print(f"Total records fetched: {len(data)}")

    # Define the columns we want to extract (matching the website's table)
    records = []
    for i, row in enumerate(data, start=1):
        record = {
            "No": i,
            "ชื่อผู้ประกอบกิจการ (Licensee Name)": row.get("LicenseeName", ""),
            "ชื่อสถานประกอบกิจการ (Power Plant Name)": row.get("PowerPlantName", ""),
            "จังหวัด (Province)": row.get("Prov_P", ""),
            "อำเภอ (District)": row.get("District_P", ""),
            "ตำบล (Sub-district)": row.get("SDistrict_P", ""),
            "เขต (Region)": row.get("RBS_P", ""),
            "ประเภทอาคาร (Building Type)": row.get("BuildingType", ""),
            "kWp": row.get("kW", ""),
            "จำหน่ายเข้าระบบของ (Sell To)": row.get("SellTo", ""),
            "ระดับแรงดันไฟฟ้า (Voltage)": row.get("sellV", ""),
            "วันที่ลงนามสัญญา (Contract Date)": row.get("ContractDate", ""),
            "COD": row.get("COD", ""),
            "รง.4 (Factory License)": "✓" if row.get("FacDate") else "",
            "พค.2 (EC License)": "✓" if row.get("ECDate") else "",
            "อ.1 (AU License)": "✓" if row.get("AUDate") else "",
            "ยื่นแบบแจ้งฯ เมื่อ (Request Date)": row.get("txtReqDate", ""),
            "วันที่ออกหนังสือรับแจ้ง (Doc Date)": row.get("txtDocDate", ""),
            "ปรับปรุงล่าสุด เมื่อ (Last Update)": row.get("txtUpdateDate", ""),
        }
        records.append(record)

    # Create DataFrame
    df = pd.DataFrame(records)

    # Save to CSV (UTF-8 with BOM for Excel compatibility with Thai text)
    csv_filename = "erc_rooftop_pv_data.csv"
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} records to {csv_filename}")

    # Also save to Excel
    excel_filename = "erc_rooftop_pv_data.xlsx"
    try:
        df.to_excel(excel_filename, index=False, engine="openpyxl")
        print(f"Saved {len(df)} records to {excel_filename}")
    except PermissionError:
        print(f"Warning: Could not save {excel_filename} (file may be open in Excel)")
        print(f"CSV file saved successfully. Close Excel and run again to save Excel version.")

    # Print first few rows as preview
    print("\n--- Preview (first 5 rows) ---")
    try:
        print(df.head().to_string())
    except UnicodeEncodeError:
        print("(Preview skipped due to console encoding limitations)")
        print(f"Data successfully saved. Open {csv_filename} or {excel_filename} to view.")

    return df


if __name__ == "__main__":
    df = scrape_erc_rooftop_pv()