import streamlit as st
import pandas as pd
import os
import time
import tempfile
from datetime import datetime
import base64
from io import BytesIO
import zipfile
import json

# Import our automation modules
from create_role import main as create_role_main
from copy_role import main as copy_role_main
from duty_role_management import main as duty_role_main
from privilege_management import main as privilege_management_main

# Page configuration
st.set_page_config(
    page_title="Oracle Cloud Role Management Automation",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #f5c6cb;
    }
    .info-message {
        background: #d1ecf1;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #bee5eb;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 5px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🔐 Oracle Cloud Role Management Automation</h1>', unsafe_allow_html=True)
    
    # Initialize session state for navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Home"
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Operation",
        ["🏠 Home", "➕ Create Role", "📋 Copy Role", "👥 Duty Role Management", "🔑 Privilege Management", "🔧 Diagnostics", "📊 Results"],
        index=["🏠 Home", "➕ Create Role", "📋 Copy Role", "👥 Duty Role Management", "🔑 Privilege Management", "🔧 Diagnostics", "📊 Results"].index(st.session_state.current_page)
    )
    
    # Update session state when sidebar selection changes
    if page != st.session_state.current_page:
        st.session_state.current_page = page
        st.rerun()
    
    # Environment variables setup
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Configuration")
    
    # Environment selection
    environment = st.sidebar.selectbox(
        "Oracle Environment",
        ["dev1", "dev2", "dev3"],
        help="Select your Oracle Cloud environment"
    )
    
    # Environment variables input
    username = st.sidebar.text_input("Oracle Username", type="default", help="Your Oracle Cloud username")
    password = st.sidebar.text_input("Oracle Password", type="password", help="Your Oracle Cloud password")
    
    # Connect button
    if username and password:
        if st.sidebar.button("🔗 Connect", help="Connect to Oracle Cloud"):
            with st.spinner("Connecting..."):
                try:
                    # Import test function
                    from selenium import webdriver
                    from selenium.webdriver.chrome.service import Service
                    from selenium.webdriver.common.by import By
                    from selenium.webdriver.support.ui import WebDriverWait, Select
                    from selenium.webdriver.support import expected_conditions as EC
                    from webdriver_manager.chrome import ChromeDriverManager
                    
                    # Set up driver with optimized options for faster startup
                    options = webdriver.ChromeOptions()
                    options.add_argument("--headless")  # Run in background
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-gpu")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--disable-extensions")
                    options.add_argument("--disable-plugins")
                    options.add_argument("--disable-images")
                    # options.add_argument("--disable-javascript")  # Removed - breaks login process
                    options.add_argument("--disable-web-security")
                    options.add_argument("--disable-features=VizDisplayCompositor")
                    options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    options.add_experimental_option('useAutomationExtension', False)
                    options.add_experimental_option("prefs", {
                        "profile.default_content_setting_values.notifications": 2,
                        "profile.default_content_settings.popups": 0
                    })
                    
                    # Build URL based on environment
                    base_url = f"https://iabbzv-{environment}.fa.ocs.oraclecloud.com"
                    security_console_url = f"{base_url}/hcmUI/faces/FndOverview?fnd=%3B%3B%3B%3Bfalse%3B256%3B%3B%3B&fndGlobalItemNodeId=ASE_FUSE_SECURITY_CONSOLE"
                    
                    # Initialize driver with robust settings
                    try:
                        from chromedriver_fix import initialize_driver_robust
                        driver = initialize_driver_robust()
                    except Exception as driver_error:
                        st.sidebar.error("❌ Connection failed: ChromeDriver error")
                        return
                    
                    try:
                        # Navigate to login page
                        driver.get(security_console_url)
                        time.sleep(2)
                        
                        # Try multiple selectors for username field
                        username_field = None
                        username_selectors = [
                            (By.ID, "userid"),
                            (By.ID, "username"),
                            (By.NAME, "userid"),
                            (By.NAME, "username"),
                            (By.CSS_SELECTOR, "input[type='text']"),
                            (By.CSS_SELECTOR, "input[placeholder*='user']"),
                            (By.CSS_SELECTOR, "input[placeholder*='User']")
                        ]
                        
                        for selector_type, selector_value in username_selectors:
                            try:
                                username_field = WebDriverWait(driver, 3).until(
                                    EC.presence_of_element_located((selector_type, selector_value))
                                )
                                break
                            except:
                                continue
                        
                        if not username_field:
                            st.sidebar.error("❌ Connection failed: Invalid environment")
                            return
                        
                        # Try multiple selectors for password field
                        password_field = None
                        password_selectors = [
                            (By.ID, "password"),
                            (By.NAME, "password"),
                            (By.CSS_SELECTOR, "input[type='password']")
                        ]
                        
                        for selector_type, selector_value in password_selectors:
                            try:
                                password_field = driver.find_element(selector_type, selector_value)
                                break
                            except:
                                continue
                        
                        if not password_field:
                            st.sidebar.error("❌ Connection failed: Invalid environment")
                            return
                        
                        # Enter credentials
                        username_field.clear()
                        username_field.send_keys(username)
                        password_field.clear()
                        password_field.send_keys(password)
                        
                        # Try multiple selectors for login button
                        login_button = None
                        login_selectors = [
                            (By.ID, "btnActive"),
                            (By.ID, "login-button"),
                            (By.CSS_SELECTOR, "button[type='submit']"),
                            (By.CSS_SELECTOR, "input[type='submit']"),
                            (By.XPATH, "//button[contains(text(), 'Sign In')]"),
                            (By.XPATH, "//button[contains(text(), 'Login')]"),
                            (By.XPATH, "//input[@value='Sign In']"),
                            (By.XPATH, "//input[@value='Login']")
                        ]
                        
                        for selector_type, selector_value in login_selectors:
                            try:
                                login_button = driver.find_element(selector_type, selector_value)
                                break
                            except:
                                continue
                        
                        if not login_button:
                            st.sidebar.error("❌ Connection failed: Invalid environment")
                            return
                        
                        # Submit form
                        login_button.click()
                        time.sleep(3)
                        
                        # Check if login was successful
                        current_url = driver.current_url
                        
                        # Simple check: if we're still on login page, it failed
                        if "login" in current_url.lower() or "connexion" in driver.title.lower():
                            st.sidebar.error("❌ Connection failed: Invalid credentials")
                        # If we're on Oracle Cloud page, it succeeded
                        elif "iabbzv-dev" in current_url and "hcmUI" in current_url:
                            st.sidebar.success("✅ Connected successfully!")
                        else:
                            st.sidebar.error("❌ Connection failed: Invalid environment")
                    
                    finally:
                        driver.quit()
                        
                except Exception as e:
                    st.sidebar.error("❌ Connection failed: System error")
    
    # Save credentials and environment to environment variables
    if username and password:
        os.environ["BIP_USERNAME"] = username
        os.environ["BIP_PASSWORD"] = password
        os.environ["ORACLE_ENVIRONMENT"] = environment
    
    # Home page
    if st.session_state.current_page == "🏠 Home":
        show_home_page()
    
    # Create Role page
    elif st.session_state.current_page == "➕ Create Role":
        show_create_role_page()
    
    # Copy Role page
    elif st.session_state.current_page == "📋 Copy Role":
        show_copy_role_page()
    
    # Duty Role Management page
    elif st.session_state.current_page == "👥 Duty Role Management":
        show_duty_role_page()
    
    # Privilege Management page
    elif st.session_state.current_page == "🔑 Privilege Management":
        show_privilege_management_page()
    
    # Diagnostics page
    elif st.session_state.current_page == "🔧 Diagnostics":
        show_diagnostics_page()
    
    # Results page
    elif st.session_state.current_page == "📊 Results":
        show_results_page()

