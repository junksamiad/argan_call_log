"""
Initial Email Handler for HR Email Management System
Handles new email queries by generating tickets and sending auto-replies
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from backend.email_functions.assign_ticket import init_ticket_counter
from backend.email_functions.auto_reply import AutoReplySender
from .initial_email_content import InitialEmailContent
from backend.database import EmailThread, EmailMessage, TicketCounter, MessageType, ThreadStatus

logger = logging.getLogger(__name__)


class InitialEmailHandler:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.auto_reply_sender = AutoReplySender()
        self.content_generator = InitialEmailContent()
    
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
            logger.info(f"🎫 [TICKET GEN] Generated ticket number: {ticket_number}")
            return ticket_number
            
        except Exception as e:
            logger.error(f"Error generating ticket number: {e}")
            self.db.rollback()
            # Fallback to timestamp-based ticket
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            return f"ARG-{timestamp}"
    
    async def handle_new_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a new email query by creating a ticket and sending auto-reply
        
        Args:
            email_data: Email data from SendGrid
            
        Returns:
            Dict with processing results
        """
        try:
            sender_email = email_data.get('sender')
            original_subject = email_data.get('subject', 'No Subject')
            original_body = email_data.get('body_text', '')
            
            logger.info(f"📧 [INITIAL EMAIL] Processing new email from {sender_email}")
            
            # Generate new ticket number
            ticket_number = self.generate_ticket_number()
            logger.info(f"🎫 [INITIAL EMAIL] New ticket created: {ticket_number}")
            
            # Create new thread in database
            thread = self._create_new_thread(email_data, ticket_number)
            
            # Generate auto-reply content
            content = self.content_generator.generate_auto_reply_content(
                ticket_number=ticket_number,
                original_sender=sender_email,
                original_subject=original_subject,
                original_body=original_body
            )
            
            # Format subject with ticket number
            reply_subject = self.content_generator.format_reply_subject(original_subject, ticket_number)
            
            # Send auto-reply
            reply_result = await self.auto_reply_sender.send_auto_reply(
                to_email=sender_email,
                subject=reply_subject,
                content_text=content['text'],
                content_html=content['html'],
                ticket_number=ticket_number
            )
            
            # Log the auto-reply as an outbound message
            if reply_result.get('success'):
                self._log_auto_reply_message(thread, reply_result, ticket_number)
            
            return {
                "success": True,
                "ticket_number": ticket_number,
                "thread_id": thread.id,
                "auto_reply_sent": reply_result.get('success', False),
                "message": f"New email processed successfully. Ticket: {ticket_number}"
            }
            
        except Exception as e:
            logger.error(f"Error processing new email: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to process new email"
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
        
        logger.info(f"💾 [DATABASE] Created new thread: {ticket_number}")
        return thread
    
    def _log_auto_reply_message(self, thread: EmailThread, reply_result: Dict, ticket_number: str):
        """Log the auto-reply as an outbound message"""
        try:
            message = EmailMessage(
                thread_id=thread.id,
                message_id=f"auto-reply-{datetime.utcnow().timestamp()}",
                sender=self.auto_reply_sender.email_service.from_email,
                recipients=[thread.staff_email],
                cc=self.auto_reply_sender.get_default_cc_addresses(),
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