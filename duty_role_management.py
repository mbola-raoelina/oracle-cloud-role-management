import os
import time
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
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
load_dotenv()
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


def handle_oracle_popup(driver, timeout=5):
    """
    Generic Oracle popup/warning handler that can be used across all automation scripts
    
    Detects and handles Oracle warning popups like:
    - "You can remove only roles inherited by the current role"
    - Business validation warnings
    - Confirmation dialogs
    
    Returns:
        tuple: (popup_found, popup_message, action_taken)
    """
    try:
        print("🔍 Checking for Oracle popups/warnings...")
        
        # Check for Oracle popup container
        popup_containers = [
            # Most common Oracle popup selector
            (By.CSS_SELECTOR, "div.AFPopupSelector[id*='popup-container']"),
            # Alternative popup selectors
            (By.CSS_SELECTOR, "div.AFPopupSelector"),
            (By.XPATH, "//div[contains(@class, 'AFPopupSelector')]"),
            # Warning-specific selectors
            (By.CSS_SELECTOR, "div.p_AFWarning"),
            (By.XPATH, "//div[contains(@class, 'p_AFWarning')]")
        ]
        
        popup_found = False
        popup_message = ""
        
        for selector_type, selector_value in popup_containers:
            try:
                popup = WebDriverWait(driver, timeout).until(
                    EC.visibility_of_element_located((selector_type, selector_value))
                )
                popup_found = True
                print(f"✅ Oracle popup detected with selector: {selector_value}")
                break
            except:
                continue
        
        if not popup_found:
            return False, "", "no_popup"
        
        # Extract popup message
        message_selectors = [
            # Most common message container
            (By.CSS_SELECTOR, "div.x1mu"),
            (By.CSS_SELECTOR, "div.x1mw"), 
            # Alternative message selectors
            (By.XPATH, "//div[contains(@class, 'x1mu') or contains(@class, 'x1mw')]"),
            # Generic text content in popup
            (By.XPATH, "//div[contains(@class, 'AFPopupSelector')]//div[contains(@class, 'x1') and text()]")
        ]
        
        for selector_type, selector_value in message_selectors:
            try:
                message_element = driver.find_element(selector_type, selector_value)
                popup_message = message_element.text.strip()
                if popup_message:
                    print(f"📋 Popup message: {popup_message}")
                    break
            except:
                continue
        
        # Handle the popup by clicking OK/Cancel/Close button
        button_selectors = [
            # Most common - OK/Cancel button with ID
            (By.ID, "_FOd1::msgDlg::cancel"),
            # Generic OK buttons
            (By.XPATH, "//button[contains(., 'OK')]"),
            (By.XPATH, "//button[contains(@id, 'cancel')]"),
            # Close buttons
            (By.XPATH, "//a[contains(@id, 'close')]"),
            (By.XPATH, "//button[contains(., 'Close')]"),
            # Most generic fallback
            (By.XPATH, "//div[contains(@class, 'AFPopupSelector')]//button")
        ]
        
        button_clicked = False
        for selector_type, selector_value in button_selectors:
            try:
                button = driver.find_element(selector_type, selector_value)
                if button.is_displayed() and button.is_enabled():
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)
                    print(f"✅ Popup dismissed using selector: {selector_value}")
                    button_clicked = True
                    break
            except:
                continue
        
        if not button_clicked:
            print("⚠️ Could not find button to dismiss popup, trying ESC key...")
            driver.send_keys(Keys.ESCAPE)
            time.sleep(1)
            return True, popup_message, "escaped"
        
        return True, popup_message, "dismissed"
        
    except Exception as e:
        print(f"⚠️ Error in popup handling: {str(e)}")
        return False, "", "error"


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
            "div.x1mu",           # Primary Oracle message class from your example
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
            "button[id*='::cancel']",           # Primary OK button from your example
            "button[id*='msgDlg::cancel']",     # Specific msgDlg cancel
            "a[id*='::close']",                 # Close link
            "button:contains('OK')",             # Generic OK button
            "button:contains('Cancel')",        # Generic Cancel button  
            "button:contains('Close')",         # Generic Close button
            "[onclick*='cancel']",              # Elements with cancel onclick
            "button.xux",                       # Oracle button class from your example
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
    1. Handle any Oracle popups/warnings
    2. Close any open popups/dialogs
    3. Navigate back to main page
    4. Clear any form states
    5. Verify we're in a clean state
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


