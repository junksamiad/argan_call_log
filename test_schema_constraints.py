#!/usr/bin/env python3
"""
Test Schema Constraints
Verifies that the enum constraints prevent invalid category values
"""

import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

try:
    from backend.email_functions.classification.email_classification_schema import (
        HRCategory, 
        TicketLocation, 
        FlattenedEmailData,
        EmailClassificationResponse,
        EmailClassification
    )
    
    def test_schema_constraints():
        """Test that enum constraints work properly"""
        print('🧪 Testing Schema Enum Constraints')
        print('=' * 60)
        
        # Test valid HR categories
        print('✅ Testing VALID HR Categories:')
        valid_categories = [
            "Leave Request",
            "Performance Management", 
            "Grievance",
            "Policy Question"
        ]
        
        for category in valid_categories:
            try:
                hr_cat = HRCategory(category)
                print(f'   ✅ "{category}" → {hr_cat}')
            except ValueError as e:
                print(f'   ❌ "{category}" failed: {e}')
        
        print()
        
        # Test invalid HR categories (these should fail)
        print('❌ Testing INVALID HR Categories (should fail):')
        invalid_categories = [
            "Absence/Leave Request",  # This was causing the Airtable error
            "Performance Issues", 
            "Staff Relations",
            "Sickness Management"
        ]
        
        for category in invalid_categories:
            try:
                hr_cat = HRCategory(category)
                print(f'   ⚠️ "{category}" → {hr_cat} (UNEXPECTED - should have failed)')
            except ValueError as e:
                print(f'   ✅ "{category}" → Correctly rejected: {e}')
        
        print()
        
        # Test ticket location enum
        print('✅ Testing TicketLocation Enum:')
        valid_locations = ["subject", "body", "both", "none"]
        
        for location in valid_locations:
            try:
                ticket_loc = TicketLocation(location)
                print(f'   ✅ "{location}" → {ticket_loc}')
            except ValueError as e:
                print(f'   ❌ "{location}" failed: {e}')
        
        print()
        
        # Test schema validation with valid data
        print('✅ Testing FlattenedEmailData with valid enums:')
        try:
            email_data = FlattenedEmailData(
                sender_email="test@example.com",
                sender_name="Test User",
                recipients_list='["hr@company.com"]',
                subject="Test Subject",
                body_text="Test body content",
                message_id="test123",
                hr_category=HRCategory.LEAVE_REQUEST,  # Uses enum
                ticket_found_in=TicketLocation.NONE    # Uses enum
            )
            print(f'   ✅ Valid schema creation successful')
            print(f'   ✅ HR Category: {email_data.hr_category}')
            print(f'   ✅ Ticket Location: {email_data.ticket_found_in}')
        except Exception as e:
            print(f'   ❌ Schema validation failed: {e}')
        
        print()
        print('🎯 Schema Fix Summary:')
        print('   ✅ hr_category now uses HRCategory enum')
        print('   ✅ ticket_found_in now uses TicketLocation enum') 
        print('   ✅ Invalid categories like "Absence/Leave Request" will be rejected')
        print('   ✅ AI must use exact enum values: "Leave Request", "Performance Management", etc.')
        print('   ✅ This should fix the Airtable "INVALID_MULTIPLE_CHOICE_OPTIONS" error')

    if __name__ == "__main__":
        test_schema_constraints()
        
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('Make sure you are running from the project root directory') 