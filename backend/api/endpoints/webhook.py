from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Optional
import logging
import json
import uuid
from datetime import datetime

# Comment out database imports for testing
# from backend.database import get_email_table
# from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify ngrok tunnel is working"""
    return {"message": "✅ Webhook endpoint is working!", "timestamp": datetime.now().isoformat()}

@router.post("/inbound")
async def inbound_parse(
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
    file1: Optional[UploadFile] = File(None),
    file2: Optional[UploadFile] = File(None),
    file3: Optional[UploadFile] = File(None),
    file4: Optional[UploadFile] = File(None),
    file5: Optional[UploadFile] = File(None),
):
    """
    TEST VERSION: Webhook endpoint for SendGrid Inbound Parse - Just logging for now
    Handles both regular and raw formats from SendGrid
    """
    try:
        print("=" * 60)
        print("🚀 INCOMING EMAIL RECEIVED!")
        print("=" * 60)
        print(f"📧 From: {from_email}")
        print(f"📬 To: {to}")
        print(f"📝 Subject: {subject}")
        print(f"📄 Text Preview: {text[:200] if text else 'No text body'}...")
        print(f"🔒 DKIM: {dkim}")
        print(f"🛡️ SPF: {SPF}")
        print(f"🌐 Sender IP: {sender_ip}")
        print(f"📦 Envelope: {envelope}")
        print(f"📎 Attachments: {[f.filename for f in [file1, file2, file3, file4, file5] if f]}")
        print(f"🕐 Timestamp: {datetime.now()}")
        
        # Show raw email if available
        if email:
            print(f"📧 Raw Email Preview: {email[:300]}..." if len(email) > 300 else email)
        
        print("=" * 60)
        
        # Log to uvicorn logs as well
        logger.info(f"✅ EMAIL TEST: From {from_email}, Subject: {subject}, To: {to}")
        
        # Return plain text "OK" as required by SendGrid
        return PlainTextResponse("OK - Email received and logged!")
        
    except Exception as e:
        print(f"❌ ERROR processing email: {e}")
        logger.error(f"Error processing inbound email: {e}")
        # Still return OK to avoid SendGrid retries
        return PlainTextResponse("OK") 