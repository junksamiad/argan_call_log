from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum, LargeBinary, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base
import enum


class EmailStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    CLOSED = "closed"


class EmailThread(Base):
    __tablename__ = "email_threads"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True)
    subject = Column(String(500), nullable=False)
    sender_email = Column(String(255), nullable=False)
    status = Column(Enum(EmailStatus), default=EmailStatus.OPEN)
    
    # AI-extracted fields
    staff_name = Column(String(255), nullable=True)
    query_type = Column(String(100), nullable=True)
    urgency = Column(String(50), nullable=True)
    executive_summary = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON string
    dates_mentioned = Column(Text, nullable=True)  # JSON string
    people_mentioned = Column(Text, nullable=True)  # JSON string
    
    # Response fields
    suggested_response = Column(Text, nullable=True)
    final_response = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    messages = relationship("EmailMessage", back_populates="thread")
    approved_by = relationship("User", back_populates="approved_threads")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ticket_number:
            # Generate ticket number after the instance is added to session
            from sqlalchemy.orm import object_session
            session = object_session(self)
            if session:
                session.flush()  # This will assign the ID
                self.ticket_number = f"ARG-{self.id:05d}"


class EmailMessage(Base):
    __tablename__ = "email_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"), nullable=False)
    message_id = Column(String(255), nullable=True)  # Email Message-ID header
    sender = Column(String(255), nullable=False)
    recipients = Column(JSON, nullable=True)  # List of recipients
    cc = Column(JSON, nullable=True)  # List of CC recipients
    subject = Column(String(500), nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    direction = Column(String(10), nullable=False)  # 'inbound' or 'outbound'
    raw_headers = Column(Text, nullable=True)
    
    # Timestamps
    email_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    thread = relationship("EmailThread", back_populates="messages")
    attachments = relationship("EmailAttachment", back_populates="message")


class EmailAttachment(Base):
    __tablename__ = "email_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("email_messages.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    size = Column(Integer, nullable=False)
    content = Column(LargeBinary, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    message = relationship("EmailMessage", back_populates="attachments")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # 'hr_staff' or 'ops_manager'
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    approved_threads = relationship("EmailThread", back_populates="approved_by") 