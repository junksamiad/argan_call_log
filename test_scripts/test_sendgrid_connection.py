#!/usr/bin/env python3
"""
Test SendGrid Connection
Tests SendGrid API connection and account status without sending emails
"""

import sys
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend')

async def test_sendgrid_connection():
    """Test SendGrid connection and account details"""
    print('🔗 Testing SendGrid Connection & Account Status')
    print('=' * 60)
    
    # Check environment variables
    api_key = os.getenv("SENDGRID_API_KEY", "")
    from_email = os.getenv("EMAIL_ADDRESS", "")
    
    print(f'📧 From Email: {from_email}')
    print(f'🔑 API Key Present: {"Yes" if api_key else "No"}')
    print(f'🔑 API Key Length: {len(api_key) if api_key else 0} characters')
    print(f'🔑 API Key Preview: {api_key[:10] + "..." if len(api_key) > 10 else api_key}')
    print()
    
    if not api_key:
        print('❌ No SendGrid API key found in environment variables')
        return
    
    # Test with SendGrid client
    try:
        from sendgrid import SendGridAPIClient
        
        print('🧪 Testing SendGrid API Client...')
        sg = SendGridAPIClient(api_key=api_key)
        
        # Test API key validity with a simple GET request
        response = sg.client.user.get()
        
        print(f'📊 API Response Status: {response.status_code}')
        print(f'📊 API Response Headers: {dict(response.headers)}')
        
        if response.status_code == 200:
            print('✅ SendGrid API connection successful!')
            
            # Try to get user profile info
            try:
                import json
                user_info = json.loads(response.body)
                print(f'👤 Account Email: {user_info.get("email", "Unknown")}')
                print(f'👤 Account Username: {user_info.get("username", "Unknown")}')
            except:
                print('📝 User info parsing failed, but connection works')
                
        elif response.status_code == 401:
            print('❌ SendGrid API key is invalid or expired')
        elif response.status_code == 403:
            print('⚠️ SendGrid API key has insufficient permissions')
        else:
            print(f'⚠️ SendGrid API returned unexpected status: {response.status_code}')
            print(f'📝 Response body: {response.body}')
            
    except Exception as e:
        print(f'💥 SendGrid connection failed: {e}')
        print(f'📝 Exception type: {type(e).__name__}')
    
    print()
    
    # Test HTTPX approach (what our email service uses)
    try:
        import httpx
        
        print('🧪 Testing HTTPX API approach...')
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.sendgrid.com/v3/user/profile",
                headers=headers,
                timeout=10.0
            )
            
        print(f'📊 HTTPX Response Status: {response.status_code}')
        
        if response.status_code == 200:
            print('✅ HTTPX SendGrid connection successful!')
            try:
                profile = response.json()
                print(f'👤 Profile: {profile}')
            except:
                print('📝 Profile parsing failed, but connection works')
        else:
            print(f'❌ HTTPX connection failed: {response.status_code}')
            print(f'📝 Response: {response.text}')
            
    except Exception as e:
        print(f'💥 HTTPX connection failed: {e}')
        print(f'📝 Exception type: {type(e).__name__}')
    
    print()
    print('🎯 Diagnosis:')
    print('   - If both tests succeed: API key is valid')
    print('   - If API returns 401: API key is invalid')
    print('   - If API returns 403: API key lacks permissions')  
    print('   - Check SendGrid dashboard for daily usage limits')
    print('   - Free tier: 100 emails/day max')

if __name__ == "__main__":
    asyncio.run(test_sendgrid_connection()) 