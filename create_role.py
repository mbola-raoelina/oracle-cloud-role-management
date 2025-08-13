import os
import time
import pandas as pd
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from dotenv import load_dotenv
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import pandas as pd
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
load_dotenv()
# Configuration

CHROME_DRIVER_PATH = os.path.abspath(
    "C:\\Users\\061181CA8\\Downloads\\chromedriver-win64 (3)\\chromedriver-win64\\chromedriver.exe"
)

# Dynamic URL based on environment
def get_security_console_url():
    """Get the security console URL based on environment variable"""
    environment = os.environ.get("ORACLE_ENVIRONMENT", "dev1")  # Default to dev1
    base_url = f"https://iabbzv-{environment}.fa.ocs.oraclecloud.com"
    return f"{base_url}/hcmUI/faces/FndOverview?fnd=%3B%3B%3B%3Bfalse%3B256%3B%3B%3B&fndGlobalItemNodeId=ASE_FUSE_SECURITY_CONSOLE"

SECURITY_CONSOLE_URL = get_security_console_url()


def initialize_driver():
    """Initialize Chrome WebDriver with system Chrome for Streamlit Cloud deployment"""
    options = webdriver.ChromeOptions()
    # Headless mode for better user experience
    options.add_argument("--headless")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    })

    # For Streamlit Cloud deployment, use system Chrome
    try:
        print("🔄 Initializing Chrome with system installation...")
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome initialized successfully")
        return driver
    except Exception as e:
        print(f"⚠️ System Chrome failed: {e}")
        try:
            # Fallback to ChromeDriverManager
            print("🔄 Trying ChromeDriverManager as fallback...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            print("✅ ChromeDriver initialized with ChromeDriverManager")
            return driver
        except Exception as e2:
            print(f"❌ All Chrome initialization strategies failed: {e2}")
            raise

    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def find_element_robust(driver, selectors_list, timeout=20, condition=EC.element_to_be_clickable):
    """
    Try multiple selectors until one works. More robust than single selector approach.
    
    Args:
        driver: WebDriver instance
        selectors_list: List of tuples (By, selector)
        timeout: Timeout for each selector attempt
        condition: Expected condition (default: element_to_be_clickable)
    
    Returns:
        WebElement if found
    
    Raises:
        Exception: If no selector works
    """
    for i, selector in enumerate(selectors_list):
        try:
            print(f"🔄 Trying selector {i+1}/{len(selectors_list)}: {selector[0]} = '{selector[1]}'")
            element = WebDriverWait(driver, timeout).until(condition(selector))
            print(f"✅ Found element with selector {i+1}")
            return element
        except Exception as e:
            print(f"⚠️ Selector {i+1} failed: {str(e)}")
            continue
    
    raise Exception(f"❌ Element not found with any of {len(selectors_list)} selectors")


def click_next_button(driver, instance=1, max_retries=2):
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempting to click Next button (step {instance})")
            
            # Use robust element finding with multiple selectors
            next_btn = find_element_robust(driver, [
                (By.XPATH, "//button[contains(@id, 'cb4') and contains(., 'Next')]"),
                (By.XPATH, "//button[contains(., 'Next')]"),
                (By.XPATH, "//button[@title='Next']"),
                (By.XPATH, "//button[text()='Next']")
            ], timeout=10)
            
            # Get the actual button ID for logging
            btn_id = next_btn.get_attribute('id')
            print(f"✅ Found Next button: {btn_id}")
            
            # Click the button
            driver.execute_script("arguments[0].click();", next_btn)
            print(f"✓ Clicked Next button successfully")
            time.sleep(2)  # Wait for page transition
            return True
                
        except StaleElementReferenceException:
            if attempt == max_retries - 1:
                raise
            print(f"🔄 Stale element, retrying... (attempt {attempt + 1})")
            time.sleep(1)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ Failed to click Next button after {max_retries} attempts: {str(e)}")
                raise
            print(f"🔄 Retrying... (attempt {attempt + 1}): {str(e)}")
            time.sleep(1)
    
    return False

def select_role_category(driver, role_category, max_retries=3):
    """Enhanced role category selection based on actual HTML structure"""
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}: Selecting role category '{role_category}'")
            
            # Wait for the role category input field to be present
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCat::content"))
            )
            
            # Wait a bit more for the page to be fully loaded
            time.sleep(2)
            
            # Find the dropdown trigger (the arrow button)
            dropdown_trigger = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCat::drop"))
            )
            
            # Scroll into view and click the dropdown trigger
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_trigger)
            time.sleep(1)
            
            # Click the dropdown trigger to open the popup
            driver.execute_script("arguments[0].click();", dropdown_trigger)
            print("✓ Dropdown trigger clicked")
            
            # Wait for the popup wrapper to become visible (display changes from none to block)
            popup_wrapper = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCat::popWrap"))
            )
            
            # Wait for the popup to be visible (check if display style is not 'none')
            WebDriverWait(driver, 15).until(
                lambda d: popup_wrapper.get_attribute("style") != "display:none"
            )
            print("✓ Popup is now visible")
            
            # Wait for the popup list to be populated
            popup_list = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCat::pop"))
            )
            
            # Get all options immediately without waiting for text content
            print("📋 Getting all options from popup...")
            all_options = popup_list.find_elements(By.XPATH, ".//li[@role='option']")
            print(f"📋 Found {len(all_options)} options in popup")
            
            # Print first few options for debugging
            for i, opt in enumerate(all_options[:5]):
                print(f"   Option {i}: '{opt.text}' (adfiv: {opt.get_attribute('_adfiv')})")
            
            # Try multiple strategies to find the option
            role_option = None
            
            # Strategy 1: Use _adfiv attribute (most reliable)
            try:
                # Map role categories to their _adfiv values based on the HTML
                adfiv_map = {
                    "Common - Job Roles": "6",
                    "Common - Abstract Roles": "4", 
                    "Common - Duty Roles": "5",
                    "HCM - Job Roles": "18",
                    "Financials - Job Roles": "13"
                }
                
                if role_category in adfiv_map:
                    adfiv_value = adfiv_map[role_category]
                    option_xpath = f".//li[@role='option' and @_adfiv='{adfiv_value}']"
                    role_option = popup_list.find_element(By.XPATH, option_xpath)
                    print(f"✅ Found option using _adfiv={adfiv_value}: '{role_option.text}'")
                else:
                    print(f"⚠️ No _adfiv mapping found for '{role_category}'")
            except:
                print("❌ _adfiv match failed, trying text match...")
            
            # Strategy 2: If _adfiv failed, try direct text match
            if not role_option:
                try:
                    option_xpath = f".//li[@role='option' and normalize-space(text())='{role_category}']"
                    role_option = popup_list.find_element(By.XPATH, option_xpath)
                    print(f"✅ Found option using text match: '{role_option.text}'")
                except:
                    print("❌ Text match failed, trying partial text match...")
            
            # Strategy 3: If still not found, try partial text match
            if not role_option:
                try:
                    option_xpath = f".//li[@role='option' and contains(text(), '{role_category.split()[0]}')]"
                    role_option = popup_list.find_element(By.XPATH, option_xpath)
                    print(f"✅ Found option using partial text match: '{role_option.text}'")
                except:
                    print("❌ Partial text match failed")
            
            # Strategy 4: If still not found, try by index (fallback)
            if not role_option:
                try:
                    # Try to find by index based on _adfiv value
                    if role_category in adfiv_map:
                        adfiv_value = int(adfiv_map[role_category])
                        if adfiv_value < len(all_options):
                            role_option = all_options[adfiv_value]
                            print(f"✅ Found option using index {adfiv_value}: '{role_option.text}'")
                except:
                    print("❌ Index-based search failed")
            
            # If still not found, raise exception
            if not role_option:
                available_options = [opt.text for opt in all_options if opt.text.strip()]
                raise Exception(f"Could not find option '{role_category}'. Available options: {available_options}")
            
            # Now click the found option
            print(f"🎯 Clicking option: '{role_option.text}'")
            
            # Scroll the option into view and click it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", role_option)
            time.sleep(1)
            
            # Try multiple click strategies
            try:
                # Strategy 1: Direct click
                role_option.click()
                print("✓ Clicked using direct click")
            except:
                try:
                    # Strategy 2: JavaScript click
                    driver.execute_script("arguments[0].click();", role_option)
                    print("✓ Clicked using JavaScript")
                except:
                    # Strategy 3: ActionChains click
                    ActionChains(driver).move_to_element(role_option).click().perform()
                    print("✓ Clicked using ActionChains")
            
            print(f"✓ Selected option: {role_category}")
            
            # Wait for the popup to close (check if display style becomes 'none' again)
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: popup_wrapper.get_attribute("style") == "display:none"
                )
                print("✓ Popup closed")
            except:
                print("⚠️ Could not detect popup close, but continuing...")
            
            # Wait a bit more for the page to stabilize
            time.sleep(3)
            
            # Simple verification - just check if we can continue
            print(f"✅ Role category selection completed for '{role_category}'")
            return True

        except (StaleElementReferenceException, TimeoutException) as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise
            print("🔄 Retrying...")
            time.sleep(2)
            
            # Try to close any open popup before retrying
            try:
                # Press Escape key to close popup if it's open
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
            except:
                pass
            continue

        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            if attempt == max_retries - 1:
                raise
            print("🔄 Retrying...")
            time.sleep(2)
            continue

    return False

