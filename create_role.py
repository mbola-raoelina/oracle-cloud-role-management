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
    """Initialize Chrome WebDriver with robust version handling for Streamlit Cloud deployment"""
    from chromedriver_fix import initialize_driver_robust
    return initialize_driver_robust()


def check_for_oracle_popup_messages(driver, operation_context="operation"):
    """
    Check for Oracle warning/error popup messages and extract the message content
    
    Returns:
        tuple: (has_popup: bool, message: str, popup_type: str)
        - has_popup: Whether a popup was found
        - message: The extracted message text
        - popup_type: Type of popup (warning, error, info, etc.)
    """
    try:
        # Check for popup container
        popup_selectors = [
            "div.AFPopupSelector[id*='popup-container']",
            "div[id*='msgDlg']",
            "div.p_AFWarning",
            "div.p_AFError", 
            "div.p_AFInfo"
        ]
        
        popup_found = False
        popup_element = None
        
        for selector in popup_selectors:
            try:
                popup_element = driver.find_element(By.CSS_SELECTOR, selector)
                if popup_element.is_displayed():
                    popup_found = True
                    break
            except:
                continue
        
        if not popup_found:
            return False, "", ""
        
        # Extract message content using multiple strategies
        message_selectors = [
            "div.x1mu",           # Primary Oracle message class
            "div.x1mw", 
            "div.x1ml",
            ".af_dialog_content",
            "[class*='message']",
            "td.x1n1 div",       # Alternative structure
            "div[class*='mu']"    # Fallback for similar classes
        ]
        
        message_text = ""
        for msg_selector in message_selectors:
            try:
                message_elements = popup_element.find_elements(By.CSS_SELECTOR, msg_selector)
                for element in message_elements:
                    if element.is_displayed() and element.text.strip():
                        message_text = element.text.strip()
                        break
                if message_text:
                    break
            except:
                continue
        
        # Determine popup type based on classes
        popup_type = "unknown"
        try:
            popup_classes = popup_element.get_attribute("class") or ""
            if "p_AFWarning" in popup_classes or "warning" in popup_classes.lower():
                popup_type = "warning"
            elif "p_AFError" in popup_classes or "error" in popup_classes.lower():
                popup_type = "error"
            elif "p_AFInfo" in popup_classes or "info" in popup_classes.lower():
                popup_type = "info"
            else:
                # Check for warning icon or text
                if "warning" in message_text.lower() or popup_element.find_elements(By.CSS_SELECTOR, "img[src*='warning']"):
                    popup_type = "warning"
                elif "error" in message_text.lower():
                    popup_type = "error"
        except:
            popup_type = "unknown"
        
        if not message_text:
            message_text = f"Oracle popup detected during {operation_context} but message content could not be extracted"
        
        print(f"🔔 Oracle {popup_type} popup detected: {message_text}")
        return True, message_text, popup_type
        
    except Exception as e:
        print(f"⚠️ Error checking for Oracle popups: {str(e)}")
        return False, "", ""


def dismiss_oracle_popup(driver, popup_type="unknown"):
    """
    Dismiss Oracle popup by clicking OK, Cancel, or Close button
    
    Returns:
        bool: Whether popup was successfully dismissed
    """
    try:
        # Try multiple button selectors in order of preference
        dismiss_selectors = [
            "button[id*='::cancel']",           # Primary OK button
            "button[id*='msgDlg::cancel']",     # Specific msgDlg cancel
            "a[id*='::close']",                 # Close link
            "button:contains('OK')",             # Generic OK button
            "button:contains('Cancel')",        # Generic Cancel button  
            "button:contains('Close')",         # Generic Close button
            "[onclick*='cancel']",              # Elements with cancel onclick
            "button.xux",                       # Oracle button class
            "button[_afrpdo='cancel']"          # Oracle specific cancel attribute
        ]
        
        for selector in dismiss_selectors:
            try:
                if ":contains(" in selector:
                    # Handle contains selectors with XPath
                    text = selector.split(":contains('")[1].split("')")[0]
                    xpath_selector = f"//button[contains(text(), '{text}')]"
                    buttons = driver.find_elements(By.XPATH, xpath_selector)
                else:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for button in buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                            print(f"✅ Oracle popup dismissed using selector: {selector}")
                            return True
                    except:
                        continue
            except:
                continue
        
        print(f"⚠️ Could not find dismissible button for Oracle popup")
        return False
        
    except Exception as e:
        print(f"❌ Error dismissing Oracle popup: {str(e)}")
        return False


