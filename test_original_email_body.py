"""
Test script to demonstrate original email body inclusion in auto-replies
For client's human-in-the-loop review process during initial prototype phase
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.email_functions.auto_reply import send_auto_reply


async def test_auto_reply_with_original_body():
    """Test auto-reply with original email body (currently commented out)"""
    
    # Sample original email content
    original_email = """Dear HR Team,

I hope this email finds you well. I am writing to request annual leave for the following dates:

Start Date: 15th July 2024
End Date: 22nd July 2024
Total Days: 6 working days

I have discussed this with my line manager, Sarah Johnson, and she has given her verbal approval. I understand I need to submit this request formally through HR.

Could you please let me know if these dates are approved and if there are any additional forms I need to complete?

I have ensured that my current projects will be covered during my absence:
- Project A: John Smith will handle daily reviews
- Project B: Already completed and delivered to client
- Project C: Will be completed before my leave starts

Thank you for your time and consideration.

Best regards,
Jane Doe
Marketing Assistant
jane.doe@arganconsultancy.co.uk
+44 7123 456789"""

    # Test data
    test_data = {
        'recipient': 'jane.doe@arganconsultancy.co.uk',
        'ticket_number': 'ARG-20240601-0123',
        'original_subject': 'Annual Leave Request - Jane Doe',
        'sender_name': 'Jane Doe',
        'priority': 'Normal',
        'ai_summary': 'Annual leave request for 6 working days in July 2024, with coverage arrangements in place.',
        'original_email_body': original_email
    }
    
    print("🧪 Testing auto-reply with original email body feature...")
    print("📧 Original email body will be included for human reviewer")
    print("⚠️  Currently DISABLED for testing - see comments in auto_reply.py")
    print()
    
    try:
        result = await send_auto_reply(**test_data)
        
        if result.get('success'):
            print("✅ Auto-reply would be sent successfully!")
            print(f"📋 Ticket: {test_data['ticket_number']}")
            print(f"📧 To: {test_data['recipient']}")
            print(f"📊 Priority: {test_data['priority']}")
            print()
            print("💡 To ENABLE original email body in production:")
            print("   1. Open backend/email_functions/auto_reply.py")
            print("   2. Find the 'ENABLE FOR PRODUCTION' comment (around line 130)")
            print("   3. Uncomment the block below it")
            print("   4. The human reviewer will see the full original enquiry")
            print()
            print("🔧 To DISABLE for testing:")
            print("   1. Comment out the same block")
            print("   2. Auto-replies will be shorter during development")
            
        else:
            print("❌ Auto-reply failed:")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("ORIGINAL EMAIL BODY IN AUTO-REPLY - TEST")
    print("=" * 60)
    
    asyncio.run(test_auto_reply_with_original_body()) 