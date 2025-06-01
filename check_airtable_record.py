#!/usr/bin/env python3
"""
Check Airtable Record Script
Verifies what fields are populated in a specific ticket record
"""

import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append('backend')

from backend.airtable_service import AirtableService

def check_airtable_record(ticket_number):
    """Check specific fields in an Airtable record"""
    try:
        airtable = AirtableService()
        record = airtable.find_ticket(ticket_number)
        
        if record:
            fields = record['fields']
            print(f'🔍 Airtable Record Analysis for {ticket_number}:')
            print("=" * 60)
            print(f'   Record ID: {record["id"]}')
            print(f'   Email Date: "{fields.get("Email Date", "MISSING")}"')
            print(f'   Query Type: "{fields.get("Query Type", "MISSING")}"')
            print(f'   AI Summary: "{fields.get("AI Summary", "MISSING")}"')
            print(f'   Sender Email: "{fields.get("Sender Email", "MISSING")}"')
            print(f'   Subject: "{fields.get("Subject", "MISSING")}"')
            print(f'   Body Text Length: {len(fields.get("Body Text", ""))} chars')
            
            # Check conversation history
            conv_json = fields.get('Conversation History', '[]')
            try:
                conv = json.loads(conv_json)
                if conv and len(conv) > 0:
                    entry = conv[0]
                    print(f'\n📜 Conversation History:')
                    print(f'   Sender Name: "{entry.get("sender_name", "MISSING")}"')
                    print(f'   Timestamp: "{entry.get("timestamp", "MISSING")}"')
                    print(f'   AI Summary: "{entry.get("ai_summary", "MISSING")}"')
                    print(f'   Body Text Length: {len(entry.get("body_text", ""))} chars')
                else:
                    print(f'\n📜 Conversation History: Empty or missing')
            except Exception as e:
                print(f'\n📜 Conversation History: ❌ Failed to parse - {e}')
                
            return True
        else:
            print(f'❌ Record {ticket_number} not found')
            return False
            
    except Exception as e:
        print(f'❌ Error checking record: {e}')
        return False

if __name__ == "__main__":
    # Check the latest test records
    tickets_to_check = ["ARG-20250601-0003", "ARG-20250601-0002", "ARG-20250601-0001"]
    
    for ticket in tickets_to_check:
        check_airtable_record(ticket)
        print()  # Empty line between records 