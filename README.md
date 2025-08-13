# 🔐 Oracle Cloud Role Management Automation - Streamlit App

A comprehensive web application for automating Oracle Cloud role management operations including role creation, copying, duty role management, and privilege management.

## 🚀 Features

### ✨ Core Functionality
- **➕ Create Role**: Batch creation of new roles with custom specifications
- **📋 Copy Role**: Duplicate existing roles with new names and codes
- **👥 Duty Role Management**: Add/remove duty roles from existing roles
- **🔑 Privilege Management**: Add/remove privileges within roles

### 🛡️ Robust Automation
- **Multi-selector fallback system**: Handles dynamic Oracle Cloud UI changes
- **Auto-managed ChromeDriver**: No manual driver downloads needed
- **Connection testing**: Verify credentials before running automation
- **Multi-environment support**: Choose between dev1, dev2, dev3 environments
- **Cloud-ready deployment**: Optimized for Streamlit Cloud
- **Comprehensive error handling**: Detailed logging and recovery

### 🎨 Modern UI
- **Intuitive web interface**: User-friendly Streamlit dashboard
- **Real-time progress tracking**: Live status updates during operations
- **File validation**: Automatic Excel file format checking
- **Results analytics**: Downloadable reports and statistics

## 📋 Prerequisites

### For Local Development
- Python 3.8+
- Chrome browser installed
- Oracle Cloud account with appropriate permissions

### For Cloud Deployment
- Streamlit Cloud account (free tier available)
- Oracle Cloud account with appropriate permissions

## 🛠️ Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd create-copy-oracle-roles
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   BIP_USERNAME=your_oracle_username
   BIP_PASSWORD=your_oracle_password
   ```

4. **Run the application**
   ```bash
   streamlit run streamlit_app.py
   ```

### Cloud Deployment (Streamlit Cloud)

1. **Prepare your repository**
   - Ensure all files are committed to GitHub
   - Verify `requirements.txt` is in the root directory
   - Make sure `streamlit_app.py` is the main entry point

2. **Deploy to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set the main file path to `streamlit_app.py`
   - Deploy!

3. **Configure credentials**
   - Use the sidebar in the deployed app to enter your Oracle credentials
   - Credentials are stored in session memory (not persisted)

## 📁 File Structure

```
create-copy-oracle-roles/
├── streamlit_app.py          # Main Streamlit application
├── create_role.py            # Role creation automation
├── copy_role.py              # Role copying automation
├── duty_role_management.py   # Duty role management automation
├── privilege_management.py   # Privilege management automation
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── .env                      # Environment variables (create locally)
```

## 📊 Excel File Formats

### Create Role
Required columns: `Role Name`, `Role Code`, `Role Category`

### Copy Role
Required columns: `Existing Role Name`, `Existing Role Code`, `New Role Name`, `New Role Code`

### Duty Role Management
Required columns: `Existing Role Name to Edit`, `Existing Role Code`, `Duty Role Name`, `Duty Role Code`, `Action` (ADD/DELETE)

### Privilege Management
Required columns: `Existing Role Name to Edit`, `Existing Role Code`, `Privilege Name`, `Action` (ADD/DELETE)

## 🔧 Technical Architecture

### ChromeDriver Management
- **Problem**: Large ChromeDriver files (18MB+) can't be uploaded to cloud platforms
- **Solution**: Uses `webdriver-manager` to automatically download the correct driver version
- **Benefits**: 
  - No manual driver management
  - Automatic version matching
  - Cloud deployment friendly
  - Cross-platform compatibility

### Robust Element Detection
- **Multi-selector fallback system**: Tries multiple selectors for each element
- **Dynamic class handling**: Adapts to Oracle Cloud UI changes
- **JavaScript interactions**: Bypasses overlay and clickability issues
- **Comprehensive error handling**: Detailed logging and recovery strategies

### Cloud Optimization
- **Session-based credentials**: Secure credential handling
- **Temporary file management**: Proper cleanup of uploaded files
- **Memory-efficient processing**: Optimized for cloud resource constraints
- **Error recovery**: Graceful handling of network and UI issues

## 🚀 Usage Guide

### 1. Access the Application
- **Local**: Open `http://localhost:8501` in your browser
- **Cloud**: Access your deployed Streamlit Cloud URL

### 2. Configure Credentials
- Select your Oracle environment (dev1, dev2, dev3) from the dropdown
- Enter your Oracle Cloud username and password
- Click "Test Connection" to verify your credentials before running automation
- Credentials are required for all operations

### 3. Choose Operation
- Navigate to the desired operation using the sidebar menu
- Each operation has its own dedicated page with instructions

### 4. Upload Excel File
- Prepare your Excel file according to the required format
- Upload the file using the file uploader
- The app will validate the file format and show a preview

### 5. Start Automation
- Click the "Start" button to begin the automation
- Monitor progress through the real-time status updates
- Download results when the operation completes

### 6. View Results
- Check the "Results" page for historical data
- Download CSV files of operation results
- Analyze success/failure statistics

## 🔒 Security Considerations

### Credential Management
- **Local deployment**: Use `.env` file for secure credential storage
- **Cloud deployment**: Enter credentials in the web interface (session-based)
- **No persistence**: Credentials are not stored permanently in cloud deployments

### Network Security
- **HTTPS only**: All cloud deployments use secure connections
- **Session isolation**: Each user session is isolated
- **Temporary files**: Uploaded files are cleaned up after processing

## 🐛 Troubleshooting

### Common Issues

#### ChromeDriver Issues
```bash
# If you encounter ChromeDriver problems locally:
pip install --upgrade webdriver-manager
```

#### File Upload Issues
- Ensure Excel files are in `.xlsx` or `.xls` format
- Check that required columns are present
- Verify file size is reasonable (< 10MB)

#### Authentication Issues
- Verify Oracle Cloud credentials are correct
- Ensure account has appropriate permissions
- Check if account is locked or requires MFA

#### Network Issues
- Verify internet connectivity
- Check Oracle Cloud service status
- Ensure firewall allows browser automation

### Debug Mode
For detailed debugging, you can run the individual automation scripts directly:
```bash
python create_role.py
python copy_role.py
python duty_role_management.py
python privilege_management.py
```

## 📈 Performance Optimization

### For Large Datasets
- Process files in batches of 50-100 records
- Monitor memory usage during long operations
- Use the progress tracking to monitor status

### For Cloud Deployment
- The app is optimized for Streamlit Cloud's resource constraints
- Automatic cleanup prevents memory leaks
- Efficient file handling for cloud environments

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Testing
- Test with various Excel file formats
- Verify all automation operations work correctly
- Test error handling scenarios
- Validate cloud deployment compatibility

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
- Check the troubleshooting section above
- Review the error messages in the application
- Check Oracle Cloud service status
- Verify your account permissions

### Reporting Issues
When reporting issues, please include:
- Operation being performed
- Error message details
- Excel file format (without sensitive data)
- Browser and system information
- Steps to reproduce the issue

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with all four automation modules
- Streamlit web interface
- Cloud deployment support
- Robust element detection system
- Comprehensive error handling

---

**Note**: This application is designed for Oracle Cloud environments. Ensure you have appropriate permissions and follow your organization's security policies when using this automation tool.
