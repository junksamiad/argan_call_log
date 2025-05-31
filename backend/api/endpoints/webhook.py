from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import Optional
import logging
import json
import uuid
import re
from datetime import datetime
from sqlalchemy.orm import Session
import hashlib

# Import our auto-reply system
from backend.services.auto_reply_service import AutoReplyService
from backend.models.database import Base
from backend.utils.database import get_db
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

def extract_email_address(email_string: str) -> str:
    """
    Extract clean email address from various formats:
    - 'user@example.com' -> 'user@example.com'
    - 'Name <user@example.com>' -> 'user@example.com'
    - 'Name user@example.com' -> 'user@example.com'
    """
    if not email_string:
        return ""
    
    # Look for email in angle brackets first
    angle_match = re.search(r'<([^>]+@[^>]+)>', email_string)
    if angle_match:
        return angle_match.group(1).strip()
    
    # Look for email pattern in the string
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email_string)
    if email_match:
        return email_match.group(0).strip()
    
    # If no pattern found, return the original (might already be clean)
    return email_string.strip()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify ngrok tunnel is working"""
    return {"message": "✅ Webhook endpoint is working!", "timestamp": datetime.now().isoformat()}

@router.post("/inbound")
async def inbound_parse(
    db: Session = Depends(get_db),
    # SendGrid Raw format sends 'email' field instead of 'headers'
    email: str = Form(None),  # Raw email content
    headers: str = Form(None),  # Regular format headers (make optional)
    subject: str = Form(None),
    text: str = Form(None),
    html: str = Form(None),
    from_email: str = Form(..., alias="from"),
    to: str = Form(...),
    envelope: str = Form(None),
    charsets: str = Form(None),
    SPF: str = Form(None),
    dkim: str = Form(None),
    sender_ip: str = Form(None),
    # Add more potential fields that SendGrid might send
    attachments: str = Form(None),
    attachment_info: str = Form(None),
    file1: Optional[UploadFile] = File(None),
    file2: Optional[UploadFile] = File(None),
    file3: Optional[UploadFile] = File(None),
    file4: Optional[UploadFile] = File(None),
    file5: Optional[UploadFile] = File(None),
):
    """
    Webhook endpoint for SendGrid Inbound Parse
    Processes incoming emails and sends auto-replies with ticket numbers
    """
    try:
        # Clean the sender email address (remove display name if present)
        clean_sender_email = extract_email_address(from_email)
        
        # Create a simple deduplication key based on sender, subject, and timestamp
        dedup_key = f"{clean_sender_email}:{subject}:{datetime.now().strftime('%Y%m%d%H%M')}"
        dedup_hash = hashlib.md5(dedup_key.encode()).hexdigest()
        
        print("=" * 60)
        print("🚀 INCOMING EMAIL RECEIVED!")
        print("=" * 60)
        print(f"📧 From: {from_email}")
        print(f"🧹 Cleaned From: {clean_sender_email}")
        print(f"📬 To: {to}")
        print(f"📝 Subject: {subject}")
        print(f"📄 Text Content: '{text}'" if text else "📄 No text content")
        print(f"📄 HTML Content: {'Present' if html else 'None'}")
        print(f"📧 Raw Email: {'Present' if email else 'None'}")
        print(f"📎 Attachments: {attachments if attachments else 'None'}")
        print(f"🔑 Dedup Hash: {dedup_hash}")
        print(f"🕐 Timestamp: {datetime.now()}")
        
        # If no text content but we have raw email, try to extract it
        email_body_text = text
        if not email_body_text and email:
            # Try to extract text from raw email
            try:
                import email as email_parser
                from email.mime.text import MIMEText
                msg = email_parser.message_from_string(email)
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            email_body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    if msg.get_content_type() == "text/plain":
                        email_body_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                print(f"📧 Extracted from raw: '{email_body_text[:200]}...'" if email_body_text else "📧 No text extracted from raw")
            except Exception as e:
                print(f"❌ Error parsing raw email: {e}")
        
        # Check for recent duplicate processing (simple in-memory cache for demo)
        # In production, you'd use Redis or database
        cache_key = f"processed_{dedup_hash}"
        if hasattr(db, '_email_cache'):
            if cache_key in db._email_cache:
                print("⚠️  DUPLICATE EMAIL DETECTED - Skipping processing")
                return PlainTextResponse("OK")
        else:
            db._email_cache = {}
        
        # Mark as processed (expires after 10 minutes)
        db._email_cache[cache_key] = datetime.now()
        
        # Clean old cache entries (basic cleanup)
        if len(db._email_cache) > 100:
            db._email_cache.clear()
        
        # Prepare email data for auto-reply service
        email_data = {
            'sender': clean_sender_email,  # Use cleaned email address
            'subject': subject or 'No Subject',
            'body_text': email_body_text or 'No text content',
            'body_html': html,
            'message_id': f"sendgrid-{uuid.uuid4()}",
            'recipients': [to],
            'email_date': datetime.utcnow(),
            'envelope': envelope,
            'sender_ip': sender_ip,
            'dkim': dkim,
            'spf': SPF
        }
        
        # Process with auto-reply service
        auto_reply_service = AutoReplyService(db)
        result = await auto_reply_service.process_incoming_email_and_reply(email_data)
        
        if result.get('success'):
            print(f"✅ EMAIL PROCESSED SUCCESSFULLY!")
            print(f"🎫 Ticket Number: {result.get('ticket_number')}")
            print(f"📧 Auto-reply sent: {result.get('auto_reply_sent')}")
            logger.info(f"✅ Email processed: Ticket {result.get('ticket_number')}, From {clean_sender_email}")
        else:
            print(f"❌ EMAIL PROCESSING FAILED: {result.get('message')}")
            logger.error(f"❌ Email processing failed: {result.get('error')}")
        
        print("=" * 60)
        
        # Return plain text "OK" as required by SendGrid
        return PlainTextResponse("OK")
        
    except Exception as e:
        print(f"❌ ERROR processing email: {e}")
        logger.error(f"Error processing inbound email: {e}")
        import traceback
        traceback.print_exc()
        # Still return OK to avoid SendGrid retries
        return PlainTextResponse("OK") 