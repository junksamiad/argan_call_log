#!/usr/bin/env python3
"""
Complete Email Pipeline Test
Simulates 3 emails being processed in rapid succession to test:
- AI classification
- Airtable storage  
- Auto-reply with retry mechanism
- Connection handling improvements
"""

import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

from backend.email_functions.email_router import route_email_async
from backend.airtable_service import AirtableService

async def test_email_pipeline_complete():
    """Test the complete email pipeline with 3 rapid emails"""
    print('🚀 Testing Complete Email Pipeline (3 Rapid Emails)')
    print('🎯 END-TO-END STRESS TEST - Real SendGrid Email Delivery!')
    print('📧 Auto-replies will be sent to actual email addresses')
    print('=' * 70)
    
    # Clear existing test records first
    print('🧹 Clearing existing test records...')
    try:
        airtable = AirtableService()
        all_records = airtable.table.all()
        test_emails_for_cleanup = ['junksamiad@gmail.com', 'bloxtersamiad@gmail.com', 'cvrcontractsltd@gmail.com']
        
        for record in all_records:
            sender = record['fields'].get('Sender Email', '')
            if any(test_email in sender for test_email in test_emails_for_cleanup):
                airtable.table.delete(record['id'])
                print(f'🗑️ Deleted test record: {record["fields"].get("Ticket Number", "Unknown")}')
        
        print('✅ Test records cleared')
    except Exception as e:
        print(f'⚠️ Error clearing records: {e}')
    
    print()
    
    # Test emails with different HR scenarios - USING REAL EMAIL ADDRESSES FOR END-TO-END TESTING
    test_emails = [
        {
            "sender": "junksamiad@gmail.com",
            "sender_name": "Alice Johnson", 
            "subject": "Performance Review Concerns and Improvement Plan Guidance",
            "body_text": """Dear HR Team,

I hope you are well. I am writing to seek guidance regarding a performance review situation with one of my team members, Mark Thompson, who has been consistently underperforming over the past three months.

Specifically, I need advice on:
- How to structure a Performance Improvement Plan (PIP)
- Required documentation for formal performance management
- Timeline expectations for improvement
- Potential disciplinary procedures if performance doesn't improve

Mark has missed several project deadlines and quality standards have declined significantly. I've had informal conversations but formal action is now needed.

Please advise on the proper HR procedures and provide any relevant templates or documentation.

Best regards,
Alice Johnson
Department Manager""",
            "email_date": datetime.utcnow().isoformat(),
            "message_id": f"test-msg-001-{int(datetime.utcnow().timestamp())}"
        },
        {
            "sender": "bloxtersamiad@gmail.com", 
            "sender_name": "Bob Wilson",
            "subject": "Urgent: Workplace Harassment Complaint Requires Immediate Attention",
            "body_text": """Dear HR Team,

I need to report a serious workplace harassment situation that requires urgent attention and guidance on proper procedures.

One of our employees, Sarah Mitchell, has filed a formal complaint against her supervisor, David Brown, alleging:
- Inappropriate comments about her appearance
- Creating a hostile work environment
- Potential retaliation for previous complaints

This is extremely urgent as Sarah is threatening to involve external authorities if not handled properly. I need immediate guidance on:
- Formal investigation procedures
- Interim protective measures
- Documentation requirements
- Communication protocols
- Timeline for resolution

Please respond ASAP as this situation is escalating quickly.

Regards,
Bob Wilson
Operations Manager""",
            "email_date": datetime.utcnow().isoformat(),
            "message_id": f"test-msg-002-{int(datetime.utcnow().timestamp())}"
        },
        {
            "sender": "cvrcontractsltd@gmail.com",
            "sender_name": "Carol Davis", 
            "subject": "Staff Annual Leave Coordination and Policy Questions",
            "body_text": """Hello HR Team,

I'm writing to request assistance with coordinating annual leave for our department during the busy summer period.

We have several challenges:
- Multiple staff requesting overlapping vacation dates
- Minimum staffing requirements for client coverage
- New employee probation periods affecting leave entitlement
- Policy clarification needed for carry-over days

Specific questions:
1. What's the maximum number of people who can be on leave simultaneously?
2. How do we handle disputes over popular vacation periods?
3. Can probationary employees take annual leave?
4. What's our policy on unpaid leave requests?

I need this information to complete our summer schedule planning by next Friday.

Thank you,
Carol Davis
Team Lead""",
            "email_date": datetime.utcnow().isoformat(),
            "message_id": f"test-msg-003-{int(datetime.utcnow().timestamp())}"
        }
    ]
    
    # Process emails in rapid succession (like real webhook scenario)
    results = []
    start_time = datetime.utcnow()
    
    print(f'📧 Processing {len(test_emails)} emails in rapid succession...')
    print('⏱️ Starting at:', start_time.strftime('%H:%M:%S.%f')[:-3])
    print()
    
    # Create tasks to run concurrently (simulating near-simultaneous webhook calls)
    tasks = []
    for i, email_data in enumerate(test_emails, 1):
        print(f'🚀 [{i}] Initiating: {email_data["sender"]} - {email_data["subject"][:50]}...')
        task = asyncio.create_task(
            route_email_async(email_data),
            name=f"email-{i}"
        )
        tasks.append(task)
        
        # Small delay to simulate realistic timing (but still rapid)
        await asyncio.sleep(0.1)
    
    print('\n⏳ Waiting for all emails to complete processing...')
    print('=' * 50)
    
    # Wait for all tasks to complete
    completed_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = datetime.utcnow()
    total_time = (end_time - start_time).total_seconds()
    
    print('\n📊 PROCESSING RESULTS:')
    print('=' * 50)
    
    success_count = 0
    auto_reply_count = 0
    
    for i, result in enumerate(completed_results, 1):
        if isinstance(result, Exception):
            print(f'❌ [{i}] FAILED: {result}')
        else:
            success_count += 1
            ticket = result.get('ticket_number', 'Unknown')
            record_id = result.get('airtable_record_id', 'Unknown')
            classification = result.get('ai_classification', 'Unknown')
            confidence = result.get('ai_confidence', 0)
            
            print(f'✅ [{i}] SUCCESS: {ticket}')
            print(f'    📊 Record ID: {record_id}')
            print(f'    🤖 AI Classification: {classification} (confidence: {confidence:.2f})')
            
            # Check if auto-reply was sent (this would be in logs)
            auto_reply_count += 1  # Assume success for now, we'll check logs
            
    print('\n⏱️ TIMING ANALYSIS:')
    print('=' * 50)
    print(f'📅 Start Time: {start_time.strftime("%H:%M:%S.%f")[:-3]}')
    print(f'📅 End Time: {end_time.strftime("%H:%M:%S.%f")[:-3]}')
    print(f'⏱️ Total Processing Time: {total_time:.3f} seconds')
    print(f'⚡ Average per Email: {total_time/len(test_emails):.3f} seconds')
    
    print('\n📈 SUMMARY STATISTICS:')
    print('=' * 50)
    print(f'📧 Total Emails Processed: {len(test_emails)}')
    print(f'✅ Successful Processing: {success_count}/{len(test_emails)}')
    print(f'📤 Auto-Replies Expected: {auto_reply_count}')
    print(f'⚡ Processing Rate: {len(test_emails)/total_time:.1f} emails/second')
    
    # Verify Airtable records
    print('\n🔍 VERIFYING AIRTABLE RECORDS:')
    print('=' * 50)
    
    try:
        airtable = AirtableService()
        all_records = airtable.table.all()
        
        test_tickets = []
        for record in all_records:
            sender = record['fields'].get('Sender Email', '')
            if any(test_email in sender for test_email in ['junksamiad@gmail.com', 'bloxtersamiad@gmail.com', 'cvrcontractsltd@gmail.com']):
                ticket = record['fields'].get('Ticket Number', 'Unknown')
                ai_summary = record['fields'].get('AI Summary', '')
                hr_category = record['fields'].get('Query Type', '')
                auto_reply_sent = record['fields'].get('Auto Reply Sent', False)
                
                test_tickets.append({
                    'ticket': ticket,
                    'sender': sender,
                    'hr_category': hr_category,
                    'ai_summary_length': len(ai_summary),
                    'auto_reply_sent': auto_reply_sent
                })
                
                print(f'🎫 {ticket}: {sender}')
                print(f'   📝 HR Category: {hr_category}')
                print(f'   🤖 AI Summary: {len(ai_summary)} chars')
                print(f'   📤 Auto-Reply: {"✅ Sent" if auto_reply_sent else "❌ Not Sent"}')
                print()
        
        print(f'💾 Total Test Records in Airtable: {len(test_tickets)}')
        
        # Check for any missing records
        if len(test_tickets) != len(test_emails):
            print(f'⚠️ WARNING: Expected {len(test_emails)} records, found {len(test_tickets)}')
            
    except Exception as e:
        print(f'❌ Error verifying Airtable records: {e}')
    
    print('\n🏁 TEST COMPLETE!')
    print('=' * 50)
    
    if success_count == len(test_emails):
        print('🎉 ALL EMAILS PROCESSED SUCCESSFULLY!')
        print('💡 Check the logs above for retry attempts and connection handling details.')
        print('📧 CHECK YOUR EMAIL INBOXES for the 3 auto-reply emails:')
        print('   • junksamiad@gmail.com')
        print('   • bloxtersamiad@gmail.com') 
        print('   • cvrcontractsltd@gmail.com')
        print('✅ If all 3 auto-replies arrived, the stress test passed completely!')
    else:
        print(f'⚠️ {len(test_emails) - success_count} emails failed processing.')
        print('💡 Check the error details above and logs for retry attempts.')
    
    return {
        'total_emails': len(test_emails),
        'successful': success_count,
        'processing_time': total_time,
        'results': completed_results
    }

if __name__ == "__main__":
    asyncio.run(test_email_pipeline_complete()) 