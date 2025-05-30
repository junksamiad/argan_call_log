#!/usr/bin/env python3
"""
Airtable Setup Script
Sets up the required table and fields for the Argan HR Email Management System
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "call_log")

# Airtable API endpoints
TABLES_URL = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_BASE_ID}/tables"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

def check_credentials():
    """Check if Airtable credentials are configured"""
    if not AIRTABLE_API_KEY:
        print("❌ AIRTABLE_API_KEY not found in .env file")
        return False
    if not AIRTABLE_BASE_ID:
        print("❌ AIRTABLE_BASE_ID not found in .env file")
        return False
    print("✅ Airtable credentials found")
    return True

def get_base_schema():
    """Get the current base schema"""
    try:
        response = requests.get(TABLES_URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get base schema: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Error getting base schema: {e}")
        return None

def find_table(schema, table_name):
    """Find a table in the schema by name"""
    if not schema or 'tables' not in schema:
        return None
    
    for table in schema['tables']:
        if table['name'] == table_name:
            return table
    return None

def create_table_with_fields():
    """Create the table with required fields"""
    print(f"🔨 Creating table '{TABLE_NAME}' with required fields...")
    
    table_data = {
        "name": TABLE_NAME,
        "description": "Email log for Argan HR Consultancy - tracks all incoming emails and tickets",
        "fields": [
            {
                "name": "Ticket Number",
                "type": "singleLineText",
                "description": "Unique ticket identifier (e.g., ARG-12345)"
            },
            {
                "name": "Subject", 
                "type": "multilineText",
                "description": "Email subject line"
            },
            {
                "name": "Sender Email",
                "type": "email",
                "description": "Email address of the sender"
            },
            {
                "name": "Recipients",
                "type": "multilineText", 
                "description": "Comma-separated list of recipients"
            },
            {
                "name": "Body Text",
                "type": "multilineText",
                "description": "Plain text version of email body"
            },
            {
                "name": "Body HTML",
                "type": "multilineText",
                "description": "HTML version of email body"
            },
            {
                "name": "Direction",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Inbound", "color": "blueLight2"},
                        {"name": "Outbound", "color": "greenLight2"}
                    ]
                },
                "description": "Email direction"
            },
            {
                "name": "Message Type",
                "type": "singleSelect", 
                "options": {
                    "choices": [
                        {"name": "Initial Email", "color": "orangeLight2"},
                        {"name": "Reply", "color": "purpleLight2"}
                    ]
                },
                "description": "Type of message"
            },
            {
                "name": "Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Open", "color": "redLight2"},
                        {"name": "Active", "color": "yellowLight2"},
                        {"name": "Closed", "color": "greenLight2"},
                        {"name": "Pending", "color": "grayLight2"}
                    ]
                },
                "description": "Current status of the ticket"
            },
            {
                "name": "Created At",
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                },
                "description": "When the email was received"
            },
            {
                "name": "Raw Headers",
                "type": "multilineText",
                "description": "Raw email headers for debugging"
            },
            {
                "name": "Attachments",
                "type": "multilineText",
                "description": "List of attachment filenames"
            }
        ]
    }
    
    try:
        response = requests.post(TABLES_URL, headers=HEADERS, json=table_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully created table '{TABLE_NAME}' with all fields!")
            print(f"📋 Table ID: {result.get('id', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to create table: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def main():
    print("🚀 Setting up Airtable for Argan HR Email Management System")
    print("=" * 60)
    
    # Check credentials
    if not check_credentials():
        print("\n📝 Please update your .env file with:")
        print("AIRTABLE_API_KEY=your-api-key")
        print("AIRTABLE_BASE_ID=your-base-id")
        return
    
    # Get current schema
    print(f"\n🔍 Checking base schema...")
    schema = get_base_schema()
    if not schema:
        return
    
    # Check if table exists
    existing_table = find_table(schema, TABLE_NAME)
    if existing_table:
        print(f"✅ Table '{TABLE_NAME}' already exists!")
        print(f"📊 Current fields: {len(existing_table.get('fields', []))} fields")
        
        # List current fields
        if 'fields' in existing_table:
            print("\n📋 Current fields:")
            for field in existing_table['fields']:
                print(f"   - {field['name']} ({field['type']})")
        
        print(f"\n💡 If you need to add missing fields, you can do so manually in Airtable")
        print(f"   or delete the table '{TABLE_NAME}' and run this script again to recreate it.")
    else:
        print(f"❌ Table '{TABLE_NAME}' not found")
        print(f"🔨 Creating table with all required fields...")
        
        if create_table_with_fields():
            print(f"\n✅ Setup complete! Your Airtable is ready to receive emails.")
        else:
            print(f"\n❌ Setup failed. Please check your credentials and try again.")
    
    print(f"\n📋 Next steps:")
    print(f"1. Make sure your .env file has: AIRTABLE_TABLE_NAME={TABLE_NAME}")
    print(f"2. Start your server: export PYTHONPATH=\"${{PYTHONPATH}}:$(pwd)\" && uvicorn backend.main:app --reload")
    print(f"3. Use ngrok to expose your server for SendGrid webhooks")

if __name__ == "__main__":
    main() 