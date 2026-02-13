"""
Debug script to test a single popup extraction
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def create_driver():
    """Create a new WebDriver instance"""
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    # Running in visible mode to see what happens
    # options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def main():
    url = "http://app04.erc.or.th/ELicense/Licenser/05_Reporting/504_ListLicensing_Columns_New.aspx?LicenseType=1"

    print("="*80)
    print("DEBUG: Testing Single Popup Extraction")
    print("="*80)

    driver = create_driver()

    try:
        print(f"\n[1] Loading page: {url}")
        driver.get(url)
        time.sleep(5)

        print(f"[2] Page loaded, waiting for table...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_MasterContentPlaceHolder_RadGrid_ctl00"))
        )
        time.sleep(2)

        print(f"[3] Finding detail buttons...")
        detail_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='image'][src*='icon_view']")
        print(f"    Found {len(detail_buttons)} buttons")

        if not detail_buttons:
            print("[ERROR] No detail buttons found!")
            return

        # Click the first button
        button = detail_buttons[0]
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(1)

        print(f"\n[4] Clicking first detail button...")
        print(f"    Current windows: {len(driver.window_handles)}")
        print(f"    Current window handle: {driver.current_window_handle}")

        button.click()

        print(f"\n[5] Waiting 5 seconds after click...")
        time.sleep(5)

        print(f"\n[6] Checking page state:")
        print(f"    Number of windows: {len(driver.window_handles)}")
        print(f"    Window handles: {driver.window_handles}")

        # Check for iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"    Number of iframes: {len(iframes)}")
        for i, iframe in enumerate(iframes):
            iframe_id = iframe.get_attribute('id') or '(no id)'
            iframe_src = iframe.get_attribute('src') or '(no src)'
            iframe_class = iframe.get_attribute('class') or '(no class)'
            print(f"      iframe {i}: id='{iframe_id}', src='{iframe_src[:50]}...', class='{iframe_class}'")

        # Check for RadWindow elements
        print(f"\n[7] Checking for RadWindow elements...")
        radwindows = driver.find_elements(By.CSS_SELECTOR, "[class*='RadWindow'], [class*='radWindow']")
        print(f"    Found {len(radwindows)} RadWindow elements")
        for rw in radwindows:
            print(f"      {rw.tag_name}: class='{rw.get_attribute('class')}', visible={rw.is_displayed()}")

        # Try to find any popups or overlays
        print(f"\n[8] Checking for popup/overlay elements...")
        popups = driver.find_elements(By.CSS_SELECTOR, "[class*='popup'], [class*='Popup'], [class*='modal'], [class*='Modal'], [class*='overlay'], [class*='Overlay']")
        print(f"    Found {len(popups)} popup-like elements")

        # Take screenshot
        screenshot_file = "debug_after_click.png"
        driver.save_screenshot(screenshot_file)
        print(f"\n[9] Screenshot saved: {screenshot_file}")

        print("\n[10] Waiting 10 more seconds for you to observe the browser...")
        time.sleep(10)

        print("\n" + "="*80)
        print("DEBUG COMPLETE - Check the browser window and screenshot")
        print("="*80)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    main()