def click_next_button_OLD(driver, max_retries=3):
    """Enhanced next button handler for both create and copy flows"""
    for attempt in range(max_retries):
        try:
            # Generic selector that works for both flows
            next_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH,
                    "//button[contains(@id, 'cb4') and contains(., 'Next')]"))
            )
            
            # Scroll and click with JavaScript
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            
            # Wait for page transition
            WebDriverWait(driver, 15).until(
                EC.invisibility_of_element_located((By.XPATH,
                    "//button[contains(@id, 'cb4') and contains(., 'Next') and @aria-disabled='true']"))
            )
            return True
            
        except StaleElementReferenceException:
            if attempt == max_retries - 1:
                raise
            print(f"Stale element detected, retrying ({attempt + 1}/{max_retries})")
            time.sleep(1)
            
        except TimeoutException:
            if attempt == max_retries - 1:
                raise
            print(f"Timeout waiting for Next button, retrying ({attempt + 1}/{max_retries})")
            time.sleep(1)
            
    return False

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
    """ENHANCED DEBUG VERSION - Let's see exactly what's happening"""
    for attempt in range(max_retries):
        try:
            print(f"\n🔄 === DEBUGGING NEXT BUTTON CLICK (step {instance}, attempt {attempt+1}) ===")
            
            # 1. DETAILED PAGE STATE ANALYSIS
            print("📋 STEP 1: Analyzing current page state...")
            current_step = get_current_step_number(driver)
            expected_next_step = current_step + 1
            print(f"📍 Currently at step {current_step}, expecting to go to step {expected_next_step}")
            
            # 2. CHECK ALL BUTTONS ON PAGE
            print("📋 STEP 2: Finding ALL buttons on page...")
            all_buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"🔍 Found {len(all_buttons)} total buttons on page:")
            for i, btn in enumerate(all_buttons[:10]):  # Show first 10 buttons
                try:
                    btn_id = btn.get_attribute('id') or 'NO_ID'
                    btn_text = btn.text.strip() or 'NO_TEXT'
                    btn_title = btn.get_attribute('title') or 'NO_TITLE'
                    btn_visible = btn.is_displayed()
                    btn_enabled = btn.is_enabled()
                    print(f"  Button {i+1}: ID='{btn_id}', Text='{btn_text}', Title='{btn_title}', Visible={btn_visible}, Enabled={btn_enabled}")
                except:
                    print(f"  Button {i+1}: ERROR reading attributes")
            
            # 3. CHECK FOR POPUPS
            print("📋 STEP 3: Checking for popups...")
            popups = driver.find_elements(By.CSS_SELECTOR, "div.AFPopupSelector, div[id*='popup'], div[id*='msgDlg']")
            print(f"🔍 Found {len(popups)} popups on page")
            for i, popup in enumerate(popups):
                try:
                    popup_id = popup.get_attribute('id') or 'NO_ID'
                    popup_visible = popup.is_displayed()
                    print(f"  Popup {i+1}: ID='{popup_id}', Visible={popup_visible}")
                except:
                    print(f"  Popup {i+1}: ERROR reading attributes")
            
            # 4. FIND NEXT BUTTON WITH DETAILED LOGGING
            print("📋 STEP 4: Finding Next button with detailed selector testing...")
            selectors = [
                (By.XPATH, "//button[contains(@id, 'cb4') and contains(., 'Next')]"),
                (By.XPATH, "//button[contains(., 'Next')]"),
                (By.XPATH, "//button[@title='Next']"),
                (By.XPATH, "//button[text()='Next']")
            ]
            
            next_btn = None
            for i, selector in enumerate(selectors):
                try:
                    print(f"🔍 Testing selector {i+1}: {selector[1]}")
                    elements = driver.find_elements(selector[0], selector[1])
                    print(f"  Found {len(elements)} elements")
                    for j, elem in enumerate(elements):
                        elem_id = elem.get_attribute('id') or 'NO_ID'
                        elem_text = elem.text.strip() or 'NO_TEXT'
                        elem_title = elem.get_attribute('title') or 'NO_TITLE'
                        elem_visible = elem.is_displayed()
                        elem_enabled = elem.is_enabled()
                        print(f"    Element {j+1}: ID='{elem_id}', Text='{elem_text}', Title='{elem_title}', Visible={elem_visible}, Enabled={elem_enabled}")
                        if next_btn is None and elem_visible and elem_enabled:
                            next_btn = elem
                            print(f"    ✅ SELECTED this element as Next button")
                except Exception as e:
                    print(f"  ❌ Selector {i+1} failed: {str(e)}")
            
            if next_btn is None:
                raise Exception("❌ No suitable Next button found!")
            
            # 5. DETAILED BUTTON ANALYSIS
            print("📋 STEP 5: Analyzing selected Next button...")
            btn_id = next_btn.get_attribute('id')
            btn_text = next_btn.text.strip()
            btn_title = next_btn.get_attribute('title')
            btn_class = next_btn.get_attribute('class')
            btn_onclick = next_btn.get_attribute('onclick')
            print(f"✅ Selected Next button details:")
            print(f"  ID: '{btn_id}'")
            print(f"  Text: '{btn_text}'")
            print(f"  Title: '{btn_title}'")
            print(f"  Class: '{btn_class}'")
            print(f"  OnClick: '{btn_onclick}'")
            
            # 6. SAFETY CHECK
            print("📋 STEP 6: Safety validation...")
            if 'cancel' in btn_text.lower() or 'cancel' in btn_title.lower():
                raise Exception(f"❌ SAFETY ABORT: This is a Cancel button! Text='{btn_text}', Title='{btn_title}'")
            if 'rhSrCan' in btn_id:
                raise Exception(f"❌ SAFETY ABORT: This is the popup Cancel button! ID='{btn_id}'")
            print("✅ Safety check passed")
            
            # 7. CLICK THE BUTTON
            print("📋 STEP 7: Clicking the button...")
            driver.execute_script("arguments[0].click();", next_btn)
            print(f"✓ Clicked button successfully")
            
            # 8. IMMEDIATE POST-CLICK ANALYSIS
            print("📋 STEP 8: Post-click analysis...")
            time.sleep(1)  # Brief pause to see immediate effects
            current_step_after = get_current_step_number(driver)
            print(f"📍 Step after click: {current_step_after} (was {current_step}, expected {expected_next_step})")
            
            # Check if any new popups appeared after click
            post_click_popups = driver.find_elements(By.CSS_SELECTOR, "div.AFPopupSelector, div[id*='popup'], div[id*='msgDlg']")
            print(f"🔍 Popups after click: {len(post_click_popups)}")
            
            print("📋 STEP 9: Waiting for navigation transition...")
            if wait_for_step_transition(driver, expected_next_step, timeout=30):
                print(f"✅ Step {instance} transition completed successfully")
                print("=" * 80)
                return True
            else:
                # If train navigation failed, try one more time with longer wait
                print("⚠️ Train navigation detection failed, trying extended wait...")
                time.sleep(5)  # Give Oracle more time
                
                # Check again
                final_step = get_current_step_number(driver)
                if final_step == expected_next_step:
                    print(f"✅ Step {instance} transition completed (delayed)")
                    print("=" * 80)
                    return True
                elif final_step > expected_next_step:
                    print(f"⚠️ Navigation overshot! Currently at step {final_step}, expected {expected_next_step}")
                    print("=" * 80)
                    return True
                else:
                    print(f"❌ Navigation failed: still at step {final_step}, expected {expected_next_step}")
                    print("=" * 80)
                    raise Exception(f"Navigation failed: still at step {final_step}, expected {expected_next_step}")
                
        except StaleElementReferenceException:
            if attempt == max_retries - 1:
                raise
            print(f"🔄 Stale element, retrying... (attempt {attempt + 1})")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
            print("=" * 80)
            if attempt == max_retries - 1:
                print(f"❌ Failed to click Next button after {max_retries} attempts: {str(e)}")
                raise
            print(f"🔄 Retrying... (attempt {attempt + 1})")
            time.sleep(1)
    
    return False

