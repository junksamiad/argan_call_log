#!/usr/bin/env python3
"""
Check .env file and API key format
"""

from dotenv import load_dotenv
import os

def check_env():
    print("🔍 CHECKING .ENV FILE")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file exists")
    else:
        print("❌ .env file not found")
        return
    
    # Get API key
    key = os.getenv('SENDGRID_API_KEY')
    email = os.getenv('EMAIL_ADDRESS')
    
    print(f"📧 Email Address: {email}")
    
    if key:
        print("✅ SENDGRID_API_KEY found")
        print(f"🔑 Length: {len(key)} characters")
        print(f"🔑 First 15 chars: '{key[:15]}'")
        print(f"🔑 Last 10 chars: '{key[-10:]}'")
        print(f"🔍 Contains spaces: {'Yes' if ' ' in key else 'No'}")
        print(f"🔍 Contains newlines: {'Yes' if chr(10) in key or chr(13) in key else 'No'}")
        print(f"🔍 Starts with SG.: {'Yes' if key.startswith('SG.') else 'No'}")
        
        # Check for common issues
        if ' ' in key:
            print("⚠️  WARNING: API key contains spaces!")
        if chr(10) in key or chr(13) in key:
            print("⚠️  WARNING: API key contains newline characters!")
        if not key.startswith('SG.'):
            print("⚠️  WARNING: API key doesn't start with 'SG.'!")
            
    else:
        print("❌ SENDGRID_API_KEY not found")
        
        # Show what variables are available
        print("\n📋 Available environment variables:")
        for var_name in os.environ:
            if 'SENDGRID' in var_name.upper() or 'EMAIL' in var_name.upper():
                print(f"   {var_name}: {os.environ[var_name][:20]}...")

if __name__ == "__main__":
    check_env() 