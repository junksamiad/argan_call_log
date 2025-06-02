#!/usr/bin/env python3
"""
Debug Duplicate Records
Check if multiple records are being created for single emails
"""

import sys
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.airtable_service import AirtableService

def debug_duplicate_records():
    """Check for duplicate records that might explain the sender name issue"""
    try:
        airtable = AirtableService()
        
        # Get all records from today
        all_records = airtable.table.all()
        today = datetime.now().strftime("%Y%m%d")
        
        print('🔍 Checking for Duplicate Records')
        print('=' * 60)
        
        # Group records by various criteria to find duplicates
        by_subject = {}
        by_sender = {}
        by_ticket_prefix = {}
        
        today_records = []
        
        for record in all_records:
            fields = record['fields']
            ticket = fields.get('Ticket Number', '')
            
            # Focus on today's records
            if ticket.startswith(f'ARG-{today}-'):
                today_records.append({
                    'id': record['id'],
                    'ticket': ticket,
                    'sender': fields.get('Sender Email', ''),
                    'subject': fields.get('Subject', ''),
                    'created': fields.get('Created At', ''),
                    'auto_reply_sent': fields.get('Auto Reply Sent', False),
                    'ai_summary': fields.get('AI Summary', ''),
                    'query_type': fields.get('Query Type', '')
                })
        
        print(f'📊 Found {len(today_records)} records from today ({today})')
        print()
        
        # Check for potential duplicates
        duplicates_found = False
        
        for i, record in enumerate(today_records):
            for j, other_record in enumerate(today_records):
                if i >= j:  # Avoid comparing with self and duplicating comparisons
                    continue
                    
                same_sender = record['sender'] == other_record['sender']
                same_subject = record['subject'] == other_record['subject']
                
                if same_sender and same_subject:
                    duplicates_found = True
                    print(f'🚨 POTENTIAL DUPLICATE FOUND:')
                    print(f'   Record 1: {record["ticket"]} (ID: {record["id"][:8]}...)')
                    print(f'   Record 2: {other_record["ticket"]} (ID: {other_record["id"][:8]}...)')
                    print(f'   Same Sender: {record["sender"]}')
                    print(f'   Same Subject: {record["subject"][:50]}...')
                    print(f'   Record 1 Auto-Reply: {record["auto_reply_sent"]}')
                    print(f'   Record 2 Auto-Reply: {other_record["auto_reply_sent"]}')
                    print(f'   Record 1 AI Summary: {"✅" if record["ai_summary"] else "❌"}')
                    print(f'   Record 2 AI Summary: {"✅" if other_record["ai_summary"] else "❌"}')
                    print()
        
        if not duplicates_found:
            print('✅ No obvious duplicates found')
            print()
        
        # Show all today's records for analysis
        print('📋 All Today\'s Records:')
        print('-' * 60)
        for record in today_records:
            print(f'🎫 {record["ticket"]}')
            print(f'   From: {record["sender"]}')
            print(f'   Subject: {record["subject"][:50]}...')
            print(f'   Auto-Reply Sent: {record["auto_reply_sent"]}')
            print(f'   AI Summary: {"✅" if record["ai_summary"] else "❌"}')
            print(f'   Query Type: {record["query_type"] or "None"}')
            print(f'   Created: {record["created"]}')
            print()
        
        # Check conversation history for sender names
        print('👤 Sender Name Analysis:')
        print('-' * 60)
        for record in today_records:
            full_record = airtable.find_ticket(record['ticket'])
            if full_record:
                conv_json = full_record['fields'].get('Conversation History', '[]')
                try:
                    conv = json.loads(conv_json)
                    if conv and len(conv) > 0:
                        sender_name = conv[0].get('sender_name', '')
                        print(f'🎫 {record["ticket"]}: "{sender_name}"')
                    else:
                        print(f'🎫 {record["ticket"]}: No conversation history')
                except:
                    print(f'🎫 {record["ticket"]}: Failed to parse conversation')
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    debug_duplicate_records() 