# --------------------------------------------------------------------
# Function to add a duty role (for Action = 'ADD')
# --------------------------------------------------------------------
def add_duty_role(driver, existing_role_name, existing_role_code, duty_role_name, duty_role_code):
    try:
        # [1] Search for existing role to edit with optimized timing
        search_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content"))
        )
        search_input.clear()
        driver.execute_script("arguments[0].value='';", search_input)
        time.sleep(1)
        search_input.send_keys(existing_role_name)
        time.sleep(1)  # Brief pause to let Oracle register the input
        
        # PRESS ENTER to trigger the search
        search_input.send_keys(Keys.RETURN)
        
        # Smart wait for search results - check if results appear quickly
        print("⏰ Waiting for search results...")
        start_time = time.time()
        
        # Use a shorter initial timeout with polling
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
            )
            elapsed = time.time() - start_time
            print(f"✓ Search results loaded quickly ({elapsed:.1f}s)")
            time.sleep(1)  # Short stabilization wait
        except:
            # If not loaded quickly, wait longer
            print("⏰ Search taking longer, extending wait...")
            try:
                WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
                )
                elapsed = time.time() - start_time
                print(f"✓ Search results loaded after extended wait ({elapsed:.1f}s)")
                time.sleep(3)  # Longer stabilization wait for slow loads
            except:
                elapsed = time.time() - start_time
                print(f"❌ Search results failed to load after {elapsed:.1f}s")
                raise Exception("Search results did not appear within timeout")

        # [2] Locate the correct role container using existing_role_code
        role_containers = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(@id, 'resList:') and contains(@class, 'xjb')]")
            )
        )
        print(f"🔎 Found {len(role_containers)} role containers")
        correct_container = None
        for container in role_containers:
            try:
                name_element = container.find_element(
                    By.XPATH, ".//tr[td//label[text()='Name']]/td[2]//span"
                )
                code_element = container.find_element(
                    By.XPATH, ".//tr[td//label[text()='Code']]/td[2]"
                )
            except Exception as inner_e:
                print(f"⚠️ Skipping container due to missing elements: {inner_e}")
                continue
            if name_element.text.strip() == existing_role_name and code_element.text.strip() == existing_role_code:
                print(f"✅ Found correct role: Name='{name_element.text.strip()}', Code='{code_element.text.strip()}'")
                correct_container = container
                break
        if not correct_container:
            raise Exception(f"❌ No matching role found for name '{existing_role_name}' with code '{existing_role_code}'.")

        # [3] Open Actions menu
        actions_btn = correct_container.find_element(
            By.XPATH, ".//button[contains(@id, 'cb1') and @title='Actions']"
        )
        ActionChains(driver).move_to_element(actions_btn).pause(0.5).click().perform()
        print("✓ Actions menu opened for the correct role")

        # [4] Select "Edit Role" from dropdown
        edit_option = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//tr[@id='_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:resList:0:cmiEdit']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", edit_option)
        print("✓ Edit Role selected")

        # [5] Navigate through steps with robust train navigation
        initial_step = get_current_step_number(driver)
        print(f"📍 Starting navigation from step {initial_step}")
        
        for step in range(3):
            current_step = get_current_step_number(driver)
            target_step = current_step + 1
            
            print(f"🔄 Navigating from step {current_step} to step {target_step} (iteration {step+1}/3)")
            
            # Click Next button with robust navigation detection
            if click_next_button(driver, instance=step+1):
                # Verify we actually moved to the next step
                final_step = get_current_step_number(driver)
                if final_step >= target_step:
                    print(f"✓ Step {step+1} completed successfully (now at step {final_step})")
                else:
                    raise Exception(f"Navigation verification failed: clicked Next but still at step {final_step}, expected {target_step}")
            else:
                raise Exception(f"Failed to click Next button for step {step+1}")

        # [5.5] CRITICAL: Verify we're on Role Hierarchy (Step 4) before duty role operations
        current_step = get_current_step_number(driver)
        if current_step != 4:
            print(f"⚠️ Navigation issue detected: Currently on Step {current_step}, need Step 4 (Role Hierarchy)")
            
            # Attempt recovery navigation
            if current_step < 4:
                print(f"🔄 Attempting to navigate forward from Step {current_step} to Step 4...")
                steps_needed = 4 - current_step
                for i in range(steps_needed):
                    try:
                        if click_next_button(driver, instance=f"recovery_{i+1}"):
                            recovery_step = get_current_step_number(driver)
                            print(f"✓ Recovery navigation {i+1}/{steps_needed}: now at Step {recovery_step}")
                        else:
                            raise Exception(f"Recovery navigation failed at step {i+1}")
                    except Exception as e:
                        raise Exception(f"❌ Recovery navigation failed: {str(e)}")
                
                # Verify recovery was successful
                final_step = get_current_step_number(driver)
                if final_step != 4:
                    raise Exception(f"❌ Recovery failed: Expected Step 4, still at Step {final_step}")
                print(f"✅ Recovery successful: Now on Role Hierarchy (Step 4)")
            else:
                raise Exception(f"❌ WRONG PAGE: Currently on Step {current_step} (past Role Hierarchy). Cannot recover - need to restart role editing process.")
        else:
            print(f"✅ Verified: Currently on Role Hierarchy (Step 4) - proceeding with duty role operations")

        # [6] Click on "Add Role Membership" button (main page)
        add_role_btn = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:4:rhSp1:rhtv:_ATp:addRole"),
            (By.XPATH, "//div[contains(@id, 'addRole')]"),
            (By.XPATH, "//div[contains(@title, 'Add Role Membership')]"),
            (By.XPATH, "//div[contains(@class, 'xeq') and contains(@title, 'Add Role Membership')]")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", add_role_btn)
        print("✓ 'Add Role Membership' button clicked")

        # [7] Wait for the duty role pop-up to appear
        popup_container = find_element_robust(driver, [
            (By.XPATH, "//div[contains(@class, 'AFPopupSelector') and contains(@id, 'rhSrchPu::popup-container')]"),
            (By.XPATH, "//div[contains(@id, 'rhSrchPu::popup-container')]"),
            (By.XPATH, "//div[@class='AFPopupSelector'][contains(@id, 'rhSrchPu')]")
        ], timeout=10, condition=EC.visibility_of_element_located)
        print("✓ Duty role pop-up appeared")

        # [8] In the pop-up, input the duty role name and press Enter
        duty_search_input = find_element_robust(driver, [
            (By.XPATH, "//input[contains(@id, 'rhSrcBx::content')]"),
            (By.XPATH, "//input[contains(@id, 'rhSrcBx')]"),
            (By.XPATH, "//input[@placeholder='Enter 3 or more characters to search']"),
            (By.XPATH, "//input[@aria-label='Search']")
        ], timeout=10, condition=EC.visibility_of_element_located)
        duty_search_input.clear()
        duty_search_input.send_keys(duty_role_name)
        duty_search_input.send_keys(Keys.RETURN)
        print("✓ Duty role search initiated")

        # [9] Locate the correct duty role container using duty_role_code
        duty_role_containers = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@id, 'rhRsLst') and contains(@class, 'xjb')]"))
        )
        print(f"🔎 Found {len(duty_role_containers)} duty role containers")
        
        # Find the correct duty role by matching name and code
        correct_duty_role_code = None
        for i, container in enumerate(duty_role_containers):
            try:
                duty_name_element = container.find_element(
                    By.XPATH, ".//tr[td//label[text()='Name']]/td[2]//span"
                )
                duty_code_element = container.find_element(
                    By.XPATH, ".//tr[td//label[text()='Code']]/td[2]"
                )
            except Exception as inner_e:
                print(f"⚠️ Skipping duty container due to missing elements: {inner_e}")
                continue
            if duty_name_element.text.strip() == duty_role_name and duty_code_element.text.strip() == duty_role_code:
                print(f"✅ Found correct duty role: Name='{duty_name_element.text.strip()}', Code='{duty_code_element.text.strip()}'")
                correct_duty_role_code = duty_code_element.text.strip()
                break
        if not correct_duty_role_code:
            raise Exception(f"❌ No matching duty role found for name '{duty_role_name}' with code '{duty_role_code}'.")

        # Re-acquire the element reference to avoid stale element issues
        time.sleep(2)  # Wait for DOM to stabilize
        correct_duty_container = find_element_robust(driver, [
            (By.XPATH, f"//div[contains(@id, 'rhRsLst') and contains(@class, 'xjb')]//tr[td//label[text()='Code']]/td[2][normalize-space()='{correct_duty_role_code}']/ancestor::div[contains(@class, 'xjb')]"),
            (By.XPATH, f"//div[contains(@id, 'rhRsLst') and contains(@class, 'xjb')]//span[normalize-space()='{duty_role_name}']/ancestor::div[contains(@class, 'xjb')]"),
            (By.XPATH, f"//div[contains(@id, 'rhRsLst') and contains(@class, 'xjb')]//td[normalize-space()='{correct_duty_role_code}']/ancestor::div[contains(@class, 'xjb')]")
        ], timeout=10)
        
        # Scroll to the element and click it
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", correct_duty_container)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", correct_duty_container)
        print("✓ Duty role container clicked")

        # [10] Click on "Add Role Membership" button inside the pop-up
        add_membership_btn = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:4:rhSp1:rhSrAdd"),
            (By.XPATH, "//button[contains(@id, 'rhSrAdd')]"),
            (By.XPATH, "//button[contains(., 'Add Role Membership')]"),
            (By.XPATH, "//button[@title='Add Role Membership']")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", add_membership_btn)
        print("✓ 'Add Role Membership' action confirmed")
        
        # CRITICAL: Give Oracle more time to process the ADD operation (especially for remote execution)
        time.sleep(5)  # Increased from 2 to 5 seconds for remote stability
        print("🔄 Closing Add Role Membership popup after processing time...")
        
        try:
            # Close the popup after adequate processing time
            close_btn = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:4:rhSp1:d1::close"),
                (By.XPATH, "//a[contains(@id, 'd1::close')]"),
                (By.XPATH, "//a[@title='Close']"),
                (By.XPATH, "//div[contains(@id, 'rhSrchPu::popup-container')]//a[contains(@id, '::close')]")
            ], timeout=15)  # Increased timeout for remote execution
            driver.execute_script("arguments[0].click();", close_btn)
            print("✓ Add Role Membership popup closed after processing")
            time.sleep(3)  # Increased from 2 to 3 seconds for popup closure
        except Exception as close_error:
            print(f"⚠️ Failed to close popup immediately: {str(close_error)}")
        
        # VERIFICATION: Check if the ADD operation was successful before proceeding
        print("🔍 Verifying duty role was added successfully...")
        try:
            # Wait a bit more for Oracle to update the display
            time.sleep(2)
            
            # Try to refresh or re-check the role hierarchy to confirm addition
            # This helps ensure Oracle has processed the change before navigation
            verification_elements = driver.find_elements(By.XPATH, f"//span[contains(text(), '{duty_role_name}')]")
            if verification_elements:
                print(f"✅ Verification: Found duty role '{duty_role_name}' in role hierarchy")
            else:
                print(f"⚠️ Verification: Could not immediately verify duty role '{duty_role_name}' was added")
        except Exception as verify_error:
            print(f"⚠️ Verification step failed: {str(verify_error)}")
        
        # NOW check for Oracle warning/error popups after add attempt
        has_popup, popup_message, popup_type = check_for_oracle_popup_messages(driver, "duty role addition")
        
        if has_popup:
            # Handle Oracle business rule warnings/errors
            print(f"🔔 Oracle {popup_type} encountered: {popup_message}")
            
            # Dismiss the popup
            dismiss_success = dismiss_oracle_popup(driver, popup_type)
            if dismiss_success:
                print("✓ Oracle popup dismissed successfully")
            else:
                print("⚠️ Oracle popup could not be dismissed automatically")
            
            # Raise an exception with the Oracle message so it gets captured in the results
            if popup_type == "warning":
                raise Exception(f"Oracle Warning: {popup_message}")
            elif popup_type == "error":
                raise Exception(f"Oracle Error: {popup_message}")
            else:
                raise Exception(f"Oracle Message ({popup_type}): {popup_message}")

        # [11] Popup already closed immediately after adding - no need to close again
        print("✓ Popup was already closed immediately after adding duty role")
        
        # SIMPLE: Close any remaining popups before navigation
        try:
            time.sleep(2)  # Brief pause for popup to close
            remaining_popups = driver.find_elements(By.CSS_SELECTOR, "div.AFPopupSelector")
            if remaining_popups:
                print("⚠️ Closing remaining popups before navigation...")
                dismiss_oracle_popup(driver, "pre-navigation")
                time.sleep(1)
        except:
            pass  # Continue even if popup closure fails

        # [12] Navigate through final steps with robust train navigation
        initial_step = get_current_step_number(driver)
        print(f"📍 Starting final navigation from step {initial_step}")
        
        for step in range(2):
            current_step = get_current_step_number(driver)
            target_step = current_step + 1
            
            print(f"🔄 Navigating from step {current_step} to step {target_step} (final iteration {step+1}/2)")
            
            # Click Next button with robust navigation detection
            if click_next_button(driver, instance=step+1):
                # Verify we actually moved to the next step
                final_step = get_current_step_number(driver)
                if final_step >= target_step:
                    print(f"✓ Final step {step+1} completed successfully (now at step {final_step})")
                else:
                    raise Exception(f"Navigation verification failed: clicked Next but still at step {final_step}, expected {target_step}")
            else:
                raise Exception(f"Failed to click Next button for final step {step+1}")

        # [13] Click Save and Close and handle confirmation
        save_button = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"),
            (By.XPATH, "//button[contains(@id, 'cb1') and contains(., 'Save')]"),
            (By.XPATH, "//button[contains(., 'Save')]")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", save_button)
        time.sleep(3)
        
        # Wait for confirmation popup and get message
        confirmation_popup = find_element_robust(driver, [
            (By.CSS_SELECTOR, "div.AFPopupSelector[id*='_FOd1::popup-container']"),
            (By.CSS_SELECTOR, "div.AFPopupSelector")
        ], timeout=10, condition=EC.visibility_of_element_located)
        
        confirmation_message = find_element_robust(driver, [
            (By.CSS_SELECTOR, "div.x1mu"),
            (By.CSS_SELECTOR, "div.x1mw"),
            (By.XPATH, "//div[contains(@class, 'x1mu') or contains(@class, 'x1mw')]")
        ], timeout=10, condition=EC.visibility_of_element_located).text
        print(f"✅ Confirmation Message: {confirmation_message}")
        time.sleep(3)
        
        ok_button = find_element_robust(driver, [
            (By.ID, "_FOd1::msgDlg::cancel"),
            (By.XPATH, "//button[contains(., 'OK')]"),
            (By.XPATH, "//button[@_afrpdo='cancel']")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", ok_button)
        print("✓ Save and Close confirmed")
        
        # CRITICAL: Wait for popup to fully close and navigate back to main page
        time.sleep(3)  # Allow popup to close completely
        
        # Check if we're still on role editing page and navigate back
        try:
            # If we're still in role editing, we need to cancel/close out
            cancel_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Cancel') or contains(@title, 'Cancel')]")
            if cancel_buttons:
                print("⚠️ Still on role editing page - clicking Cancel to return to main page")
                for cancel_btn in cancel_buttons[:2]:  # Try first 2 cancel buttons
                    try:
                        if cancel_btn.is_displayed() and cancel_btn.is_enabled():
                            driver.execute_script("arguments[0].click();", cancel_btn)
                            time.sleep(2)
                            print("✓ Clicked Cancel to exit role editing")
                            break
                    except:
                        continue
        except Exception as nav_error:
            print(f"⚠️ Navigation cleanup failed: {str(nav_error)}")
        
        # Force return to main page
        print("🔄 Ensuring return to main Security Console page...")
        driver.get(SECURITY_CONSOLE_URL)
        time.sleep(3)
        print("✅ Returned to main page")

        print("✅ Duty role membership addition completed successfully")
        return confirmation_message

    except Exception as e:
        print("💥 Critical failure during duty role addition:", e)
        raise
    finally:
        print("🛑 Cleanup completed for duty role addition, returning control to main process.")

# --------------------------------------------------------------------
# Function to delete a duty role (for Action = 'DELETE')
# --------------------------------------------------------------------
def delete_duty_role(driver, existing_role_name, existing_role_code, duty_role_code):
    try:
        # [1] Search for existing role to edit with optimized timing (same as in add_duty_role)
        search_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content"))
        )
        search_input.clear()
        driver.execute_script("arguments[0].value='';", search_input)
        time.sleep(1)
        search_input.send_keys(existing_role_name)
        time.sleep(1)  # Brief pause to let Oracle register the input
        
        # PRESS ENTER to trigger the search
        search_input.send_keys(Keys.RETURN)
        
        # Smart wait for search results - check if results appear quickly
        print("⏰ Waiting for search results...")
        start_time = time.time()
        
        # Use a shorter initial timeout with polling
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
            )
            elapsed = time.time() - start_time
            print(f"✓ Search results loaded quickly ({elapsed:.1f}s)")
            time.sleep(1)  # Short stabilization wait
        except:
            # If not loaded quickly, wait longer
            print("⏰ Search taking longer, extending wait...")
            try:
                WebDriverWait(driver, 25).until(
                    EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
                )
                elapsed = time.time() - start_time
                print(f"✓ Search results loaded after extended wait ({elapsed:.1f}s)")
                time.sleep(3)  # Longer stabilization wait for slow loads
            except:
                elapsed = time.time() - start_time
                print(f"❌ Search results failed to load after {elapsed:.1f}s")
                raise Exception("Search results did not appear within timeout")

        # [2] Locate the correct role container using existing_role_code
        role_containers = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@id, 'resList:') and contains(@class, 'xjb')]"))
        )
        print(f"🔎 Found {len(role_containers)} role containers")
        correct_container = None
        for container in role_containers:
            try:
                name_element = container.find_element(By.XPATH, ".//tr[td//label[text()='Name']]/td[2]//span")
                code_element = container.find_element(By.XPATH, ".//tr[td//label[text()='Code']]/td[2]")
            except Exception as inner_e:
                print(f"⚠️ Skipping container due to missing elements: {inner_e}")
                continue
            if name_element.text.strip() == existing_role_name and code_element.text.strip() == existing_role_code:
                print(f"✅ Found correct role: Name='{name_element.text.strip()}', Code='{code_element.text.strip()}'")
                correct_container = container
                break
        if not correct_container:
            raise Exception(f"❌ No matching role found for name '{existing_role_name}' with code '{existing_role_code}'.")

        # [3] Open Actions menu
        actions_btn = correct_container.find_element(By.XPATH, ".//button[contains(@id, 'cb1') and @title='Actions']")
        ActionChains(driver).move_to_element(actions_btn).pause(0.5).click().perform()
        print("✓ Actions menu opened for the correct role")

        # [4] Select "Edit Role" from dropdown
        edit_option = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//tr[@id='_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:resList:0:cmiEdit']"))
        )
        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", edit_option)
        print("✓ Edit Role selected")

        # [5] Navigate through steps with robust train navigation
        initial_step = get_current_step_number(driver)
        print(f"📍 Starting navigation from step {initial_step}")
        
        for step in range(3):
            current_step = get_current_step_number(driver)
            target_step = current_step + 1
            
            print(f"🔄 Navigating from step {current_step} to step {target_step} (iteration {step+1}/3)")
            
            # Click Next button with robust navigation detection
            if click_next_button(driver, instance=step+1):
                # Verify we actually moved to the next step
                final_step = get_current_step_number(driver)
                if final_step >= target_step:
                    print(f"✓ Step {step+1} completed successfully (now at step {final_step})")
                else:
                    raise Exception(f"Navigation verification failed: clicked Next but still at step {final_step}, expected {target_step}")
            else:
                raise Exception(f"Failed to click Next button for step {step+1}")

        # [5.5D] CRITICAL: Verify we're on Role Hierarchy (Step 4) before duty role operations
        current_step = get_current_step_number(driver)
        if current_step != 4:
            print(f"⚠️ Navigation issue detected: Currently on Step {current_step}, need Step 4 (Role Hierarchy)")
            
            # Attempt recovery navigation
            if current_step < 4:
                print(f"🔄 Attempting to navigate forward from Step {current_step} to Step 4...")
                steps_needed = 4 - current_step
                for i in range(steps_needed):
                    try:
                        if click_next_button(driver, instance=f"recovery_{i+1}"):
                            recovery_step = get_current_step_number(driver)
                            print(f"✓ Recovery navigation {i+1}/{steps_needed}: now at Step {recovery_step}")
                        else:
                            raise Exception(f"Recovery navigation failed at step {i+1}")
                    except Exception as e:
                        raise Exception(f"❌ Recovery navigation failed: {str(e)}")
                
                # Verify recovery was successful
                final_step = get_current_step_number(driver)
                if final_step != 4:
                    raise Exception(f"❌ Recovery failed: Expected Step 4, still at Step {final_step}")
                print(f"✅ Recovery successful: Now on Role Hierarchy (Step 4)")
            else:
                raise Exception(f"❌ WRONG PAGE: Currently on Step {current_step} (past Role Hierarchy). Cannot recover - need to restart role editing process.")
        else:
            print(f"✅ Verified: Currently on Role Hierarchy (Step 4) - proceeding with duty role deletion")

        # [6D] Instead of clicking "Add Role Membership", input the duty role code to delete
        try:
            delete_input = find_element_robust(driver, [
                (By.XPATH, "//input[contains(@id, 'rhgrv:Ase2Ip::content')]"),
                (By.XPATH, "//input[contains(@id, 'Ase2Ip::content')]"),
                (By.XPATH, "//input[contains(@id, 'Ase2Ip')]"),
                (By.XPATH, "//input[@name='_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:4:rhSp1:rhtv:_ATp:rhgrv:Ase2Ip']")
            ], timeout=10, condition=EC.visibility_of_element_located)
            delete_input.clear()
            delete_input.send_keys(duty_role_code)
            delete_input.send_keys(Keys.RETURN)
            print("✓ Duty role delete search initiated")
            time.sleep(2)
        except Exception as e:
            print(f"🔴 Duty role delete input failed: {str(e)}")
            raise

        # [7D] Wait for the results table to appear and select the row with the matching duty role code
        try:
            # Wait for the table to be present first - optimized table detection (reduced from 7 to 3 selectors)
            table = find_element_robust(driver, [
                # Strategy 1: Most common - Oracle table classes
                (By.XPATH, "//table[contains(@class, 'x1hg') or contains(@class, 'x1hi')]"),
                # Strategy 2: ID-based (more specific)
                (By.XPATH, "//div[contains(@id, 'rhgrv')]//table"),
                # Strategy 3: Summary attribute fallback
                (By.XPATH, "//table[contains(@summary, 'Details') or contains(@id, 'rhgrv')]")
            ], timeout=8, condition=EC.presence_of_element_located)
            print("✓ Results table found")
            
            # Use optimized find_element_robust with 4 strategic selectors (reduced from 12)
            correct_duty_row = find_element_robust(driver, [
                # Strategy 1: Most specific - with table class and span (90% success rate)
                (By.XPATH, f"//table[contains(@class, 'x1hg') or contains(@class, 'x1hi')]//tr[td[2]//span[normalize-space(.)='{duty_role_code}']]"),
                # Strategy 2: Fallback without span (handles cases where span is missing)
                (By.XPATH, f"//table[contains(@class, 'x1hg') or contains(@class, 'x1hi')]//tr[td[2][normalize-space(.)='{duty_role_code}']]"),
                # Strategy 3: Generic without table class (handles dynamic table changes)
                (By.XPATH, f"//tr[td[2]//span[normalize-space(.)='{duty_role_code}']] | //tr[td[2][normalize-space(.)='{duty_role_code}']]"),
                # Strategy 4: Most permissive - contains text (last resort)
                (By.XPATH, f"//tr[td[2][contains(normalize-space(.), '{duty_role_code}')]]")
            ], timeout=8)
            
            # Scroll to the element and click it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", correct_duty_row)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", correct_duty_row)
            print("✓ Duty role row selected for deletion")
            time.sleep(3)
        except Exception as e:
            raise Exception(f"❌ No matching duty role row found for code '{duty_role_code}': {str(e)}")



        # [8D] Click the Delete button (main page)
        try:
            delete_btn = find_element_robust(driver, [
                (By.XPATH, "//div[contains(@id, 'dltrole')]"),
                (By.XPATH, "//div[contains(@id, 'rhtv:_ATp:dltrole')]"),
                (By.XPATH, "//div[contains(@title, 'Delete')]"),
                (By.XPATH, "//div[contains(@class, 'xeq') and contains(@title, 'Delete')]")
            ], timeout=10)
            driver.execute_script("arguments[0].click();", delete_btn)
            print("✓ Delete button clicked")
        except Exception as e:
            print(f"🔴 Delete button click failed: {str(e)}")
            raise

        # [9D] In the confirmation pop-up, click Yes
        try:
            yes_button = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:4:rhSp1:cb11"),
                (By.XPATH, "//button[contains(@id, 'cb11')]"),
                (By.XPATH, "//button[contains(., 'Yes')]"),
                (By.XPATH, "//button[@title='Yes']")
            ], timeout=10)
            driver.execute_script("arguments[0].click();", yes_button)
            print("✓ 'Yes' clicked in delete confirmation pop-up")
            
            # CRITICAL: Check for Oracle warning/error popups after delete attempt
            time.sleep(2)  # Give Oracle time to process and show any warnings
            has_popup, popup_message, popup_type = check_for_oracle_popup_messages(driver, "duty role deletion")
            
            if has_popup:
                # Handle Oracle business rule warnings/errors
                print(f"🔔 Oracle {popup_type} encountered: {popup_message}")
                
                # Dismiss the popup
                dismiss_success = dismiss_oracle_popup(driver, popup_type)
                if dismiss_success:
                    print("✓ Oracle popup dismissed successfully")
                else:
                    print("⚠️ Oracle popup could not be dismissed automatically")
                
                # Raise an exception with the Oracle message so it gets captured in the results
                if popup_type == "warning":
                    raise Exception(f"Oracle Warning: {popup_message}")
                elif popup_type == "error":
                    raise Exception(f"Oracle Error: {popup_message}")
                else:
                    raise Exception(f"Oracle Message ({popup_type}): {popup_message}")
            
        except Exception as e:
            # Check if this is an Oracle popup message exception (which we want to preserve)
            if "Oracle Warning:" in str(e) or "Oracle Error:" in str(e) or "Oracle Message:" in str(e):
                print(f"🔴 Duty role deletion failed due to Oracle business rule: {str(e)}")
                raise  # Re-raise to preserve the Oracle message
            else:
                print(f"🔴 Delete confirmation failed: {str(e)}")
                raise
        
        # SIMPLE: Close any remaining popups before navigation
        try:
            time.sleep(2)  # Brief pause for popup to close
            remaining_popups = driver.find_elements(By.CSS_SELECTOR, "div.AFPopupSelector")
            if remaining_popups:
                print("⚠️ Closing remaining popups before navigation...")
                dismiss_oracle_popup(driver, "pre-navigation")
                time.sleep(1)
        except:
            pass  # Continue even if popup closure fails

        # [10] Navigate through final steps with robust train navigation
        initial_step = get_current_step_number(driver)
        print(f"📍 Starting final navigation from step {initial_step}")
        
        for step in range(2):
            current_step = get_current_step_number(driver)
            target_step = current_step + 1
            
            print(f"🔄 Navigating from step {current_step} to step {target_step} (final iteration {step+1}/2)")
            
            # Click Next button with robust navigation detection
            if click_next_button(driver, instance=step+1):
                # Verify we actually moved to the next step
                final_step = get_current_step_number(driver)
                if final_step >= target_step:
                    print(f"✓ Final step {step+1} completed successfully (now at step {final_step})")
                else:
                    raise Exception(f"Navigation verification failed: clicked Next but still at step {final_step}, expected {target_step}")
            else:
                raise Exception(f"Failed to click Next button for final step {step+1}")

        # [11] Click Save and Close and handle confirmation
        save_button = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"),
            (By.XPATH, "//button[contains(@id, 'cb1') and contains(., 'Save')]"),
            (By.XPATH, "//button[contains(., 'Save')]")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", save_button)
        time.sleep(3)
        
        # Wait for confirmation popup and get message
        confirmation_popup = find_element_robust(driver, [
            (By.CSS_SELECTOR, "div.AFPopupSelector[id*='_FOd1::popup-container']"),
            (By.CSS_SELECTOR, "div.AFPopupSelector")
        ], timeout=10, condition=EC.visibility_of_element_located)
        
        confirmation_message = find_element_robust(driver, [
            (By.CSS_SELECTOR, "div.x1mu"),
            (By.CSS_SELECTOR, "div.x1mw"),
            (By.XPATH, "//div[contains(@class, 'x1mu') or contains(@class, 'x1mw')]")
        ], timeout=10, condition=EC.visibility_of_element_located).text
        print(f"✅ Confirmation Message: {confirmation_message}")
        time.sleep(3)
        
        ok_button = find_element_robust(driver, [
            (By.ID, "_FOd1::msgDlg::cancel"),
            (By.XPATH, "//button[contains(., 'OK')]"),
            (By.XPATH, "//button[@_afrpdo='cancel']")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", ok_button)
        print("✓ Save and Close confirmed")
        
        # CRITICAL: Wait for popup to fully close and navigate back to main page
        time.sleep(3)  # Allow popup to close completely
        
        # Check if we're still on role editing page and navigate back
        try:
            # If we're still in role editing, we need to cancel/close out
            cancel_buttons = driver.find_elements(By.XPATH, "//button[contains(., 'Cancel') or contains(@title, 'Cancel')]")
            if cancel_buttons:
                print("⚠️ Still on role editing page - clicking Cancel to return to main page")
                for cancel_btn in cancel_buttons[:2]:  # Try first 2 cancel buttons
                    try:
                        if cancel_btn.is_displayed() and cancel_btn.is_enabled():
                            driver.execute_script("arguments[0].click();", cancel_btn)
                            time.sleep(2)
                            print("✓ Clicked Cancel to exit role editing")
                            break
                    except:
                        continue
        except Exception as nav_error:
            print(f"⚠️ Navigation cleanup failed: {str(nav_error)}")
        
        # Force return to main page
        print("🔄 Ensuring return to main Security Console page...")
        driver.get(SECURITY_CONSOLE_URL)
        time.sleep(3)
        print("✅ Returned to main page")

        print("✅ Duty role deletion completed successfully")
        return confirmation_message

    except Exception as e:
        print("💥 Critical failure during duty role deletion:", e)
        raise
    finally:
        print("🛑 Cleanup completed for duty role deletion, returning control to main process.")

# --------------------------------------------------------------------
# Main execution code
# --------------------------------------------------------------------
def main():
    driver = None
    df = None
    try:
        # Read input Excel file with required columns
        # Get input file path from environment variable (set by Streamlit) or use default
        input_file = os.environ.get("INPUT_FILE_PATH", "duty_role_input.xlsx")
        required_columns = {
            'Existing Role Name to Edit',
            'Existing Role Code',
            'Duty Role Name',
            'Duty Role Code',
            'Action'  # New column: value should be "ADD" or "DELETE"
        }
        df = pd.read_excel(input_file)
        print(f"📖 Loaded Excel file '{input_file}' with {len(df)} records to process")
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        # Prepare results columns
        df['Confirmation Message'] = ''
        df['Status'] = 'Pending'
        df['Timestamp'] = ''
        df['Error Details'] = ''

        # Initialize browser and login
        driver = initialize_driver()
        driver.maximize_window()
        driver.get(SECURITY_CONSOLE_URL)
        print("🚀 Browser initialized")
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

        # Process each record
        for index, row in df.iterrows():
            current_status = 'Failed'
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[index, 'Timestamp'] = timestamp
            try:
                print(f"\n⏳ Processing row {index+1}/{len(df)} at {timestamp}")
                action = row['Action'].strip().upper()
                print(f"📝 Action: {action} for role '{row['Existing Role Name to Edit']}'")
                if action == "ADD":
                    confirmation = add_duty_role(
                        driver,
                        existing_role_name=row['Existing Role Name to Edit'],
                        existing_role_code=row['Existing Role Code'],
                        duty_role_name=row['Duty Role Name'],
                        duty_role_code=row['Duty Role Code']
                    )
                elif action == "DELETE":
                    confirmation = delete_duty_role(
                        driver,
                        existing_role_name=row['Existing Role Name to Edit'],
                        existing_role_code=row['Existing Role Code'],
                        duty_role_code=row['Duty Role Code']
                    )
                else:
                    raise Exception(f"Unsupported Action '{row['Action']}'. Expected 'ADD' or 'DELETE'.")
                df.at[index, 'Confirmation Message'] = confirmation
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
                        
            try:
                df.to_excel("duty_role_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")
            
            # Note: Page reset is now handled within add_duty_role/delete_duty_role functions
            # Browser state is reset above for failures via reset_browser_state()

        output_file = f"duty_role_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\n💾 Saved final results to '{output_file}'")

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        if df is not None:
            try:
                partial_file = f"duty_role_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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
