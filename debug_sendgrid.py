#!/usr/bin/env python3
"""
Debug SendGrid API Key and Permissions
"""

import os
import ssl
import certifi
from dotenv import load_dotenv

# Fix SSL certificate issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

def debug_sendgrid():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv('SENDGRID_API_KEY')
    email_address = os.getenv('EMAIL_ADDRESS')
    
    print("🔍 SENDGRID DEBUG INFORMATION")
    print("=" * 50)
    
    # Check if API key exists
    if not api_key:
        print("❌ No SENDGRID_API_KEY found in .env file")
        return False
    
    # Check API key format
    print(f"📧 Email Address: {email_address}")
    print(f"🔑 API Key Length: {len(api_key)} characters")
    print(f"🔑 API Key Starts With: {api_key[:10]}...")
    print(f"🔑 API Key Ends With: ...{api_key[-10:]}")
    
    if not api_key.startswith('SG.'):
        print("❌ ERROR: API key should start with 'SG.'")
        print("   Your key starts with:", api_key[:5])
        return False
    else:
        print("✅ API key format looks correct (starts with 'SG.')")
    
    # Test basic API connection
    try:
        from sendgrid import SendGridAPIClient
        
        print("\n🔗 Testing SendGrid API Connection...")
        sg = SendGridAPIClient(api_key=api_key)
        
        # Try a simple API call
        response = sg.client.user.get()
        print(f"📊 API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key is valid and working!")
            
            # Try to get account details
            try:
                import json
                user_data = json.loads(response.body)
                print(f"👤 Account Username: {user_data.get('username', 'Unknown')}")
                print(f"📧 Account Email: {user_data.get('email', 'Unknown')}")
            except:
                print("ℹ️  Could not parse user details")
            
            return True
            
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - API key is invalid or expired")
            print("\n💡 Possible solutions:")
            print("   1. Check if you copied the API key correctly")
            print("   2. Verify the API key hasn't expired")
            print("   3. Ensure the API key has proper permissions")
            print("   4. Try creating a new API key in SendGrid dashboard")
            return False
            
        elif response.status_code == 403:
            print("❌ 403 Forbidden - API key lacks permissions")
            print("\n💡 Your API key needs these permissions:")
            print("   - Mail Send (for sending emails)")
            print("   - User Read (for basic account info)")
            return False
            
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(f"Response body: {response.body}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False

def check_sendgrid_permissions():
    """Check specific SendGrid permissions"""
    load_dotenv()
    api_key = os.getenv('SENDGRID_API_KEY')
    
    if not api_key:
        return False
    
    try:
        from sendgrid import SendGridAPIClient
        sg = SendGridAPIClient(api_key=api_key)
        
        print("\n🔐 Checking API Key Permissions...")
        
        # Check mail send permission
        try:
            # This endpoint requires mail send permission
            response = sg.client.mail.send.post(request_body={
                "personalizations": [{"to": [{"email": "test@example.com"}]}],
                "from": {"email": "test@example.com"},
                "subject": "Test",
                "content": [{"type": "text/plain", "value": "Test"}]
            })
            # We expect this to fail with validation error, not permission error
            print("✅ Mail Send permission: Available")
        except Exception as e:
            if "401" in str(e) or "unauthorized" in str(e).lower():
                print("❌ Mail Send permission: Missing")
            elif "400" in str(e) or "validation" in str(e).lower():
                print("✅ Mail Send permission: Available (validation error expected)")
            else:
                print(f"⚠️  Mail Send permission: Unknown ({e})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
        return False

if __name__ == "__main__":
    success = debug_sendgrid()
    
    if success:
        check_sendgrid_permissions()
        print("\n🎉 SendGrid API key is working!")
        print("You should be able to send emails.")
    else:
        print("\n❌ SendGrid API key issues found.")
        print("Please fix the API key before proceeding.")
        
        print("\n📋 How to fix:")
        print("1. Go to SendGrid Dashboard: https://app.sendgrid.com/")
        print("2. Navigate to Settings > API Keys")
        print("3. Create a new API key with 'Mail Send' permissions")
        print("4. Copy the key and update your .env file")
        print("5. Make sure the key starts with 'SG.'") 