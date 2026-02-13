"""
ERC Energy License Scraper - Improved Version
Clicks detail popups and extracts data from nested tables with proper handling
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup

class ERCLicenseScraper:
    def __init__(self):
        """Initialize scraper"""
        self.base_url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"
        self.all_data = []
        self.driver = None

    def create_driver(self):
        """Create a new WebDriver instance"""
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        return driver

    def clean_text(self, text):
        """Clean cell text - remove &nbsp;, extra spaces, return None if empty"""
        if not text:
            return None
        text = text.replace('\xa0', '').replace('&nbsp;', '').strip()
        # Collapse multiple spaces/newlines
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        return text if text else None

    def extract_popup_data(self, driver):
        """Extract all data from the detail pop-up window using BeautifulSoup"""
        try:
            # Wait for popup to appear
            time.sleep(4)

            # Try to switch to popup iframe or window
            context_switched = False

            # Method 1: Try direct RadWindowManager iframe by name (fastest)
            try:
                iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[name="RadWindowManager"]')
                driver.switch_to.frame(iframe)
                context_switched = True
                print(f"[iframe:RadWindowManager] ", end='', flush=True)
            except Exception:
                # Method 2: Try finding iframe by src containing detail page
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            iframe_src = iframe.get_attribute('src') or ''
                            iframe_name = iframe.get_attribute('name') or ''
                            if '644_Licensing' in iframe_src or 'LicensingDetail' in iframe_src:
                                driver.switch_to.frame(iframe)
                                context_switched = True
                                print(f"[iframe:{iframe_name or 'by_src'}] ", end='', flush=True)
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"[iframe_error:{str(e)[:20]}] ", end='', flush=True)

            # Method 2: Check if popup opened as a new window
            if not context_switched:
                try:
                    main_window = driver.current_window_handle
                    if len(driver.window_handles) > 1:
                        for handle in driver.window_handles:
                            if handle != main_window:
                                driver.switch_to.window(handle)
                                print(f"[window] ", end='', flush=True)
                                context_switched = True
                                break
                        time.sleep(1)
                except Exception as e:
                    print(f"[window_error:{str(e)[:20]}] ", end='', flush=True)

            if not context_switched:
                print(f"[WARNING:main_page] ", end='', flush=True)

            # Get page source
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            data = {}

            # Extract basic license information
            data['ประเภทใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'LicenseTypeName'))
            data['เลขทะเบียนใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'lblLicensesNo_1'))
            data['อายุใบอนุญาต_ปี'] = self.clean_text(self.get_span_text(soup, 'lblLicensing_Age_1'))
            data['วันที่ออกใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'lblLicensing_Start_DT_1'))
            data['วันที่หมดอายุ'] = self.clean_text(self.get_span_text(soup, 'Licensing_Exp_DT_1'))

            # Extract licensee information
            data['ชื่อผู้รับใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'LicenseeName'))
            data['สถานะภาพทางกฎหมาย'] = self.clean_text(self.get_span_text(soup, 'RowID_EL_M_LicenseeType'))
            data['เลขทะเบียนนิติบุคคล'] = self.clean_text(self.get_span_text(soup, 'TaxID'))
            data['เลขประจำตัวผู้เสียภาษี'] = self.clean_text(self.get_span_text(soup, 'TaxID2'))
            data['วันที่จดทะเบียน'] = self.clean_text(self.get_span_text(soup, 'Company_RegistDate'))
            data['ที่อยู่ผู้รับใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address'))

            # Extract contact info
            data['มือถือ'] = self.clean_text(self.get_span_text(soup, 'L_MobileNo'))
            data['โทรศัพท์'] = self.clean_text(self.get_span_text(soup, 'L_TelNo'))
            data['โทรสาร'] = self.clean_text(self.get_span_text(soup, 'L_FaxNo'))
            data['Website'] = self.clean_text(self.get_span_text(soup, 'L_Website'))
            data['Email'] = self.clean_text(self.get_span_text(soup, 'L_eMail'))

            # Extract power plant information
            data['ชื่อสถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'PowerPlantName'))
            data['ที่อยู่สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address_PowerPlant'))
            data['โทรศัพท์_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'PP_TelNo'))
            data['โทรสาร_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'PP_FaxNo'))
            data['GPS_N'] = self.clean_text(self.get_span_text(soup, 'GPS_N'))
            data['GPS_E'] = self.clean_text(self.get_span_text(soup, 'GPS_E'))

            # Extract application data
            data['เลขที่ใบคำขอ'] = self.clean_text(self.get_span_text(soup, 'RequestNo_1'))
            data['วันที่ยื่นคำขอ'] = self.clean_text(self.get_span_text(soup, 'RequestDate_1'))
            data['เลขที่การประชุม'] = self.clean_text(self.get_span_text(soup, 'MeetingNo_1'))
            data['วันที่ประชุม'] = self.clean_text(self.get_span_text(soup, 'MeetingDate_1'))
            data['วันที่เริ่มก่อสร้าง'] = self.clean_text(self.get_span_text(soup, 'ConstructDate_1'))
            data['มติที่ประชุม'] = self.clean_text(self.get_span_text(soup, 'MeetingDetail_1'))

            # Extract capacity
            data['กำลังผลิต_MW'] = self.clean_text(self.get_span_text(soup, 'GenPower_MW'))
            data['กำลังผลิต_kVA'] = self.clean_text(self.get_span_text(soup, 'GenPower_kVA'))
            data['กำลังผลิตสูงสุด_kW'] = self.clean_text(self.get_span_text(soup, 'PeakGen_KW'))

            # Extract SCOD and COD dates
            data['วันที่_SCOD'] = self.clean_text(self.get_span_text(soup, 'SCODDate'))
            data['วันที่_COD'] = self.clean_text(self.get_span_text(soup, 'CODDate'))

            # Extract production plan data from RadGridPowerProductionPlan
            production_plans = []
            plan_table = soup.find('table', {'id': lambda x: x and 'RadGridPowerProductionPlan' in x and 'ctl00' in x})
            if plan_table:
                # Find direct child tbody (not nested ones in headers)
                tbody = plan_table.find('tbody', recursive=False)
                if not tbody:
                    tbody = [child for child in plan_table.children if child.name == 'tbody']
                    tbody = tbody[0] if tbody else None
                if tbody:
                    rows = tbody.find_all('tr', id=True)  # Get all rows with id attribute
                    for row in rows:
                        plan = {
                            'วัตถุประสงค์': self.clean_text(self.get_span_text_from_element(row, 'lblPowerProductObjectiveName')),
                            'ระดับแรงดัน_kV': self.clean_text(self.get_span_text_from_element(row, 'lblkV')),
                            'กำลังผลิต_MW': self.clean_text(self.get_span_text_from_element(row, 'lblProductionCapacity_MW')),
                            'ปริมาณสูงสุด_MW': self.clean_text(self.get_span_text_from_element(row, 'lblMaximumVolume_MW')),
                            'เลขที่สัญญา': self.clean_text(self.get_span_text_from_element(row, 'lblContactNo')),
                            'วันที่มีผลบังคับ': self.clean_text(self.get_span_text_from_element(row, 'lblEffectiveDate')),
                            'อายุ': self.clean_text(self.get_span_text_from_element(row, 'lblAge')),
                            'SCOD': self.clean_text(self.get_span_text_from_element(row, 'lblSCOD'))
                        }
                        if plan['วัตถุประสงค์']:
                            production_plans.append(plan)

            data['แผนการผลิต'] = production_plans

            # Extract production process data from RadGridPowerProductPorcess
            processes = []
            process_table = soup.find('table', {'id': lambda x: x and 'RadGridPowerProductPorcess' in x and 'ctl00' in x})
            if process_table:
                # Find direct child tbody (not nested ones in headers)
                tbody = process_table.find('tbody', recursive=False)
                if not tbody:
                    tbody = [child for child in process_table.children if child.name == 'tbody']
                    tbody = tbody[0] if tbody else None
                if tbody:
                    # Get all tr elements that have an id attribute (data rows)
                    rows = tbody.find_all('tr', id=True)
                    for row in rows:
                        process = {
                            'หน่วยที่': self.clean_text(self.get_span_text_from_element(row, 'lblNo')),
                            'ประเภทเทคโนโลยี': self.clean_text(self.get_span_text_from_element(row, 'lblPowerGenTypeName')),
                            'ชื่อหน่วยผลิต': self.clean_text(self.get_span_text_from_element(row, 'lblProductUnit')),
                            'ชนิดการผลิต': self.clean_text(self.get_span_text_from_element(row, 'lblPowerProductionTypeName')),
                            'กำลังผลิตติดตั้ง_MW': self.clean_text(self.get_span_text_from_element(row, 'lblInstalledCapacity_MW')),
                            'กำลังผลิตติดตั้ง_kVA': self.clean_text(self.get_span_text_from_element(row, 'lblInstalledCapacity_kVA')),
                            'เชื้อเพลิงหลัก_ประเภท': self.clean_text(self.get_span_text_from_element(row, 'lblFuelsMainName')),
                            'เชื้อเพลิงหลัก_รายละเอียด': self.clean_text(self.get_span_text_from_element(row, 'lblMainFuelDescription')),
                            'เชื้อเพลิงเสริม_ประเภท': self.clean_text(self.get_span_text_from_element(row, 'lblFuelsAddName')),
                            'เชื้อเพลิงเสริม_รายละเอียด': self.clean_text(self.get_span_text_from_element(row, 'lblAddFuelDescription'))
                        }
                        if process.get('ประเภทเทคโนโลยี') or process.get('เชื้อเพลิงหลัก_ประเภท'):
                            processes.append(process)

            data['กระบวนการผลิต'] = processes

            # Extract machine/equipment data from RadGridMachine
            machines = []
            machine_table = soup.find('table', {'id': lambda x: x and 'RadGridMachine' in x and 'ctl00' in x})
            if machine_table:
                # Find direct child tbody (not nested ones in headers)
                tbody = machine_table.find('tbody', recursive=False)
                if not tbody:
                    tbody = [child for child in machine_table.children if child.name == 'tbody']
                    tbody = tbody[0] if tbody else None
                if tbody:
                    rows = tbody.find_all('tr', id=True)  # Get all rows with id attribute
                    for row in rows:
                        machine = {
                            'หน่วยการผลิตที่': self.clean_text(self.get_span_text_from_element(row, 'lblPowerGenUnitName')),
                            'รายการเครื่องจักร': self.clean_text(self.get_span_text_from_element(row, 'lblMachineName')),
                            'ประเภทเครื่องจักร': self.clean_text(self.get_span_text_from_element(row, 'lblMachineType')),
                            'ขนาดพิกัด_Rated_Capacity': self.clean_text(self.get_span_text_from_element(row, 'lblRateCapacity')),
                            'Power_Factor_Efficiency': self.clean_text(self.get_span_text_from_element(row, 'lblPowerFactor')),
                            'บริษัทและประเทศผู้ผลิต': self.clean_text(self.get_span_text_from_element(row, 'lblSourceOfMachine')),
                            'สภาพเครื่องจักร': self.clean_text(self.get_span_text_from_element(row, 'lblMachineStatusName'))
                        }
                        # Only add if has data
                        if machine.get('รายการเครื่องจักร') or machine.get('ประเภทเครื่องจักร'):
                            machines.append(machine)

            data['เครื่องจักร'] = machines

            return data

        except Exception as e:
            print(f"    Error extracting popup data: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_span_text(self, soup, id_contains):
        """Helper to get text from span by partial ID match"""
        span = soup.find('span', {'id': lambda x: x and id_contains in x})
        return span.get_text() if span else None

    def get_span_text_from_element(self, element, id_contains):
        """Helper to get text from span within an element"""
        span = element.find('span', {'id': lambda x: x and id_contains in x})
        return span.get_text() if span else None

    def get_total_pages(self, driver):
        """Get total number of pages from the pagination area"""
        try:
            # The page shows "of 133" text near the page input
            paging_div = driver.find_element(By.CSS_SELECTOR, "div.rgWrap.rgInfoPart")
            text = paging_div.text  # e.g. "Displaying page 1 of 133, items from 1 to 15 of 1994."
            import re
            match = re.search(r'of\s+(\d+),', text)
            if match:
                return int(match.group(1))
        except Exception:
            pass

        # Fallback: try to find the "of X" text near pagination
        try:
            page_source = driver.page_source
            import re
            match = re.search(r'of\s+(\d+)\s*,\s*items', page_source)
            if match:
                return int(match.group(1))
        except Exception:
            pass

        return 1

    def close_popup(self, driver):
        """Close the detail popup"""
        try:
            main_window = driver.current_window_handle

            # Check if we're in a popup window (not iframe)
            if len(driver.window_handles) > 1:
                # Close popup window and switch back
                driver.close()
                driver.switch_to.window(main_window)
                time.sleep(0.5)
                return

            # Otherwise, handle iframe popup
            # First switch back to default content
            driver.switch_to.default_content()
            time.sleep(0.5)

            # Try multiple methods to close the iframe popup
            try:
                # Method 1: Click the close button inside the iframe popup chrome
                close_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.rwCloseButton, .rwCloseButton"))
                )
                close_btn.click()
                time.sleep(0.5)
            except:
                try:
                    # Method 2: Try the ปิด button
                    close_btn = driver.find_element(By.XPATH, "//input[@value='ปิด']")
                    close_btn.click()
                    time.sleep(0.5)
                except:
                    try:
                        # Method 3: Use JavaScript to close RadWindow
                        driver.execute_script("""
                            var radWindow = window.radopen ? window.radopen(null, null) : null;
                            if (radWindow) radWindow.close();
                        """)
                        time.sleep(0.5)
                    except:
                        # Method 4: Press ESC key as last resort
                        from selenium.webdriver.common.keys import Keys
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)

            # Wait for popup to fully close
            time.sleep(1)

        except Exception as e:
            print(f" [close_error: {str(e)[:30]}]", end='', flush=True)
            # Try ESC as absolute fallback
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except:
                pass

    def scrape_page(self, page_number, max_records=None):
        """Scrape all detail popups from a single page"""
        print(f"\n{'='*70}")
        print(f"  Processing Page {page_number}")
        print(f"{'='*70}")

        page_data = []

        try:
            # Navigate to the page
            if page_number == 1:
                self.driver.get(self.base_url)
                time.sleep(3)
            else:
                # Enter page number and go - try better selector first
                try:
                    page_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='RadGridPagingTemplate2_RadNumericTextBox1']"))
                    )
                except:
                    # Fallback to generic selector
                    page_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.rgPageText, input[type='text'][title*='page']"))
                    )
                page_input.clear()
                page_input.send_keys(str(page_number))
                from selenium.webdriver.common.keys import Keys
                page_input.send_keys(Keys.ENTER)
                time.sleep(3)

            # Wait for table to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_MasterContentPlaceHolder_RadGrid_ctl00"))
            )
            time.sleep(2)

            # Find all detail buttons (paper icons)
            detail_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='image'][src*='icon_view']")
            total_buttons = len(detail_buttons)

            if max_records:
                total_buttons = min(total_buttons, max_records)

            print(f"  Found {total_buttons} records on page {page_number}")

            for idx in range(total_buttons):
                try:
                    # Re-find buttons to avoid stale element reference
                    detail_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='image'][src*='icon_view']")

                    if idx >= len(detail_buttons):
                        print(f"    Warning: Button index {idx} out of range")
                        break

                    button = detail_buttons[idx]

                    # Get row number for tracking
                    row_num = idx + 1 + (page_number - 1) * 15

                    print(f"    [{row_num}] Extracting details... ", end='', flush=True)

                    # Try to click button with retry logic
                    clicked = False
                    for attempt in range(3):
                        try:
                            # Scroll to button
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(0.5)

                            # Try JavaScript click if regular click fails
                            try:
                                button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", button)

                            clicked = True
                            break
                        except Exception as e:
                            if attempt < 2:
                                print(f"[retry{attempt+1}] ", end='', flush=True)
                                time.sleep(1)
                            else:
                                raise e

                    if not clicked:
                        raise Exception("Could not click button after 3 attempts")

                    time.sleep(3)

                    # Verify popup appeared
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[name="RadWindowManager"]'))
                        )
                    except TimeoutException:
                        print(f"[no_popup] ", end='', flush=True)
                        continue

                    # Extract popup data
                    detail_data = self.extract_popup_data(self.driver)
                    detail_data['_record_number'] = row_num
                    detail_data['_page_number'] = page_number
                    detail_data['_row_on_page'] = idx + 1

                    page_data.append(detail_data)
                    print(f"[OK]")

                    # Close popup
                    self.close_popup(self.driver)
                    time.sleep(1)

                except StaleElementReferenceException:
                    print(f"    Stale element at index {idx}, retrying...")
                    continue
                except Exception as e:
                    print(f"[ERROR] {e}")
                    try:
                        self.close_popup(self.driver)
                    except:
                        pass
                    continue

            print(f"  Completed page {page_number}: {len(page_data)} records extracted")

        except Exception as e:
            print(f"  Error processing page {page_number}: {e}")

        return page_data

    def scrape(self, max_pages=None, max_records_per_page=None):
        """Scrape all pages or limit to max_pages"""
        print(f"\n{'='*70}")
        print(f"  ERC Energy License Scraper")
        print(f"{'='*70}")

        self.driver = self.create_driver()

        try:
            # Navigate to first page
            self.driver.get(self.base_url)
            time.sleep(3)

            # Get total pages from website
            detected_pages = self.get_total_pages(self.driver)
            total_pages = min(max_pages, detected_pages) if max_pages else detected_pages

            print(f"\n[CONFIG] Scraping Configuration:")
            print(f"   Total pages detected: {detected_pages}")
            print(f"   Pages to scrape: {total_pages}")
            if max_records_per_page:
                print(f"   Max records per page: {max_records_per_page}")
            print()

            # Scrape each page
            for page_num in range(1, total_pages + 1):
                page_data = self.scrape_page(page_num, max_records=max_records_per_page)
                self.all_data.extend(page_data)

            print(f"\n[COMPLETE] Total records extracted: {len(self.all_data)}")

        finally:
            if self.driver:
                self.driver.quit()

    def save_to_excel(self, filename=None):
        """Save data to Excel with formatting"""
        if not self.all_data:
            print("No data to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erc_license_details_{timestamp}.xlsx"

        print(f"\n[SAVE] Saving data to Excel: {filename}")

        # Flatten nested data for Excel
        flattened_data = []
        for record in self.all_data:
            flat_record = {}

            # Copy basic fields
            for key, value in record.items():
                if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                    flat_record[key] = value

            # Flatten production plans
            plans = record.get('แผนการผลิต', [])
            if plans:
                for i, plan in enumerate(plans, 1):
                    for k, v in plan.items():
                        flat_record[f'แผนการผลิต_{i}_{k}'] = v

            # Flatten processes
            processes = record.get('กระบวนการผลิต', [])
            if processes:
                for i, proc in enumerate(processes, 1):
                    for k, v in proc.items():
                        flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

            # Flatten machines
            machines = record.get('เครื่องจักร', [])
            if machines:
                for i, machine in enumerate(machines, 1):
                    for k, v in machine.items():
                        flat_record[f'เครื่องจักร_{i}_{k}'] = v

            flattened_data.append(flat_record)

        # Convert to DataFrame
        df = pd.DataFrame(flattened_data)

        # Sort by record number
        if '_record_number' in df.columns:
            df = df.sort_values('_record_number')

        # Save to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='License Details', index=False)

            # Get worksheet
            worksheet = writer.sheets['License Details']

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        print(f"[OK] Data saved successfully!")
        print(f"   File: {filename}")
        print(f"   Records: {len(df)}")
        print(f"   Columns: {len(df.columns)}")

    def save_to_csv(self, filename=None):
        """Save data to CSV"""
        if not self.all_data:
            print("No data to save!")
            return

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"erc_license_details_{timestamp}.csv"

        # Flatten data same as Excel
        flattened_data = []
        for record in self.all_data:
            flat_record = {}
            for key, value in record.items():
                if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                    flat_record[key] = value

            plans = record.get('แผนการผลิต', [])
            if plans:
                for i, plan in enumerate(plans, 1):
                    for k, v in plan.items():
                        flat_record[f'แผนการผลิต_{i}_{k}'] = v

            processes = record.get('กระบวนการผลิต', [])
            if processes:
                for i, proc in enumerate(processes, 1):
                    for k, v in proc.items():
                        flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

            machines = record.get('เครื่องจักร', [])
            if machines:
                for i, machine in enumerate(machines, 1):
                    for k, v in machine.items():
                        flat_record[f'เครื่องจักร_{i}_{k}'] = v

            flattened_data.append(flat_record)

        df = pd.DataFrame(flattened_data)

        if '_record_number' in df.columns:
            df = df.sort_values('_record_number')

        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"[OK] CSV saved: {filename}")


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("  ERC Energy License Detail Scraper")
    print("  Extract from pop-up windows with improved table handling")
    print("="*70)

    # Configuration
    MAX_PAGES = None        # Number of pages to scrape (None for all 133 pages)
    MAX_RECORDS = None      # Max records per page (None for all ~15 per page)

    # For testing, use: MAX_PAGES = 5, MAX_RECORDS = 10
    # For full scrape (133 pages × 15 records = ~1,995 records), use: None, None

    # Create scraper
    scraper = ERCLicenseScraper()

    try:
        # Scrape data
        scraper.scrape(max_pages=MAX_PAGES, max_records_per_page=MAX_RECORDS)

        # Save to Excel
        scraper.save_to_excel()

        # Also save to CSV
        scraper.save_to_csv()

        print("\n" + "="*70)
        print("  [SUCCESS] Scraping completed successfully!")
        print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n[WARNING] Scraping interrupted by user")
        print(f"   Partial data collected: {len(scraper.all_data)} records")

        if scraper.all_data:
            save = input("\n   Save partial data? (y/n): ")
            if save.lower() == 'y':
                scraper.save_to_excel()
                scraper.save_to_csv()

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
