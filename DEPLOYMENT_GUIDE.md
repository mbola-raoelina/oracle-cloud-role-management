# Oracle Automation App - Deployment Guide

## Overview
This guide will help you fix the ChromeDriver version mismatch issue and deploy your Oracle automation app to Streamlit Cloud.

## Prerequisites
- All Oracle automation scripts (`create_role.py`, `copy_role.py`, `duty_role_management.py`, `privilege_management.py`)
- Streamlit app (`streamlit_app.py`)
- Git repository set up

## Step 1: Fix ChromeDriver Version Mismatch

### 1.1 Test the ChromeDriver Fix
```bash
python chromedriver_fix.py
```

### 1.2 Update All Automation Scripts
```bash
python update_automation_scripts.py
```

This will automatically update all your automation scripts to use the robust ChromeDriver initialization.

### 1.3 Verify the Updates
Check that each automation script now contains:
```python
def initialize_driver():
    """Initialize Chrome WebDriver with robust version handling for Streamlit Cloud deployment"""
    from chromedriver_fix import initialize_driver_robust
    return initialize_driver_robust()
```

## Step 2: Prepare Configuration Files

### 2.1 packages.txt
Ensure your `packages.txt` contains:
```txt
chromium
chromium-driver
xvfb
```

### 2.2 requirements.txt
Ensure your `requirements.txt` contains:
```txt
streamlit>=1.28.0
selenium>=4.15.0
webdriver-manager>=4.0.0
pandas>=2.0.0
openpyxl>=3.1.0
xlrd>=2.0.0
numpy>=1.24.0
requests>=2.31.0
```

### 2.3 .streamlit/config.toml
Create `.streamlit/config.toml`:
```toml
[server]
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

## Step 3: Update .gitignore

Ensure your `.gitignore` contains:
```gitignore
# Environment variables
.env
.env.local

# Python virtual environments
venv/
env/
mon_env/

# Input files
*.xlsx
*.xls
input_files/

# Temporary files
temp/
tmp/
*.tmp

# Jupyter notebooks
*.ipynb

# Conversion files
*.pyc
__pycache__/

# Logs
*.log

# Cache files
*.cache
```

## Step 4: Deploy to Streamlit Cloud

### 4.1 Commit and Push Changes
```bash
git add .
git commit -m "Fix ChromeDriver version mismatch for Streamlit Cloud deployment"
git push origin main
```

### 4.2 Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set the main file path to `streamlit_app.py`
4. Add your secrets in the Streamlit Cloud dashboard:
   - `BIP_USERNAME`: Your Oracle username
   - `BIP_PASSWORD`: Your Oracle password
   - `ORACLE_ENVIRONMENT`: Default environment (dev1, dev2, or dev3)

### 4.3 Monitor Deployment
- Check the build logs for any errors
- Ensure all packages are installed correctly
- Verify Chrome and ChromeDriver are available

## Step 5: Test the Deployment

### 5.1 Test Connection Feature
1. Open your deployed Streamlit app
2. Go to the sidebar and click "Test Connection"
3. Select an environment (dev1, dev2, or dev3)
4. Verify the connection test passes without ChromeDriver errors

### 5.2 Test Automation Features
1. Test each automation feature:
   - Create Role
   - Copy Role
   - Duty Role Management
   - Privilege Management
2. Upload sample Excel files
3. Verify the automation completes successfully

## Troubleshooting

### ChromeDriver Still Failing?
If you still get ChromeDriver errors:

1. **Check Streamlit Cloud logs** for detailed error messages
2. **Verify packages.txt** format (no comments, correct package names)
3. **Test locally** with `python chromedriver_fix.py`
4. **Check file permissions** for ChromeDriver

### Common Issues and Solutions

#### Issue: "session not created" error
**Solution**: The robust ChromeDriver initialization should handle this automatically.

#### Issue: Package installation failures
**Solution**: Check that `packages.txt` has correct package names and no comments.

#### Issue: Import errors
**Solution**: Ensure `requirements.txt` contains all necessary dependencies.

#### Issue: Permission denied
**Solution**: ChromeDriver should have execute permissions (handled by the fix).

## Expected Results

After successful deployment:
- ✅ Connection testing works without ChromeDriver errors
- ✅ All automation features function correctly
- ✅ Excel file uploads and processing work
- ✅ No version mismatch errors
- ✅ App runs smoothly on Streamlit Cloud

## Monitoring and Maintenance

### Regular Checks
- Monitor Streamlit Cloud logs for any new issues
- Test the connection feature periodically
- Verify all automation features still work after updates

### Updates
- Keep dependencies updated in `requirements.txt`
- Monitor for new ChromeDriver versions
- Test locally before deploying updates

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Streamlit Cloud logs
3. Test locally to isolate the issue
4. Refer to the ChromeDriver fix guide for detailed solutions
