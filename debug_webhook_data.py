#!/usr/bin/env python3
"""
Debug Webhook Data
Helper script to understand what SendGrid is sending in webhooks
"""

import json
from datetime import datetime

def debug_webhook_structure():
    """Help understand SendGrid webhook data structure"""
    
    print("🔍 SendGrid Inbound Email Webhook Debug Guide")
    print("=" * 60)
    
    print("📋 Expected SendGrid Inbound Email Webhook Fields:")
    print("- text: Plain text body of the email")
    print("- html: HTML body of the email")  
    print("- from: Sender email address")
    print("- to: Recipient email address")
    print("- subject: Email subject line")
    print("- headers: Email headers (JSON string)")
    print("- attachment-info: Attachment data (JSON string)")
    print("- charsets: Character set information (JSON string)")
    print()
    
    print("🚨 COMMON ISSUES:")
    print("1. SendGrid might send 'text' instead of 'body_text'")
    print("2. Body content might be in 'headers' field")
    print("3. Content might be base64 encoded")
    print("4. Multiple formats might exist (text vs html)")
    print()
    
    print("🔧 DEBUGGING STEPS:")
    print("1. Check SendGrid inbound email webhook configuration")
    print("2. Verify webhook URL is receiving POST data")
    print("3. Log ALL webhook fields to identify body content location")
    print("4. Check for encoding issues (UTF-8, base64, etc.)")
    print()
    
    print("📖 SendGrid Documentation:")
    print("https://docs.sendgrid.com/for-developers/parsing-email/inbound-email")
    print()
    
    # Sample webhook data structure
    sample_webhook = {
        "headers": "Received: from mail.example.com...",
        "dkim": "{@example.com : pass}",
        "to": "test@example.com",
        "html": "<html><body>Email HTML content</body></html>",
        "from": "sender@example.com",
        "text": "Email plain text content",  # This is what we're missing!
        "sender_ip": "192.168.1.1",
        "spam_report": "...",
        "envelope": '{"to":["test@example.com"],"from":"sender@example.com"}',
        "attachments": "0",
        "subject": "Test Email Subject",
        "spam_score": "0.1",
        "charsets": '{"to":"UTF-8","html":"UTF-8","subject":"UTF-8","from":"UTF-8","text":"UTF-8"}',
        "SPF": "pass"
    }
    
    print("📋 Sample Webhook Data Structure:")
    print(json.dumps(sample_webhook, indent=2))
    print()
    
    print("🎯 KEY FIELDS FOR BODY CONTENT:")
    print("- 'text': Plain text email body (PRIMARY)")
    print("- 'html': HTML email body (SECONDARY)")
    print("- Check if fields are nested or differently named")

if __name__ == "__main__":
    debug_webhook_structure() 