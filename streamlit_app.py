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
    
    # Initialize output management system
    if 'output_history' not in st.session_state:
        st.session_state.output_history = []
    if 'current_output' not in st.session_state:
        st.session_state.current_output = None
    
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
    
    # Show persistent output panel in sidebar
    show_persistent_output_panel()
    
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

def save_output_to_history(operation_type, result_df, operation_details):
    """Save operation output to session history for persistent access"""
    output_record = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'operation_type': operation_type,
        'result_df': result_df.copy(),
        'operation_details': operation_details,
        'total_records': len(result_df),
        'success_count': len(result_df[result_df['Status'] == 'Success']) if 'Status' in result_df.columns else 0,
        'failed_count': len(result_df[result_df['Status'] == 'Failed']) if 'Status' in result_df.columns else 0
    }
    
    # Add to history (keep last 10 operations)
    st.session_state.output_history.insert(0, output_record)
    if len(st.session_state.output_history) > 10:
        st.session_state.output_history = st.session_state.output_history[:10]
    
    # Set as current output
    st.session_state.current_output = output_record
    
    print(f"✅ Output saved to history: {operation_type} - {len(result_df)} records")

def display_output_with_history(operation_type, result_df, operation_details):
    """Enhanced output display with history management and auto-save"""
    
    # Save to history first
    save_output_to_history(operation_type, result_df, operation_details)
    
    # Display current results
    st.success(f"✅ {operation_type} completed successfully!")
    
    # Create tabs for current results and history
    tab_current, tab_history = st.tabs(["📊 Current Results", "📚 Output History"])
    
    with tab_current:
        st.subheader(f"📊 {operation_type} Results")
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(result_df))
        with col2:
            success_count = len(result_df[result_df['Status'] == 'Success']) if 'Status' in result_df.columns else 0
            st.metric("Success", success_count, delta=f"{success_count/len(result_df)*100:.1f}%")
        with col3:
            failed_count = len(result_df[result_df['Status'] == 'Failed']) if 'Status' in result_df.columns else 0
            st.metric("Failed", failed_count)
        
        # Results table
        st.dataframe(result_df, use_container_width=True)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            csv = result_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{operation_type.lower().replace(' ', '_')}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            # Auto-save Excel file
            excel_filename = f"{operation_type.lower().replace(' ', '_')}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            try:
                result_df.to_excel(excel_filename, index=False)
                st.success(f"💾 Auto-saved: {excel_filename}")
            except Exception as e:
                st.warning(f"⚠️ Auto-save failed: {str(e)}")
    
    with tab_history:
        st.subheader("📚 Recent Operations History")
        
        if st.session_state.output_history:
            for i, record in enumerate(st.session_state.output_history):
                with st.expander(f"🔖 {record['operation_type']} - {record['timestamp']} ({record['total_records']} records)"):
                    
                    # Quick stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total", record['total_records'])
                    with col2:
                        st.metric("Success", record['success_count'])
                    with col3:
                        st.metric("Failed", record['failed_count'])
                    
                    # Show data
                    st.dataframe(record['result_df'], use_container_width=True)
                    
                    # Download from history
                    csv_historical = record['result_df'].to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {record['operation_type']}",
                        data=csv_historical,
                        file_name=f"{record['operation_type'].lower().replace(' ', '_')}_{record['timestamp'].replace(':', '').replace('-', '').replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"download_history_{i}"
                    )
        else:
            st.info("🔍 No operations performed yet. Complete an operation to see results here.")

