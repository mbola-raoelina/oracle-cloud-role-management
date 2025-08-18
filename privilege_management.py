import os
import sys
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
                    print(f"🔄 This may cause privilege operations to happen on wrong page!")
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



# ============================================================
# Function to add a privilege to a role (Action = "ADD")
# ============================================================
def add_privilege(driver, existing_role_name, existing_role_code, privilege_code):
    try:
        # [1] Search for the existing role to edit with optimized timing
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

        # [2] Locate the correct role container using name and code
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
        edit_option = find_element_robust(driver, [
            (By.XPATH, "//tr[contains(@id, 'cmiEdit')]"),
            (By.XPATH, "//tr[contains(., 'Edit Role')]"),
            (By.XPATH, "//a[contains(., 'Edit Role')]"),
            (By.XPATH, "//*[contains(text(), 'Edit Role')]")
        ], timeout=20)
        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", edit_option)
        print("✓ Edit Role selected")

        # [5] Click Next button 1 time (for privilege process)
        click_next_button(driver)
        print("✓ Next button clicked (1 time)")
        time.sleep(2)

        # [5.5] CRITICAL: Verify we're on Function Security Policies (Step 2) before privilege operations
        current_step = get_current_step_number(driver)
        if current_step != 2:
            print(f"⚠️ Navigation issue detected: Currently on Step {current_step}, need Step 2 (Function Security Policies)")
            
            # Attempt recovery navigation
            if current_step < 2:
                print(f"🔄 Attempting to navigate forward from Step {current_step} to Step 2...")
                steps_needed = 2 - current_step
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
                if final_step != 2:
                    raise Exception(f"❌ Recovery failed: Expected Step 2, still at Step {final_step}")
                print(f"✅ Recovery successful: Now on Function Security Policies (Step 2)")
            elif current_step == 1:
                # Special case: if we're still on Basic Information, click Next once more
                print(f"🔄 Still on Basic Information (Step 1), clicking Next to reach Step 2...")
                if click_next_button(driver, instance="recovery_to_step2"):
                    final_step = get_current_step_number(driver)
                    if final_step != 2:
                        raise Exception(f"❌ Failed to reach Step 2, currently at Step {final_step}")
                    print(f"✅ Successfully navigated to Function Security Policies (Step 2)")
                else:
                    raise Exception(f"❌ Failed to navigate from Step 1 to Step 2")
            else:
                raise Exception(f"❌ WRONG PAGE: Currently on Step {current_step} (past Function Security Policies). Cannot recover - need to restart role editing process.")
        else:
            print(f"✅ Verified: Currently on Function Security Policies (Step 2) - proceeding with privilege operations")

        # [6] Click "Add Function Security Policy" button (privilege add)
        add_priv_btn = find_element_robust(driver, [
            (By.XPATH, "//div[contains(@id, 'ctb1')]"),
            (By.XPATH, "//*[contains(., 'Add Function Security Policy')]"),
            (By.XPATH, "//button[contains(., 'Add Function Security Policy')]"),
            (By.XPATH, "//a[contains(., 'Add Function Security Policy')]")
        ], timeout=20)
        add_priv_btn.click()
        print("✓ 'Add Function Security Policy' button clicked")

        # [7] In the pop-up, enter the privilege code in the input and press Enter
        priv_search_input = find_element_robust(driver, [
            (By.XPATH, "//input[contains(@id, 'fsSrcBx::content')]"),
            (By.XPATH, "//input[contains(@id, 'search')]"),
            (By.XPATH, "//input[@placeholder*='search' or @placeholder*='Search']"),
            (By.XPATH, "//input[contains(@class, 'search')]")
        ], timeout=20, condition=EC.visibility_of_element_located)
        priv_search_input.clear()
        priv_search_input.send_keys(privilege_code)
        time.sleep(2)
        priv_search_input.send_keys(Keys.RETURN)
        time.sleep(1)
        priv_search_input.send_keys(Keys.RETURN)
        # Find and click the search button explicitly
        # search_button = driver.find_element(By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:0:fsSp1:cil1")
        # search_button.click()

        time.sleep(2)
        print("✓ Privilege search initiated in pop-up")

        # # [8] Wait for the pop-up results table and click the row with an exact match
        # try:
        #     xpath_expr = f"//table[contains(@class, 'x1hi')]//tr[td[2]//span[normalize-space(text())='{privilege_code}']]"
        #     correct_priv_row = WebDriverWait(driver, 20).until(
        #         EC.element_to_be_clickable((By.XPATH, xpath_expr))
        #     )
        #     correct_priv_row.click()
        #     print("✓ Privilege row selected in pop-up")
        # except Exception as e:
        #     raise Exception(f"❌ No matching privilege row found for code '{privilege_code}': {str(e)}")
        
        # [7D] Locate the correct privilege container in the pop-up using a similar approach as step [2]
        try:
            # Wait for all privilege containers in the pop-up to be present.
            priv_containers = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@id, 'fsSp1:fsRsLst') and contains(@class, 'xjb')]")
                )
            )
            print(f"🔎 Found {len(priv_containers)} privilege containers in pop-up")
            
            correct_priv_container = None
            for container in priv_containers:
                try:
                    # Locate the "Code" cell inside the container
                    code_element = container.find_element(
                        By.XPATH, ".//tr[td//label[text()='Code']]/td[2]"
                    )
                except Exception as inner_e:
                    print(f"⚠️ Skipping container due to missing 'Code' element: {inner_e}")
                    continue

                if code_element.text.strip() == privilege_code:
                    print(f"✅ Found privilege container with Code '{code_element.text.strip()}'")
                    correct_priv_container = container
                    break

            if not correct_priv_container:
                raise Exception(f"❌ No matching privilege container found for code '{privilege_code}'.")

            # Scroll into view and click the container
            driver.execute_script("arguments[0].scrollIntoView(true);", correct_priv_container)
            time.sleep(1)
            correct_priv_container.click()
            print("✓ Privilege container selected in pop-up")
        except Exception as e:
            raise Exception(f"❌ Privilege container selection failed: {str(e)}")


        # [9] Click on "Add Privilege to Role" button in the pop-up
        add_privilege_btn = find_element_robust(driver, [
            (By.XPATH, "//button[contains(@id, 'fsPAdd')]"),
            (By.XPATH, "//button[contains(., 'Add Privilege to Role')]"),
            (By.XPATH, "//*[contains(., 'Add Privilege to Role')]")
        ], timeout=20)
        add_privilege_btn.click()
        time.sleep(2)
        print("✓ 'Add Privilege to Role' action confirmed")

        # [10] Close the pop-up - using specific selectors based on the actual HTML structure
        try:
            close_btn = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:2:fsSp1:d1::close"),
                (By.XPATH, "//div[contains(@id, 'srchPu::popup-container')]//a[contains(@id, '::close')]"),
                (By.XPATH, "//a[contains(@id, 'd1::close')]"),
                (By.XPATH, "//a[contains(@id, '::close')]"),
                (By.XPATH, "//a[@title='Close']"),
                (By.XPATH, "//*[contains(@class, 'close')]"),
                (By.XPATH, "//a[contains(., 'Close')]")
            ], timeout=20)
            close_btn.click()
            print("✓ Close button clicked")
        except Exception as e:
            print(f"⚠️ Close button not found, trying Cancel button instead: {str(e)}")
            # Fallback to Cancel button
            cancel_btn = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:2:fsSp1:fsSrCan"),
                (By.XPATH, "//button[contains(@id, 'fsSrCan')]"),
                (By.XPATH, "//button[contains(., 'Cancel')]"),
                (By.XPATH, "//button[@title='Cancel']")
            ], timeout=10)
            cancel_btn.click()
            print("✓ Cancel button clicked as fallback")
        time.sleep(2)
        print("✓ Privilege pop-up closed")

        # [11] Navigate through steps with robust train navigation
        initial_step = get_current_step_number(driver)
        print(f"📍 Starting navigation from step {initial_step}")
        
        for step in range(4):
            current_step = get_current_step_number(driver)
            target_step = current_step + 1
            
            print(f"🔄 Navigating from step {current_step} to step {target_step} (iteration {step+1}/4)")
            
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

        # [12] Click Save and Close and handle confirmation
        save_button = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"),
            (By.XPATH, "//button[contains(@id, 'cb1')]"),
            (By.XPATH, "//button[contains(., 'Save')]"),
            (By.XPATH, "//button[contains(., 'Save and Close')]")
        ], timeout=20)
        save_button.click()
        time.sleep(3)
        
        # Wait for confirmation popup and handle it with exact selectors from HTML
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector[id*='_FOd1::popup-container']"))
        )
        
        # Get confirmation message using the exact selector from HTML
        confirmation_message = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x1mu"))
        ).text
        print(f"✅ Confirmation Message: {confirmation_message}")
        time.sleep(3)
        
        # Click OK button using the exact ID from HTML
        ok_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "_FOd1::msgDlg::cancel"))
        )
        ok_button.click()
        print("✓ Save and Close confirmed")

        print("✅ Privilege addition completed successfully")
        return confirmation_message

    except Exception as e:
        print("💥 Critical failure during privilege addition:", e)
        raise
    finally:
        print("🛑 Cleanup completed for privilege addition, returning control to main process.")

