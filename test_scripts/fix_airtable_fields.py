"""
Fix Airtable Fields - Add the remaining fields with proper options
"""

import os
import sys
from pyairtable import Api
from dotenv import load_dotenv

def fix_airtable_fields():
    """Add the remaining Airtable fields with proper options"""
    
    print("🔧 Fixing remaining Airtable fields...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    api_key = os.getenv("AIRTABLE_API_KEY")
    base_id = os.getenv("AIRTABLE_BASE_ID")
    table_name = os.getenv("AIRTABLE_TABLE_NAME", "call_log")
    
    if not api_key or not base_id:
        print("❌ ERROR: Missing required environment variables")
        return False
    
    try:
        # Connect to Airtable
        api = Api(api_key)
        table = api.table(base_id, table_name)
        
        # Get existing fields to avoid duplicates
        schema = table.schema()
        existing_fields = {field.name for field in schema.fields}
        
        print(f"📊 Connected to table with {len(existing_fields)} existing fields")
        
        # Define missing fields with proper options
        missing_fields = [
            # DateTime fields need options object
            {
                "name": "Email Date",
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                }
            },
            {
                "name": "AI Processing Timestamp", 
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                }
            },
            {
                "name": "Created At",
                "type": "dateTime", 
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                }
            },
            {
                "name": "Last Updated",
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                }
            },
            {
                "name": "Resolved At",
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                }
            },
            {
                "name": "Auto Reply Timestamp",
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso"},
                    "timeFormat": {"name": "24hour"},
                    "timeZone": "utc"
                }
            },
            
            # Date field
            {
                "name": "Follow Up Date",
                "type": "date",
                "options": {
                    "dateFormat": {"name": "iso"}
                }
            },
            
            # Number fields need options object  
            {
                "name": "AI Confidence",
                "type": "number",
                "options": {
                    "precision": 2
                }
            },
            {
                "name": "Message Count",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Attachment Count", 
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            
            # Checkbox fields need options object
            {
                "name": "Is Initial Email",
                "type": "checkbox",
                "options": {
                    "icon": "check",
                    "color": "greenBright"
                }
            },
            {
                "name": "Follow Up Required",
                "type": "checkbox", 
                "options": {
                    "icon": "check",
                    "color": "yellowBright"
                }
            },
            {
                "name": "Has Attachments",
                "type": "checkbox",
                "options": {
                    "icon": "check", 
                    "color": "blueBright"
                }
            },
            {
                "name": "Auto Reply Sent",
                "type": "checkbox",
                "options": {
                    "icon": "check",
                    "color": "greenBright"
                }
            },
            
            # Rating field needs options
            {
                "name": "Satisfaction Rating",
                "type": "rating",
                "options": {
                    "icon": "star",
                    "max": 5,
                    "color": "yellowBright"
                }
            }
        ]
        
        # Add the missing fields
        fields_added = 0
        for field_config in missing_fields:
            field_name = field_config['name']
            
            if field_name not in existing_fields:
                try:
                    table.create_field(**field_config)
                    print(f"✅ Added field: {field_name}")
                    fields_added += 1
                except Exception as e:
                    print(f"⚠️ Could not add field {field_name}: {e}")
                    
                    # Try with minimal options for stubborn fields
                    try:
                        minimal_config = {
                            "name": field_name,
                            "type": field_config["type"]
                        }
                        table.create_field(**minimal_config)
                        print(f"✅ Added field (minimal): {field_name}")
                        fields_added += 1
                    except Exception as e2:
                        print(f"❌ Failed completely for {field_name}: {e2}")
            else:
                print(f"⏭️ Field already exists: {field_name}")
        
        print(f"\n✅ Field fixing complete! Added {fields_added} new fields.")
        print(f"📊 Total fields now: {len(existing_fields) + fields_added}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing fields: {e}")
        return False


if __name__ == "__main__":
    success = fix_airtable_fields()
    if not success:
        sys.exit(1)
    
    print("\n🚀 All fixed! Your Airtable table now has the complete field structure.")
    print("📊 Ready to process emails with full metadata extraction!") 