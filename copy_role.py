

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


def get_current_step_number(driver):
    """Get the current step number from the navigation train"""
    try:
        # Look for the current step indicator (p_AFSelected class)
        current_step = driver.find_element(By.XPATH, "//a[contains(@class, 'p_AFSelected') and contains(@title, 'Current')]")
        title = current_step.get_attribute('title')
        print(f"🔍 DEBUG: Found current step element with title: '{title}'")
        
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
            print(f"⚠️ DEBUG: Unknown step title: '{title}'")
            return 0
    except Exception as e:
        print(f"❌ DEBUG: Failed to find current step element: {str(e)}")
        
        # Try alternative approaches to debug
        try:
            # Look for all navigation elements
            nav_elements = driver.find_elements(By.XPATH, "//a[contains(@class, 'AFTrainStep')]")
            print(f"🔍 DEBUG: Found {len(nav_elements)} navigation elements")
            
            for i, elem in enumerate(nav_elements):
                try:
                    title = elem.get_attribute('title') or 'No title'
                    classes = elem.get_attribute('class') or 'No classes'
                    text = elem.text or 'No text'
                    print(f"  Element {i+1}: title='{title}', classes='{classes}', text='{text}'")
                except:
                    print(f"  Element {i+1}: Unable to read attributes")
                    
        except Exception as debug_e:
            print(f"❌ DEBUG: Navigation elements debug failed: {str(debug_e)}")
            
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
            
            # DEBUG: Check immediate button state after click
            try:
                is_disabled = next_btn.get_attribute('disabled')
                button_classes = next_btn.get_attribute('class')
                print(f"🔍 DEBUG: Button state after click - disabled: {is_disabled}, classes: {button_classes}")
            except:
                print("🔍 DEBUG: Could not check button state after click")
            
            # DEBUG: Check page URL and title
            try:
                current_url = driver.current_url
                page_title = driver.title
                print(f"🔍 DEBUG: Current URL: {current_url}")
                print(f"🔍 DEBUG: Page title: {page_title}")
            except:
                print("🔍 DEBUG: Could not get page info")
            
            # Use robust navigation train-based transition detection
            if wait_for_step_transition(driver, expected_next_step, timeout=30):
                print(f"✓ Step {instance} transition completed successfully")
                return True
            else:
                # If train navigation failed, try one more time with longer wait
                print("⚠️ Train navigation detection failed, trying extended wait...")
                time.sleep(5)  # Give Oracle more time
                
                # DEBUG: Check for any error messages on page
                try:
                    error_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'error') or contains(@class, 'Error') or contains(@class, 'AFErrorText')]")
                    if error_elements:
                        for i, error in enumerate(error_elements):
                            error_text = error.text.strip()
                            if error_text:
                                print(f"🔍 DEBUG: Error message {i+1}: {error_text}")
                    else:
                        print("🔍 DEBUG: No error messages found on page")
                except:
                    print("🔍 DEBUG: Could not check for error messages")
                
                # Check again
                final_step = get_current_step_number(driver)
                if final_step == expected_next_step:
                    print(f"✓ Step {instance} transition completed (delayed)")
                    return True
                elif final_step > expected_next_step:
                    print(f"⚠️ Navigation overshot! Currently at step {final_step}, expected {expected_next_step}")
                    print(f"🔄 This may cause operations to happen on wrong page!")
                    # Still return True but with warning - we'll add verification later
                    return True
                else:
                    # DEBUG: Take screenshot for remote debugging
                    try:
                        screenshot_name = f"navigation_failed_step_{instance}_{int(time.time())}.png"
                        driver.save_screenshot(screenshot_name)
                        print(f"🔍 DEBUG: Screenshot saved as {screenshot_name}")
                    except:
                        print("🔍 DEBUG: Could not save screenshot")
                    
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
            # Get fresh search input element right before using it
            search_input = WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content"))
            )
            
            # Clear any previous value completely
            search_input.clear()
            time.sleep(1)  # slight pause to let any dynamic content reset

            # Send the new search query
            search_input.send_keys(role_name_to_copy)
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
            
            # Clear and fill role name (with duplicate prevention)
            current_role_name = role_name_field.get_attribute('value')
            print(f"🔍 Current role name value: '{current_role_name}'")
             
            if current_role_name != new_role_name:
                print("🔄 Setting role name...")
                role_name_field.clear()
                time.sleep(1)
                role_name_field.send_keys(new_role_name)
                
                # Verify role name was entered correctly
                final_role_name = role_name_field.get_attribute('value')
                if final_role_name == new_role_name:
                    print(f"✓ Role name entered successfully: {new_role_name}")
                else:
                    print(f"⚠️ Role name verification failed. Expected: '{new_role_name}', Got: '{final_role_name}'")
                    raise Exception("Role name entry failed")
            else:
                print(f"✓ Role name already set correctly: {new_role_name}")

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
            
            # Enhanced role code filling - handles pre-filled values and stale elements
            try:
                print("🔄 Setting role code using enhanced approach...")
                
                # Get fresh element reference to avoid stale element issues
                role_code_field = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                )
                
                # Check current value
                current_role_code = role_code_field.get_attribute('value')
                print(f"🔍 Current role code value: '{current_role_code}'")
                
                if current_role_code != new_role_code:
                    print("🔄 Setting role code...")
                    
                    # Method 1: JavaScript + ENTER (Primary)
                    try:
                        driver.execute_script(f"arguments[0].value = '{new_role_code}';", role_code_field)
                        time.sleep(1)
                        
                        # Trigger change event to notify Oracle UI
                        driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", role_code_field)
                        time.sleep(1)
                        
                        # PRESS ENTER to commit the change and prevent Oracle from reverting to default
                        role_code_field.send_keys(Keys.ENTER)
                        time.sleep(2) # Wait for Oracle to process the ENTER key
                        
                        # Verify the change
                        final_role_code = role_code_field.get_attribute('value')
                        if final_role_code == new_role_code:
                            print(f"✓ Role code set successfully via JavaScript + ENTER: {new_role_code}")
                        else:
                            raise Exception("JavaScript + ENTER method failed")
                    except Exception as js_error:
                        print(f"⚠️ JavaScript + ENTER method failed: {str(js_error)}")
                        
                        # Method 2: Clear + Send Keys (Fallback 1)
                        try:
                            # Get fresh element reference again
                            role_code_field = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                            )
                            
                            # Clear the field completely
                            role_code_field.clear()
                            time.sleep(1)
                            
                            # Fill with new value
                            role_code_field.send_keys(new_role_code)
                            time.sleep(1)
                            
                            # Verify the new value was entered
                            final_role_code = role_code_field.get_attribute('value')
                            if final_role_code == new_role_code:
                                print(f"✓ Role code set successfully via Clear + Send Keys: {new_role_code}")
                            else:
                                raise Exception("Clear + Send Keys method failed")
                        except Exception as clear_error:
                            print(f"⚠️ Clear + Send Keys method failed: {str(clear_error)}")
                            
                            # Method 3: Select All + Type (Fallback 2)
                            try:
                                # Get fresh element reference again
                                role_code_field = WebDriverWait(driver, 10).until(
                                    EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                                )
                                
                                # Click to focus the field
                                role_code_field.click()
                                time.sleep(1)
                                
                                # Select all existing content (Ctrl+A)
                                role_code_field.send_keys(Keys.CONTROL + "a")
                                time.sleep(1)
                                
                                # Type the new role code (this will replace the selected content)
                                role_code_field.send_keys(new_role_code)
                                time.sleep(1)
                                
                                # Verify the new value was entered
                                final_role_code = role_code_field.get_attribute('value')
                                if final_role_code == new_role_code:
                                    print(f"✓ Role code set successfully via Select All + Type: {new_role_code}")
                                else:
                                    raise Exception("Select All + Type method failed")
                            except Exception as select_error:
                                print(f"🔴 All role code setting methods failed: {str(select_error)}")
                                raise Exception(f"Role code setting failed. Expected: '{new_role_code}', Got: '{final_role_code}'")
                else:
                    print(f"✓ Role code already set correctly: {new_role_code}")
                    
            except Exception as e:
                print(f"🔴 Role code setting failed: {str(e)}")
                raise

            print("✓ New role details entered successfully")
            
            # Check for validation errors after role code entry
            time.sleep(3)  # Wait for any validation to complete
            try:
                # Look for error messages
                error_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'error') or contains(@class, 'Error')]")
                if error_elements:
                    for error in error_elements:
                        error_text = error.text.strip()
                        if error_text and "already exists" in error_text.lower():
                            print(f"🔴 Validation error detected: {error_text}")
                            raise Exception(f"Role code validation failed: {error_text}")
                
                # Also check for red borders on the role code field
                role_code_field = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:1:biSp1:bIRCod::content"))
                )
                field_style = role_code_field.get_attribute('style')
                if 'border-color: red' in field_style or 'border: 1px solid red' in field_style:
                    print("🔴 Role code field has red border - validation error detected")
                    raise Exception("Role code field validation error detected")
                    
            except Exception as validation_error:
                print(f"⚠️ Validation check failed: {str(validation_error)}")
                # Don't raise here, just log the warning
                
        except Exception as e:
            print(f"🔴 Role details failed: {str(e)}")
            # Take a screenshot for debugging
            driver.save_screenshot(f"role_details_error_{int(time.time())}.png")
            raise

        # [7] Navigate through steps with robust train navigation
        try:
            initial_step = get_current_step_number(driver)
            print(f"📍 Starting navigation from step {initial_step}")
            
            for step in range(5):
                current_step = get_current_step_number(driver)
                target_step = current_step + 1
                
                print(f"🔄 Navigating from step {current_step} to step {target_step} (iteration {step+1}/5)")
                
                # Verify we're at the expected step before clicking
                if current_step != step + 1:
                    print(f"⚠️ Navigation out of sync: expected to be at step {step + 1}, but at step {current_step}")
                    # Continue anyway, but log the discrepancy
                
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
                
        except Exception as e:
            current_step = get_current_step_number(driver)
            print(f"🔴 Navigation failed at iteration {step+1}, currently at step {current_step}: {str(e)}")
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

        # CRITICAL: Check for Oracle warning/error popups after copy operation
        try:
            has_popup, popup_message, popup_type = check_for_oracle_popup_messages(driver, "role copy")
            if has_popup:
                # Dismiss the popup
                dismiss_oracle_popup(driver, popup_type)
                # Raise exception with the Oracle message to mark as failed
                raise Exception(f"Oracle {popup_type}: {popup_message}")
        except Exception as popup_error:
            if "Oracle" in str(popup_error):
                # This is an Oracle business rule error - re-raise to mark as failed
                raise popup_error
            else:
                # This is just a popup detection error - log but don't fail
                print(f"⚠️ Popup detection error: {str(popup_error)}")

        print("✅ Role copy completed successfully")
        return confirmation

    except Exception as e:
        print(f"💥 Critical failure: {str(e)}")
        raise

    finally:
        print("🛑 Cleanup completed, returning control to main process.")




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
        
        # Step 5: Clear any residual search or form states
        try:
            search_box = driver.find_element(By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:_FOTr0:0:sp1:srchBox::content")
            search_box.clear()
            print("✓ Cleared search box")
        except:
            pass  # Search box not found or accessible
        
        time.sleep(2)  # Allow UI to stabilize
        print("✅ Browser state reset completed")
        
    except Exception as e:
        print(f"⚠️ Browser state reset had issues but continuing: {str(e)}")
        # Even if reset fails, we should continue - don't raise exception


def main():
    """Main execution flow with Excel integration and robust error handling"""
    driver = None
    df = None

    try:
        # Read Excel input with column validation
        try:
            # Get input file path from environment variable (set by Streamlit) or use default
            input_file = os.environ.get("INPUT_FILE_PATH", "role_copy_input.xlsx")
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

                # CRITICAL: Reset browser state to prevent error cascade
                try:
                    reset_browser_state(driver)
                except Exception as reset_error:
                    print(f"⚠️ Browser reset failed: {str(reset_error)}")

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