def show_home_page():
    st.markdown("""
    <div class="feature-card">
        <h2>🚀 Welcome to Oracle Cloud Role Management Automation</h2>
        <p>This application provides a comprehensive solution for managing Oracle Cloud roles and privileges through an intuitive web interface.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Quick Access - Click any feature to get started:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create Role Card - Clickable
        if st.button("➕ Create Role", key="home_create_role", use_container_width=True):
            st.session_state.current_page = "➕ Create Role"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" style="margin-top: 10px;">
            <h3>➕ Create Role</h3>
            <p>Create new roles with custom names, codes, and categories. Upload Excel files with role specifications for batch processing.</p>
            <ul>
                <li>Batch role creation</li>
                <li>Custom role categories</li>
                <li>Excel file support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Copy Role Card - Clickable
        if st.button("📋 Copy Role", key="home_copy_role", use_container_width=True):
            st.session_state.current_page = "📋 Copy Role"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" style="margin-top: 10px;">
            <h3>📋 Copy Role</h3>
            <p>Duplicate existing roles with new names and codes. Perfect for creating role templates or variations.</p>
            <ul>
                <li>Role duplication</li>
                <li>Template creation</li>
                <li>Batch processing</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Duty Role Management Card - Clickable
        if st.button("👥 Duty Role Management", key="home_duty_role", use_container_width=True):
            st.session_state.current_page = "👥 Duty Role Management"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" style="margin-top: 10px;">
            <h3>👥 Duty Role Management</h3>
            <p>Add or remove duty roles from existing roles. Manage role hierarchies and permissions efficiently.</p>
            <ul>
                <li>Add duty roles</li>
                <li>Remove duty roles</li>
                <li>Role hierarchy management</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Privilege Management Card - Clickable
        if st.button("🔑 Privilege Management", key="home_privilege", use_container_width=True):
            st.session_state.current_page = "🔑 Privilege Management"
            st.rerun()
        
        st.markdown("""
        <div class="feature-card" style="margin-top: 10px;">
            <h3>🔑 Privilege Management</h3>
            <p>Manage privileges within roles. Add or remove specific permissions and access controls.</p>
            <ul>
                <li>Add privileges</li>
                <li>Remove privileges</li>
                <li>Permission management</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Diagnostics Card - Clickable
    if st.button("🔧 Diagnostics", key="home_diagnostics", use_container_width=True):
        st.session_state.current_page = "🔧 Diagnostics"
        st.rerun()
    
    st.markdown("""
    <div class="feature-card" style="margin-top: 10px;">
        <h3>🔧 Diagnostics</h3>
        <p>Diagnose ChromeDriver and system issues. Test connections and troubleshoot deployment problems.</p>
        <ul>
            <li>System diagnostics</li>
            <li>ChromeDriver testing</li>
            <li>Connection troubleshooting</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # System Status
    st.markdown("---")
    st.subheader("🔧 System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("✅ **ChromeDriver**: Auto-managed via webdriver-manager")
    
    with col2:
        st.info("✅ **Connection Testing**: Test credentials before automation")
    
    with col3:
        st.info("✅ **Multi-Environment**: Support for dev1, dev2, dev3")

def show_create_role_page():
    # Back to Home button
    if st.button("🏠 Back to Home", key="create_role_back"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    
    st.header("➕ Create Role")
    
    st.markdown("""
    <div class="info-message">
        <strong>Instructions:</strong> Upload an Excel file with role specifications. The file should contain columns: 
        <code>Role Name</code>, <code>Role Code</code>, <code>Role Category</code>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Excel file for role creation",
        type=['xlsx', 'xls'],
        help="Upload Excel file with role specifications"
    )
    
    if uploaded_file is not None:
        # Show file preview
        try:
            df = pd.read_excel(uploaded_file)
            st.subheader("📋 File Preview")
            st.dataframe(df.head())
            
            # Validate required columns
            required_columns = {'Role Name', 'Role Code', 'Role Category'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
            else:
                st.success(f"✅ File validation passed! Found {len(df)} roles to create.")
                
                # Start automation button
                if st.button("🚀 Start Role Creation", key="create_role_btn"):
                    if not os.environ.get("BIP_USERNAME") or not os.environ.get("BIP_PASSWORD"):
                        st.error("❌ Please configure your Oracle credentials in the sidebar first!")
                    else:
                        with st.spinner("🔄 Creating roles..."):
                            try:
                                # Save uploaded file temporarily
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                                    tmp_file.write(uploaded_file.getvalue())
                                    tmp_file_path = tmp_file.name
                                
                                # Change to the directory with the automation script
                                original_dir = os.getcwd()
                                script_dir = os.path.dirname(os.path.abspath(__file__))
                                os.chdir(script_dir)
                                
                                # Set the input file path for the automation script
                                os.environ["INPUT_FILE_PATH"] = tmp_file_path
                                
                                # Run the automation
                                create_role_main()
                                
                                # Return to original directory
                                os.chdir(original_dir)
                                
                                st.success("✅ Role creation completed successfully!")
                                
                                # Show results
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('role_create_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    st.subheader("📊 Results")
                                    st.dataframe(result_df)
                                    
                                    # Download button
                                    csv = result_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Results",
                                        data=csv,
                                        file_name=f"role_creation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                                
                            except Exception as e:
                                st.error(f"❌ Error during role creation: {str(e)}")
                            finally:
                                # Cleanup
                                if 'tmp_file_path' in locals():
                                    os.unlink(tmp_file_path)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def show_copy_role_page():
    # Back to Home button
    if st.button("🏠 Back to Home", key="copy_role_back"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    
    st.header("📋 Copy Role")
    
    st.markdown("""
    <div class="info-message">
        <strong>Instructions:</strong> Upload an Excel file with role copy specifications. The file should contain columns: 
        <code>Role to Copy</code>, <code>New Role Name</code>, <code>New Role Code</code>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Excel file for role copying",
        type=['xlsx', 'xls'],
        help="Upload Excel file with role copy specifications"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.subheader("📋 File Preview")
            st.dataframe(df.head())
            
            # Validate required columns
            required_columns = {'Role to Copy', 'New Role Name', 'New Role Code'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
            else:
                st.success(f"✅ File validation passed! Found {len(df)} roles to copy.")
                
                # Start automation button
                if st.button("🚀 Start Role Copying", key="copy_role_btn"):
                    if not os.environ.get("BIP_USERNAME") or not os.environ.get("BIP_PASSWORD"):
                        st.error("❌ Please configure your Oracle credentials in the sidebar first!")
                    else:
                        with st.spinner("🔄 Copying roles..."):
                            try:
                                # Save uploaded file temporarily
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                                    tmp_file.write(uploaded_file.getvalue())
                                    tmp_file_path = tmp_file.name
                                
                                # Change to the directory with the automation script
                                original_dir = os.getcwd()
                                script_dir = os.path.dirname(os.path.abspath(__file__))
                                os.chdir(script_dir)
                                
                                # Set the input file path for the automation script
                                os.environ["INPUT_FILE_PATH"] = tmp_file_path
                                
                                # Run the automation
                                copy_role_main()
                                
                                # Return to original directory
                                os.chdir(original_dir)
                                
                                st.success("✅ Role copying completed successfully!")
                                
                                # Show results
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('role_copy_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    st.subheader("📊 Results")
                                    st.dataframe(result_df)
                                    
                                    # Download button
                                    csv = result_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Results",
                                        data=csv,
                                        file_name=f"role_copy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                                
                            except Exception as e:
                                st.error(f"❌ Error during role copying: {str(e)}")
                            finally:
                                # Cleanup
                                if 'tmp_file_path' in locals():
                                    os.unlink(tmp_file_path)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def show_duty_role_page():
    # Back to Home button
    if st.button("🏠 Back to Home", key="duty_role_back"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    
    st.header("👥 Duty Role Management")
    
    st.markdown("""
    <div class="info-message">
        <strong>Instructions:</strong> Upload an Excel file with duty role specifications. The file should contain columns: 
        <code>Existing Role Name to Edit</code>, <code>Existing Role Code</code>, <code>Duty Role Name</code>, <code>Duty Role Code</code>, <code>Action</code> (ADD/DELETE)
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Excel file for duty role management",
        type=['xlsx', 'xls'],
        help="Upload Excel file with duty role specifications"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.subheader("📋 File Preview")
            st.dataframe(df.head())
            
            # Validate required columns
            required_columns = {'Existing Role Name to Edit', 'Existing Role Code', 'Duty Role Name', 'Duty Role Code', 'Action'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
            else:
                st.success(f"✅ File validation passed! Found {len(df)} duty role operations.")
                
                # Start automation button
                if st.button("🚀 Start Duty Role Management", key="duty_role_btn"):
                    if not os.environ.get("BIP_USERNAME") or not os.environ.get("BIP_PASSWORD"):
                        st.error("❌ Please configure your Oracle credentials in the sidebar first!")
                    else:
                        with st.spinner("🔄 Managing duty roles..."):
                            try:
                                # Save uploaded file temporarily
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                                    tmp_file.write(uploaded_file.getvalue())
                                    tmp_file_path = tmp_file.name
                                
                                # Change to the directory with the automation script
                                original_dir = os.getcwd()
                                script_dir = os.path.dirname(os.path.abspath(__file__))
                                os.chdir(script_dir)
                                
                                # Set the input file path for the automation script
                                os.environ["INPUT_FILE_PATH"] = tmp_file_path
                                
                                # Run the automation
                                duty_role_main()
                                
                                # Return to original directory
                                os.chdir(original_dir)
                                
                                st.success("✅ Duty role management completed successfully!")
                                
                                # Show results
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('duty_role_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    st.subheader("📊 Results")
                                    st.dataframe(result_df)
                                    
                                    # Download button
                                    csv = result_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Results",
                                        data=csv,
                                        file_name=f"duty_role_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                                
                            except Exception as e:
                                st.error(f"❌ Error during duty role management: {str(e)}")
                            finally:
                                # Cleanup
                                if 'tmp_file_path' in locals():
                                    os.unlink(tmp_file_path)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def show_privilege_management_page():
    # Back to Home button
    if st.button("🏠 Back to Home", key="privilege_back"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    
    st.header("🔑 Privilege Management")
    
    st.markdown("""
    <div class="info-message">
        <strong>Instructions:</strong> Upload an Excel file with privilege specifications. The file should contain columns: 
        <code>Existing Role Name to Edit</code>, <code>Existing Role Code</code>, <code>Privilege Code</code>, <code>Privilege Name</code>, <code>Action</code> (ADD/DELETE)
    </div>
    """, unsafe_allow_html=True)
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose Excel file for privilege management",
        type=['xlsx', 'xls'],
        help="Upload Excel file with privilege specifications"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.subheader("📋 File Preview")
            st.dataframe(df.head())
            
            # Validate required columns
            required_columns = {'Existing Role Name to Edit', 'Existing Role Code', 'Privilege Code', 'Privilege Name', 'Action'}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {missing_columns}")
            else:
                st.success(f"✅ File validation passed! Found {len(df)} privilege operations.")
                
                # Start automation button
                if st.button("🚀 Start Privilege Management", key="privilege_btn"):
                    if not os.environ.get("BIP_USERNAME") or not os.environ.get("BIP_PASSWORD"):
                        st.error("❌ Please configure your Oracle credentials in the sidebar first!")
                    else:
                        with st.spinner("🔄 Managing privileges..."):
                            try:
                                # Save uploaded file temporarily
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                                    tmp_file.write(uploaded_file.getvalue())
                                    tmp_file_path = tmp_file.name
                                
                                # Change to the directory with the automation script
                                original_dir = os.getcwd()
                                script_dir = os.path.dirname(os.path.abspath(__file__))
                                os.chdir(script_dir)
                                
                                # Set the input file path for the automation script
                                os.environ["INPUT_FILE_PATH"] = tmp_file_path
                                
                                # Run the automation
                                privilege_management_main()
                                
                                # Return to original directory
                                os.chdir(original_dir)
                                
                                st.success("✅ Privilege management completed successfully!")
                                
                                # Show results
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('privilege_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    st.subheader("📊 Results")
                                    st.dataframe(result_df)
                                    
                                    # Download button
                                    csv = result_df.to_csv(index=False)
                                    st.download_button(
                                        label="📥 Download Results",
                                        data=csv,
                                        file_name=f"privilege_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                        mime="text/csv"
                                    )
                                
                            except Exception as e:
                                st.error(f"❌ Error during privilege management: {str(e)}")
                            finally:
                                # Cleanup
                                if 'tmp_file_path' in locals():
                                    os.unlink(tmp_file_path)
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def show_diagnostics_page():
    # Back to Home button
    if st.button("🏠 Back to Home", key="diagnostics_back"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    
    st.header("🔧 System Diagnostics")
    
    st.markdown("""
    <div class="info-message">
        <strong>Purpose:</strong> This page helps diagnose ChromeDriver and system issues on Streamlit Cloud deployment.
        Run diagnostics to understand what's happening with the ChromeDriver setup.
    </div>
    """, unsafe_allow_html=True)
    
    # Run diagnostics button
    if st.button("🔍 Run System Diagnostics", key="run_diagnostics"):
        with st.spinner("Running diagnostics..."):
            try:
                # Capture diagnostic output
                import subprocess
                import sys
                import io
                
                # Redirect stdout to capture output
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                
                try:
                    # Import and run diagnostics
                    from diagnose_chromedriver import main as run_diagnostics
                    run_diagnostics()
                    
                    # Get the output
                    diagnostic_output = new_stdout.getvalue()
                    
                    # Display results
                    st.subheader("📊 Diagnostic Results")
                    st.code(diagnostic_output, language="text")
                    
                    # Save diagnostic results
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    diagnostic_file = f"diagnostic_results_{timestamp}.txt"
                    
                    with open(diagnostic_file, 'w') as f:
                        f.write(diagnostic_output)
                    
                    st.success(f"✅ Diagnostics completed! Results saved to {diagnostic_file}")
                    
                    # Download button for diagnostic results
                    st.download_button(
                        label="📥 Download Diagnostic Results",
                        data=diagnostic_output,
                        file_name=diagnostic_file,
                        mime="text/plain"
                    )
                    
                finally:
                    # Restore stdout
                    sys.stdout = old_stdout
                    
            except Exception as e:
                st.error(f"❌ Error running diagnostics: {str(e)}")
                st.error("This might indicate that the diagnostic script is not available or has issues.")
    
    # ChromeDriver test button
    st.markdown("---")
    st.subheader("🧪 ChromeDriver Test")
    
    if st.button("🚀 Test ChromeDriver Initialization", key="test_chromedriver"):
        with st.spinner("Testing ChromeDriver..."):
            try:
                # Import and test ChromeDriver
                from chromedriver_fix import test_chromedriver
                
                # Capture output
                import io
                import sys
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                
                try:
                    success = test_chromedriver()
                    
                    # Get the output
                    test_output = new_stdout.getvalue()
                    
                    # Display results
                    st.subheader("📊 ChromeDriver Test Results")
                    st.code(test_output, language="text")
                    
                    if success:
                        st.success("✅ ChromeDriver test passed!")
                    else:
                        st.error("❌ ChromeDriver test failed!")
                        
                finally:
                    # Restore stdout
                    sys.stdout = old_stdout
                    
            except Exception as e:
                st.error(f"❌ Error testing ChromeDriver: {str(e)}")
    
    # Manual ChromeDriver download test
    st.markdown("---")
    st.subheader("📥 Manual ChromeDriver Download Test")
    
    chrome_version = st.text_input("Chrome Version (e.g., 120.0.6099.224)", value="120.0.6099.224")
    
    if st.button("🔍 Test ChromeDriver Download", key="test_download"):
        with st.spinner("Testing ChromeDriver download..."):
            try:
                from chromedriver_fix import download_chromedriver_for_version
                
                # Capture output
                import io
                import sys
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                
                try:
                    chromedriver_path = download_chromedriver_for_version(chrome_version)
                    
                    # Get the output
                    download_output = new_stdout.getvalue()
                    
                    # Display results
                    st.subheader("📊 Download Test Results")
                    st.code(download_output, language="text")
                    
                    if chromedriver_path:
                        st.success(f"✅ ChromeDriver downloaded successfully to: {chromedriver_path}")
                    else:
                        st.error("❌ ChromeDriver download failed!")
                        
                finally:
                    # Restore stdout
                    sys.stdout = old_stdout
                    
            except Exception as e:
                st.error(f"❌ Error testing download: {str(e)}")

def show_results_page():
    # Back to Home button
    if st.button("🏠 Back to Home", key="results_back"):
        st.session_state.current_page = "🏠 Home"
        st.rerun()
    
    st.header("📊 Results & Analytics")
    
    # Get all result files
    script_dir = os.path.dirname(os.path.abspath(__file__))
    result_files = []
    
    for file in os.listdir(script_dir):
        if file.endswith('.xlsx') and any(prefix in file for prefix in ['role_create_results_', 'role_copy_results_', 'duty_role_results_', 'privilege_results_']):
            result_files.append(file)
    
    if not result_files:
        st.info("📭 No result files found. Run some operations first to see results here.")
        return
    
    # Show latest results
    st.subheader("📈 Latest Results")
    
    for result_file in sorted(result_files, key=lambda x: os.path.getctime(os.path.join(script_dir, x)), reverse=True)[:5]:
        try:
            df = pd.read_excel(os.path.join(script_dir, result_file))
            
            # Create expander for each result file
            with st.expander(f"📄 {result_file} ({len(df)} records)"):
                st.dataframe(df)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    success_count = len(df[df['Status'] == 'Success']) if 'Status' in df.columns else 0
                    st.metric("Success", success_count)
                with col3:
                    failed_count = len(df[df['Status'] == 'Failed']) if 'Status' in df.columns else 0
                    st.metric("Failed", failed_count)
                
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label=f"📥 Download {result_file}",
                    data=csv,
                    file_name=result_file.replace('.xlsx', '.csv'),
                    mime="text/csv"
                )
        
        except Exception as e:
            st.error(f"❌ Error reading {result_file}: {str(e)}")

if __name__ == "__main__":
    main()
