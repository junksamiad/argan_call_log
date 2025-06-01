#!/usr/bin/env python3
"""
Check Latest Record - First Name Demo
"""

import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.airtable_service import AirtableService
from backend.email_functions.initial_email.initial_email import extract_sender_name_for_auto_reply

def check_latest_record():
    """Check latest record and demo first name extraction"""
    try:
        airtable = AirtableService()
        record = airtable.find_ticket('ARG-20250601-0005')
        
        if record:
            fields = record['fields']
            conv_json = fields.get('Conversation History', '[]')
            conv = json.loads(conv_json)
            
            if conv and len(conv) > 0:
                entry = conv[0]
                full_sender_name = entry.get('sender_name', '')
                
                print(f'📋 Latest Record Analysis:')
                print(f'   Ticket: ARG-20250601-0005')
                print(f'   Full Sender Name in DB: "{full_sender_name}"')
                
                # Test what auto-reply would use
                email_data = {'sender_name': full_sender_name}
                first_name = extract_sender_name_for_auto_reply(email_data)
                
                print(f'   Auto-Reply First Name: "{first_name}"')
                print(f'   Auto-Reply Greeting: "Hi {first_name},"')
                print()
                print(f'✅ Improvement: "Hi {first_name}," instead of "Hi {full_sender_name},"')
                print()
                print('📧 This creates a more personal and friendly auto-reply!')
                return True
        
        print('❌ Record not found')
        return False
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == "__main__":
    check_latest_record() 