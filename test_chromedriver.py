#!/usr/bin/env python3
"""
Test script to verify ChromeDriver initialization works correctly
with the robust version handling approach.
"""

import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def test_initialize_driver():
    """Test the ChromeDriver initialization with robust version handling"""
    options = webdriver.ChromeOptions()
    # Headless mode for testing
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
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    })

    # Strategy 1: Try ChromeDriverManager first (most reliable for version compatibility)
    try:
        print("🔄 Testing ChromeDriverManager for version compatibility...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ ChromeDriver initialized successfully with ChromeDriverManager")
        # Test basic functionality
        driver.get("https://www.google.com")
        print(f"✅ Successfully loaded page: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"⚠️ ChromeDriverManager failed: {e}")
        
        # Strategy 2: Try system Chrome with specific binary path
        try:
            print("🔄 Testing system Chrome with specific binary...")
            options.binary_location = "/usr/bin/chromium"
            driver = webdriver.Chrome(options=options)
            print("✅ Chrome initialized with system binary")
            # Test basic functionality
            driver.get("https://www.google.com")
            print(f"✅ Successfully loaded page: {driver.title}")
            driver.quit()
            return True
        except Exception as e2:
            print(f"⚠️ System Chrome failed: {e2}")
            
            # Strategy 3: Try without specifying binary location
            try:
                print("🔄 Testing system Chrome without binary specification...")
                options.binary_location = None  # Reset binary location
                driver = webdriver.Chrome(options=options)
                print("✅ Chrome initialized without binary specification")
                # Test basic functionality
                driver.get("https://www.google.com")
                print(f"✅ Successfully loaded page: {driver.title}")
                driver.quit()
                return True
            except Exception as e3:
                print(f"❌ All Chrome initialization strategies failed: {e3}")
                return False

if __name__ == "__main__":
    print("🧪 Testing ChromeDriver initialization...")
    success = test_initialize_driver()
    if success:
        print("🎉 All tests passed! ChromeDriver initialization is working correctly.")
        sys.exit(0)
    else:
        print("❌ Tests failed! ChromeDriver initialization is not working.")
        sys.exit(1)
