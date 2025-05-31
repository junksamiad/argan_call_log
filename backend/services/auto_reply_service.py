"""
Auto Reply Service for HR Email Management System
Handles automatic replies to incoming emails with ticket number generation
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.services.email_service import EmailService
from backend.models.database import EmailThread, EmailMessage, TicketCounter
from backend.models.schemas import MessageType, ThreadStatus
from config.settings import settings

logger = logging.getLogger(__name__)


class AutoReplyService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.email_service = EmailService()
        self.advice_email = "advice@arganconsultancy.co.uk"
    
    def generate_ticket_number(self) -> str:
        """
        Generate a unique ticket number in format: ARG-YYYYMMDD-XXXX
        Where XXXX is a sequential number for the day
        """
        try:
            # Get current date
            today = datetime.now().strftime("%Y%m%d")
            
            # Get or create ticket counter for today
            counter = self.db.query(TicketCounter).first()
            if not counter:
                counter = TicketCounter(last_number=0)
                self.db.add(counter)
                self.db.flush()
            
            # Increment counter
            counter.last_number += 1
            next_number = counter.last_number
            
            # Format ticket number
            ticket_number = f"ARG-{today}-{next_number:04d}"
            
            # Ensure uniqueness (in case of race conditions)
            existing = self.db.query(EmailThread).filter_by(ticket_number=ticket_number).first()
            if existing:
                # If exists, increment and try again
                counter.last_number += 1
                next_number = counter.last_number
                ticket_number = f"ARG-{today}-{next_number:04d}"
            
            self.db.commit()
            logger.info(f"Generated ticket number: {ticket_number}")
            return ticket_number
            
        except Exception as e:
            logger.error(f"Error generating ticket number: {e}")
            self.db.rollback()
            # Fallback to timestamp-based ticket
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"ARG-{timestamp}"
    
    def extract_existing_ticket_number(self, subject: str) -> Optional[str]:
        """
        Extract existing ticket number from subject line
        Looks for patterns like [ARG-YYYYMMDD-XXXX] or ARG-YYYYMMDD-XXXX
        """
        patterns = [
            r'\[?(ARG-\d{8}-\d{4})\]?',
            r'#(ARG-\d{8}-\d{4})',
            r'Ticket:?\s*(ARG-\d{8}-\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, subject, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def format_reply_subject(self, original_subject: str, ticket_number: str) -> str:
        """
        Format the reply subject with ticket number
        """
        # Remove common reply prefixes
        subject = re.sub(r'^(Re:|RE:|Fwd:|FWD:)\s*', '', original_subject, flags=re.IGNORECASE).strip()
        
        # Check if ticket number already exists in subject
        if ticket_number.upper() in subject.upper():
            return f"Re: {subject}"
        
        # Add ticket number to subject
        return f"Re: [{ticket_number}] {subject}"
    
    def generate_auto_reply_content(self, ticket_number: str, original_sender: str, original_subject: str = "", original_body: str = "") -> Dict[str, str]:
        """
        Generate the content for the auto-reply email
        """
        # Clean up the original body for display
        original_content = original_body.strip() if original_body else "No message content"
        if len(original_content) > 500:
            original_content = original_content[:500] + "..."
        
        text_content = f"""Dear Colleague,

Thank you for contacting Argan Consultancy HR Services.

This is your ticket number: {ticket_number}
Please use this ticket number for all future correspondence regarding this matter.

Your query has been received and logged in our system. A member of our HR team will review your request and respond as soon as possible.

If your matter is urgent, please call our office directly.

---
Your Original Message:
Subject: {original_subject}
Message: {original_content}
---

Best regards,
Argan Consultancy HR Team