# ============================================================
# Function to delete a privilege from a role (Action = "DELETE")
# ============================================================
def delete_privilegeOLD(driver, existing_role_name, existing_role_code, privilege_code):
    
        # [1] Search for existing role to edit (same as in add_privilege)
        search_input = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content"))
        )
        search_input.clear()
        driver.execute_script("arguments[0].value='';", search_input)
        time.sleep(1)
        search_input.send_keys(existing_role_name)
        search_input.send_keys(Keys.RETURN)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
        )
        print("✓ Search results loaded")

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

        # [5] Click Next button 1 time
        click_next_button(driver)
        print("✓ Next button clicked (1 time)")
        time.sleep(2)

        # [6D] Instead of entering the privilege code, click on the container/row whose first cell (Name) matches the provided privilege name.
        try:
            # Wait for the container that holds the function security policy rows in the pop-up to be visible.
            policy_container = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//div[contains(@id, 'fsSp1:atPol') and contains(@id, '::db')]")
                )
            )
            print("✓ Function Security Policy container visible")
            
            # Build a dynamic XPath that locates the row within the container where the first <td> (the Name cell) 
            # has text that exactly matches the provided privilege name.
            xpath_expr = f".//table[contains(@class, 'x1hi')]//tr[td[1][normalize-space(.)='{privilege_name}']]"
            
            correct_priv_row = policy_container.find_element(By.XPATH, xpath_expr)
            driver.execute_script("arguments[0].scrollIntoView(true);", correct_priv_row)
            time.sleep(1)
            correct_priv_row.click()
            print(f"✓ Privilege container row with matching name '{privilege_name}' selected for deletion")
            time.sleep(1)
        except Exception as e:
            raise Exception(f"❌ Failed to select privilege container for deletion by name '{privilege_name}': {str(e)}")


        # # [7D] Wait for the results table to appear and select the row with matching privilege code
        # try:
        #     xpath_expr = f"//table[contains(@class, 'x1hi')]//tr[td[2]//span[normalize-space(text())='{privilege_code}']]"
        #     correct_priv_row = WebDriverWait(driver, 20).until(
        #         EC.element_to_be_clickable((By.XPATH, xpath_expr))
        #     )
        #     correct_priv_row.click()
        #     print("✓ Privilege row selected for deletion")
        # except Exception as e:
        #     raise Exception(f"❌ No matching privilege row found for code '{privilege_code}': {str(e)}")
        # [8D] After selecting the correct privilege row, wait a moment and then click on the Delete button
        try:
            time.sleep(1)  # small pause before clicking delete
            delete_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@id='_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:2:fsSp1:atPol:_ATp:dltPolicy']")
                )
            )
            delete_btn.click()
            print("✓ Delete button clicked for privilege")
        except Exception as e:
            raise Exception(f"❌ Delete button click failed: {str(e)}")

        # [9D] In the confirmation pop-up, click the Yes button
        try:
            yes_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@id='_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:2:fsSp1:cb5']")
                )
            )
            yes_button.click()
            print("✓ 'Yes' clicked in delete confirmation pop-up")
        except Exception as e:
            raise Exception(f"❌ Delete confirmation failed: {str(e)}")

        # [10] Click Next button 4 times on the main page
        try:
            for step in range(4):
                click_next_button(driver)
                print(f"✓ Next step {step+1} completed")
                time.sleep(2)
        except Exception as e:
            raise Exception(f"❌ Next button click failed at step {step+1}: {str(e)}")

        # [11] Click Save and Close and handle confirmation
        try:
            save_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable(
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1")
                )
            )
            save_button.click()
            time.sleep(3)
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector"))
            )
            confirmation_message = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x1mw"))
            ).text
            print(f"✅ Confirmation Message: {confirmation_message}")
            time.sleep(3)
            ok_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'OK')]"))
            )
            ok_button.click()
            print("✓ Save and Close confirmed")
        except Exception as e:
            raise Exception(f"❌ Save and Close failed: {str(e)}")





 #============================================================
