#!/usr/bin/env python3
"""
Comprehensive ChromeDriver Fix for Streamlit Cloud
Addresses ChromeDriver version mismatch issues on Streamlit Cloud deployment.
"""

import os
import sys
import subprocess
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
import tempfile
import zipfile
import requests
import re

def get_chrome_version():
    """Get the installed Chrome version"""
    try:
        if platform.system() == "Linux":
            # Try multiple ways to get Chrome version on Linux
            commands = [
                ['chromium', '--version'],
                ['google-chrome', '--version'],
                ['chrome', '--version'],
                ['chromium-browser', '--version']
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        # Extract version number using regex
                        version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                        if version_match:
                            return version_match.group(1)
                        # Fallback: try to get the last number sequence
                        parts = result.stdout.strip().split()
                        for part in reversed(parts):
                            if re.match(r'^\d+\.\d+\.\d+\.\d+$', part):
                                return part
                except:
                    continue
                    
        elif platform.system() == "Windows":
            # Windows Chrome version detection
            try:
                result = subprocess.run(['reg', 'query', 
                                       'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', 
                                       '/v', 'version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'version' in line.lower():
                            version = line.split()[-1]
                            return version
            except:
                pass
                
        elif platform.system() == "Darwin":  # macOS
            try:
                result = subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', 
                                       '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if version_match:
                        return version_match.group(1)
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ Could not detect Chrome version: {e}")
    
    return None

def get_chromedriver_version(driver_path=None):
    """Get ChromeDriver version"""
    try:
        if driver_path:
            result = subprocess.run([driver_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
        else:
            result = subprocess.run(['chromedriver', '--version'], 
                                  capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version_match = re.search(r'ChromeDriver (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if version_match:
                return version_match.group(1)
    except Exception as e:
        print(f"⚠️ Could not detect ChromeDriver version: {e}")
    
    return None

def download_chromedriver_for_version(chrome_version):
    """Download ChromeDriver for a specific Chrome version"""
    try:
        major_version = chrome_version.split('.')[0]
        print(f"🎯 Attempting to download ChromeDriver for Chrome version {major_version}")
        
        # Try to get the latest compatible version
        latest_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        response = requests.get(latest_url, timeout=10)
        
        if response.status_code == 200:
            chromedriver_version = response.text.strip()
            print(f"📥 Found ChromeDriver version: {chromedriver_version}")
            
            # Download the appropriate version for Linux
            download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_linux64.zip"
            
            temp_dir = tempfile.mkdtemp()
            chromedriver_path = os.path.join(temp_dir, "chromedriver")
            zip_path = os.path.join(temp_dir, "chromedriver.zip")
            
            print(f"📥 Downloading from: {download_url}")
            response = requests.get(download_url, timeout=30)
            
            if response.status_code == 200:
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                os.chmod(chromedriver_path, 0o755)
                print(f"✅ ChromeDriver downloaded and extracted to: {chromedriver_path}")
                return chromedriver_path
            else:
                print(f"❌ Failed to download ChromeDriver: HTTP {response.status_code}")
        else:
            print(f"❌ Failed to get latest version: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error downloading ChromeDriver: {e}")
    
    return None

def initialize_driver_robust():
    """
    Robust ChromeDriver initialization with multiple fallback strategies
    specifically designed for Streamlit Cloud deployment
    """
    chrome_version = get_chrome_version()
    print(f"🔍 Detected Chrome version: {chrome_version}")
    
    options = webdriver.ChromeOptions()
    
    # Essential options for Streamlit Cloud
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Additional options to reduce warnings
    options.add_argument("--disable-logging")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-component-update")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-client-side-phishing-detection")
    options.add_argument("--disable-hang-monitor")
    options.add_argument("--disable-prompt-on-repost")
    options.add_argument("--disable-domain-reliability")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    
    # Anti-detection options
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    })

    # Strategy 1: Use webdriver-manager with latest version (FASTEST - currently working)
    try:
        print("🔄 Strategy 1: Using webdriver-manager with latest version...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ ChromeDriver initialized with webdriver-manager (latest)")
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"⚠️ Strategy 1 failed: {e}")

    # Strategy 2: Use webdriver-manager with specific version matching
    try:
        print("🔄 Strategy 2: Using webdriver-manager with version matching...")
        
        # If we detected Chrome version, try to match it
        if chrome_version:
            major_version = chrome_version.split('.')[0]
            print(f"🎯 Attempting to match ChromeDriver version {major_version}...")
            
            # Try to get a compatible ChromeDriver version
            try:
                service = Service(ChromeDriverManager(version=major_version).install())
                driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ ChromeDriver initialized with version matching (Chrome {chrome_version})")
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                return driver
            except Exception as e:
                print(f"⚠️ Version-specific ChromeDriver failed: {e}")
        
    except Exception as e:
        print(f"⚠️ Strategy 2 failed: {e}")

    # Strategy 3: Manual ChromeDriver download for specific version
    if chrome_version:
        try:
            print("🔄 Strategy 3: Manual ChromeDriver download for specific version...")
            chromedriver_path = download_chromedriver_for_version(chrome_version)
            if chromedriver_path:
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ ChromeDriver initialized with manual download for Chrome {chrome_version}")
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                return driver
        except Exception as e:
            print(f"⚠️ Strategy 3 failed: {e}")
    
    # Strategy 4: Use system Chrome with specific binary paths
    binary_paths = [
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
        "/usr/bin/chromium-browser"
    ]
    
    for binary_path in binary_paths:
        try:
            print(f"🔄 Strategy 4: Trying system Chrome with binary: {binary_path}")
            options.binary_location = binary_path
            driver = webdriver.Chrome(options=options)
            print(f"✅ Chrome initialized with binary: {binary_path}")
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            print(f"⚠️ Binary {binary_path} failed: {e}")
            continue
    
    # Strategy 5: Use system Chrome without specifying binary
    try:
        print("🔄 Strategy 5: Trying system Chrome without binary specification...")
        options.binary_location = None
        driver = webdriver.Chrome(options=options)
        print("✅ Chrome initialized without binary specification")
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"⚠️ Strategy 5 failed: {e}")
    
    # Strategy 6: Last resort - try with minimal options
    try:
        print("🔄 Strategy 6: Minimal Chrome options...")
        minimal_options = webdriver.ChromeOptions()
        minimal_options.add_argument("--headless")
        minimal_options.add_argument("--no-sandbox")
        minimal_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=minimal_options)
        print("✅ Chrome initialized with minimal options")
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except Exception as e:
        print(f"⚠️ Strategy 6 failed: {e}")
    
    raise Exception("❌ All ChromeDriver initialization strategies failed!")

def test_chromedriver():
    """Test the ChromeDriver initialization"""
    print("🧪 Testing ChromeDriver initialization...")
    
    try:
        driver = initialize_driver_robust()
        
        # Test basic functionality
        print("🌐 Testing basic web navigation...")
        driver.get("https://www.google.com")
        print(f"✅ Successfully loaded page: {driver.title}")
        
        # Test JavaScript execution
        print("🔧 Testing JavaScript execution...")
        result = driver.execute_script("return navigator.userAgent;")
        print(f"✅ JavaScript execution successful: {result[:50]}...")
        
        driver.quit()
        print("🎉 All tests passed! ChromeDriver is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_chromedriver()
    sys.exit(0 if success else 1)
