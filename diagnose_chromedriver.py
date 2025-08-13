#!/usr/bin/env python3
"""
ChromeDriver Diagnostic Script for Streamlit Cloud
This script helps diagnose ChromeDriver issues on Streamlit Cloud deployment.
"""

import os
import sys
import subprocess
import platform
import requests
import tempfile
import zipfile
import re

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_system_info():
    """Check system information"""
    print_section("SYSTEM INFORMATION")
    
    print(f"Platform: {platform.system()}")
    print(f"Platform Release: {platform.release()}")
    print(f"Platform Version: {platform.version()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")

def check_chrome_installation():
    """Check Chrome/Chromium installation"""
    print_section("CHROME/CHROMIUM INSTALLATION")
    
    chrome_paths = [
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
        "/usr/bin/chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome-stable"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"   Version: {result.stdout.strip()}")
                else:
                    print(f"   Error: {result.stderr.strip()}")
            except Exception as e:
                print(f"   Error running: {e}")
        else:
            print(f"❌ Not found: {path}")

def check_chromedriver_installation():
    """Check ChromeDriver installation"""
    print_section("CHROMEDRIVER INSTALLATION")
    
    chromedriver_paths = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
        "/snap/bin/chromedriver"
    ]
    
    for path in chromedriver_paths:
        if os.path.exists(path):
            print(f"✅ Found: {path}")
            try:
                result = subprocess.run([path, '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"   Version: {result.stdout.strip()}")
                else:
                    print(f"   Error: {result.stderr.strip()}")
            except Exception as e:
                print(f"   Error running: {e}")
        else:
            print(f"❌ Not found: {path}")

def check_environment_variables():
    """Check relevant environment variables"""
    print_section("ENVIRONMENT VARIABLES")
    
    relevant_vars = [
        'PATH',
        'CHROME_BIN',
        'CHROMEDRIVER_PATH',
        'WEBDRIVER_CHROME_DRIVER',
        'ORACLE_ENVIRONMENT',
        'BIP_USERNAME',
        'BIP_PASSWORD'
    ]
    
    for var in relevant_vars:
        value = os.environ.get(var)
        if value:
            if 'PASSWORD' in var:
                print(f"{var}: {'*' * len(value)} (hidden)")
            else:
                print(f"{var}: {value}")
        else:
            print(f"{var}: Not set")

def check_python_packages():
    """Check installed Python packages"""
    print_section("PYTHON PACKAGES")
    
    required_packages = [
        'selenium',
        'webdriver-manager',
        'requests',
        'pandas',
        'openpyxl',
        'streamlit'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}: Installed")
        except ImportError:
            print(f"❌ {package}: Not installed")

def test_chrome_version_detection():
    """Test Chrome version detection methods"""
    print_section("CHROME VERSION DETECTION")
    
    if platform.system() == "Linux":
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
                    print(f"✅ {cmd[0]}: {result.stdout.strip()}")
                    # Try to extract version
                    version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                    if version_match:
                        print(f"   Extracted version: {version_match.group(1)}")
                else:
                    print(f"❌ {cmd[0]}: {result.stderr.strip()}")
            except Exception as e:
                print(f"❌ {cmd[0]}: {e}")

def test_chromedriver_download():
    """Test ChromeDriver download functionality"""
    print_section("CHROMEDRIVER DOWNLOAD TEST")
    
    # Test with a known Chrome version (120)
    test_version = "120.0.6099.224"
    major_version = test_version.split('.')[0]
    
    print(f"Testing download for Chrome version: {test_version}")
    print(f"Major version: {major_version}")
    
    try:
        # Get latest ChromeDriver version for this Chrome version
        latest_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        print(f"Checking: {latest_url}")
        
        response = requests.get(latest_url, timeout=10)
        if response.status_code == 200:
            chromedriver_version = response.text.strip()
            print(f"✅ Latest ChromeDriver version: {chromedriver_version}")
            
            # Test download URL
            download_url = f"https://chromedriver.storage.googleapis.com/{chromedriver_version}/chromedriver_linux64.zip"
            print(f"Download URL: {download_url}")
            
            response = requests.head(download_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Download URL is accessible")
                print(f"Content-Length: {response.headers.get('content-length', 'Unknown')}")
            else:
                print(f"❌ Download URL not accessible: HTTP {response.status_code}")
        else:
            print(f"❌ Failed to get latest version: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing download: {e}")

def test_selenium_import():
    """Test Selenium import and basic functionality"""
    print_section("SELENIUM TEST")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        print("✅ Selenium imports successful")
        
        # Test webdriver-manager
        try:
            driver_path = ChromeDriverManager().install()
            print(f"✅ webdriver-manager path: {driver_path}")
        except Exception as e:
            print(f"❌ webdriver-manager error: {e}")
            
    except ImportError as e:
        print(f"❌ Selenium import failed: {e}")

def main():
    """Run all diagnostic tests"""
    print("🚀 ChromeDriver Diagnostic for Streamlit Cloud")
    print("This script will help diagnose ChromeDriver issues")
    
    check_system_info()
    check_chrome_installation()
    check_chromedriver_installation()
    check_environment_variables()
    check_python_packages()
    test_chrome_version_detection()
    test_chromedriver_download()
    test_selenium_import()
    
    print_section("DIAGNOSTIC COMPLETE")
    print("Please share this output to help diagnose ChromeDriver issues.")

if __name__ == "__main__":
    main()
