#!/usr/bin/env python3
"""
Script to update all automation scripts with the robust ChromeDriver initialization
"""

import os
import re

def update_script_file(file_path):
    """Update a single automation script with the robust ChromeDriver initialization"""
    
    # Read the current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the file already has the robust initialization
    if "from chromedriver_fix import initialize_driver_robust" in content:
        print(f"✅ {file_path} already updated")
        return False
    
    # Find the existing initialize_driver function
    pattern = r'def initialize_driver\(\):.*?(?=def|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        old_function = match.group(0)
        new_function = '''def initialize_driver():
    """Initialize Chrome WebDriver with robust version handling for Streamlit Cloud deployment"""
    from chromedriver_fix import initialize_driver_robust
    return initialize_driver_robust()
'''
        
        # Replace the old function with the new one
        updated_content = content.replace(old_function, new_function)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ Updated {file_path}")
        return True
    else:
        print(f"⚠️ Could not find initialize_driver function in {file_path}")
        return False

def main():
    """Update all automation scripts"""
    
    # List of automation scripts to update
    automation_scripts = [
        'create_role.py',
        'copy_role.py', 
        'duty_role_management.py',
        'privilege_management.py'
    ]
    
    print("🔄 Updating automation scripts with robust ChromeDriver initialization...")
    
    updated_count = 0
    for script in automation_scripts:
        if os.path.exists(script):
            if update_script_file(script):
                updated_count += 1
        else:
            print(f"⚠️ File not found: {script}")
    
    print(f"\n📊 Summary: Updated {updated_count} out of {len(automation_scripts)} scripts")
    
    if updated_count > 0:
        print("\n🎉 Success! Your automation scripts have been updated.")
        print("📝 Next steps:")
        print("1. Test the fix locally: python chromedriver_fix.py")
        print("2. Deploy to Streamlit Cloud")
        print("3. Test the connection feature in the deployed app")
    else:
        print("\n⚠️ No scripts were updated. Please check if the files exist and contain the initialize_driver function.")

if __name__ == "__main__":
    main()
