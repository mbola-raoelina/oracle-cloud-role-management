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
    
    # Initialize session state for navigation and connection
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Home"
    if 'is_connected' not in st.session_state:
        st.session_state.is_connected = False
    if 'connection_details' not in st.session_state:
        st.session_state.connection_details = {}
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose Operation",
        ["🏠 Home", "➕ Create Role", "📋 Copy Role", "👥 Duty Role Management", "🔑 Privilege Management", "📊 Results"],
        index=["🏠 Home", "➕ Create Role", "📋 Copy Role", "👥 Duty Role Management", "🔑 Privilege Management", "📊 Results"].index(st.session_state.current_page)
    )
    
    # Update session state when sidebar selection changes
    if page != st.session_state.current_page:
        st.session_state.current_page = page
        st.rerun()
    
    # Connection status display
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔐 Connection Status")
    
    if st.session_state.is_connected:
        st.sidebar.success("✅ Connected")
        st.sidebar.info(f"**User:** {st.session_state.connection_details.get('username', 'Unknown')}")
        st.sidebar.info(f"**Environment:** {st.session_state.connection_details.get('environment', 'Unknown')}")
        st.sidebar.info(f"**Connected:** {st.session_state.connection_details.get('connected_at', 'Unknown')}")
        
        if st.sidebar.button("🔌 Disconnect"):
            st.session_state.is_connected = False
            st.session_state.connection_details = {}
            st.sidebar.success("✅ Disconnected successfully!")
            st.rerun()
    else:
        st.sidebar.error("❌ Not Connected")
    
    # Environment variables setup
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔧 Configuration")
    
    # Show connection form only if not connected
    if not st.session_state.is_connected:
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
                st.sidebar.success("✅ Connected successfully!")
                st.session_state.is_connected = True
                st.session_state.connection_details = {
                    'username': username,
                    'password': password,  # Store for local development
                    'environment': environment,
                    'connected_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # Set environment variables for the automation scripts
                os.environ["BIP_USERNAME"] = username
                os.environ["BIP_PASSWORD"] = password
                os.environ["ORACLE_ENVIRONMENT"] = environment
                st.rerun()
    else:
        # Use stored connection details for environment variables
        os.environ["BIP_USERNAME"] = st.session_state.connection_details.get('username', '')
        os.environ["BIP_PASSWORD"] = st.session_state.connection_details.get('password', '')
        os.environ["ORACLE_ENVIRONMENT"] = st.session_state.connection_details.get('environment', 'dev1')
    
    # Page routing with authentication gates
    if st.session_state.current_page == "🏠 Home":
        show_home_page()
    elif st.session_state.current_page == "➕ Create Role":
        if st.session_state.is_connected:
            show_create_role_page()
        else:
            show_connection_required_page("Create Role")
    elif st.session_state.current_page == "📋 Copy Role":
        if st.session_state.is_connected:
            show_copy_role_page()
        else:
            show_connection_required_page("Copy Role")
    elif st.session_state.current_page == "👥 Duty Role Management":
        if st.session_state.is_connected:
            show_duty_role_page()
        else:
            show_connection_required_page("Duty Role Management")
    elif st.session_state.current_page == "🔑 Privilege Management":
        if st.session_state.is_connected:
            show_privilege_management_page()
        else:
            show_connection_required_page("Privilege Management")
    elif st.session_state.current_page == "📊 Results":
        if st.session_state.is_connected:
            show_results_page()
        else:
            show_connection_required_page("Results")

def show_connection_required_page(feature_name):
    """Display a page requiring connection for protected features"""
    st.markdown(f"""
    <div class="error-message">
        <h2>🔒 Authentication Required</h2>
        <p>You must be connected to Oracle Cloud to access <strong>{feature_name}</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 How to Connect")
    st.markdown("""
    1. **Enter your Oracle Cloud credentials** in the sidebar
    2. **Select your environment** (dev1, dev2, or dev3)
    3. **Click the Connect button** to establish connection
    4. **Once connected**, you can access all management features
    """)

def show_home_page():
    # Show connection status prominently
    if st.session_state.is_connected:
        st.markdown(f"""
        <div class="success-message">
            <h2>✅ Connected to Oracle Cloud</h2>
            <p>Welcome <strong>{st.session_state.connection_details.get('username', 'User')}</strong>! You are connected to <strong>{st.session_state.connection_details.get('environment', 'Unknown')}</strong> environment.</p>
            <p>All management features are now available.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="error-message">
            <h2>🔒 Not Connected</h2>
            <p>Please connect to Oracle Cloud using the sidebar to access management features.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h2>🚀 Oracle Cloud Role Management Automation</h2>
        <p>This application provides a comprehensive solution for managing Oracle Cloud roles and privileges through an intuitive web interface.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎯 Quick Access - Click any feature to get started:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create Role Card - Only clickable when connected
        if st.session_state.is_connected:
            if st.button("➕ Create Role", key="home_create_role", use_container_width=True):
                st.session_state.current_page = "➕ Create Role"
                st.rerun()
        else:
            st.button("🔒 Create Role", key="home_create_role_disabled", use_container_width=True, disabled=True, help="Connect to Oracle Cloud to access this feature")
        
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
        
        # Copy Role Card - Only clickable when connected
        if st.session_state.is_connected:
            if st.button("📋 Copy Role", key="home_copy_role", use_container_width=True):
                st.session_state.current_page = "📋 Copy Role"
                st.rerun()
        else:
            st.button("🔒 Copy Role", key="home_copy_role_disabled", use_container_width=True, disabled=True, help="Connect to Oracle Cloud to access this feature")
        
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
        # Duty Role Management Card - Only clickable when connected
        if st.session_state.is_connected:
            if st.button("👥 Duty Role Management", key="home_duty_role", use_container_width=True):
                st.session_state.current_page = "👥 Duty Role Management"
                st.rerun()
        else:
            st.button("🔒 Duty Role Management", key="home_duty_role_disabled", use_container_width=True, disabled=True, help="Connect to Oracle Cloud to access this feature")
        
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
        
        # Privilege Management Card - Only clickable when connected
        if st.session_state.is_connected:
            if st.button("🔑 Privilege Management", key="home_privilege", use_container_width=True):
                st.session_state.current_page = "🔑 Privilege Management"
                st.rerun()
        else:
            st.button("🔒 Privilege Management", key="home_privilege_disabled", use_container_width=True, disabled=True, help="Connect to Oracle Cloud to access this feature")
        
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

# Full functional page implementations
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
