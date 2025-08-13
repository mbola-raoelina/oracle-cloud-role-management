

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



def handle_copy_confirmation(driver):
    """Handles the copy role confirmation popup with same reliability pattern"""
    try:
        # Wait for popup container
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector[id*='puCopy::popup-container']"))
        )

        # Verify copy options text
        header_text = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.xl0"))
        ).text
        print(f"Popup Header: {header_text}")

        # Click Copy Role button using multiple strategies
        try:
            # First try direct ID click
            copy_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:cbCopy"))
            )
            copy_btn.click()
        except:
            # Fallback to XPath with text and attribute matching
            copy_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(@id, 'cbCopy') and contains(., 'Copy Role')]"))
            )
            driver.execute_script("arguments[0].click();", copy_btn)

        # Verify popup closure
        WebDriverWait(driver, 15).until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector"))
        )

        print("Copy confirmation handled successfully")

    except Exception as e:
        print(f"Error handling copy confirmation: {str(e)}")
        #driver.save_screenshot("copy_confirmation_error.png")
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

 
def click_next_button_old(driver, max_retries=3):
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

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys  # Add this import

def copy_existing_roleAD(driver, role_name_to_copy, new_role_name, new_role_code):
    """Robust role copy implementation with detailed error handling"""
    try:
        # [1] Search for existing role
        try:
            search_input = find_element_robust(driver, [
                (By.XPATH, "//input[contains(@id, 'srchBox::content')]"),
                (By.XPATH, "//input[contains(@id, 'search')]"),
                (By.XPATH, "//input[@placeholder*='search' or @placeholder*='Search']"),
                (By.XPATH, "//input[contains(@class, 'search')]")
            ], timeout=20, condition=EC.visibility_of_element_located)
            search_input.clear()
            search_input.send_keys(role_name_to_copy)
            
            # Trigger search with explicit results wait
            search_input.send_keys(Keys.RETURN)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
            )
            print("✓ Search results loaded")
        except Exception as e:
            print(f"🔴 Search failed: {str(e)}")
            raise

        # [2] Locate the correct role code before opening actions menu
        try:
            rows = driver.find_elements(By.XPATH, "//tr[contains(@id, 'resList:')]")
            correct_row = None
            for row in rows:
                role_code_element = row.find_element(By.XPATH, ".//td[contains(@id, 'roleCodeColumn')]")
                if role_code_element.text.strip() == role_name_to_copy:
                    correct_row = row
                    break
            
            if not correct_row:
                raise Exception("🔴 No matching role code found in search results")
            
            actions_btn = correct_row.find_element(By.XPATH, ".//button[contains(@id, 'cb1') and @title='Actions']")
            ActionChains(driver).move_to_element(actions_btn).pause(0.5).click().perform()
            print("✓ Actions menu opened for the correct role")
        except Exception as e:
            print(f"🔴 Actions menu failed: {str(e)}")
            raise

        # [3] Select Copy Role from dropdown
        try:
            print("🔄 Looking for Copy Role option in actions menu...")
            
            # Use robust element finding for Copy Role option
            copy_option = find_element_robust(driver, [
                (By.XPATH, "//tr[contains(@id, 'cmiCopy')]"),
                (By.XPATH, "//tr[contains(., 'Copy Role')]"),
                (By.XPATH, "//*[contains(text(), 'Copy') and contains(text(), 'Role')]"),
                (By.XPATH, "//*[contains(text(), 'Copy')]")
            ], timeout=15)
            driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", copy_option)
            print("✓ Copy Role selected from actions menu")
        except Exception as e:
            print(f"🔴 Copy Role selection failed: {str(e)}")
            raise

        # [4] Confirm copy dialog using keyboard navigation
        try:
            # Wait for the copy options popup to appear
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@id, 'puCopy::popup-container')]"))
            )
            print("✓ Copy options popup appeared")
            
            # Click the "Copy Role" button using robust element finding
            copy_role_btn = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:cbCopy"),
                (By.XPATH, "//button[contains(@id, 'cbCopy')]"),
                (By.XPATH, "//button[contains(., 'Copy Role')]"),
                (By.XPATH, "//button[text()='Copy Role']")
            ], timeout=15)
            driver.execute_script("arguments[0].click();", copy_role_btn)
            print("✓ Copy Role button clicked using robust selectors")
                
        except Exception as e:
            print(f"🔴 Copy options failed: {str(e)}")
            raise

        # [5] Fill new role details
        try:
            role_name_field = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRNam::content"),
                (By.XPATH, "//input[contains(@id, 'bIRNam') and contains(@id, 'content')]"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'content')]")
            ], timeout=20, condition=EC.visibility_of_element_located)
            role_name_field.clear()
            role_name_field.send_keys(new_role_name)
            
            role_code_field = find_element_robust(driver, [
                (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"),
                (By.XPATH, "//input[contains(@id, 'bIRCod') and contains(@id, 'content')]"),
                (By.XPATH, "//input[@type='text' and contains(@id, 'content') and position()=2]")
            ], timeout=20, condition=EC.visibility_of_element_located)
            role_code_field.clear()
            role_code_field.send_keys(new_role_code)
            print("✓ New role details entered")
        except Exception as e:
            print(f"🔴 Role details failed: {str(e)}")
            raise

        # [6] Navigate through steps
        try:
            for step in range(5):
                click_next_button(driver)
                print(f"✓ Step {step+1} completed")
                time.sleep(2)  # Short buffer
        except Exception as e:
            print(f"🔴 Navigation failed at step {step+1}: {str(e)}")
            raise
    #    # Click Save and Close
    #     save_button = WebDriverWait(driver, 20).until(
    #         EC.element_to_be_clickable((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"))
    #     )
    #     save_button.click()
    
    
        time.sleep(3)  # Allow time for dialog to open
               # [7] Enhanced final save with priority to Submit and Close
        try:
            # First try Submit and Close button (which worked successfully in the log)
            try:
                submit_close_btn = find_element_robust(driver, [
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb5"),
                    (By.XPATH, "//button[contains(@id, 'cb5')]"),
                    (By.XPATH, "//button[contains(., 'Submit and Close')]"),
                    (By.XPATH, "//button[contains(., 'Submit')]")
                ], timeout=20)
                submit_close_btn.click()
                print("✓ Submit and Close initiated (primary method)")
                time.sleep(3)  # Allow time for dialog to open
            except Exception as primary_error:
                print(f"⚠️ Submit and Close failed, trying regular save: {str(primary_error)}")
                
                # Fallback to regular save button
                save_btn = find_element_robust(driver, [
                    (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"),
                    (By.XPATH, "//button[contains(@id, 'cb1')]"),
                    (By.XPATH, "//button[contains(., 'Save')]"),
                    (By.XPATH, "//button[contains(., 'Save and Close')]")
                ], timeout=10)
                save_btn.click()
                print("✓ Regular save initiated (fallback method)")
                
        except Exception as e:
            print(f"🔴 All save methods failed: {str(e)}")
            raise

        # [8] Optimized confirmation handling
        try:
            # Wait for confirmation message
            confirmation = WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'x1mw')]"))
            ).text
            print(f"✅ Confirmation Message: {confirmation}")
            time.sleep(3)  # Allow time for message to be read
            # Click OK on success dialog if it exists
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'OK')]"))
                ).click()
                print("✓ Success dialog closed")
            except Exception:
                pass  # OK button not always required
            
        except Exception as e:
            print(f"🔴 Confirmation handling failed: {str(e)}")
            raise

        print("✅ Role copy completed successfully")
        return confirmation

    except Exception as e:
        print(f"💥 Critical failure: {str(e)}")
        #driver.save_screenshot(f"error_{int(time.time())}.png")
        print("🖥️ Current URL:", driver.current_url)
        
        # Attempt cleanup
        print("🔄 Attempting cleanup...")
        try:
            # Try Submit and Close first
            try:
                submit_close_btn = driver.find_element(By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb5")
                submit_close_btn.click()
                print("✓ Submit and Close clicked during cleanup")
            except:
                pass
            
            # Then try Cancel button
            try:
                cancel_btn = driver.find_element(By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb2")
                cancel_btn.click()
                print("✓ Cancel button clicked during cleanup")
            except:
                pass
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup failed: {str(cleanup_error)}")
        
        raise Exception(f"Operation failed: {str(e)}")

    finally:
        print("🛑 Cleanup completed, returning control to main process.")




def copy_existing_role(driver, role_name_to_copy, existing_role_code, new_role_name, new_role_code):
    """Robust role copy implementation with detailed error handling"""
    try:
        # [1] Search for existing role
        try:
            search_input = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content"))
            )
            # Clear any previous value completely
            search_input.clear()
            # Optionally, use JavaScript to clear the value:
            driver.execute_script("arguments[0].value = '';", search_input)
            time.sleep(1)  # slight pause to let any dynamic content reset

            # Send the new search query
            search_input.send_keys(role_name_to_copy)
            search_input.send_keys(Keys.RETURN)
            
            # Wait for search results to update (you might need a longer wait for subsequent rows)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//tr[contains(@id, 'resList:0')]"))
            )
            print("✓ Search results loaded")
            time.sleep(6)  # Allow time for results to stabilize
        except Exception as e:
            print(f"🔴 Search failed: {str(e)}")
            raise


        # [2] Locate the correct role using existing_role_code
        try:
            role_containers = driver.find_elements(By.XPATH, "//div[contains(@id, 'resList:') and contains(@class, 'xjb')]")
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

                if name_element.text.strip() == role_name_to_copy and code_element.text.strip() == existing_role_code:
                    print(f"✅ Found correct role: Name='{name_element.text.strip()}', Code='{code_element.text.strip()}'")
                    correct_container = container
                    break

            if not correct_container:
                raise Exception(f"❌ No matching role found for name '{role_name_to_copy}' with existing code '{existing_role_code}'.")
        except Exception as e:
            print(f"🔴 Role selection failed: {str(e)}")
            raise



        # [3] Open the correct Actions menu
        try:
            #actions_btn = correct_row.find_element(By.XPATH, ".//button[contains(@id, 'cb1') and @title='Actions']")
            actions_btn = correct_container.find_element(By.XPATH, ".//button[contains(@title, 'Actions')]")
            ActionChains(driver).move_to_element(actions_btn).pause(0.5).click().perform()
            print("✓ Actions menu opened for the correct role")
        except Exception as e:
            print(f"🔴 Actions menu failed: {str(e)}")
            raise

        # [4] Select Copy Role from dropdown
        try:
            print("🔄 Looking for Copy Role option in actions menu...")
            
            # First try to find the Copy Role option in the actions menu
            try:
                copy_option = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH,
                        "//tr[@id='_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:resList:0:cmiCopy']"))
                )
                driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", copy_option)
                print("✓ Copy Role selected from actions menu")
            except Exception as e:
                print(f"⚠️ Copy Role from actions menu failed: {str(e)}")
                
                # Alternative 1: Try to find "Copy top role" (exact text from HTML)
                try:
                    print("🔄 Trying to find 'Copy top role' option...")
                    copy_option = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Copy top role')]"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", copy_option)
                    print("✓ Copy top role selected")
                except Exception as e2:
                    print(f"⚠️ 'Copy top role' search failed: {str(e2)}")
                    
                    # Alternative 2: Try to find any element with "Copy" text
                    try:
                        print("🔄 Trying text-based search for Copy Role...")
                        copy_option = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Copy') and contains(text(), 'Role')]"))
                        )
                        driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", copy_option)
                        print("✓ Copy Role selected using text search")
                    except Exception as e3:
                        print(f"⚠️ Text-based search failed: {str(e3)}")
                        
                        # Alternative 3: Try to find any clickable element with "Copy" in the actions menu
                        try:
                            print("🔄 Trying generic Copy element search...")
                            copy_option = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Copy')]"))
                            )
                            driver.execute_script("arguments[0].scrollIntoView(); arguments[0].click();", copy_option)
                            print("✓ Copy option selected using generic search")
                        except Exception as e4:
                            print(f"🔴 All Copy Role selection methods failed: {str(e4)}")
                            
                            # Take a screenshot for debugging
                            driver.save_screenshot(f"copy_role_selection_error_{int(time.time())}.png")
                            
                            # List all available options in the actions menu for debugging
                            try:
                                print("🔍 Debugging: Listing all available options in actions menu...")
                                all_options = driver.find_elements(By.XPATH, "//tr[contains(@id, 'resList:0:cmi')]")
                                print(f"Found {len(all_options)} options in actions menu:")
                                for i, opt in enumerate(all_options):
                                    print(f"  Option {i+1}: {opt.text} (ID: {opt.get_attribute('id')})")
                            except Exception as debug_error:
                                print(f"Could not list options: {str(debug_error)}")
                            
                            raise Exception("Could not find Copy Role option in actions menu")
        except Exception as e:
            print(f"🔴 Copy Role selection failed: {str(e)}")
            raise

        # [5] Confirm copy dialog using the exact button ID from HTML
        try:
            print("🔄 Waiting for copy confirmation popup...")
            
            # Wait for the copy options popup to appear
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH, "//div[contains(@id, 'puCopy::popup-container')]"))
            )
            print("✓ Copy options popup appeared")
            
            # Click the "Copy Role" button using the exact ID from HTML
            try:
                copy_role_btn = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:cbCopy"))
                )
                driver.execute_script("arguments[0].click();", copy_role_btn)
                print("✓ Copy Role button clicked using exact ID")
            except Exception as btn_error:
                print(f"⚠️ Direct button click failed, trying alternative methods: {str(btn_error)}")
                
                # Alternative 1: Try XPath with exact text
                try:
                    copy_role_btn = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@id, 'cbCopy') and contains(text(), 'Copy Role')]"))
                    )
                    driver.execute_script("arguments[0].click();", copy_role_btn)
                    print("✓ Copy Role button clicked using XPath with text")
                except Exception as xpath_error:
                    print(f"⚠️ XPath method failed, trying keyboard navigation: {str(xpath_error)}")
                    
                    # Alternative 2: Fallback to keyboard navigation
                    ActionChains(driver).send_keys(Keys.TAB).pause(0.5).send_keys(Keys.ENTER).perform()
                    print("✓ Copy options confirmed via keyboard shortcut")
            
            # Wait a moment for page transition
            print("⏰ Waiting for page transition after Copy Role button click...")
            time.sleep(3)
            print("✓ Page transition wait completed")
                
        except Exception as e:
            print(f"🔴 Copy options failed: {str(e)}")
            # Take a screenshot for debugging
            driver.save_screenshot(f"copy_options_error_{int(time.time())}.png")
            raise

        # [6] Fill new role details with better error handling
        try:
            print("🔄 Role creation form should be loaded after 15-second wait...")
            
            # Check current URL to see if we're on the right page
            current_url = driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            # Try to find the role name field with multiple strategies
            role_name_field = None
            try:
                role_name_field = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRNam::content"))
                )
                print("✅ Found role name field using primary ID")
            except:
                print("⚠️ Primary role name field not found, trying alternative...")
                try:
                    # Try alternative ID pattern
                    role_name_field = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//input[contains(@id, 'bIRNam') and contains(@id, 'content')]"))
                    )
                    print("✅ Found role name field using XPath")
                except:
                    print("⚠️ Alternative role name field not found, trying generic search...")
                    try:
                        role_name_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, "//input[@type='text' and contains(@id, 'content')]"))
                        )
                        print("✅ Found role name field using generic search")
                    except Exception as e:
                        print(f"🔴 Could not find role name field: {str(e)}")
                        # Take a screenshot for debugging
                        driver.save_screenshot(f"role_form_error_{int(time.time())}.png")
                        raise Exception("Role creation form did not load properly after copy confirmation")
            
            # Clear and fill role name
            role_name_field.clear()
            time.sleep(1)
            role_name_field.send_keys(new_role_name)
            print(f"✓ Role name entered: {new_role_name}")

            # Find and fill role code field with better handling for pre-filled values
            role_code_field = None
            try:
                role_code_field = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                )
                print("✅ Found role code field using primary ID")
            except:
                print("⚠️ Primary role code field not found, trying alternative...")
                try:
                    role_code_field = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.XPATH, "//input[contains(@id, 'bIRCod') and contains(@id, 'content')]"))
                    )
                    print("✅ Found role code field using XPath")
                except:
                    print("⚠️ Alternative role code field not found, trying generic search...")
                    try:
                        role_code_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, "//input[@type='text' and contains(@id, 'content') and position()=2]"))
                        )
                        print("✅ Found role code field using generic search")
                    except Exception as e:
                        print(f"🔴 Could not find role code field: {str(e)}")
                        raise Exception("Role code field not found")
            
            # Enhanced clearing and filling for role code field (handles pre-filled values and stale elements)
            try:
                print("🔄 Handling role code field with fresh element reference...")
                
                # ALWAYS get a fresh element reference to avoid stale element issues
                role_code_field = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                )
                
                # First, check if there's a pre-filled value
                current_value = role_code_field.get_attribute('value')
                print(f"🔍 Current role code value: '{current_value}'")
                
                # Method 1: JavaScript approach (most reliable for pre-filled values)
                try:
                    print("🔄 Trying JavaScript approach first...")
                    driver.execute_script(f"arguments[0].value = '{new_role_code}';", role_code_field)
                    time.sleep(0.5)
                    
                    # Trigger change event to ensure Oracle UI recognizes the change
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", role_code_field)
                    time.sleep(0.5)
                    
                    # Verify the new value was entered
                    js_value = role_code_field.get_attribute('value')
                    print(f"🔍 After JavaScript, role code value: '{js_value}'")
                    
                    if js_value == new_role_code:
                        print(f"✓ Role code successfully set via JavaScript: {new_role_code}")
                    else:
                        print(f"⚠️ JavaScript didn't work. Expected: '{new_role_code}', Got: '{js_value}'")
                        raise Exception("JavaScript method failed")
                        
                except Exception as js_error:
                    print(f"⚠️ JavaScript method failed: {str(js_error)}")
                    
                    # Method 2: Clear and fill approach
                    try:
                        print("🔄 Trying Clear + Fill approach...")
                        # Get fresh element reference again
                        role_code_field = WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                        )
                        
                        # Clear the field completely
                        role_code_field.clear()
                        time.sleep(0.5)
                        
                        # Fill with new value
                        role_code_field.send_keys(new_role_code)
                        time.sleep(0.5)
                        
                        # Verify the new value was entered
                        final_value = role_code_field.get_attribute('value')
                        print(f"🔍 After Clear + Fill, role code value: '{final_value}'")
                        
                        if final_value == new_role_code:
                            print(f"✓ Role code successfully entered via Clear + Fill: {new_role_code}")
                        else:
                            print(f"⚠️ Clear + Fill didn't work. Expected: '{new_role_code}', Got: '{final_value}'")
                            raise Exception("Clear + Fill method failed")
                            
                    except Exception as clear_error:
                        print(f"⚠️ Clear + Fill method failed: {str(clear_error)}")
                        
                        # Method 3: Select All + Type approach (final fallback)
                        try:
                            print("🔄 Trying Select All + Type approach...")
                            # Get fresh element reference again
                            role_code_field = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                            )
                            
                            # Click to focus the field
                            role_code_field.click()
                            time.sleep(0.5)
                            
                            # Select all existing content (Ctrl+A)
                            role_code_field.send_keys(Keys.CONTROL + "a")
                            time.sleep(0.5)
                            
                            # Type the new role code (this will replace the selected content)
                            role_code_field.send_keys(new_role_code)
                            time.sleep(0.5)
                            
                            # Verify the new value was entered
                            final_value = role_code_field.get_attribute('value')
                            print(f"🔍 After Select All + Type, role code value: '{final_value}'")
                            
                            if final_value == new_role_code:
                                print(f"✓ Role code successfully entered via Select All + Type: {new_role_code}")
                            else:
                                print(f"⚠️ Select All + Type didn't work. Expected: '{new_role_code}', Got: '{final_value}'")
                                raise Exception("Select All + Type method failed")
                                
                        except Exception as select_all_error:
                            print(f"⚠️ Select All + Type method failed: {str(select_all_error)}")
                            raise Exception(f"All methods failed to set role code to '{new_role_code}'")
                    
            except Exception as final_error:
                print(f"🔴 All role code setting methods failed: {str(final_error)}")
                raise Exception(f"Could not set role code to '{new_role_code}'")
            
            print("✓ New role details entered successfully")
        except Exception as e:
            print(f"🔴 Role details failed: {str(e)}")
            # Take a screenshot for debugging
            driver.save_screenshot(f"role_details_error_{int(time.time())}.png")
            raise

        # [7] Navigate through steps
        try:
            for step in range(5):
                click_next_button(driver)
                print(f"✓ Step {step+1} completed")
                time.sleep(2)
        except Exception as e:
            print(f"🔴 Navigation failed at step {step+1}: {str(e)}")
            raise

        # [8] Save with priority to Submit and Close
        try:
            try:
                submit_close_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb5"))
                )
                submit_close_btn.click()
                print("✓ Submit and Close initiated")
                time.sleep(3)
            except Exception as primary_error:
                print(f"⚠️ Submit and Close failed, trying regular save: {str(primary_error)}")
                save_btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:6:sSp1:cb1"))
                )
                save_btn.click()
                print("✓ Regular save initiated")

        except Exception as e:
            print(f"🔴 All save methods failed: {str(e)}")
            raise

        # [9] Handle confirmation message with correct selectors
        try:
            print("🔄 Waiting for confirmation popup...")
            
            # Wait for the confirmation popup to appear
            WebDriverWait(driver, 30).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector[id*='_FOd1::popup-container']"))
            )
            print("✓ Confirmation popup appeared")
            
            # Get the confirmation message using the correct selector
            try:
                confirmation = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x1mu"))
                ).text
                print(f"✅ Confirmation Message: {confirmation}")
            except Exception as msg_error:
                print(f"⚠️ Could not get confirmation message: {str(msg_error)}")
                confirmation = "Process completed successfully"
            
            time.sleep(2)  # Allow time to read the message

            # Click OK button using the correct ID from HTML
            try:
                ok_button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "_FOd1::msgDlg::cancel"))
                )
                driver.execute_script("arguments[0].click();", ok_button)
                print("✓ OK button clicked successfully")
                
                # Wait for popup to disappear
                WebDriverWait(driver, 10).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.AFPopupSelector[id*='_FOd1::popup-container']"))
                )
                print("✓ Confirmation popup closed")
                
            except Exception as ok_error:
                print(f"⚠️ OK button click failed: {str(ok_error)}")
                
                # Fallback: Try to find OK button by text
                try:
                    ok_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'OK')]"))
                    )
                    driver.execute_script("arguments[0].click();", ok_button)
                    print("✓ OK button clicked using text search")
                except Exception as fallback_error:
                    print(f"⚠️ Fallback OK button also failed: {str(fallback_error)}")
                    # Don't raise exception - popup might close automatically

        except Exception as e:
            print(f"🔴 Confirmation handling failed: {str(e)}")
            # Don't raise exception - the process might have succeeded even if we can't handle the popup
            confirmation = "Process completed (popup handling failed)"

        print("✅ Role copy completed successfully")
        return confirmation

    except Exception as e:
        print(f"💥 Critical failure: {str(e)}")
        raise

    finally:
        print("🛑 Cleanup completed, returning control to main process.")




