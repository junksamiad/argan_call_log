#!/usr/bin/env python3
"""
Test script to verify AI date extraction fix
Tests that the AI no longer hallucinates dates when they're not explicitly present
"""

import sys
import os
import json

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agents import ConversationParsingAgent

def test_date_extraction():
    """Test that AI only extracts explicit dates and doesn't hallucinate"""
    
    print("🧪 Testing AI Date Extraction Fix")
    print("=" * 50)
    
    # Sample email content similar to what caused the issue
    test_email = """Hi Sue,

Yes, that response looks good – happy for you to go ahead.

Thanks,
Sam

Ops-manager

Care Homes UK Ltd


> On 3 Jun 2025, at 21:30, Argan HR <argan-bot@arganhrconsultancy.co.uk> wrote:
> 
> Hi Sam,
>  
> Joanne Lake (care home manager at Lakeside) has asked about sick pay entitlement for one of her staff who's recently been off.
>  
> Here's the draft reply I've prepared – let me know if you're happy for me to send this on:
>  
> Assuming Maria's absence was due to illness and lasted more than three consecutive days, she would qualify for Statutory Sick Pay (SSP). You'll need to ensure an SSP1 form is issued if it exceeds 7 days, and it's good practice to request a self-cert form or GP note depending on the duration.
>  
> Let me know if she has a history of similar absences or if there are any exceptional circumstances.
>  
> Kind regards, 
> Sue Robinson 
> Senior HR Consultant

>> ---------- Original Message ----------
>> From: Argan HR Consultancy <email@email.adaptixinnovation.co.uk>
>> To: cvrcontractsltd@gmail.com
>> CC: argan-bot@arganhrconsultancy.co.uk
>> Date: 03/06/2025 21:26 BST
>> Subject: [ARG-20250603-0003] Argan HR Consultancy - Call Logged
>>  
>>  
>> Argan HR Consultancy - Auto Reply
>> 
>> Hi Joanne
>> 
>> Thank you for contacting Argan HR Consultancy. We have received your enquiry and assigned it ticket number ARG-20250603-0003.
>> 
>> Original Subject: Query Regarding Sick Pay for Staff Member
>> 
>> Priority: Normal
>> 
>> Ticket Number: ARG-20250603-0003
>> 
>> We will review your request and respond within our standard timeframe:
>> 
>> Urgent matters: Within 4 hours
>> High priority: Within 24 hours
>> Normal requests: Within 2-3 business days
>> If you need to follow up on this matter, please reference ticket number ARG-20250603-0003 in your subject line.
>> 
>> Original Enquiry (for reference):
>> 
>> Hi, 
>> 
>> One of our care assistants, Maria, has been off sick for a few days this week, and she's asking whether she will be entitled to sick pay. 
>> 
>> Could you confirm what she's entitled to and what documentation (if any) we should collect from her? 
>> 
>> Thanks, 
>> Joanne Lake 
>> Manager – Lakeside Care Home
>> Thank you for your patience.
>> 
>> Best regards,
>> Argan HR Consultancy Team
>> 
>> This is an automated response. Please do not reply to this email.
>> 
>>"""
    
    print("📧 Testing with email content where:")
    print("  - Sam's message has NO explicit date")
    print("  - Sue's message has explicit date: '3 Jun 2025, at 21:30'")
    print("  - Reference content should be ignored")
    print()
    
    # Initialize the AI agent
    agent = ConversationParsingAgent()
    
    # Parse the conversation
    result_json = agent.parse_conversation_thread_sync(test_email)
    
    # Parse the result
    conversation_entries = json.loads(result_json)
    
    print("🤖 AI Extraction Results:")
    print("=" * 30)
    
    for i, entry in enumerate(conversation_entries, 1):
        print(f"📧 Entry {i}:")
        print(f"   👤 Sender: {entry['sender_name']} ({entry['sender_email']})")
        print(f"   📅 Date: '{entry['sender_email_date']}'")
        print(f"   📝 Content: {entry['sender_content'][:50]}...")
        print()
    
    # Analyze results
    print("🔍 Analysis:")
    print("-" * 20)
    
    success = True
    
    if len(conversation_entries) != 2:
        print(f"❌ Expected 2 entries, got {len(conversation_entries)}")
        success = False
    else:
        print(f"✅ Correct number of entries: {len(conversation_entries)}")
    
    # Check Sam's entry (should have empty date)
    if conversation_entries:
        sam_entry = None
        sue_entry = None
        
        for entry in conversation_entries:
            if 'Sam' in entry['sender_name']:
                sam_entry = entry
            elif 'Sue' in entry['sender_name']:
                sue_entry = entry
        
        if sam_entry:
            if sam_entry['sender_email_date'] == "":
                print("✅ Sam's entry correctly has empty date (no date was explicit)")
            else:
                print(f"❌ Sam's entry has date '{sam_entry['sender_email_date']}' - should be empty!")
                success = False
        
        if sue_entry:
            if sue_entry['sender_email_date'] and "21:30" in sue_entry['sender_email_date']:
                print("✅ Sue's entry correctly extracted explicit date")
            else:
                print(f"❌ Sue's entry date incorrect: '{sue_entry['sender_email_date']}'")
                success = False
    
    print()
    if success:
        print("🎉 SUCCESS: AI is now correctly handling date extraction!")
    else:
        print("💥 FAILURE: AI is still hallucinating dates or missing entries")
    
    return success

if __name__ == "__main__":
    test_date_extraction() 