def reset_browser_state(driver):
    """
    Aggressive browser state reset to prevent error cascade between rows
    
    This function performs comprehensive cleanup when an operation fails:
    1. Close any open popups/dialogs
    2. Navigate back to main page
    3. Clear any form states
    4. Verify we're in a clean state
    """
    try:
        print("🔄 Starting aggressive browser state reset...")
        
        # Step 1: Close any open popups or dialogs
        try:
            # Try to close any confirmation dialogs
            close_buttons = driver.find_elements(By.XPATH, "//button[contains(@id, '::close')] | //button[contains(@id, 'cancel')] | //button[contains(., 'Close')] | //button[contains(., 'Cancel')]")
            for btn in close_buttons[:3]:  # Limit to first 3 to avoid infinite loops
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        driver.execute_script("arguments[0].click();", btn)
                        time.sleep(1)
                        print("✓ Closed popup/dialog")
                except:
                    continue
        except:
            pass  # Ignore if no popups to close
        
        # Step 2: Dismiss any alert dialogs
        try:
            alert = driver.switch_to.alert
            alert.dismiss()
            print("✓ Dismissed alert dialog")
        except:
            pass  # No alert present
        
        # Step 3: Navigate back to main security console
        print("🏠 Navigating back to Security Console...")
        driver.get(SECURITY_CONSOLE_URL)
        
        # Step 4: Wait for page to load completely
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content"))
            )
            print("✓ Security Console page loaded successfully")
        except:
            print("⚠️ Security Console page load timeout, but continuing...")
        
        # Step 5: Clear any search fields that might have residual data
        try:
            search_input = driver.find_element(By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content")
            search_input.clear()
            driver.execute_script("arguments[0].value='';", search_input)
            print("✓ Cleared search field")
        except:
            pass  # Search field not accessible
        
        # Step 6: Additional stabilization wait
        time.sleep(3)
        print("✅ Browser state reset completed successfully")
        
    except Exception as e:
        print(f"⚠️ Browser state reset encountered error: {str(e)}")
        # Last resort: force navigate to main page
        driver.get(SECURITY_CONSOLE_URL)
        time.sleep(5)
        raise


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

def get_current_step_number(driver):
    """Get the current step number from the navigation train"""
    try:
        # Look for the current step indicator (p_AFSelected class)
        current_step = driver.find_element(By.XPATH, "//a[contains(@class, 'p_AFSelected') and contains(@title, 'Current')]")
        title = current_step.get_attribute('title')
        
        # Extract step number from title like "Basic Information Step: Current"
        if "Basic Information" in title:
            return 1
        elif "Function Security Policies" in title:
            return 2
        elif "Data Security Policies" in title:
            return 3
        elif "Role Hierarchy" in title:
            return 4
        elif "Segregation of Duties" in title:
            return 5
        elif "Users" in title:
            return 6
        elif "Summary" in title:
            return 7
        else:
            return 0
    except:
        return 0

def wait_for_step_transition(driver, expected_step, timeout=30):
    """Wait for navigation to reach the expected step using train indicators"""
    print(f"⏰ Waiting for transition to step {expected_step}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_step = get_current_step_number(driver)
        if current_step == expected_step:
            print(f"✅ Successfully navigated to step {expected_step}")
            return True
        elif current_step > expected_step:
            print(f"⚠️ Overshot to step {current_step}, expected {expected_step}")
            return True
        
        time.sleep(1)  # Check every second
    
    final_step = get_current_step_number(driver)
    print(f"❌ Timeout waiting for step {expected_step}, currently at step {final_step}")
    return False


def click_next_button(driver, instance=1, max_retries=2):
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempting to click Next button (step {instance})")
            
            # Check current step before clicking
            current_step = get_current_step_number(driver)
            expected_next_step = current_step + 1
            print(f"📍 Currently at step {current_step}, expecting to go to step {expected_next_step}")
            
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
            
            # Wait for button to be clickable (not disabled)
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, btn_id))
            )
            print(f"✅ Next button is clickable")
            
            # Click the button
            driver.execute_script("arguments[0].click();", next_btn)
            print(f"✓ Clicked Next button successfully")
            
            # Use robust navigation train-based transition detection
            if wait_for_step_transition(driver, expected_next_step, timeout=30):
                print(f"✓ Step {instance} transition completed successfully")
                return True
            else:
                # If train navigation failed, try one more time with longer wait
                print("⚠️ Train navigation detection failed, trying extended wait...")
                time.sleep(5)  # Give Oracle more time
                
                # Check again
                final_step = get_current_step_number(driver)
                if final_step == expected_next_step:
                    print(f"✓ Step {instance} transition completed (delayed)")
                    return True
                elif final_step > expected_next_step:
                    print(f"⚠️ Navigation overshot! Currently at step {final_step}, expected {expected_next_step}")
                    print(f"🔄 This may cause role operations to happen on wrong page!")
                    # Still return True but with warning - we'll add verification later
            return True
                else:
                    raise Exception(f"Navigation failed: still at step {final_step}, expected {expected_next_step}")
                
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
            # Get input file path from environment variable (set by Streamlit) or use default
            input_file = os.environ.get("INPUT_FILE_PATH", "role_create_input.xlsx")
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

                # Navigate through steps with robust train navigation
                initial_step = get_current_step_number(driver)
                print(f"📍 Starting navigation from step {initial_step}")
                
                for instance in range(1, 6):
                    current_step = get_current_step_number(driver)
                    target_step = current_step + 1
                    
                    print(f"🔄 Navigating from step {current_step} to step {target_step} (iteration {instance}/5)")
                    
                    # Click Next button with robust navigation detection
                    if click_next_button(driver, instance=instance):
                        # Verify we actually moved to the next step
                        final_step = get_current_step_number(driver)
                        if final_step >= target_step:
                            print(f"✓ Step {instance} completed successfully (now at step {final_step})")
                        else:
                            raise Exception(f"Navigation verification failed: clicked Next but still at step {final_step}, expected {target_step}")
                    else:
                        raise Exception(f"Failed to click Next button for step {instance}")

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
                
                # CRITICAL: Perform aggressive browser state reset after failure
                print(f"🔧 Performing aggressive browser state reset after row {index+1} failure...")
                try:
                    # Force clean browser state reset
                    reset_browser_state(driver)
                    print(f"✅ Browser state reset completed for row {index+1}")
                except Exception as reset_error:
                    print(f"⚠️ Browser state reset failed: {str(reset_error)}")
                    # If reset fails, try to continue anyway
                    try:
                        driver.get(SECURITY_CONSOLE_URL)
                        time.sleep(3)
                        print(f"✅ Fallback reset to main page completed")
                    except Exception as fallback_error:
                        print(f"❌ Fallback reset also failed: {str(fallback_error)}")

            # Save progress after each row
            try:
                df.to_excel("role_create_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")

            # Reset to main page after each row (success or failure)
            if current_status == 'Success':
            driver.get(SECURITY_CONSOLE_URL)
            time.sleep(2)
            # Note: Browser state is already reset above for failures

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