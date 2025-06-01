"""
Clear Airtable records for fresh testing
"""
from backend.airtable_service import AirtableService

try:
    airtable = AirtableService()
    records = airtable.table.all()
    
    if records:
        print(f'Deleting {len(records)} existing records to start fresh...')
        for record in records:
            airtable.table.delete(record['id'])
            print(f'Deleted record {record["id"]}')
        print('✅ All records deleted. Ready for fresh test.')
    else:
        print('No records to delete.')

except Exception as e:
    print(f'Error: {e}') 