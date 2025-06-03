"""
Minimal HR Email Management Server - Backend2
Just logs incoming SendGrid webhook payloads for debugging
"""

import logging
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging to see everything in console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HR Email Management System - Backend2",
    description="Minimal version for debugging SendGrid webhook payloads",
    version="2.0.0-debug"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "HR Email Management System - Backend2",
        "version": "2.0.0-debug",
        "status": "running",
        "purpose": "debugging_webhook_payloads",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/webhook/inbound")
async def handle_inbound_email(request: Request):
    """
    Handle incoming emails from SendGrid webhook
    Route to main orchestrator for processing
    """
    try:
        # Get the raw body with UTF-8 error handling at the top level
        try:
            raw_body = await request.body()
        except UnicodeDecodeError as e:
            logger.warning(f"⚠️ [WEBHOOK] UTF-8 error getting request body: {e}")
            logger.info(f"🔧 [WEBHOOK] Attempting to handle problematic encoding...")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "encoding_error", 
                    "message": "Request contains invalid UTF-8 characters",
                    "error": str(e)
                }
            )
        
        # Always use our custom parser that handles UTF-8 errors
        logger.info(f"🔧 [WEBHOOK] Using custom multipart parser with UTF-8 error handling...")
        from .utils import parse_multipart_form_data
        raw_payload = parse_multipart_form_data(raw_body)
        
        # Log incoming email
        logger.info("=" * 80)
        logger.info("🚀 INCOMING EMAIL WEBHOOK!")
        logger.info("=" * 80)
        logger.info(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
        logger.info(f"📏 Content Length: {len(raw_body)} bytes")
        logger.info(f"📦 Content Type: {request.headers.get('content-type', 'unknown')}")
        logger.info(f"📋 Parsed Fields: {list(raw_payload.keys())}")
        
        # Route to main orchestrator with UTF-8 error handling
        try:
            from .main import process_email
            result = await process_email(raw_payload)
        except UnicodeDecodeError as e:
            logger.error(f"❌ [WEBHOOK] UTF-8 decode error in main processing: {e}")
            logger.info(f"🔧 [WEBHOOK] Returning error response for UTF-8 issue")
            return JSONResponse(
                status_code=400,
                content={
                    "status": "processing_encoding_error",
                    "message": "Email processing failed due to encoding issues", 
                    "error": str(e)
                }
            )
        
        if result.get('success'):
            logger.info("✅ EMAIL PROCESSING SUCCESSFUL!")
            logger.info(f"🔀 Path taken: {result.get('path_taken', 'unknown')}")
            logger.info("=" * 80)
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": result.get('message', 'Email processed successfully'),
                    "path_taken": result.get('path_taken'),
                    "timestamp": result.get('timestamp')
                }
            )
        else:
            logger.error("❌ EMAIL PROCESSING FAILED!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            logger.info("=" * 80)
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": result.get('message', 'Email processing failed'),
                    "error": result.get('error')
                }
            )
            
    except UnicodeDecodeError as e:
        logger.error(f"❌ UTF-8 decode error in webhook handler: {e}")
        logger.info(f"🔧 [WEBHOOK] Position {e.start}-{e.end} contains problematic bytes")
        logger.info("=" * 80)
        
        return JSONResponse(
            status_code=400,
            content={
                "status": "utf8_error",
                "message": "Webhook contains invalid UTF-8 characters - auto-reply forwarding loop detected",
                "error": str(e),
                "position": f"{e.start}-{e.end}"
            }
        )
    except Exception as e:
        logger.error(f"❌ Critical error in webhook handler: {e}")
        logger.info("=" * 80)
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Critical webhook processing error",
                "error": str(e)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}")
        print(f"❌ ERROR: {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Failed to process webhook: {str(e)}"
            }
        )


if __name__ == "__main__":
    print("🚀 Starting HR Email Management Server - Backend2 (Debug Mode)")
    print("📧 Webhook endpoint: POST /webhook/inbound")
    print("🔍 Purpose: Log SendGrid webhook payloads")
    print("=" * 60)
    
    uvicorn.run(
        "backend2.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 