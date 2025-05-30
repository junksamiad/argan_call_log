#!/usr/bin/env python3
"""
Test IONOS webmail login to verify credentials
"""

import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "argan-bot@arganhrconsultancy.co.uk")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "Dashboard2025!")

print("=== IONOS Webmail Login Test ===")
print(f"Email: {EMAIL_ADDRESS}")
print(f"Password length: {len(EMAIL_PASSWORD)} characters")
print()

def test_webmail_login():
    """Test login to IONOS webmail"""
    
    # IONOS webmail login endpoint
    login_url = "https://mail.ionos.com/"
    
    # Create a session to handle cookies
    session = requests.Session()
    
    # Common headers to appear like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print("1. Accessing IONOS webmail login page...")
        response = session.get(login_url, headers=headers)
        
        if response.status_code == 200:
            print("✓ Successfully reached login page")
        else:
            print(f"✗ Got status code: {response.status_code}")
            
        # Check if we're redirected to a specific login form
        print(f"\n2. Final URL: {response.url}")
        
        # Look for login form indicators
        if "login" in response.url.lower() or "signin" in response.url.lower():
            print("✓ Login form detected")
        
        # Check page content for clues
        content_lower = response.text.lower()
        if "username" in content_lower or "email" in content_lower:
            print("✓ Username/email field found")
        if "password" in content_lower:
            print("✓ Password field found")
            
        print("\n3. Login Details:")
        print(f"   Email: {EMAIL_ADDRESS}")
        print(f"   Password: {'*' * len(EMAIL_PASSWORD)}")
        
        print("\n4. Next Steps:")
        print("   - Open https://mail.ionos.com/ in your browser")
        print("   - Try logging in with the credentials above")
        print("   - If login fails, the password is incorrect")
        print("   - If login succeeds, check for any security settings")
        
        # Additional checks
        print("\n5. Additional Information:")
        if "ionos" in response.text.lower():
            print("✓ IONOS branding detected on page")
        
        # Try to find any API endpoints or form actions
        if 'action="' in response.text:
            import re
            actions = re.findall(r'action="([^"]+)"', response.text)
            if actions:
                print(f"✓ Found form actions: {actions[:3]}")  # Show first 3
                
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to IONOS webmail")
        print("   Check your internet connection")
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        
    print("\n" + "="*50)
    print("RECOMMENDATION:")
    print("Since automated login testing is complex due to:")
    print("- CSRF tokens")
    print("- Captchas")
    print("- Dynamic JavaScript")
    print("\nPlease manually test the login:")
    print(f"1. Go to: https://mail.ionos.com/")
    print(f"2. Enter email: {EMAIL_ADDRESS}")
    print(f"3. Enter password: {EMAIL_PASSWORD}")
    print("4. If login works → password is correct")
    print("5. If login fails → password is wrong or account issue")
    print("\nAfter successful login, check:")
    print("- Account settings")
    print("- Security settings")
    print("- IMAP/SMTP access settings")

if __name__ == "__main__":
    test_webmail_login() 