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



# ============================================================
# Function to add a privilege to a role (Action = "ADD")
# ============================================================
def add_privilege(driver, existing_role_name, existing_role_code, privilege_code):
    try:
        # [1] Search for the existing role to edit
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

        # [11] Click Next button 4 times on the main page
        for step in range(4):
            click_next_button(driver)
            print(f"✓ Next step {step+1} completed")
            time.sleep(2)

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
        # [1] Search for the existing role to edit
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

        # [9] Click Next button 4 times on the main page
        for step in range(4):
            click_next_button(driver)
            print(f"✓ Next step {step+1} completed")
            time.sleep(2)

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
            try:
                df.to_excel("privilege_progress.xlsx", index=False)
                print(f"💾 Saved progress after row {index+1} (Status: {current_status})")
            except Exception as save_error:
                print(f"⚠️ Failed to save progress: {str(save_error)}")
            driver.get(SECURITY_CONSOLE_URL)
            time.sleep(2)

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
