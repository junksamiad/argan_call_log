#!/usr/bin/env python3
"""
Test First Name Extraction
Tests the modified extract_sender_name_for_auto_reply function
"""

import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.append('backend')

from backend.email_functions.initial_email.initial_email import extract_sender_name_for_auto_reply

def test_first_name_extraction():
    """Test the first name extraction with various inputs"""
    
    print('🧪 Testing First Name Extraction for Auto-Reply:')
    print('=' * 60)
    
    # Test cases
    test_cases = [
        {
            'name': 'Full Name with Space',
            'email_data': {'sender_name': 'Sarah Thompson'}, 
            'expected': 'Sarah'
        },
        {
            'name': 'Single Name',
            'email_data': {'sender_name': 'John'}, 
            'expected': 'John'
        },
        {
            'name': 'Title with Name',
            'email_data': {'sender_name': 'Dr. Jane Smith'}, 
            'expected': 'Dr.'
        },
        {
            'name': 'Multiple Names',
            'email_data': {'sender_name': 'Mary Elizabeth Johnson'}, 
            'expected': 'Mary'
        },
        {
            'name': 'Fallback from Email',
            'email_data': {'sender': 'test@example.com', 'sender_name': ''}, 
            'expected': 'test'
        },
        {
            'name': 'Email with Numbers',
            'email_data': {'sender': 'cvrcontractsltd@gmail.com', 'sender_name': ''}, 
            'expected': 'cvrcontractsltd'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f'Test {i}: {test["name"]}')
        
        result = extract_sender_name_for_auto_reply(test['email_data'])
        status = '✅ PASS' if result == test['expected'] else '❌ FAIL'
        
        print(f'   Input: {test["email_data"]}')
        print(f'   Expected: "{test["expected"]}"')
        print(f'   Got: "{result}"')
        print(f'   Status: {status}')
        print()
    
    print('📧 Auto-Reply Examples:')
    print('   "Hi Sarah," instead of "Hi Sarah Thompson,"')
    print('   "Hi John," instead of "Hi John Smith,"')
    print('   "Hi Dr.," instead of "Hi Dr. Jane Smith,"')
    print()
    print('✨ This creates a more personal and friendly greeting!')

if __name__ == "__main__":
    test_first_name_extraction() 