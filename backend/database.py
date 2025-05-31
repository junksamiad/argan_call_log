from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, event, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func
from sqlalchemy.pool import StaticPool
from datetime import datetime
from enum import Enum
import uuid
import os
import logging

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///argan_email.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    try:
        # Import here to ensure event listeners are registered
        from backend.email_functions.classification import assign_ticket
        
        Base.metadata.create_all(bind=engine)
        logger.info("💾 [DATABASE] Database tables created successfully")
        
        # Initialize ticket counter
        with SessionLocal() as db:
            assign_ticket.init_ticket_counter(db)
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enums for database field values
class MessageType(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    INTERNAL_NOTE = "internal_note"


class ThreadStatus(str, Enum):
    OPEN = "open"
    PENDING_APPROVAL = "pending_approval"
    CLOSED = "closed"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class QueryType(str, Enum):
    LEAVE_REQUEST = "leave_request"
    POLICY_QUESTION = "policy_question"
    COMPLAINT = "complaint"
    GENERAL_INQUIRY = "general_inquiry"
    PAYROLL = "payroll"
    BENEFITS = "benefits"
    TRAINING = "training"
    OTHER = "other"

Base = declarative_base()


class TicketCounter(Base):
    """Table to track the last used ticket number"""
    __tablename__ = "ticket_counter"
    
    id = Column(Integer, primary_key=True, default=1)
    last_number = Column(Integer, default=0)


class EmailThread(Base):
    __tablename__ = "email_threads"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    ticket_number = Column(String, unique=True, index=True)  # Will be set by event listener
    subject = Column(String)
    status = Column(String, default="open")  # open, pending_approval, closed
    priority = Column(String, default="normal")  # low, normal, high, urgent
    
    # Staff member who initiated the query
    staff_email = Column(String)
    staff_name = Column(String)
    
    # Extracted information
    query_type = Column(String)
    department = Column(String)
    extracted_data = Column(JSON)  # Store structured data from AI extraction
    summary = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    messages = relationship("EmailMessage", back_populates="thread", order_by="EmailMessage.created_at")
    
    
class EmailMessage(Base):
    __tablename__ = "email_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"))
    message_id = Column(String, unique=True)  # Email message ID
    
    # Email details
    sender = Column(String)
    recipients = Column(JSON)  # List of recipients
    cc = Column(JSON)  # List of CC recipients
    subject = Column(String)
    body_text = Column(Text)
    body_html = Column(Text)
    
    # Message type
    message_type = Column(String)  # inbound, outbound, internal_note
    direction = Column(String)  # in, out
    
    # AI-generated response suggestion
    suggested_response = Column(Text)
    suggestion_approved = Column(Boolean, default=False)
    
    # Approval tracking
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String)
    approved_at = Column(DateTime(timezone=True))
    
    # Timestamps
    email_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    thread = relationship("EmailThread", back_populates="messages")
    attachments = relationship("EmailAttachment", back_populates="message")
    

class EmailAttachment(Base):
    __tablename__ = "email_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("email_messages.id"))
    filename = Column(String)
    content_type = Column(String)
    size = Column(Integer)
    storage_path = Column(String)
    
    # Relationships
    message = relationship("EmailMessage", back_populates="attachments")
    

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(String)  # admin, hr_staff, ops_manager, viewer
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 