#!/usr/bin/env python3
"""
Airtable Table Setup Script for HR Email Management System - Backend2
Verifies connection and provides manual table setup instructions

Run this script to verify your Airtable connection and get setup instructions.
"""

import os
import sys
from pyairtable import Api
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def create_airtable_table():
    """
    Create the argan_call_log table in Airtable using the Meta API
    """
    
    # Get Airtable credentials
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = "argan_call_log"
    
    if not api_key or not base_id:
        print("❌ Error: AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in .env file")
        return False
    
    try:
        print("🚀 Creating Airtable table...")
        print("=" * 60)
        print(f"📋 Base ID: {base_id}")
        print(f"📊 Table Name: {table_name}")
        print()
        
        # First check if table already exists
        api = Api(api_key)
        try:
            table = api.table(base_id, table_name)
            schema = table.schema()
            print("✅ Table already exists!")
            print(f"📊 Table has {len(schema.fields)} fields")
            return True
        except:
            print("📋 Table doesn't exist, creating it...")
        
        # Create table using Airtable Meta API
        url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Define the table schema
        table_schema = {
            "name": table_name,
            "description": "HR Email Management System - Email tickets and conversations",
            "fields": [
                {
                    "name": "ticket_number",
                    "type": "singleLineText",
                    "description": "Unique ticket identifier (ARG-YYYYMMDD-NNNN)"
                },
                {
                    "name": "status",
                    "type": "singleSelect",
                    "description": "Current status of the ticket",
                    "options": {
                        "choices": [
                            {"name": "new", "color": "redBright"},
                            {"name": "in_progress", "color": "yellowBright"},
                            {"name": "resolved", "color": "greenBright"},
                            {"name": "closed", "color": "grayBright"}
                        ]
                    }
                },
                {
                    "name": "created_at",
                    "type": "dateTime",
                    "description": "When the email was received and processed",
                    "options": {
                        "dateFormat": {"name": "iso"},
                        "timeFormat": {"name": "24hour"},
                        "timeZone": "utc"
                    }
                },
                {
                    "name": "subject",
                    "type": "singleLineText",
                    "description": "Email subject line"
                },
                {
                    "name": "email_body",
                    "type": "multilineText",
                    "description": "Email body content (text or HTML)"
                },
                {
                    "name": "original_sender",
                    "type": "email",
                    "description": "Original sender's email address (extracted from forwarded emails)"
                },
                {
                    "name": "message_id",
                    "type": "singleLineText",
                    "description": "Email Message-ID header for deduplication"
                },
                {
                    "name": "raw_headers",
                    "type": "multilineText",
                    "description": "Email headers for conversation linking (Message-ID, In-Reply-To, References)"
                },
                {
                    "name": "spf_result",
                    "type": "singleLineText",
                    "description": "SPF validation result from SendGrid"
                },
                {
                    "name": "dkim_result",
                    "type": "singleLineText",
                    "description": "DKIM validation result from SendGrid"
                },
                {
                    "name": "has_attachments",
                    "type": "checkbox",
                    "description": "Whether this email contains attachments",
                    "options": {
                        "icon": "check",
                        "color": "greenBright"
                    }
                },
                {
                    "name": "attachment_count",
                    "type": "number",
                    "description": "Number of attachments in the email",
                    "options": {
                        "precision": 0
                    }
                },
                {
                    "name": "attachment_info",
                    "type": "multilineText",
                    "description": "JSON data containing attachment details"
                },
                {
                    "name": "initial_auto_reply_sent",
                    "type": "checkbox",
                    "description": "Whether the initial auto-reply with ticket number was sent",
                    "options": {
                        "icon": "check",
                        "color": "blueBright"
                    }
                },
                {
                    "name": "initial_conversation_query",
                    "type": "multilineText",
                    "description": "JSON structure containing the initial customer query (sender_email, sender_email_date, sender_email_content)"
                },
                {
                    "name": "conversation_history",
                    "type": "multilineText",
                    "description": "JSON array containing all subsequent conversation entries parsed from forwarded email threads"
                }
            ]
        }
        
        print("📋 Creating table with 14 fields...")
        response = requests.post(url, headers=headers, json=table_schema)
        
        if response.status_code == 200:
            result = response.json()
            table_id = result.get('id')
            print(f"✅ Table '{table_name}' created successfully!")
            print(f"📊 Table ID: {table_id}")
            print(f"📋 Created {len(table_schema['fields'])} fields")
            print("=" * 60)
            print("🎉 Airtable setup complete!")
            print("\n✅ Your backend2 server can now connect to this table!")
            return True
        else:
            print(f"❌ Failed to create table. HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Error creating Airtable table: {e}")
        return False


def print_manual_setup_instructions():
    """
    Print instructions for manually creating the table in Airtable
    """
    print("\n📋 MANUAL SETUP REQUIRED")
    print("=" * 60)
    print("Please create the 'argan_call_log' table manually in Airtable:")
    print()
    print("1. Go to your Airtable base in the web interface")
    print("2. Create a new table named 'argan_call_log'")
    print("3. Add these fields with the specified types:")
    print()
    
    fields = [
        ("ticket_number", "Single line text"),
        ("status", "Single select (options: new, in_progress, resolved, closed)"),
        ("created_at", "Date & time"),
        ("subject", "Single line text"),
        ("email_body", "Long text"),
        ("original_sender", "Email"),
        ("message_id", "Single line text"),
        ("raw_headers", "Long text"),
        ("spf_result", "Single line text"),
        ("dkim_result", "Single line text"),
        ("has_attachments", "Checkbox"),
        ("attachment_count", "Number"),
        ("attachment_info", "Long text"),
        ("initial_auto_reply_sent", "Checkbox")
    ]
    
    for i, (field_name, field_type) in enumerate(fields, 1):
        print(f"   {i:2d}. {field_name:<25} -> {field_type}")
    
    print()
    print("4. For 'status' field, add these options:")
    print("   - new (red)")
    print("   - in_progress (yellow)")
    print("   - resolved (green)")
    print("   - closed (gray)")
    print()
    print("5. Run this script again to verify the setup")
    print("=" * 60)


if __name__ == "__main__":
    print("🏗️  Airtable Table Creation - HR Email Management System")
    print("=" * 60)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("❌ Error: .env file not found")
        print("Please create a .env file with your Airtable credentials:")
        print("AIRTABLE_API_KEY=your_api_key_here")
        print("AIRTABLE_BASE_ID=your_base_id_here")
        sys.exit(1)
    
    success = create_airtable_table()
    
    if success:
        print("\n✅ Table creation completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Table creation failed!")
        sys.exit(1) 