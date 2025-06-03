"""
HR Email Management Server with AI Classification and Airtable Integration
Handles incoming emails via SendGrid webhook and processes them with AI
"""

import logging
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

from backend.email_functions.email_router import route_email_async
from backend.email_functions.webhook_handler import WebhookHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HR Email Management System",
    description="AI-powered email classification and routing system for Argan Consultancy",
    version="2.0.0"
)

# Initialize webhook handler
webhook_handler = WebhookHandler()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "HR Email Management System",
        "version": "2.0.0",
        "status": "running",
        "ai_enabled": True,
        "database": "Airtable",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check with dependencies"""
    try:
        # Check Airtable connection
        from backend.airtable_service import AirtableService
        airtable = AirtableService()
        airtable_status = airtable.health_check()
        
        # Check OpenAI connection
        import os
        openai_configured = bool(os.getenv("OPENAI_API_KEY"))
        
        return {
            "status": "healthy",
            "checks": {
                "airtable": "connected" if airtable_status else "disconnected",
                "openai": "configured" if openai_configured else "not_configured",
                "email_processing": "ready"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


@app.post("/webhook/inbound")
async def handle_inbound_email(request: Request):
    """
    Handle incoming emails from SendGrid webhook
    Process with AI classification and route accordingly
    """
    try:
        # Parse the webhook data
        email_data = await webhook_handler.parse_webhook(request)
        
        if not email_data:
            logger.error("❌ No email data received from webhook")
            raise HTTPException(status_code=400, detail="Invalid webhook data")
        
        # Log incoming email details
        logger.info("=" * 60)
        logger.info("🚀 INCOMING EMAIL RECEIVED!")
        logger.info("=" * 60)
        logger.info(f"📧 From: {email_data.get('sender_name', 'Unknown')} <{email_data.get('sender', 'unknown@unknown.com')}>")
        logger.info(f"🧹 Cleaned From: {email_data.get('sender', 'unknown@unknown.com')}")
        logger.info(f"📬 To: {email_data.get('recipients', ['Unknown'])}")
        logger.info(f"📝 Subject: {email_data.get('subject', 'No Subject')}")
        logger.info(f"📄 Body Text: {(email_data.get('body_text', 'No text content')[:50] + '...') if len(email_data.get('body_text', '')) > 50 else email_data.get('body_text', 'No text content')}")
        logger.info(f"📄 HTML Content: {'Present' if email_data.get('body_html') else 'None'}")
        logger.info(f"📧 Raw Email: {'Present' if email_data.get('raw_email') else 'None'}")
        logger.info(f"📎 Attachments: {email_data.get('attachments', 'None')}")
        logger.info(f"🔑 Dedup Hash: {email_data.get('dedup_hash', 'None')}")
        logger.info(f"🕐 Timestamp: {email_data.get('timestamp', 'Unknown')}")
        
        # Extract body from raw email if needed
        if email_data.get('raw_email') and not email_data.get('body_text'):
            extracted_text = webhook_handler.extract_text_from_raw_email(email_data['raw_email'])
            if extracted_text:
                email_data['body_text'] = extracted_text
                logger.info(f"📧 Extracted from raw: '{extracted_text[:50]}...'")
        
        # Process the email using AI router
        result = await route_email_async(email_data)
        
        if result.get('success'):
            logger.info("✅ EMAIL PROCESSING SUCCESSFUL!")
            logger.info(f"🎫 Ticket: {result.get('ticket_number', 'N/A')}")
            logger.info(f"🤖 AI Classification: {result.get('ai_classification', 'N/A')}")
            logger.info(f"📊 Airtable Record: {result.get('airtable_record_id', 'N/A')}")
            logger.info("=" * 60)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": result.get('message', 'Email processed successfully'),
                    "ticket_number": result.get('ticket_number'),
                    "ai_classification": result.get('ai_classification'),
                    "confidence": result.get('ai_confidence'),
                    "airtable_record_id": result.get('airtable_record_id')
                }
            )
        else:
            logger.error("❌ EMAIL PROCESSING FAILED!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            logger.info("=" * 60)
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": result.get('message', 'Email processing failed'),
                    "error": result.get('error')
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Email processing failed: {e}")
        logger.info("=" * 60)
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "error": str(e)
            }
        )


@app.get("/stats")
async def get_processing_stats():
    """Get email processing statistics from Airtable"""
    try:
        from backend.airtable_service import AirtableService
        airtable = AirtableService()
        
        # Get all records
        all_records = airtable.table.all()
        
        # Calculate stats
        total_emails = len(all_records)
        new_emails = len([r for r in all_records if r['fields'].get('AI Classification') == 'NEW_EMAIL'])
        existing_emails = len([r for r in all_records if r['fields'].get('AI Classification') == 'EXISTING_EMAIL'])
        
        return {
            "total_emails_processed": total_emails,
            "new_emails": new_emails,
            "existing_emails": existing_emails,
            "auto_replies_sent": len([r for r in all_records if r['fields'].get('Auto Reply Sent')]),
            "average_confidence": sum([r['fields'].get('AI Confidence', 0) for r in all_records]) / max(total_emails, 1),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/conversation/{ticket_number}")
async def get_full_conversation(ticket_number: str):
    """
    Get the complete conversation history for a ticket using the computed formula field
    
    Args:
        ticket_number: Ticket number (e.g., ARG-20250603-1234)
        
    Returns:
        Complete conversation data including all messages and metadata
    """
    try:
        from backend.airtable_service import AirtableService
        airtable = AirtableService()
        
        # Export full conversation data
        conversation_data = airtable.export_conversation_data(ticket_number)
        
        if not conversation_data:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Ticket not found",
                    "ticket_number": ticket_number
                }
            )
        
        logger.info(f"📄 [API] Exported conversation for {ticket_number}: {conversation_data['message_count']} messages")
        
        return {
            "status": "success",
            "data": conversation_data,
            "export_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting conversation for {ticket_number}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "ticket_number": ticket_number
            }
        )


@app.get("/conversation/{ticket_number}/messages")
async def get_conversation_messages_only(ticket_number: str):
    """
    Get just the conversation messages array for a ticket (no metadata)
    
    Args:
        ticket_number: Ticket number (e.g., ARG-20250603-1234)
        
    Returns:
        Array of conversation messages in chronological order
    """
    try:
        from backend.airtable_service import AirtableService
        airtable = AirtableService()
        
        # Get just the messages
        messages = airtable.get_full_conversation_history(ticket_number)
        
        if not messages:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Ticket not found or no messages",
                    "ticket_number": ticket_number
                }
            )
        
        return {
            "status": "success",
            "ticket_number": ticket_number,
            "messages": messages,
            "message_count": len(messages),
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting messages for {ticket_number}: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "ticket_number": ticket_number
            }
        )


if __name__ == "__main__":
    print("🚀 Starting HR Email Management Server v2.0")
    print("📊 Database: Airtable")
    print("🤖 AI Classification: Enabled")
    print("=" * 50)
    
    uvicorn.run(
        "backend.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 