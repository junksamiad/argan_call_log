"""
Test the auto-reply function specifically to debug delivery issues
"""

import asyncio
from dotenv import load_dotenv
from backend.email_functions.auto_reply import send_auto_reply

async def test_auto_reply():
    """Test the auto-reply function directly"""
    
    load_dotenv()
    
    print("🧪 Testing auto-reply function specifically...")
    print("=" * 50)
    
    # Test with the same data that would come from webhook
    result = await send_auto_reply(
        recipient="bloxtersamiad@gmail.com",
        ticket_number="ARG-20250531-TEST",
        original_subject="Test Email...over and out",
        sender_name="Lee H",
        priority="Normal",
        ai_summary="Test email from user requesting system testing",
        cc_addresses=None  # CC is disabled for testing
    )
    
    print(f"📧 Auto-reply result: {result}")
    print("=" * 50)
    
    if result.get('success'):
        print("✅ Auto-reply sent successfully!")
        print("📱 Check your email (including spam folder)")
        print("📝 Subject should be: [ARG-20250531-TEST] Thank you for contacting Argan Consultancy HR")
        print("📧 From: email@email.adaptixinnovation.co.uk")
        print("💡 If you don't receive this but got the direct test, check:")
        print("   - Spam folder specifically for this subject")
        print("   - Gmail's 'Promotions' or 'Updates' tabs")
        print("   - Email content might be triggering filters")
    else:
        print("❌ Auto-reply failed!")
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_auto_reply()) 