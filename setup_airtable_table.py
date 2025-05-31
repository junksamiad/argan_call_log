"""
Airtable Table Setup Script
Automatically creates the required table structure for the HR Email Management System
"""

import os
import sys
from pyairtable import Api
from dotenv import load_dotenv

def setup_airtable_table():
    """Set up the Airtable table with all required fields"""
    
    print("🚀 Setting up Airtable table for HR Email Management System")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME", "call_log")
    
    if not api_key or not base_id:
        print("❌ ERROR: Missing required environment variables")
        print("Please ensure AIRTABLE_API_KEY and AIRTABLE_BASE_ID are set in .env")
        return False
    
    try:
        # Connect to Airtable
        api = Api(api_key)
        
        print(f"📊 Connecting to base: {base_id}")
        print(f"📊 Table name: {table_name}")
        
        # Define the field structure with corrected API format
        fields_to_create = [
            # Core Email Fields - skip these as they already exist
            # {"name": "Ticket Number", "type": "singleLineText"},
            # {"name": "Sender Email", "type": "email"},
            # {"name": "Subject", "type": "singleLineText"},
            
            {"name": "Sender Name", "type": "singleLineText"},
            {"name": "Body Text", "type": "multilineText"},
            {"name": "Body HTML", "type": "multilineText"},
            {"name": "Message ID", "type": "singleLineText"},
            {"name": "Email Date", "type": "dateTime"},
            {"name": "Recipients", "type": "multilineText"},  # JSON string
            {"name": "CC Recipients", "type": "multilineText"},  # JSON string
            
            # Status and Priority with correct options format
            {
                "name": "Status", 
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Open"},
                        {"name": "In Progress"},
                        {"name": "Waiting for Response"},
                        {"name": "Closed"}
                    ]
                }
            },
            {
                "name": "Priority", 
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Low"},
                        {"name": "Normal"},
                        {"name": "High"},
                        {"name": "Urgent"}
                    ]
                }
            },
            {
                "name": "Message Type", 
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Inbound"},
                        {"name": "Outbound"},
                        {"name": "Reply"},
                        {"name": "Internal Note"}
                    ]
                }
            },
            
            # AI Classification Fields
            {"name": "AI Classification", "type": "singleLineText"},
            {"name": "AI Confidence", "type": "number"},
            {"name": "Urgency Keywords", "type": "multilineText"},  # JSON string
            {"name": "Sentiment Tone", "type": "singleLineText"},
            {"name": "AI Processing Timestamp", "type": "dateTime"},
            {"name": "AI Notes", "type": "multilineText"},
            
            # Conversation and Threading
            {"name": "Conversation History", "type": "multilineText"},  # JSON string
            {"name": "Message Count", "type": "number"},
            {"name": "Is Initial Email", "type": "checkbox"},
            
            # Technical Fields
            {"name": "DKIM Status", "type": "singleLineText"},
            {"name": "SPF Status", "type": "singleLineText"},
            {"name": "Sender IP", "type": "singleLineText"},
            {"name": "Envelope Data", "type": "multilineText"},
            
            # HR Processing Fields
            {"name": "Query Type", "type": "singleSelect", "options": {
                "choices": [
                    {"name": "Leave Request"},
                    {"name": "Policy Question"},
                    {"name": "Complaint"},
                    {"name": "Payroll"},
                    {"name": "Benefits"},
                    {"name": "Training"},
                    {"name": "General Inquiry"},
                    {"name": "Other"}
                ]
            }},
            {"name": "Department", "type": "singleLineText"},
            {"name": "Assigned To", "type": "singleLineText"},
            {"name": "Resolution Notes", "type": "multilineText"},
            {"name": "Follow Up Required", "type": "checkbox"},
            {"name": "Follow Up Date", "type": "date"},
            
            # Timestamps
            {"name": "Created At", "type": "dateTime"},
            {"name": "Last Updated", "type": "dateTime"},
            {"name": "Resolved At", "type": "dateTime"},
            
            # Attachments and Files
            {"name": "Has Attachments", "type": "checkbox"},
            {"name": "Attachment Count", "type": "number"},
            {"name": "Attachment Names", "type": "multilineText"},  # JSON string
            
            # Customer Satisfaction
            {"name": "Satisfaction Rating", "type": "rating", "options": {"max": 5}},
            {"name": "Feedback", "type": "multilineText"},
            
            # Auto-Reply Tracking
            {"name": "Auto Reply Sent", "type": "checkbox"},
            {"name": "Auto Reply Timestamp", "type": "dateTime"},
            {"name": "Response Template Used", "type": "singleLineText"}
        ]
        
        # Check if table exists by trying to access it
        try:
            table = api.table(base_id, table_name)
            table_schema = table.schema()
            print(f"📊 Table '{table_name}' already exists")
            
            # Get existing fields - fix to use field objects
            existing_fields = {field.name: field for field in table_schema.fields}
            
            # Add missing fields
            fields_added = 0
            for field_config in fields_to_create:
                field_name = field_config['name']
                if field_name not in existing_fields:
                    try:
                        # Use the simplified API call
                        table.create_field(**field_config)
                        print(f"✅ Added field: {field_name}")
                        fields_added += 1
                    except Exception as e:
                        print(f"⚠️ Could not add field {field_name}: {e}")
                        # Try without options for complex field types
                        try:
                            simple_config = {
                                "name": field_name,
                                "type": field_config["type"]
                            }
                            table.create_field(**simple_config)
                            print(f"✅ Added field (simplified): {field_name}")
                            fields_added += 1
                        except Exception as e2:
                            print(f"❌ Failed completely for {field_name}: {e2}")
                else:
                    print(f"⏭️ Field already exists: {field_name}")
            
            print(f"\n✅ Table setup complete! Added {fields_added} new fields.")
            
        except Exception as table_error:
            # Table doesn't exist, create it
            print(f"📊 Creating new table: {table_name}")
            
            try:
                # Create table with minimal fields first (Airtable requires at least one field)
                minimal_fields = [
                    {"name": "Ticket Number", "type": "singleLineText"},
                    {"name": "Sender Email", "type": "email"},
                    {"name": "Subject", "type": "singleLineText"}
                ]
                
                base = api.base(base_id)
                created_table = base.create_table(
                    name=table_name,
                    fields=minimal_fields
                )
                
                print(f"✅ Created table: {created_table.name}")
                
                # Now add the remaining fields
                table = api.table(base_id, table_name)
                fields_added = len(minimal_fields)
                
                for field_config in fields_to_create:
                    try:
                        table.create_field(**field_config)
                        print(f"✅ Added field: {field_config['name']}")
                        fields_added += 1
                    except Exception as e:
                        print(f"⚠️ Could not add field {field_config['name']}: {e}")
                        # Try simplified version
                        try:
                            simple_config = {
                                "name": field_config['name'],
                                "type": field_config["type"]
                            }
                            table.create_field(**simple_config)
                            print(f"✅ Added field (simplified): {field_config['name']}")
                            fields_added += 1
                        except Exception as e2:
                            print(f"❌ Failed completely for {field_config['name']}: {e2}")
                
                print(f"✅ Added {fields_added} total fields")
                
            except Exception as create_error:
                print(f"❌ Error creating table: {create_error}")
                return False
        
        print(f"\n🎉 Airtable setup successful!")
        print(f"📊 Base ID: {base_id}")
        print(f"📊 Table: {table_name}")
        print(f"📊 Total fields: {len(fields_to_create)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Airtable: {e}")
        return False


if __name__ == "__main__":
    success = setup_airtable_table()
    if not success:
        sys.exit(1)
    
    print("\n🚀 Next steps:")
    print("1. Start your server: uvicorn backend.server:app --reload")
    print("2. Test email processing with the new Airtable integration")
    print("3. Check your Airtable base to see the data!") 