---
This is an automated response. Please do not reply to this email directly.
For urgent matters, please contact our office.
"""

        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
    <div style="background-color: #2c5aa0; color: white; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">Argan Consultancy HR Services</h2>
    </div>
    
    <div style="padding: 20px; background-color: #f8f9fa;">
        <p>Dear Colleague,</p>
        
        <p>Thank you for contacting Argan Consultancy HR Services.</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">📋 Your Ticket Number</h3>
            <p style="font-size: 18px; font-weight: bold; color: #155724; margin: 0;">
                {ticket_number}
            </p>
            <p style="margin: 10px 0 0 0; font-style: italic;">
                Please use this ticket number for all future correspondence regarding this matter.
            </p>
        </div>
        
        <p>Your query has been received and logged in our system. A member of our HR team will review your request and respond as soon as possible.</p>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 10px; margin: 20px 0;">
            <p style="margin: 0;"><strong>⚡ Urgent matters:</strong> Please call our office directly.</p>
        </div>
        
        <div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0;">
            <h4 style="color: #1976d2; margin-top: 0;">📝 Your Original Message</h4>
            <p style="margin: 5px 0; font-weight: bold; color: #1976d2;">Subject:</p>
            <p style="margin: 0 0 10px 0; font-style: italic;">{original_subject}</p>
            <p style="margin: 5px 0; font-weight: bold; color: #1976d2;">Message:</p>
            <p style="margin: 0; padding: 10px; background-color: white; border-radius: 3px; font-style: italic;">{original_content}</p>
        </div>
        
        <p>Best regards,<br>
        <strong>Argan Consultancy HR Team</strong></p>
    </div>
    
    <div style="background-color: #e9ecef; padding: 15px; font-size: 12px; color: #6c757d; text-align: center;">
        <p style="margin: 0;">This is an automated response. Please do not reply to this email directly.</p>
        <p style="margin: 5px 0 0 0;">For urgent matters, please contact our office.</p>
    </div>
</body>
</html>
"""
        
        return {
            "text": text_content,
            "html": html_content
        }
    
    async def process_incoming_email_and_reply(self, email_data: Dict) -> Dict[str, any]:
        """
        Process an incoming email and send an automatic reply
        
        Args:
            email_data: Dictionary containing email information
                - sender: sender email address
                - subject: email subject
                - body_text: email body text
                - body_html: email body HTML (optional)
                - message_id: unique message ID
                - recipients: list of recipients
                - cc: list of CC recipients (optional)
                - email_date: datetime of email
        
        Returns:
            Dictionary with processing results
        """
        try:
            sender_email = email_data.get('sender')
            original_subject = email_data.get('subject', 'No Subject')
            
            logger.info(f"Processing incoming email from {sender_email} with subject: {original_subject}")
            
            # Check if this is a reply to an existing ticket
            existing_ticket = self.extract_existing_ticket_number(original_subject)
            
            if existing_ticket:
                # This is a reply to an existing ticket
                logger.info(f"Found existing ticket number: {existing_ticket}")
                ticket_number = existing_ticket
                
                # Find existing thread
                thread = self.db.query(EmailThread).filter_by(ticket_number=ticket_number).first()
                if thread:
                    # Add message to existing thread
                    self._add_message_to_existing_thread(thread, email_data)
                else:
                    # Thread not found, create new one with the extracted ticket number
                    thread = self._create_new_thread(email_data, ticket_number)
            else:
                # This is a new query, generate new ticket number
                ticket_number = self.generate_ticket_number()
                logger.info(f"Generated new ticket number: {ticket_number}")
                
                # Create new thread
                thread = self._create_new_thread(email_data, ticket_number)
            
            # Send auto-reply
            reply_result = await self._send_auto_reply(
                sender_email=sender_email,
                original_subject=original_subject,
                ticket_number=ticket_number,
                original_body=email_data.get('body_text', '')
            )
            
            # Log the auto-reply as an outbound message
            if reply_result.get('success'):
                self._log_auto_reply_message(thread, reply_result, ticket_number)
            
            return {
                "success": True,
                "ticket_number": ticket_number,
                "thread_id": thread.id,
                "auto_reply_sent": reply_result.get('success', False),
                "message": f"Email processed successfully. Ticket: {ticket_number}"
            }
            
        except Exception as e:
            logger.error(f"Error processing incoming email: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process incoming email"
            }
    
    def _create_new_thread(self, email_data: Dict, ticket_number: str) -> EmailThread:
        """Create a new email thread"""
        thread = EmailThread(
            ticket_number=ticket_number,
            subject=email_data.get('subject', 'No Subject'),
            staff_email=email_data.get('sender'),
            staff_name=email_data.get('sender_name', email_data.get('sender')),
            query_type='general_inquiry',  # Default, can be updated by AI later
            status=ThreadStatus.OPEN.value,
            priority='normal',
            summary=f"New query from {email_data.get('sender')}"
        )
        
        self.db.add(thread)
        self.db.flush()  # Get the ID
        
        # Add the original message
        message = EmailMessage(
            thread_id=thread.id,
            message_id=email_data.get('message_id'),
            sender=email_data.get('sender'),
            recipients=email_data.get('recipients', []),
            cc=email_data.get('cc', []),
            subject=email_data.get('subject'),
            body_text=email_data.get('body_text'),
            body_html=email_data.get('body_html'),
            message_type=MessageType.INBOUND.value,
            direction='in',
            email_date=email_data.get('email_date', datetime.utcnow())
        )
        
        self.db.add(message)
        self.db.commit()
        
        logger.info(f"Created new thread {ticket_number}")
        return thread
    
    def _add_message_to_existing_thread(self, thread: EmailThread, email_data: Dict):
        """Add a message to an existing thread"""
        message = EmailMessage(
            thread_id=thread.id,
            message_id=email_data.get('message_id'),
            sender=email_data.get('sender'),
            recipients=email_data.get('recipients', []),
            cc=email_data.get('cc', []),
            subject=email_data.get('subject'),
            body_text=email_data.get('body_text'),
            body_html=email_data.get('body_html'),
            message_type=MessageType.INBOUND.value,
            direction='in',
            email_date=email_data.get('email_date', datetime.utcnow())
        )
        
        self.db.add(message)
        
        # Update thread
        thread.updated_at = datetime.utcnow()
        if thread.status == ThreadStatus.CLOSED.value:
            thread.status = ThreadStatus.OPEN.value
        
        self.db.commit()
        logger.info(f"Added message to existing thread {thread.ticket_number}")
    
    async def _send_auto_reply(self, sender_email: str, original_subject: str, ticket_number: str, original_body: str) -> Dict[str, any]:
        """Send the automatic reply email"""
        try:
            # Format subject
            reply_subject = self.format_reply_subject(original_subject, ticket_number)
            
            # Generate content
            content = self.generate_auto_reply_content(ticket_number, sender_email, original_subject, original_body)
            
            # Send email with CC to advice email
            result = await self.email_service.send_hr_response(
                to_email=sender_email,
                subject=reply_subject,
                content_text=content['text'],
                content_html=content['html'],
                ticket_number=ticket_number
            )
            
            # COMMENTED OUT FOR TESTING - Also send a copy to the advice email
            # if result.get('success'):
            #     await self.email_service.send_hr_response(
            #         to_email=self.advice_email,
            #         subject=f"Copy: {reply_subject}",
            #         content_text=f"This is a copy of the auto-reply sent to {sender_email}\n\n{content['text']}",
            #         content_html=f"<p><em>This is a copy of the auto-reply sent to {sender_email}</em></p>{content['html']}",
            #         ticket_number=ticket_number
            #     )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending auto-reply: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _log_auto_reply_message(self, thread: EmailThread, reply_result: Dict, ticket_number: str):
        """Log the auto-reply as an outbound message"""
        try:
            message = EmailMessage(
                thread_id=thread.id,
                message_id=f"auto-reply-{datetime.utcnow().timestamp()}",
                sender=self.email_service.from_email,
                recipients=[thread.staff_email],
                cc=[self.advice_email],
                subject=reply_result.get('subject', f"Auto-reply: {ticket_number}"),
                body_text="Auto-reply sent with ticket number",
                message_type=MessageType.OUTBOUND.value,
                direction='out',
                email_date=datetime.utcnow()
            )
            
            self.db.add(message)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging auto-reply message: {e}") 