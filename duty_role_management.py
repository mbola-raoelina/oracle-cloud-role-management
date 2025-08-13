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

# --------------------------------------------------------------------
# Function to add a duty role (for Action = 'ADD')
# --------------------------------------------------------------------
def add_duty_role(driver, existing_role_name, existing_role_code, duty_role_name, duty_role_code):
    try:
        # [1] Search for existing role to edit
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

        # [5] Click Next button 3 times
        for step in range(3):
            click_next_button(driver)
            print(f"✓ Step {step+1} completed")
            time.sleep(2)

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

        # [11] Click on the Close button in the pop-up
        close_btn = find_element_robust(driver, [
            (By.ID, "_FOpt1:_FOr1:0:_FONSr2:0:MAnt2:4:rhSp1:d1::close"),
            (By.XPATH, "//a[contains(@id, 'd1::close')]"),
            (By.XPATH, "//a[@title='Close']"),
            (By.XPATH, "//div[contains(@id, 'rhSrchPu::popup-container')]//a[contains(@id, '::close')]")
        ], timeout=10)
        driver.execute_script("arguments[0].click();", close_btn)
        print("✓ Pop-up closed")

        # [12] Click Next button 2 times on the main page
        for step in range(2):
            click_next_button(driver)
            print(f"✓ Next step {step+1} completed")
            time.sleep(2)

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
        # [1] Search for existing role to edit (same as in add_duty_role)
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

        # [5] Click Next button 3 times
        for step in range(3):
            click_next_button(driver)
            print(f"✓ Step {step+1} completed")
            time.sleep(2)

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
            # Wait for the table to be present first - use robust table detection
            table = find_element_robust(driver, [
                (By.XPATH, "//table[contains(@class, 'x1hg')]"),
                (By.XPATH, "//table[contains(@class, 'x1hi')]"),
                (By.XPATH, "//table[contains(@class, 'x1hg') or contains(@class, 'x1hi')]"),
                (By.XPATH, "//table[contains(@summary, 'Details')]"),
                (By.XPATH, "//table[contains(@id, 'rhgrv')]"),
                (By.XPATH, "//div[contains(@id, 'rhgrv')]//table"),
                (By.XPATH, "//table[contains(@class, 'x1hg') or contains(@class, 'x1hi') or contains(@class, 'x1hg')]")
            ], timeout=10, condition=EC.presence_of_element_located)
            print("✓ Results table found")
            
            # Use find_element_robust to find the correct row with multiple fallback selectors
            correct_duty_row = find_element_robust(driver, [
                # Try with current class x1hg
                (By.XPATH, f"//table[contains(@class, 'x1hg')]//tr[td[2]//span[normalize-space(.)='{duty_role_code}']]"),
                (By.XPATH, f"//table[contains(@class, 'x1hg')]//tr[td[2][normalize-space(.)='{duty_role_code}']]"),
                # Try with old class x1hi (in case it changes back)
                (By.XPATH, f"//table[contains(@class, 'x1hi')]//tr[td[2]//span[normalize-space(.)='{duty_role_code}']]"),
                (By.XPATH, f"//table[contains(@class, 'x1hi')]//tr[td[2][normalize-space(.)='{duty_role_code}']]"),
                # Generic selectors that work regardless of table class
                (By.XPATH, f"//tr[td[2]//span[normalize-space(.)='{duty_role_code}']]"),
                (By.XPATH, f"//tr[td[2][normalize-space(.)='{duty_role_code}']]"),
                (By.XPATH, f"//tr[td[2]//span[contains(text(), '{duty_role_code}')]]"),
                (By.XPATH, f"//tr[td[2][contains(text(), '{duty_role_code}')]]"),
                # Row class-based selectors
                (By.XPATH, f"//tr[contains(@class, 'xem')]//td[2]//span[normalize-space(.)='{duty_role_code}']/ancestor::tr"),
                (By.XPATH, f"//tr[contains(@class, 'p_AFSelected')]//td[2]//span[normalize-space(.)='{duty_role_code}']/ancestor::tr"),
                # Most generic - find any row with the duty role code in second column
                (By.XPATH, f"//tr[.//td[2][.//span[normalize-space(.)='{duty_role_code}']]]"),
                (By.XPATH, f"//tr[.//td[2][contains(., '{duty_role_code}')]]")
            ], timeout=10)
            
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
        except Exception as e:
            print(f"🔴 Delete confirmation failed: {str(e)}")
            raise
        

        # [10] Click Next button 2 times on the main page
        for step in range(2):
            click_next_button(driver)
            print(f"✓ Next step {step+1} completed")
            time.sleep(2)

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
            try:
                df.to_excel("duty_role_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")
            driver.get(SECURITY_CONSOLE_URL)
            time.sleep(2)

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