# ---------------------------
# Updated main function
# ---------------------------
def main():
    driver = None
    df = None

    try:
        # Read Excel input with column validation
        try:
            input_file = "role_create_input.xlsx"
            required_columns = {'Role Name', 'Role Code', 'Role Category'}  # Now include Role Category
            
            df = pd.read_excel(input_file)
            print(f"📖 Loaded Excel file '{input_file}' with {len(df)} roles to process")
            
            # Validate columns
            missing_cols = required_columns - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Prepare results columns
            df['Confirmation Message'] = ''
            df['Status'] = 'Pending'
            df['Timestamp'] = ''
            df['Error Details'] = ''
        except Exception as e:
            print(f"🔴 Excel file error: {str(e)}")
            raise

        # Initialize browser and login
        driver = initialize_driver()
        driver.maximize_window()
        driver.get(SECURITY_CONSOLE_URL)
        print("🚀 Browser initialized")

        try:
            print("🔐 Attempting login...")
            username_field = find_element_robust(driver, [
                (By.ID, "userid"),
                (By.NAME, "userid"),
                (By.XPATH, "//input[@name='userid']")
            ], timeout=20, condition=EC.presence_of_element_located)
            username_field.send_keys(os.getenv("BIP_USERNAME"))
            
            password_field = find_element_robust(driver, [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.XPATH, "//input[@name='password']")
            ], timeout=20, condition=EC.presence_of_element_located)
            password_field.send_keys(os.getenv("BIP_PASSWORD"))
            
            language_select = find_element_robust(driver, [
                (By.ID, "Languages"),
                (By.NAME, "Languages"),
                (By.XPATH, "//select[@name='Languages']")
            ], timeout=20, condition=EC.presence_of_element_located)
            Select(language_select).select_by_visible_text("English")
            
            login_button = find_element_robust(driver, [
                (By.ID, "btnActive"),
                (By.XPATH, "//button[contains(., 'Sign In')]"),
                (By.XPATH, "//input[@type='submit']")
            ], timeout=15)
            login_button.click()
            
            print("✅ Login successful")
            time.sleep(3)
        except Exception as e:
            print(f"🔴 Login failed: {str(e)}")
            driver.save_screenshot("login_error.png")
            raise

        # Process each role creation from Excel
        for index, row in df.iterrows():
            current_status = 'Failed'  # Default status
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[index, 'Timestamp'] = timestamp

            try:
                print(f"\n⏳ Processing row {index+1}/{len(df)} at {timestamp}")
                print(f"📝 Creating role '{row['Role Name']}' with code '{row['Role Code']}' and category '{row['Role Category']}'")

                # Navigate to Create Role form
                create_role_btn = find_element_robust(driver, [
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:cmiCrte"),
                    (By.XPATH, "//*[contains(@id, 'cmiCrte')]"),
                    (By.XPATH, "//*[contains(., 'Create Role')]")
                ], timeout=20)
                create_role_btn.click()

                # Fill Role Name
                role_name_field = find_element_robust(driver, [
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRNam::content"),
                    (By.XPATH, "//input[contains(@id, 'bIRNam') and contains(@id, 'content')]"),
                    (By.XPATH, "//input[@type='text' and contains(@id, 'content')]")
                ], timeout=20, condition=EC.presence_of_element_located)
                role_name_field.clear()
                role_name_field.send_keys(row['Role Name'])

                # Fill Role Code
                role_code_field = find_element_robust(driver, [
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"),
                    (By.XPATH, "//input[contains(@id, 'bIRCod') and contains(@id, 'content')]"),
                    (By.XPATH, "//input[@type='text' and contains(@id, 'content') and position()=2]")
                ], timeout=20, condition=EC.presence_of_element_located)
                role_code_field.clear()
                role_code_field.send_keys(row['Role Code'])

                # Select Role Category using the input value
                try:
                    if not select_role_category(driver, row['Role Category']):
                        raise RuntimeError("Role category selection failed after maximum retries")
                except Exception as e:
                    print(f"Critical failure in role category selection: {str(e)}")
                    driver.save_screenshot("role_category_error.png")
                    raise

                # Click through Next buttons
                for instance in range(1, 6):
                    click_next_button(driver, instance=instance)
                    time.sleep(3)

                # Click Save and Close with robust element finding
                print("🔄 Attempting to click Save button...")
                save_button = find_element_robust(driver, [
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"),
                    (By.XPATH, "//button[contains(@id, 'cb1')]"),
                    (By.XPATH, "//button[contains(., 'Save')]"),
                    (By.XPATH, "//button[contains(., 'Save and Close')]")
                ], timeout=10)
                driver.execute_script("arguments[0].click();", save_button)
                print("✓ Clicked Save button successfully")
                time.sleep(3)

                # Handle confirmation popup with correct HTML structure
                print("🔄 Waiting for confirmation popup...")
                
                # Wait for popup to appear using the correct selector
                try:
                    WebDriverWait(driver, 20).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector"))
                    )
                    print("✅ Confirmation popup appeared")
                except:
                    print("⚠️ Could not detect confirmation popup, but continuing...")
                
                # Try to get confirmation message using the correct selector
                confirmation_message = "Role created successfully"
                try:
                    # Based on the HTML structure, the message is in div.x1mu
                    message_element = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x1mu"))
                    )
                    confirmation_message = message_element.text
                    print(f"✅ Confirmation Message: {confirmation_message}")
                except:
                    print("⚠️ Could not get confirmation message, using default")
                
                time.sleep(2)
                
                # Try to click OK button using the correct ID
                try:
                    # Based on the HTML structure, the OK button has ID "_FOd1::msgDlg::cancel"
                    ok_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "_FOd1::msgDlg::cancel"))
                    )
                    driver.execute_script("arguments[0].click();", ok_button)
                    print("✅ Clicked OK button using correct ID")
                    time.sleep(2)
                except:
                    print("⚠️ Could not find OK button by ID, trying alternative methods...")
                    
                    # Strategy 2: Try by text content
                    try:
                        ok_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[text()='OK']"))
                        )
                        driver.execute_script("arguments[0].click();", ok_button)
                        print("✅ Clicked OK button using text match")
                        time.sleep(2)
                    except:
                        print("⚠️ Could not find OK button by text, trying generic search...")
                        
                        # Strategy 3: Try generic OK button search
                        try:
                            ok_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'OK')]"))
                            )
                            driver.execute_script("arguments[0].click();", ok_button)
                            print("✅ Clicked OK button using generic search")
                            time.sleep(2)
                        except:
                            print("⚠️ Could not find OK button, trying Escape key...")
                            
                            # Strategy 4: Try to press Escape to close popup
                            try:
                                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                                print("✅ Pressed Escape to close popup")
                                time.sleep(1)
                            except:
                                print("⚠️ Could not close popup, but continuing...")

                # Record success
                df.at[index, 'Confirmation Message'] = confirmation_message
                df.at[index, 'Status'] = 'Success'
                current_status = 'Success'
                print(f"✅ Successfully processed row {index+1}")

            except Exception as e:
                error_msg = str(e)
                df.at[index, 'Confirmation Message'] = f"Error: {error_msg}"
                df.at[index, 'Status'] = 'Failed'
                df.at[index, 'Error Details'] = error_msg
                print(f"🔴 Failed to process row {index+1}: {error_msg}")
                driver.save_screenshot(f"error_row_{index+1}.png")

            # Save progress after each row
            try:
                df.to_excel("role_create_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")

            # Navigate back to the main/security console page for the next iteration
            driver.get(SECURITY_CONSOLE_URL)
            time.sleep(2)

        # Save final results
        output_file = f"role_create_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        try:
            df.to_excel(output_file, index=False)
            print(f"\n💾 Saved final results to '{output_file}'")
        except Exception as e:
            print(f"🔴 Failed to save final results: {str(e)}")
            raise

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        if df is not None:
            print("🔄 Attempting to save partial results...")
            try:
                partial_file = f"role_create_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                df.to_excel(partial_file, index=False)
                print(f"💾 Saved partial results to '{partial_file}'")
            except Exception as save_error:
                print(f"⚠️ Failed to save partial results: {str(save_error)}")
        raise

    finally:
        if driver:
            print("\n🛑 Closing browser...")
            try:
                driver.quit()
                print("✅ Browser closed properly")
            except Exception as e:
                print(f"⚠️ Browser close failed: {str(e)}")

if __name__ == "__main__":
    main()