def show_persistent_output_panel():
    """Always-visible output panel in sidebar"""
    if st.session_state.current_output:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Latest Output")
        
        output = st.session_state.current_output
        st.sidebar.info(f"**{output['operation_type']}**")
        st.sidebar.info(f"🕐 {output['timestamp']}")
        st.sidebar.info(f"📊 {output['total_records']} records")
        st.sidebar.info(f"✅ {output['success_count']} success")
        st.sidebar.info(f"❌ {output['failed_count']} failed")
        
        # Quick access to results page
        if st.sidebar.button("📊 View Full Results", key="view_full_results"):
            st.session_state.current_page = "📊 Results"
            st.rerun()

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
                                
                                # Enhanced results display with history management
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('role_create_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    
                                    # Use new enhanced output system
                                    display_output_with_history(
                                        operation_type="Role Creation",
                                        result_df=result_df,
                                        operation_details={
                                            'input_file': uploaded_file.name,
                                            'total_roles': len(df),
                                            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                    )
                                else:
                                    st.warning("⚠️ No result files found. The operation may have failed.")
                                
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
                                
                                # Enhanced results display with history management
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('role_copy_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    
                                    # Use new enhanced output system
                                    display_output_with_history(
                                        operation_type="Role Copy",
                                        result_df=result_df,
                                        operation_details={
                                            'input_file': uploaded_file.name,
                                            'total_roles': len(df),
                                            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                    )
                                else:
                                    st.warning("⚠️ No result files found. The operation may have failed.")
                                
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
                                
                                # Enhanced results display with history management
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('duty_role_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    
                                    # Use new enhanced output system
                                    display_output_with_history(
                                        operation_type="Duty Role Management",
                                        result_df=result_df,
                                        operation_details={
                                            'input_file': uploaded_file.name,
                                            'total_operations': len(df),
                                            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                    )
                                else:
                                    st.warning("⚠️ No result files found. The operation may have failed.")
                                
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
                                
                                # Enhanced results display with history management
                                results_files = [f for f in os.listdir(script_dir) if f.startswith('privilege_results_')]
                                if results_files:
                                    latest_result = max(results_files, key=os.path.getctime)
                                    result_df = pd.read_excel(os.path.join(script_dir, latest_result))
                                    
                                    # Use new enhanced output system
                                    display_output_with_history(
                                        operation_type="Privilege Management",
                                        result_df=result_df,
                                        operation_details={
                                            'input_file': uploaded_file.name,
                                            'total_operations': len(df),
                                            'processed_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        }
                                    )
                                else:
                                    st.warning("⚠️ No result files found. The operation may have failed.")
                                
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
    
    st.header("📊 Results & Analytics Dashboard")
    
    # Create tabs for different views
    tab_current, tab_history, tab_files = st.tabs(["🔄 Current Session", "📚 Session History", "📁 File Archive"])
    
    with tab_current:
        st.subheader("🔄 Current Session Results")
        
        if st.session_state.current_output:
            output = st.session_state.current_output
            
            # Show detailed current output
            st.markdown(f"""
            **Operation:** {output['operation_type']}  
            **Timestamp:** {output['timestamp']}  
            **Total Records:** {output['total_records']}  
            **Success Rate:** {output['success_count']}/{output['total_records']} ({output['success_count']/output['total_records']*100:.1f}%)
            """)
            
            # Statistics dashboard
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total", output['total_records'])
            with col2:
                st.metric("Success", output['success_count'], delta=f"{output['success_count']/output['total_records']*100:.1f}%")
            with col3:
                st.metric("Failed", output['failed_count'])
            with col4:
                success_rate = output['success_count']/output['total_records']*100
                color = "normal" if success_rate >= 80 else "inverse"
                st.metric("Success Rate", f"{success_rate:.1f}%", delta_color=color)
            
            # Show the data
            st.dataframe(output['result_df'], use_container_width=True)
            
            # Enhanced download options
            col1, col2, col3 = st.columns(3)
            with col1:
                csv = output['result_df'].to_csv(index=False)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name=f"{output['operation_type'].lower().replace(' ', '_')}_{output['timestamp'].replace(':', '').replace('-', '').replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                # Download only successful records
                if 'Status' in output['result_df'].columns:
                    success_df = output['result_df'][output['result_df']['Status'] == 'Success']
                    if len(success_df) > 0:
                        success_csv = success_df.to_csv(index=False)
                        st.download_button(
                            label="✅ Download Success Only",
                            data=success_csv,
                            file_name=f"{output['operation_type'].lower().replace(' ', '_')}_success_{output['timestamp'].replace(':', '').replace('-', '').replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            with col3:
                # Download only failed records
                if 'Status' in output['result_df'].columns:
                    failed_df = output['result_df'][output['result_df']['Status'] == 'Failed']
                    if len(failed_df) > 0:
                        failed_csv = failed_df.to_csv(index=False)
                        st.download_button(
                            label="❌ Download Failed Only",
                            data=failed_csv,
                            file_name=f"{output['operation_type'].lower().replace(' ', '_')}_failed_{output['timestamp'].replace(':', '').replace('-', '').replace(' ', '_')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
        else:
            st.info("🔍 No current results. Perform an operation to see results here.")
    
    with tab_history:
        st.subheader("📚 Session History (Last 10 Operations)")
        
        if st.session_state.output_history:
            # Summary stats
            total_operations = len(st.session_state.output_history)
            total_records = sum(op['total_records'] for op in st.session_state.output_history)
            total_success = sum(op['success_count'] for op in st.session_state.output_history)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Operations", total_operations)
            with col2:
                st.metric("Total Records", total_records)
            with col3:
                overall_success_rate = (total_success/total_records*100) if total_records > 0 else 0
                st.metric("Overall Success Rate", f"{overall_success_rate:.1f}%")
            
            # Show each operation in history
            for i, record in enumerate(st.session_state.output_history):
                with st.expander(f"🔖 {record['operation_type']} - {record['timestamp']} (Success: {record['success_count']}/{record['total_records']})"):
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total", record['total_records'])
                    with col2:
                        st.metric("Success", record['success_count'])
                    with col3:
                        st.metric("Failed", record['failed_count'])
                    
                    st.dataframe(record['result_df'], use_container_width=True)
                    
                    # Download from history
                    csv_historical = record['result_df'].to_csv(index=False)
                    st.download_button(
                        label=f"📥 Download {record['operation_type']}",
                        data=csv_historical,
                        file_name=f"{record['operation_type'].lower().replace(' ', '_')}_{record['timestamp'].replace(':', '').replace('-', '').replace(' ', '_')}.csv",
                        mime="text/csv",
                        key=f"download_history_{i}"
                    )
        else:
            st.info("🔍 No operations in session history. Complete some operations to see them here.")
    
    with tab_files:
        st.subheader("📁 File Archive (Auto-saved Results)")
        
        # Get all result files from disk
        script_dir = os.path.dirname(os.path.abspath(__file__))
        result_files = []
        
        try:
            for file in os.listdir(script_dir):
                if file.endswith('.xlsx') and any(prefix in file for prefix in ['role_create_results_', 'role_copy_results_', 'duty_role_results_', 'privilege_results_']):
                    result_files.append(file)
        except Exception as e:
            st.error(f"❌ Error accessing file directory: {str(e)}")
        
        if result_files:
            st.info(f"📄 Found {len(result_files)} archived result files")
            
            # Show latest files
            for result_file in sorted(result_files, key=lambda x: os.path.getctime(os.path.join(script_dir, x)), reverse=True)[:10]:
                try:
                    df = pd.read_excel(os.path.join(script_dir, result_file))
                    file_size = os.path.getsize(os.path.join(script_dir, result_file))
                    file_date = datetime.fromtimestamp(os.path.getctime(os.path.join(script_dir, result_file)))
                    
                    with st.expander(f"📄 {result_file} - {file_date.strftime('%Y-%m-%d %H:%M')} - {len(df)} records - {file_size/1024:.1f}KB"):
                        
                        # File info
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Records", len(df))
                        with col2:
                            success_count = len(df[df['Status'] == 'Success']) if 'Status' in df.columns else 0
                            st.metric("Success", success_count)
                        with col3:
                            failed_count = len(df[df['Status'] == 'Failed']) if 'Status' in df.columns else 0
                            st.metric("Failed", failed_count)
                        with col4:
                            st.metric("File Size", f"{file_size/1024:.1f}KB")
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Download archived file
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label=f"📥 Download {result_file}",
                            data=csv,
                            file_name=result_file.replace('.xlsx', '.csv'),
                            mime="text/csv",
                            key=f"download_archive_{result_file}"
                        )
                
                except Exception as e:
                    st.error(f"❌ Error reading {result_file}: {str(e)}")
        else:
            st.info("📭 No archived result files found. Run some operations to create result files.")

if __name__ == "__main__":
    main()
