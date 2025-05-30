from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
from backend.utils.database import get_db, init_db, SessionLocal
from backend.services.email_processor import EmailProcessor
from backend.models import schemas, database
from backend.api import auth
from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="HR Email Query Management System API"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    logger.info("Application started")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Argan HR Email Management System API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/api/v1/threads", response_model=schemas.ThreadListResponse)
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
        thread_dict = thread.__dict__
        thread_dict['message_count'] = len(thread.messages)
        if thread.messages:
            thread_dict['last_message_date'] = max(msg.created_at for msg in thread.messages)
        thread_responses.append(schemas.EmailThreadResponse(**thread_dict))
    
    return schemas.ThreadListResponse(
        threads=thread_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@app.get("/api/v1/threads/{thread_id}", response_model=schemas.EmailThreadResponse)
async def get_thread(thread_id: int, db: Session = Depends(get_db)):
    """Get a specific email thread"""
    thread = db.query(database.EmailThread).filter(database.EmailThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread_dict = thread.__dict__
    thread_dict['message_count'] = len(thread.messages)
    if thread.messages:
        thread_dict['last_message_date'] = max(msg.created_at for msg in thread.messages)
        
    return schemas.EmailThreadResponse(**thread_dict)


@app.get("/api/v1/threads/{thread_id}/messages", response_model=List[schemas.EmailMessageResponse])
async def get_thread_messages(thread_id: int, db: Session = Depends(get_db)):
    """Get all messages in a thread"""
    messages = db.query(database.EmailMessage).filter(
        database.EmailMessage.thread_id == thread_id
    ).order_by(database.EmailMessage.created_at).all()
    
    return [schemas.EmailMessageResponse.from_orm(msg) for msg in messages]


@app.post("/api/v1/threads/{thread_id}/reply")
async def send_reply(
    thread_id: int,
    reply: schemas.EmailReplyRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send a reply to an email thread"""
    processor = EmailProcessor(db)
    
    success = processor.send_reply(
        thread_id=thread_id,
        body=reply.body,
        recipients=reply.recipients,
        cc=reply.cc
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
        
    return {"message": "Reply sent successfully", "thread_id": thread_id}


@app.post("/api/v1/process-emails")
async def process_emails(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger email processing"""
    def process():
        with SessionLocal() as db_session:
            processor = EmailProcessor(db_session)
            processor.process_new_emails()
            
    background_tasks.add_task(process)
    return {"message": "Email processing started"}


@app.put("/api/v1/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: int,
    status: schemas.ThreadStatus,
    db: Session = Depends(get_db)
):
    """Update thread status"""
    thread = db.query(database.EmailThread).filter(database.EmailThread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    thread.status = status.value
    db.commit()
    
    return {"message": "Status updated", "thread_id": thread_id, "status": status.value}


@app.put("/api/v1/messages/{message_id}/approve")
async def approve_message(
    message_id: int,
    approved_by: str,
    db: Session = Depends(get_db)
):
    """Approve a message for sending"""
    message = db.query(database.EmailMessage).filter(database.EmailMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
        
    message.approved_by = approved_by
    message.approved_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Message approved", "message_id": message_id}


# Include auth routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 