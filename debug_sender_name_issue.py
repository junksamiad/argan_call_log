#!/usr/bin/env python3
"""
Debug Sender Name Issue
Investigates why the sender name isn't being extracted properly for auto-reply
"""

import sys
import json
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.airtable_service import AirtableService

def debug_sender_name_issue():
    """Debug the specific issue with ARG-20250601-0002"""
    try:
        airtable = AirtableService()
        record = airtable.find_ticket('ARG-20250601-0002')
        
        if record:
            fields = record['fields']
            print('🔍 Analyzing ARG-20250601-0002 (the cvrcontractsltd email):')
            print('=' * 60)
            print(f'   Sender Email: {fields.get("Sender Email", "MISSING")}')
            print(f'   Subject: {fields.get("Subject", "MISSING")}')
            
            # Check conversation history for sender name
            conv_json = fields.get('Conversation History', '[]')
            try:
                conv = json.loads(conv_json)
                if conv and len(conv) > 0:
                    entry = conv[0]
                    stored_sender_name = entry.get('sender_name', '')
                    print(f'   Conversation Sender Name: "{stored_sender_name}"')
                    print(f'   Conversation AI Summary: "{entry.get("ai_summary", "MISSING")}"')
                    
                    print()
                    print('🤔 Analysis:')
                    if stored_sender_name and stored_sender_name != 'cvrcontractsltd':
                        print(f'   ✅ Sender name IS extracted and stored: "{stored_sender_name}"')
                        print(f'   ❌ But auto-reply used fallback: "cvrcontractsltd"')
                        print()
                        print('💡 Possible issues:')
                        print('   1. Classification data structure mismatch in auto-reply')
                        print('   2. AI classification not available when auto-reply was sent')
                        print('   3. Different data flow for real vs test emails')
                        
                        # Test the name extraction function
                        from backend.email_functions.initial_email.initial_email import extract_sender_name_for_auto_reply
                        
                        # Simulate what should happen
                        email_data = {'sender': 'cvrcontractsltd@gmail.com', 'sender_name': ''}
                        
                        # Test with mock classification data
                        class MockEmailData:
                            def __init__(self):
                                self.sender_name = stored_sender_name
                        
                        class MockClassificationData:
                            def __init__(self):
                                self.EMAIL_DATA = MockEmailData()
                        
                        mock_classification = MockClassificationData()
                        
                        print()
                        print('🧪 Testing name extraction with stored data:')
                        extracted_name = extract_sender_name_for_auto_reply(email_data, mock_classification)
                        print(f'   Result: "{extracted_name}"')
                        
                        if extracted_name != 'cvrcontractsltd':
                            print('   ✅ Function works correctly with proper data')
                            print('   🔧 Issue: Classification data not properly passed to auto-reply')
                        else:
                            print('   ❌ Function still returns fallback')
                    else:
                        print(f'   ❌ Sender name not properly extracted: "{stored_sender_name}"')
                        
            except Exception as e:
                print(f'   ❌ Failed to parse conversation history: {e}')
        else:
            print('❌ Record ARG-20250601-0002 not found')
            
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    debug_sender_name_issue() 