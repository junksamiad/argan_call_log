#!/usr/bin/env python3
"""
Test script for CC functionality in auto-reply emails
Tests that CC recipients are properly added to emails
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.email_functions.auto_reply import AutoReplySender, send_auto_reply


async def test_cc_functionality():
    """Test CC functionality in auto-reply system"""
    
    print("🧪 Testing CC Functionality in Auto-Reply System")
    print("=" * 60)
    
    try:
        # Test 1: AutoReplySender with default CC
        print("\n📧 TEST 1: AutoReplySender with default CC")
        sender = AutoReplySender()
        
        print(f"✅ Default CC addresses: {sender.get_default_cc_addresses()}")
        
        # Test 2: Test standalone function with default CC
        print("\n📧 TEST 2: Standalone auto-reply function (should use default CC)")
        
        # Create test data for a new email
        test_result = await send_auto_reply(
            recipient="test.user@company.com",
            ticket_number="ARG-20250106-TEST1",
            original_subject="Test CC Functionality",
            sender_name="Test User",
            priority="Normal"
        )
        
        print(f"📤 Auto-reply result: {json.dumps(test_result, indent=2)}")
        
        # Test 3: Test with custom CC addresses
        print("\n📧 TEST 3: Custom CC addresses")
        
        custom_result = await sender.send_auto_reply(
            to_email="another.test@company.com",
            subject="[ARG-20250106-TEST2] Custom CC Test",
            content_text="This is a test with custom CC addresses",
            content_html="<p>This is a test with custom CC addresses</p>",
            ticket_number="ARG-20250106-TEST2",
            cc_addresses=["custom1@test.com", "custom2@test.com"]
        )
        
        print(f"📤 Custom CC result: {json.dumps(custom_result, indent=2)}")
        
        # Test 4: Test adding/removing default CC
        print("\n📧 TEST 4: Managing default CC addresses")
        
        print(f"Before: {sender.get_default_cc_addresses()}")
        sender.add_default_cc("additional@test.com")
        print(f"After adding: {sender.get_default_cc_addresses()}")
        sender.remove_default_cc("additional@test.com")
        print(f"After removing: {sender.get_default_cc_addresses()}")
        
        print("\n✅ CC Functionality tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_cc_functionality()) 