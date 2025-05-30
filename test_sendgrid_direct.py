#!/usr/bin/env python3
"""
Direct HTTP test to SendGrid API
"""

import os
import ssl
import certifi
import requests
import json
from dotenv import load_dotenv

# Fix SSL certificate issues on macOS
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

def test_sendgrid_direct():
    load_dotenv()
    api_key = os.getenv('SENDGRID_API_KEY')
    
    if not api_key:
        print("❌ No API key found")
        return
    
    print("🔍 DIRECT SENDGRID API TEST")
    print("=" * 40)
    print(f"🔑 Using API key: {api_key[:15]}...{api_key[-10:]}")
    
    # Test 1: Basic user info endpoint
    print("\n📡 Test 1: GET /user (basic account info)")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'https://api.sendgrid.com/v3/user',
            headers=headers,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: API key is valid!")
            user_data = response.json()
            print(f"👤 Username: {user_data.get('username', 'Unknown')}")
            print(f"📧 Email: {user_data.get('email', 'Unknown')}")
            return True
            
        elif response.status_code == 401:
            print("❌ 401 Unauthorized")
            print(f"📄 Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"🔍 Error details: {error_data}")
            except:
                print("🔍 Could not parse error response")
                
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    
    # Test 2: Try a simple mail send validation
    print("\n📡 Test 2: POST /mail/send (validation test)")
    
    # This should fail with validation error, not auth error
    test_email_data = {
        "personalizations": [
            {
                "to": [{"email": "test@example.com"}]
            }
        ],
        "from": {"email": "test@example.com"},
        "subject": "Test",
        "content": [
            {
                "type": "text/plain",
                "value": "Test email"
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers=headers,
            json=test_email_data,
            timeout=10
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ 401 Unauthorized - API key issue")
            print(f"📄 Response: {response.text}")
        elif response.status_code == 400:
            print("✅ 400 Bad Request - API key works, validation failed (expected)")
            print("🎉 This means your API key has mail send permissions!")
        elif response.status_code == 202:
            print("⚠️  202 Accepted - Email would be sent (unexpected for test data)")
        else:
            print(f"📊 Status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    return False

def check_sendgrid_status():
    """Check if SendGrid service is operational"""
    print("\n🌐 Checking SendGrid service status...")
    
    try:
        # Check SendGrid status page
        response = requests.get('https://status.sendgrid.com/api/v2/status.json', timeout=5)
        if response.status_code == 200:
            status_data = response.json()
            print(f"📊 SendGrid Status: {status_data.get('status', {}).get('description', 'Unknown')}")
        else:
            print("⚠️  Could not check SendGrid status")
    except:
        print("⚠️  Could not reach SendGrid status page")

if __name__ == "__main__":
    check_sendgrid_status()
    test_sendgrid_direct() 