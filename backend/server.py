"""
Argan Auto-Reply System Server
Main FastAPI application entry point
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Form, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
import uvicorn
import uuid
import re
import hashlib

# Configuration
from pydantic_settings import BaseSettings
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load .env file explicitly - this ensures .env takes priority
load_dotenv()

# API Response Models
class EmailThreadResponse(BaseModel):
    id: int
    thread_id: str
    ticket_number: str
    subject: str
    status: str
    priority: str
    staff_email: str
    staff_name: str
    query_type: Optional[str]
    department: Optional[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    message_count: int = 0
    last_message_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EmailMessageResponse(BaseModel):
    id: int
    thread_id: int
    message_id: str
    sender: str
    recipients: List[str]
    cc: List[str] = []
    subject: str
    body_text: str
    body_html: Optional[str]
    message_type: str
    direction: str
    suggested_response: Optional[str]
    requires_approval: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    email_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    threads: List[EmailThreadResponse]
    total: int
    page: int
    page_size: int

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///argan_email.db")
    
    # Email Configuration - SendGrid
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "support@email.adaptixinnovation.co.uk")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_WEBHOOK_VERIFICATION_KEY: Optional[str] = os.getenv("SENDGRID_WEBHOOK_VERIFICATION_KEY", None)
    PARSE_DOMAIN: str = os.getenv("PARSE_DOMAIN", "email.adaptixinnovation.co.uk")
    
    # Airtable Configuration (for future use)
    AIRTABLE_API_KEY: str = os.getenv("AIRTABLE_API_KEY", "")
    AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "")
    AIRTABLE_TABLE_NAME: str = os.getenv("AIRTABLE_TABLE_NAME", "call_log")
    
    # App Configuration
    TICKET_PREFIX: str = os.getenv("TICKET_PREFIX", "ARG")
    
    class Config:
        case_sensitive = True

settings = Settings()

from backend.database import get_db, init_db, SessionLocal
from backend import database
from backend.database import ThreadStatus
from backend.email_functions.email_router import EmailRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Argan Call Log - Auto-Reply System",
    version="1.0.0",
    description="HR Email Auto-Reply System with Ticket Generation"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("🚀 [SERVER] Argan Auto-Reply System started")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🎯 Argan Auto-Reply System",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "webhook_test": "/webhook/test",
            "sendgrid_inbound": "/webhook/inbound",
            "threads": "/api/v1/threads"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "system": "auto-reply",
        "database": "connected"
    }


@app.get("/webhook/test")
async def test_webhook():
    """Simple test endpoint to verify ngrok tunnel is working"""
    return {"message": "✅ Webhook endpoint is working!", "timestamp": datetime.now().isoformat()}


@app.post("/webhook/inbound")
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
        
        # Process with email router
        email_router = EmailRouter(db)
        result = await email_router.route_email(email_data)
        
        if result.get('success'):
            print(f"✅ EMAIL PROCESSED SUCCESSFULLY!")
            print(f"🎫 Ticket Number: {result.get('ticket_number')}")
            print(f"📧 Auto-reply sent: {result.get('auto_reply_sent')}")
            logger.info(f"🏁 [SERVER] Email processed successfully - Ticket: {result.get('ticket_number')}, From: {clean_sender_email}")
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


@app.get("/api/v1/threads", response_model=ThreadListResponse)
async def get_threads(
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of email threads with pagination"""
    query = db.query(database.EmailThread)
    
    if status:
        query = query.filter(database.EmailThread.status == status)
    if priority:
        query = query.filter(database.EmailThread.priority == priority)
        
    total = query.count()
    
    # Calculate pagination
    skip = (page - 1) * page_size
    threads = query.offset(skip).limit(page_size).all()
    
    # Convert to response model
    thread_responses = []
    for thread in threads:
        thread_dict = thread.__dict__.copy()
        thread_dict['message_count'] = len(thread.messages)
        if thread.messages:
            thread_dict['last_message_date'] = max(msg.created_at for msg in thread.messages)
        thread_responses.append(EmailThreadResponse(**thread_dict))
    
    return ThreadListResponse(
        threads=thread_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@app.get("/api/v1/threads/{thread_id}", response_model=EmailThreadResponse)
async def get_thread(thread_id: int, db: Session = Depends(get_db)):
    """Get a specific email thread"""
    thread = db.query(database.EmailThread).filter(database.EmailThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread_dict = thread.__dict__.copy()
    thread_dict['message_count'] = len(thread.messages)
    if thread.messages:
        thread_dict['last_message_date'] = max(msg.created_at for msg in thread.messages)
        
    return EmailThreadResponse(**thread_dict)


@app.get("/api/v1/threads/{thread_id}/messages", response_model=List[EmailMessageResponse])
async def get_thread_messages(thread_id: int, db: Session = Depends(get_db)):
    """Get all messages in a thread"""
    messages = db.query(database.EmailMessage).filter(
        database.EmailMessage.thread_id == thread_id
    ).order_by(database.EmailMessage.created_at).all()
    
    return [EmailMessageResponse.from_orm(msg) for msg in messages]


@app.put("/api/v1/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: int,
    status: ThreadStatus,
    db: Session = Depends(get_db)
):
    """Update thread status"""
    thread = db.query(database.EmailThread).filter(database.EmailThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread.status = status.value
    db.commit()
    
    return {"message": "Status updated", "thread_id": thread_id, "status": status.value}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 