# Function to delete a privilege from a role (Action = "DELETE")
# ============================================================
def delete_privilege(driver, existing_role_name, existing_role_code, privilege_code, privilege_name):
    try:
        # [1] Search for the existing role to edit with optimized timing
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

        # [5] Click Next button 1 time
        click_next_button(driver)
        print("✓ Next button clicked (1 time)")
        time.sleep(2)

        # [5.5D] CRITICAL: Verify we're on Function Security Policies (Step 2) before privilege operations
        current_step = get_current_step_number(driver)
        if current_step != 2:
            print(f"⚠️ Navigation issue detected: Currently on Step {current_step}, need Step 2 (Function Security Policies)")
            
            # Attempt recovery navigation
            if current_step < 2:
                print(f"🔄 Attempting to navigate forward from Step {current_step} to Step 2...")
                steps_needed = 2 - current_step
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
                if final_step != 2:
                    raise Exception(f"❌ Recovery failed: Expected Step 2, still at Step {final_step}")
                print(f"✅ Recovery successful: Now on Function Security Policies (Step 2)")
            elif current_step == 1:
                # Special case: if we're still on Basic Information, click Next once more
                print(f"🔄 Still on Basic Information (Step 1), clicking Next to reach Step 2...")
                if click_next_button(driver, instance="recovery_to_step2"):
                    final_step = get_current_step_number(driver)
                    if final_step != 2:
                        raise Exception(f"❌ Failed to reach Step 2, currently at Step {final_step}")
                    print(f"✅ Successfully navigated to Function Security Policies (Step 2)")
                else:
                    raise Exception(f"❌ Failed to navigate from Step 1 to Step 2")
            else:
                raise Exception(f"❌ WRONG PAGE: Currently on Step {current_step} (past Function Security Policies). Cannot recover - need to restart role editing process.")
        else:
            print(f"✅ Verified: Currently on Function Security Policies (Step 2) - proceeding with privilege deletion")

        # [6D] Select the privilege to delete based on privilege name in the existing privileges table
        try:
            # Wait for the table that contains existing privileges to be visible
            # Based on the HTML structure, we need to target the table with class 'x1hg' inside the container
            policy_table = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located(
                    (By.XPATH, "//table[contains(@class, 'x1hg') and @summary='Function Security Policies']")
                )
            )
            print("✓ Function Security Policies table visible")
            
            # Build an XPath that locates the row where the first cell (Privilege Name column) matches the privilege name
            # The table has 3 columns: Privilege Name, Inherited from Role, Description
            xpath_expr = f".//tr[td[1][normalize-space(.)='{privilege_name}']]"
            
            correct_priv_row = policy_table.find_element(By.XPATH, xpath_expr)
            driver.execute_script("arguments[0].scrollIntoView(true);", correct_priv_row)
            time.sleep(1)
            correct_priv_row.click()
            print(f"✓ Privilege row with name '{privilege_name}' selected for deletion")
            time.sleep(2)
        except Exception as e:
            raise Exception(f"❌ Failed to select privilege row for deletion by name '{privilege_name}': {str(e)}")

        # [7D] Click on the Delete button for privileges
        delete_btn = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:2:fsSp1:atPol:_ATp:dltPolicy"),
            (By.XPATH, "//div[contains(@id, 'dltPolicy')]"),
            (By.XPATH, "//*[contains(., 'Delete')]"),
            (By.XPATH, "//button[contains(., 'Delete')]")
        ], timeout=10)
        
        # Click the delete button
        driver.execute_script("arguments[0].click();", delete_btn)
        time.sleep(2)
        print("✓ Delete button clicked for privilege")

        # [8D] In the confirmation pop-up, click the Yes button
        yes_button = find_element_robust(driver, [
            (By.XPATH, "//button[@id='_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:2:fsSp1:cb5']"),
            (By.XPATH, "//button[contains(@id, 'cb5')]"),
            (By.XPATH, "//button[contains(., 'Yes')]"),
            (By.XPATH, "//button[text()='Yes']")
        ], timeout=20)
        yes_button.click()
        print("✓ 'Yes' clicked in delete confirmation pop-up")

        # [9] Navigate through steps with robust train navigation
        initial_step = get_current_step_number(driver)
        print(f"📍 Starting navigation from step {initial_step}")
        
        for step in range(4):
            current_step = get_current_step_number(driver)
            target_step = current_step + 1
            
            print(f"🔄 Navigating from step {current_step} to step {target_step} (iteration {step+1}/4)")
            
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

        # [10] Click Save and Close and handle confirmation
        save_button = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"),
            (By.XPATH, "//button[contains(@id, 'cb1')]"),
            (By.XPATH, "//button[contains(., 'Save')]"),
            (By.XPATH, "//button[contains(., 'Save and Close')]")
        ], timeout=20)
        save_button.click()
        time.sleep(3)
        
        # Wait for confirmation popup and handle it with exact selectors from HTML
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector[id*='_FOd1::popup-container']"))
        )
        
        # Get confirmation message using the exact selector from HTML
        confirmation_message = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x1mu"))
        ).text
        print(f"✅ Confirmation Message: {confirmation_message}")
        time.sleep(3)
        
        # Click OK button using the exact ID from HTML
        ok_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "_FOd1::msgDlg::cancel"))
        )
        ok_button.click()
        print("✓ Save and Close confirmed")

        print("✅ Privilege deletion completed successfully")
        return confirmation_message

    except Exception as e:
        print("💥 Critical failure during privilege deletion:", e)
        raise
    finally:
        print("🛑 Cleanup completed for privilege deletion, returning control to main process.")