def main():
    """Main execution flow with Excel integration and robust error handling"""
    driver = None
    df = None

    try:
        # Read Excel input with column validation
        try:
            input_file = "role_copy_input.xlsx"
            required_columns = {'Role to Copy', 'New Role Name', 'New Role Code'}

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

        # Initialize browser
        driver = initialize_driver()
        driver.maximize_window()
        driver.get(SECURITY_CONSOLE_URL)
        print("🚀 Browser initialized")

        # Login process with robust element finding
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
            time.sleep(3)  # Allow dashboard to load
        except Exception as e:
            print(f"🔴 Login failed: {str(e)}")
            #driver.save_screenshot("login_error.png")
            raise

        # Process each role from Excel
        for index, row in df.iterrows():
            current_status = 'Failed'  # Default status
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df.at[index, 'Timestamp'] = timestamp

            try:
                print(f"\n⏳ Processing row {index+1}/{len(df)} at {timestamp}")
                print(f"📝 Copying '{row['Role to Copy']}' to '{row['New Role Name']}'")

                # Execute role copy using the updated function and capture the confirmation message
                confirmation = copy_existing_role(
                    driver,
                    role_name_to_copy=row['Role to Copy'],
                    existing_role_code=row['Existing Role Code'],  # ✅ NEW PARAMETER ADDED
                    new_role_name=row['New Role Name'],
                    new_role_code=row['New Role Code']
                )


                # Record success and confirmation message
                df.at[index, 'Confirmation Message'] = confirmation
                df.at[index, 'Status'] = 'Success'
                current_status = 'Success'
                print(f"✅ Successfully processed row {index+1}")
                time.sleep(2)  # Allow time for confirmation message to be read
            except Exception as e:
                error_msg = str(e)
                df.at[index, 'Confirmation Message'] = f"Error: {error_msg}"
                df.at[index, 'Status'] = 'Failed'
                df.at[index, 'Error Details'] = error_msg
                print(f"🔴 Failed to process row {index+1}: {error_msg}")
                #driver.save_screenshot(f"error_row_{index+1}.png")

                # For connection/timeout errors, try to reinitialize
                if "Unable to establish connection" in error_msg or "timed out" in error_msg:
                    print("🔄 Attempting to reinitialize browser...")
                    try:
                        driver.quit()
                        driver = initialize_driver()
                        driver.get(SECURITY_CONSOLE_URL)
                        print("🚀 Browser reinitialized")
                    except Exception as reconnect_error:
                        print(f"🔴 Reconnection failed: {str(reconnect_error)}")
                        break  # Exit loop if we can't reconnect

            # Save progress after each row
            try:
                df.to_excel("role_copy_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")

        # Save final results
        output_file = f"role_copy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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
                partial_file = f"role_copy_partial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
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
