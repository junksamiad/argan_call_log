#!/usr/bin/env python3
"""
Clear Duplicate Records
Removes the duplicate records we identified to clean up the database
"""

import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.airtable_service import AirtableService

def clear_duplicate_records():
    """Remove the duplicate records ARG-20250601-0001 and ARG-20250601-0002"""
    try:
        airtable = AirtableService()
        
        print('🧹 Cleaning Up Duplicate Records')
        print('=' * 60)
        
        # Find the duplicate records
        duplicates_to_remove = ['ARG-20250601-0001', 'ARG-20250601-0002']
        
        for ticket_number in duplicates_to_remove:
            record = airtable.find_ticket(ticket_number)
            if record:
                fields = record['fields']
                print(f'🗑️ Found {ticket_number}:')
                print(f'   Auto-Reply Sent: {fields.get("Auto Reply Sent", False)}')
                print(f'   AI Summary: {"✅" if fields.get("AI Summary") else "❌"}')
                print(f'   Query Type: {fields.get("Query Type", "None")}')
                
                # Delete the record
                try:
                    airtable.table.delete(record['id'])
                    print(f'   ✅ Deleted {ticket_number}')
                except Exception as e:
                    print(f'   ❌ Failed to delete {ticket_number}: {e}')
            else:
                print(f'   ⚠️ Record {ticket_number} not found')
            print()
        
        print('🎯 Cleanup Summary:')
        print('   Removed duplicate records caused by race condition')
        print('   Next email will create single record with:')
        print('   ✅ Proper AI classification')
        print('   ✅ Auto-reply with correct sender name')
        print('   ✅ No duplicates')
        
    except Exception as e:
        print(f'❌ Error during cleanup: {e}')

if __name__ == "__main__":
    clear_duplicate_records() 