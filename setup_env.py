#!/usr/bin/env python3
"""
Setup script for Oracle Role Management Automation
This script creates a virtual environment and installs all required packages.
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    print("🚀 Oracle Role Management - Environment Setup")
    print("=" * 50)
    
    # Check if Python is installed
    if not run_command("python --version", "Checking Python installation"):
        print("❌ Python is not installed or not in PATH")
        return False
    
    # Create virtual environment
    venv_name = "oracle_role_env"
    if os.path.exists(venv_name):
        print(f"⚠️ Virtual environment '{venv_name}' already exists")
        response = input("Do you want to recreate it? (y/N): ")
        if response.lower() == 'y':
            if platform.system() == "Windows":
                run_command(f"rmdir /s /q {venv_name}", f"Removing existing environment '{venv_name}'")
            else:
                run_command(f"rm -rf {venv_name}", f"Removing existing environment '{venv_name}'")
        else:
            print("Using existing environment")
    
    if not os.path.exists(venv_name):
        if not run_command(f"python -m venv {venv_name}", f"Creating virtual environment '{venv_name}'"):
            return False
    
    # Determine activation script
    if platform.system() == "Windows":
        activate_script = f"{venv_name}\\Scripts\\activate"
        pip_path = f"{venv_name}\\Scripts\\pip"
    else:
        activate_script = f"{venv_name}/bin/activate"
        pip_path = f"{venv_name}/bin/pip"
    
    # Install packages
    print("\n📦 Installing required packages...")
    
    packages = [
        "selenium==4.15.2",
        "webdriver-manager==4.0.1",
        "pandas==2.1.3",
        "openpyxl==3.1.2",
        "python-dotenv==1.0.0",
        "lxml==4.9.3",
        "requests==2.31.0",
        "urllib3==2.0.7",
        "colorama==0.4.6",
        "tqdm==4.66.1"
    ]
    
    for package in packages:
        if not run_command(f"{pip_path} install {package}", f"Installing {package}"):
            print(f"⚠️ Failed to install {package}, continuing...")
    
    print("\n✅ Environment setup completed!")
    print("\n📋 Next steps:")
    print(f"1. Activate the environment:")
    if platform.system() == "Windows":
        print(f"   {venv_name}\\Scripts\\activate")
    else:
        print(f"   source {venv_name}/bin/activate")
    print("2. Run your script: python create_role.py")
    print("3. Make sure you have the Excel file 'role_create_input.xlsx' in the same directory")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