# ============================================================
# Main execution code
# ============================================================
def main():
    driver = None
    df = None
    try:
        # Read input Excel file with required columns
        # Get input file path from environment variable (set by Streamlit) or use default
        input_file = os.environ.get("INPUT_FILE_PATH", "privilege_input.xlsx")
        required_columns = {
                    'Existing Role Name to Edit',
                    'Existing Role Code',
                    'Privilege Code',
                    'Privilege Name',
                    'Action'  # Expected values: "ADD" or "DELETE"
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

        # Initialize browser and log in
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

        # Process each record from the Excel file
        for index, row in df.iterrows():
            current_status = 'Failed'
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[index, 'Timestamp'] = timestamp
            try:
                print(f"\n⏳ Processing row {index+1}/{len(df)} at {timestamp}")
                action = row['Action'].strip().upper()
                print(f"📝 Action: {action} for role '{row['Existing Role Name to Edit']}' with privilege code '{row['Privilege Code']}'")
                if action == "ADD":
                    confirmation = add_privilege(
                        driver,
                        existing_role_name=row['Existing Role Name to Edit'],
                        existing_role_code=row['Existing Role Code'],
                        privilege_code=row['Privilege Code']
                    )
                elif action == "DELETE":
                    confirmation = delete_privilege(
                        driver,
                        existing_role_name=row['Existing Role Name to Edit'],
                        existing_role_code=row['Existing Role Code'],
                        privilege_code=row['Privilege Code'],
                        privilege_name=row['Privilege Name']
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
                df.to_excel("privilege_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")
            
            # Reset to main page after each row (success or failure)
            if current_status == 'Success':
                driver.get(SECURITY_CONSOLE_URL)
                time.sleep(2)
            # Note: Browser state is already reset above for failures

        output_file = f"privilege_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(output_file, index=False)
        print(f"\n💾 Saved final results to '{output_file}'")

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        if df is not None:
            try:
                partial_file = f"privilege_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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
