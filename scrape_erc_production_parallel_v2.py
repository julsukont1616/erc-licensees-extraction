"""
ERC Production License Scraper - PARALLEL V2 with Staggered Init
Improved parallel scraping with sequential driver initialization to prevent race conditions
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException
import pandas as pd
import time
from datetime import datetime
from bs4 import BeautifulSoup
from multiprocessing import Pool, Manager, Queue
import queue
import os


class ERCLicenseScraper:

    def __init__(self, worker_id=0):
        """Initialize scraper with worker ID for debugging"""
        self.worker_id = worker_id
        self.base_url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"
        self.all_data = []
        self.driver = None

    def create_driver(self):
        """Create a new WebDriver instance with retry logic"""
        for attempt in range(3):
            try:
                options = webdriver.ChromeOptions()
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument(f'--user-data-dir=C:\\temp\\chrome_profile_{self.worker_id}_{os.getpid()}')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)

                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(30)

                # Important: Wait after driver creation before navigation
                time.sleep(2)

                return driver
            except Exception as e:
                print(f"\n[Worker {self.worker_id}] Driver creation attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    time.sleep(3)
                else:
                    raise
        return None

    def navigate_to_url(self, driver, max_retries=3):
        """Navigate to base URL with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"[Worker {self.worker_id}] Navigating to website (attempt {attempt+1})... ", end='', flush=True)
                driver.get(self.base_url)
                time.sleep(3)

                # Verify we actually loaded the page
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "ctl00_MasterContentPlaceHolder_RadGrid_ctl00"))
                    )
                    print("OK")
                    return True
                except TimeoutException:
                    print("TIMEOUT - page didn't load")
                    if attempt < max_retries - 1:
                        time.sleep(5)
                        continue
                    return False

            except WebDriverException as e:
                print(f"FAILED ({str(e)[:50]})")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    return False
        return False

    def clean_text(self, text):
        """Clean cell text - remove &nbsp;, extra spaces, return None if empty"""
        if not text:
            return None
        text = text.replace('\xa0', '').replace('&nbsp;', '').strip()
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        return text if text else None

    def extract_popup_data(self, driver):
        """Extract all data from the detail pop-up window using BeautifulSoup"""
        try:
            time.sleep(4)

            context_switched = False

            # Try to switch to popup iframe or window
            try:
                iframe = driver.find_element(By.CSS_SELECTOR, 'iframe[name="RadWindowManager"]')
                driver.switch_to.frame(iframe)
                context_switched = True
                print(f"[iframe] ", end='', flush=True)
            except Exception:
                try:
                    iframes = driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            iframe_src = iframe.get_attribute('src') or ''
                            if '644_Licensing' in iframe_src or 'LicensingDetail' in iframe_src:
                                driver.switch_to.frame(iframe)
                                context_switched = True
                                print(f"[iframe:src] ", end='', flush=True)
                                break
                        except:
                            continue
                except:
                    pass

            if not context_switched:
                try:
                    main_window = driver.current_window_handle
                    if len(driver.window_handles) > 1:
                        for handle in driver.window_handles:
                            if handle != main_window:
                                driver.switch_to.window(handle)
                                context_switched = True
                                print(f"[window] ", end='', flush=True)
                                break
                        time.sleep(1)
                except:
                    pass

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            data = {}

            # Extract all fields (same as before)
            data['ประเภทใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'LicenseTypeName'))
            data['เลขทะเบียนใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'lblLicensesNo_1'))
            data['อายุใบอนุญาต_ปี'] = self.clean_text(self.get_span_text(soup, 'lblLicensing_Age_1'))
            data['วันที่ออกใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'lblLicensing_Start_DT_1'))
            data['วันที่หมดอายุ'] = self.clean_text(self.get_span_text(soup, 'Licensing_Exp_DT_1'))

            data['ชื่อผู้รับใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'LicenseeName'))
            data['สถานะภาพทางกฎหมาย'] = self.clean_text(self.get_span_text(soup, 'RowID_EL_M_LicenseeType'))
            data['เลขทะเบียนนิติบุคคล'] = self.clean_text(self.get_span_text(soup, 'TaxID'))
            data['เลขประจำตัวผู้เสียภาษี'] = self.clean_text(self.get_span_text(soup, 'TaxID2'))
            data['วันที่จดทะเบียน'] = self.clean_text(self.get_span_text(soup, 'Company_RegistDate'))
            data['ที่อยู่ผู้รับใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address'))

            data['มือถือ'] = self.clean_text(self.get_span_text(soup, 'L_MobileNo'))
            data['โทรศัพท์'] = self.clean_text(self.get_span_text(soup, 'L_TelNo'))
            data['โทรสาร'] = self.clean_text(self.get_span_text(soup, 'L_FaxNo'))
            data['Website'] = self.clean_text(self.get_span_text(soup, 'L_Website'))
            data['Email'] = self.clean_text(self.get_span_text(soup, 'L_eMail'))
            data['หมายเหตุ_ผู้รับใบอนุญาต'] = self.clean_text(self.get_span_text(soup, 'L_Remark'))

            data['ที่อยู่_ภพ20'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address_PowerPlant2'))
            data['มือถือ_ภพ20'] = self.clean_text(self.get_span_text(soup, 'PP_MobileNo'))
            data['โทรศัพท์_ภพ20'] = self.clean_text(self.get_span_text(soup, 'PP_TelNo'))
            data['โทรสาร_ภพ20'] = self.clean_text(self.get_span_text(soup, 'PP_FaxNo'))
            data['Email_ภพ20'] = self.clean_text(self.get_span_text(soup, 'PP_eMail'))
            data['หมายเหตุ_ภพ20'] = self.clean_text(self.get_span_text(soup, 'PP_Remark'))

            data['ผู้รับมอบอำนาจ1_ชื่อ'] = self.clean_text(self.get_span_text(soup, 'C1_Name'))
            data['ผู้รับมอบอำนาจ1_อาชีพ'] = self.clean_text(self.get_span_text(soup, 'C1_Position'))
            data['ผู้รับมอบอำนาจ1_ที่อยู่'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address_Contarct1'))
            data['ผู้รับมอบอำนาจ1_มือถือ'] = self.clean_text(self.get_span_text(soup, 'C1_MobileNo'))
            data['ผู้รับมอบอำนาจ1_โทรศัพท์'] = self.clean_text(self.get_span_text(soup, 'C1_TelNo'))
            data['ผู้รับมอบอำนาจ1_โทรสาร'] = self.clean_text(self.get_span_text(soup, 'C1_FaxNo'))
            data['ผู้รับมอบอำนาจ1_Email'] = self.clean_text(self.get_span_text(soup, 'C1_eMail'))
            data['ผู้รับมอบอำนาจ1_หมายเหตุ'] = self.clean_text(self.get_span_text(soup, 'C1_Remark'))

            data['ผู้รับมอบอำนาจ2_ชื่อ'] = self.clean_text(self.get_span_text(soup, 'C2_Name'))
            data['ผู้รับมอบอำนาจ2_อาชีพ'] = self.clean_text(self.get_span_text(soup, 'C2_Position'))
            data['ผู้รับมอบอำนาจ2_ที่อยู่'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address_Contarct2'))
            data['ผู้รับมอบอำนาจ2_มือถือ'] = self.clean_text(self.get_span_text(soup, 'C2_MobileNo'))
            data['ผู้รับมอบอำนาจ2_โทรศัพท์'] = self.clean_text(self.get_span_text(soup, 'C2_TelNo'))
            data['ผู้รับมอบอำนาจ2_โทรสาร'] = self.clean_text(self.get_span_text(soup, 'C2_FaxNo'))
            data['ผู้รับมอบอำนาจ2_Email'] = self.clean_text(self.get_span_text(soup, 'C2_eMail'))
            data['ผู้รับมอบอำนาจ2_หมายเหตุ'] = self.clean_text(self.get_span_text(soup, 'C2_Remark'))

            data['ชื่อสถานประกอบกิจการไฟฟ้า'] = self.clean_text(self.get_span_text(soup, 'PowerPlantName'))
            data['ที่อยู่สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'Licensee_Address_PowerPlant'))
            data['GPS_N'] = self.clean_text(self.get_span_text(soup, 'GPS_N'))
            data['GPS_E'] = self.clean_text(self.get_span_text(soup, 'GPS_E'))
            data['มือถือ_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'P_MobileNo'))
            data['โทรศัพท์_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'P_TelNo'))
            data['โทรสาร_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'P_FaxNo'))
            data['Email_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'P_eMail'))
            data['หมายเหตุ_สถานประกอบกิจการ'] = self.clean_text(self.get_span_text(soup, 'P_Remark'))

            # Application data (3 sets)
            for i in range(1, 4):
                data[f'เลขที่ใบคำขอ_{i}'] = self.clean_text(self.get_span_text(soup, f'RequestNo_{i}'))
                data[f'วันที่ยื่นคำขอ_{i}'] = self.clean_text(self.get_span_text(soup, f'RequestDate_{i}'))
                data[f'เลขที่การประชุม_{i}'] = self.clean_text(self.get_span_text(soup, f'MeetingNo_{i}'))
                data[f'วันที่ประชุม_{i}'] = self.clean_text(self.get_span_text(soup, f'MeetingDate_{i}'))
                data[f'วันที่เริ่มก่อสร้าง_{i}'] = self.clean_text(self.get_span_text(soup, f'ConstructDate_{i}'))
                data[f'อายุใบอนุญาต_คำขอ_{i}'] = self.clean_text(self.get_span_text(soup, f'LicenseAge_{i}'))
                data[f'มติที่ประชุม_{i}'] = self.clean_text(self.get_span_text(soup, f'MeetingDetail_{i}'))
                data[f'มติเฉพาะ_{i}'] = self.clean_text(self.get_span_text(soup, f'MeetingDetailSpecific_{i}'))

            data['วันที่_SCOD'] = self.clean_text(self.get_span_text(soup, 'SCODDate'))
            data['วันที่_COD'] = self.clean_text(self.get_span_text(soup, 'CODDate'))
            data['กำลังผลิต_MW'] = self.clean_text(self.get_span_text(soup, 'GenPower_MW'))
            data['กำลังผลิต_kVA'] = self.clean_text(self.get_span_text(soup, 'GenPower_kVA'))
            data['กำลังผลิตสูงสุด_kW'] = self.clean_text(self.get_span_text(soup, 'PeakGen_KW'))
            data['ปริมาณจำหน่ายปลีก_kWh'] = self.clean_text(self.get_span_text(soup, 'RetailSupply_KWh'))

            # Extract nested tables (Production licenses don't have electricity users or operating costs)
            data['แผนการผลิต'] = self.extract_production_plans(soup)
            data['กระบวนการผลิต'] = self.extract_processes(soup)
            data['เครื่องจักร'] = self.extract_machines(soup)

            return data

        except Exception as e:
            print(f"[ERROR: {str(e)[:30]}] ", end='', flush=True)
            return {}

    def extract_production_plans(self, soup):
        """Extract production plans table"""
        plans = []
        plan_table = soup.find('table', {'id': lambda x: x and 'RadGridPowerProductionPlan' in x})
        if plan_table:
            tbody = plan_table.find('tbody', recursive=False)
            if tbody:
                rows = tbody.find_all('tr', id=True)
                for row in rows:
                    plan = {
                        'วัตถุประสงค์': self.clean_text(self.get_span_text_from_element(row, 'lblPowerProductObjectiveName')),
                        'ระดับแรงดัน_kV': self.clean_text(self.get_span_text_from_element(row, 'lblkV')),
                        'กำลังผลิต_MW': self.clean_text(self.get_span_text_from_element(row, 'lblProductionCapacity_MW')),
                        'ปริมาณสูงสุด_MW': self.clean_text(self.get_span_text_from_element(row, 'lblMaximumVolume_MW')),
                        'เลขที่สัญญา': self.clean_text(self.get_span_text_from_element(row, 'lblContactNo')),
                        'วันที่มีผลบังคับ': self.clean_text(self.get_span_text_from_element(row, 'lblEffectiveDate')),
                        'อายุ': self.clean_text(self.get_span_text_from_element(row, 'lblAge')),
                        'ขอรับ_Adder': self.clean_text(self.get_span_text_from_element(row, 'lblRequestAdder')),
                        'SCOD': self.clean_text(self.get_span_text_from_element(row, 'lblSCOD'))
                    }
                    if plan['วัตถุประสงค์']:
                        plans.append(plan)
        return plans

    def extract_processes(self, soup):
        """Extract production processes table"""
        processes = []
        process_table = soup.find('table', {'id': lambda x: x and 'RadGridPowerProductPorcess' in x})
        if process_table:
            tbody = process_table.find('tbody', recursive=False)
            if tbody:
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
        return processes

    def extract_machines(self, soup):
        """Extract machines table"""
        machines = []
        machine_table = soup.find('table', {'id': lambda x: x and 'RadGridMachine' in x})
        if machine_table:
            tbody = machine_table.find('tbody', recursive=False)
            if tbody:
                rows = tbody.find_all('tr', id=True)
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
                    if machine.get('รายการเครื่องจักร') or machine.get('ประเภทเครื่องจักร'):
                        machines.append(machine)
        return machines


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
            paging_div = driver.find_element(By.CSS_SELECTOR, "div.rgWrap.rgInfoPart")
            text = paging_div.text
            import re
            match = re.search(r'of\s+(\d+),', text)
            if match:
                return int(match.group(1))
        except:
            pass
        try:
            page_source = driver.page_source
            import re
            match = re.search(r'of\s+(\d+)\s*,\s*items', page_source)
            if match:
                return int(match.group(1))
        except:
            pass
        return 1

    def close_popup(self, driver):
        """Close the detail popup"""
        try:
            main_window = driver.current_window_handle
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(main_window)
                time.sleep(0.5)
                return

            driver.switch_to.default_content()
            time.sleep(0.5)

            try:
                close_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.rwCloseButton, .rwCloseButton"))
                )
                close_btn.click()
                time.sleep(0.5)
            except:
                try:
                    close_btn = driver.find_element(By.XPATH, "//input[@value='ปิด']")
                    close_btn.click()
                    time.sleep(0.5)
                except:
                    try:
                        driver.execute_script("""
                            var radWindow = window.radopen ? window.radopen(null, null) : null;
                            if (radWindow) radWindow.close();
                        """)
                        time.sleep(0.5)
                    except:
                        from selenium.webdriver.common.keys import Keys
                        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)

            time.sleep(1)
        except:
            try:
                from selenium.webdriver.common.keys import Keys
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                time.sleep(1)
            except:
                pass

    def scrape_page(self, page_number):
        """Scrape all detail popups from a single page"""
        print(f"\n[Worker {self.worker_id}] Page {page_number}")
        print(f"{'='*60}")

        page_data = []

        try:
            # Navigate to page
            if page_number == 1:
                if not self.navigate_to_url(self.driver):
                    print(f"[Worker {self.worker_id}] Failed to navigate to page 1")
                    return []
            else:
                try:
                    page_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[id*='RadGridPagingTemplate2_RadNumericTextBox1']"))
                    )
                except:
                    page_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input.rgPageText, input[type='text'][title*='page']"))
                    )
                page_input.clear()
                page_input.send_keys(str(page_number))
                from selenium.webdriver.common.keys import Keys
                page_input.send_keys(Keys.ENTER)
                time.sleep(3)

            # Wait for table
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ctl00_MasterContentPlaceHolder_RadGrid_ctl00"))
            )
            time.sleep(2)

            # Find detail buttons
            detail_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='image'][src*='icon_view']")
            total_buttons = len(detail_buttons)

            print(f"[Worker {self.worker_id}] Found {total_buttons} records on page {page_number}")

            for idx in range(total_buttons):
                try:
                    detail_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[type='image'][src*='icon_view']")

                    if idx >= len(detail_buttons):
                        break

                    button = detail_buttons[idx]
                    row_num = idx + 1 + (page_number - 1) * 15

                    print(f"[W{self.worker_id}][{row_num}] ", end='', flush=True)

                    # Click with retry
                    clicked = False
                    for attempt in range(3):
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                            time.sleep(0.5)
                            try:
                                button.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", button)
                            clicked = True
                            break
                        except Exception as e:
                            if attempt < 2:
                                time.sleep(1)
                            else:
                                raise e

                    if not clicked:
                        print("CLICK_FAIL ", end='', flush=True)
                        continue

                    time.sleep(3)

                    # Verify popup
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[name="RadWindowManager"]'))
                        )
                    except TimeoutException:
                        print("NO_POPUP ", end='', flush=True)
                        continue

                    # Extract data
                    detail_data = self.extract_popup_data(self.driver)
                    detail_data['_record_number'] = row_num
                    detail_data['_page_number'] = page_number
                    detail_data['_row_on_page'] = idx + 1
                    detail_data['_worker_id'] = self.worker_id

                    page_data.append(detail_data)
                    print("OK")

                    # Close popup
                    self.close_popup(self.driver)
                    time.sleep(1)

                except Exception as e:
                    print(f"ERR:{str(e)[:20]} ", end='', flush=True)
                    try:
                        self.close_popup(self.driver)
                    except:
                        pass
                    continue

            print(f"[Worker {self.worker_id}] Page {page_number} complete: {len(page_data)} records")

        except Exception as e:
            print(f"[Worker {self.worker_id}] Page {page_number} error: {e}")

        return page_data


# ============================================================
# PARALLEL WORKER WITH STAGGERED INITIALIZATION
# ============================================================

def worker_process(args):
    """Worker process with staggered initialization"""
    worker_id, page_queue, start_delay = args

    # Stagger worker startup
    time.sleep(start_delay)

    print(f"\n[Worker {worker_id}] Initializing (delayed {start_delay}s)...")

    scraper = ERCLicenseScraper(worker_id=worker_id)

    try:
        scraper.driver = scraper.create_driver()

        if not scraper.driver:
            print(f"[Worker {worker_id}] Failed to create driver")
            return []

        # Initial navigation with retry
        if not scraper.navigate_to_url(scraper.driver):
            print(f"[Worker {worker_id}] Failed initial navigation")
            return []

        print(f"[Worker {worker_id}] Ready to scrape!")

        all_data = []

        # Process pages from queue
        while True:
            try:
                page_num = page_queue.get(timeout=1)
                if page_num is None:  # Poison pill
                    break

                page_data = scraper.scrape_page(page_num)
                all_data.extend(page_data)

            except queue.Empty:
                break
            except Exception as e:
                print(f"[Worker {worker_id}] Error processing page: {e}")
                continue

        print(f"[Worker {worker_id}] Finished! Extracted {len(all_data)} total records")
        return all_data

    except Exception as e:
        print(f"[Worker {worker_id}] Fatal error: {e}")
        return []
    finally:
        if scraper.driver:
            try:
                scraper.driver.quit()
            except:
                pass


def save_data_to_files(all_data, filename_prefix):
    """Save flattened data to Excel and CSV"""
    if not all_data:
        print("No data to save!")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"{filename_prefix}_{timestamp}.xlsx"
    csv_file = f"{filename_prefix}_{timestamp}.csv"

    print(f"\n[SAVE] Saving {len(all_data)} records...")

    # Flatten nested data
    flattened_data = []
    for record in all_data:
        flat_record = {}

        for key, value in record.items():
            if key not in ['แผนการผลิต', 'กระบวนการผลิต', 'เครื่องจักร']:
                flat_record[key] = value

        for i, plan in enumerate(record.get('แผนการผลิต', []), 1):
            for k, v in plan.items():
                flat_record[f'แผนการผลิต_{i}_{k}'] = v

        for i, proc in enumerate(record.get('กระบวนการผลิต', []), 1):
            for k, v in proc.items():
                flat_record[f'กระบวนการผลิต_{i}_{k}'] = v

        for i, machine in enumerate(record.get('เครื่องจักร', []), 1):
            for k, v in machine.items():
                flat_record[f'เครื่องจักร_{i}_{k}'] = v

        flattened_data.append(flat_record)

    df = pd.DataFrame(flattened_data)

    if '_record_number' in df.columns:
        df = df.sort_values('_record_number')

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Production Licenses', index=False)
        worksheet = writer.sheets['Production Licenses']

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

    df.to_csv(csv_file, index=False, encoding='utf-8-sig')

    print(f"[OK] Excel: {excel_file}")
    print(f"[OK] CSV: {csv_file}")
    print(f"     Records: {len(df)}, Columns: {len(df.columns)}")


def main():
    """Main execution with staggered worker initialization"""
    print("\n" + "="*70)
    print("  ERC Production License Scraper - PARALLEL V2")
    print("  Staggered Initialization (4 Workers)")
    print("="*70)

    # Detect total pages
    print("\n[INIT] Detecting total pages...")
    temp_scraper = ERCLicenseScraper(worker_id=999)
    temp_scraper.driver = temp_scraper.create_driver()

    try:
        if temp_scraper.navigate_to_url(temp_scraper.driver):
            total_pages = temp_scraper.get_total_pages(temp_scraper.driver)
        else:
            print("[ERROR] Could not detect total pages")
            return
    finally:
        temp_scraper.driver.quit()

    print(f"[INFO] Total pages: {total_pages}")
    print(f"[INFO] Workers: 4 (staggered init: 0s, 3s, 6s, 9s)")
    print()

    # Create shared queue
    manager = Manager()
    task_queue = manager.Queue()

    # Fill queue with page numbers
    for page_num in range(1, total_pages + 1):
        task_queue.put(page_num)

    # Add poison pills
    for _ in range(4):
        task_queue.put(None)

    # Create worker arguments with staggered delays
    worker_args = [
        (0, task_queue, 0),   # Worker 0: start immediately
        (1, task_queue, 3),   # Worker 1: start after 3s
        (2, task_queue, 6),   # Worker 2: start after 6s
        (3, task_queue, 9),   # Worker 3: start after 9s
    ]

    start_time = time.time()

    print(f"[START] Beginning parallel scrape at {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)

    # Run workers
    with Pool(processes=4) as pool:
        results = pool.map(worker_process, worker_args)

    # Combine results
    all_data = []
    for worker_result in results:
        all_data.extend(worker_result)

    elapsed_time = time.time() - start_time

    print("\n" + "="*70)
    print(f"[COMPLETE] Scraping finished!")
    print(f"  Total records: {len(all_data)}")
    print(f"  Total time: {elapsed_time/60:.2f} minutes")
    print(f"  Average: {elapsed_time/total_pages:.1f}s per page")
    print("="*70)

    if all_data:
        save_data_to_files(all_data, "ERC_PRODUCTION_PARALLEL_V2")
        print("\n[SUCCESS] All data saved successfully!")
    else:
        print("\n[WARNING] No data extracted!")


if __name__ == "__main__":
    main()
