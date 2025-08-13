import pandas as pd
import os
from datetime import datetime

def create_sample_templates():
    """Create sample Excel template files for each operation"""
    
    # Create templates directory if it doesn't exist
    templates_dir = "sample_templates"
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # 1. Create Role Template
    create_role_data = {
        'Role Name': [
            'Sample Role 1',
            'Sample Role 2',
            'Sample Role 3'
        ],
        'Role Code': [
            'SAMPLE_ROLE_001',
            'SAMPLE_ROLE_002',
            'SAMPLE_ROLE_003'
        ],
        'Role Category': [
            'Application Role',
            'Job Role',
            'Abstract Role'
        ]
    }
    
    create_role_df = pd.DataFrame(create_role_data)
    create_role_df.to_excel(f"{templates_dir}/create_role_template.xlsx", index=False)
    
    # 2. Copy Role Template
    copy_role_data = {
        'Existing Role Name': [
            'Source Role 1',
            'Source Role 2'
        ],
        'Existing Role Code': [
            'SOURCE_ROLE_001',
            'SOURCE_ROLE_002'
        ],
        'New Role Name': [
            'Copied Role 1',
            'Copied Role 2'
        ],
        'New Role Code': [
            'COPIED_ROLE_001',
            'COPIED_ROLE_002'
        ]
    }
    
    copy_role_df = pd.DataFrame(copy_role_data)
    copy_role_df.to_excel(f"{templates_dir}/copy_role_template.xlsx", index=False)
    
    # 3. Duty Role Management Template
    duty_role_data = {
        'Existing Role Name to Edit': [
            'Target Role 1',
            'Target Role 2',
            'Target Role 3'
        ],
        'Existing Role Code': [
            'TARGET_ROLE_001',
            'TARGET_ROLE_002',
            'TARGET_ROLE_003'
        ],
        'Duty Role Name': [
            'Duty Role 1',
            'Duty Role 2',
            'Duty Role 3'
        ],
        'Duty Role Code': [
            'DUTY_ROLE_001',
            'DUTY_ROLE_002',
            'DUTY_ROLE_003'
        ],
        'Action': [
            'ADD',
            'DELETE',
            'ADD'
        ]
    }
    
    duty_role_df = pd.DataFrame(duty_role_data)
    duty_role_df.to_excel(f"{templates_dir}/duty_role_template.xlsx", index=False)
    
    # 4. Privilege Management Template
    privilege_data = {
        'Existing Role Name to Edit': [
            'Target Role 1',
            'Target Role 2',
            'Target Role 3'
        ],
        'Existing Role Code': [
            'TARGET_ROLE_001',
            'TARGET_ROLE_002',
            'TARGET_ROLE_003'
        ],
        'Privilege Name': [
            'Sample Privilege 1',
            'Sample Privilege 2',
            'Sample Privilege 3'
        ],
        'Action': [
            'ADD',
            'DELETE',
            'ADD'
        ]
    }
    
    privilege_df = pd.DataFrame(privilege_data)
    privilege_df.to_excel(f"{templates_dir}/privilege_management_template.xlsx", index=False)
    
    print("✅ Sample templates created successfully!")
    print(f"📁 Templates saved in: {templates_dir}/")
    print("\n📋 Available templates:")
    print("  - create_role_template.xlsx")
    print("  - copy_role_template.xlsx")
    print("  - duty_role_template.xlsx")
    print("  - privilege_management_template.xlsx")
    print("\n💡 Use these templates as a starting point for your Excel files.")

if __name__ == "__main__":
    create_sample_templates()
