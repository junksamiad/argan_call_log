"""
Email Classification Schema
Defines the structured output format for AI email classification
"""

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class EmailClassification(str, Enum):
    NEW_EMAIL = "NEW_EMAIL"
    EXISTING_EMAIL = "EXISTING_EMAIL"


class HRCategory(str, Enum):
    """HR domain categories matching Airtable Query Type field"""
    LEAVE_REQUEST = "Leave Request"
    POLICY_QUESTION = "Policy Question"
    PERFORMANCE_MANAGEMENT = "Performance Management"
    DISCIPLINARY = "Disciplinary"
    EMPLOYEE_RELATIONS = "Employee Relations"
    GRIEVANCE = "Grievance"
    COMPLAINT = "Complaint"
    PAYROLL = "Payroll"
    BENEFITS = "Benefits"
    TRAINING = "Training"
    RECRUITMENT = "Recruitment"
    GENERAL_INQUIRY = "General Inquiry"
    OTHER = "Other"


class TicketLocation(str, Enum):
    """Where ticket number was found in email"""
    SUBJECT = "subject"
    BODY = "body"
    BOTH = "both"
    NONE = "none"


class ContactInfo(BaseModel):
    """Contact information extracted from email"""
    sender_email: str
    sender_name: Optional[str] = None
    sender_domain: Optional[str] = None
    recipients: List[str] = []
    cc_recipients: List[str] = []
    reply_to: Optional[str] = None


class EmailMetadata(BaseModel):
    """Technical email metadata"""
    message_id: str
    subject: str
    email_date: Optional[str] = None
    content_type: Optional[str] = None
    encoding: Optional[str] = None
    priority: Optional[str] = None
    spam_score: Optional[str] = None
    dkim_status: Optional[str] = None
    spf_status: Optional[str] = None


class EmailContent(BaseModel):
    """Email content and structure"""
    body_text: str
    body_html: Optional[str] = None
    original_content: str  # Raw content before processing
    quoted_content: Optional[str] = None  # Any quoted/replied content
    signature: Optional[str] = None
    attachments: List[str] = []  # Attachment filenames
    thread_depth: int = 0  # How deep in conversation thread


class TicketInfo(BaseModel):
    """Ticket-related information if found"""
    ticket_number: Optional[str] = None
    ticket_found_in: Optional[TicketLocation] = None  # Now uses enum
    confidence_score: float = 0.0  # AI confidence in ticket detection
    context_around_ticket: Optional[str] = None  # Text surrounding ticket reference


class UrgencyIndicators(BaseModel):
    """Urgency and priority indicators"""
    urgency_keywords: List[str] = []  # urgent, asap, emergency, etc.
    deadline_mentions: List[str] = []  # Any date/time references
    escalation_indicators: List[str] = []  # manager, director mentions
    sentiment_tone: Optional[str] = None  # positive, negative, neutral, urgent


class FlattenedEmailData(BaseModel):
    """Flattened structure for easier parsing"""
    # Contact fields
    sender_email: str
    sender_name: Optional[str] = None
    sender_domain: Optional[str] = None
    recipients_list: str  # JSON string of recipients
    cc_recipients_list: str = "[]"  # JSON string of CC recipients
    
    # Content fields
    subject: str
    body_text: str
    body_html: Optional[str] = None
    message_id: str
    email_date: Optional[str] = None
    
    # Ticket fields
    ticket_number: Optional[str] = None
    ticket_found_in: Optional[TicketLocation] = None  # Now uses enum constraint
    ticket_confidence: float = 0.0
    
    # Urgency fields
    urgency_keywords_list: str = "[]"  # JSON string of keywords (kept flexible)
    deadline_mentions_list: str = "[]"  # JSON string of deadlines (kept flexible)
    sentiment_tone: Optional[str] = None  # Kept flexible for AI descriptive analysis
    
    # AI Analysis fields
    ai_summary: Optional[str] = None  # AI-generated summary of email content
    hr_category: Optional[HRCategory] = None  # Now uses enum constraint - FIXED!
    
    # Technical fields
    attachments_list: str = "[]"  # JSON string of attachment names
    thread_depth: int = 0
    dkim_status: Optional[str] = None
    spf_status: Optional[str] = None


class EmailClassificationResponse(BaseModel):
    """Main response structure from AI classifier"""
    EMAIL_CLASSIFICATION: EmailClassification
    EMAIL_DATA: FlattenedEmailData
    
    # Processing metadata
    processing_timestamp: str
    ai_model_used: str = "gpt-4.1"
    confidence_score: float
    notes: Optional[str] = None  # Any additional AI observations 