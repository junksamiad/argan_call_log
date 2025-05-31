"""
Email Router for HR Email Management System
Routes incoming emails to appropriate handlers based on ticket number existence
"""

import logging
import re
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

from .initial_email.initial_email import InitialEmailHandler
from .existing_email.existing_email import ExistingEmailHandler

logger = logging.getLogger(__name__)


class EmailRouter:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.initial_email_handler = InitialEmailHandler(db_session)
        self.existing_email_handler = ExistingEmailHandler(db_session)
    
    def extract_ticket_number(self, subject: str) -> Optional[str]:
        """
        Extract ticket number from email subject line
        Looks for patterns like [ARG-YYYYMMDD-XXXX] or ARG-YYYYMMDD-XXXX
        """
        if not subject:
            return None
            
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
    
    async def route_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an incoming email to the appropriate handler
        
        Args:
            email_data: Email data from SendGrid
            
        Returns:
            Dict with processing results
        """
        try:
            subject = email_data.get('subject', '')
            sender = email_data.get('sender')
            
            logger.info(f"📬 [EMAIL ROUTER] Routing email from {sender} with subject: {subject}")
            
            # Check if this is a reply to an existing ticket
            ticket_number = self.extract_ticket_number(subject)
            
            if ticket_number:
                # Route to existing email handler
                logger.info(f"🔄 [EMAIL ROUTER] → Existing ticket handler for: {ticket_number}")
                return await self.existing_email_handler.handle_reply_email(email_data, ticket_number)
            else:
                # Route to initial email handler (new ticket)
                logger.info(f"🆕 [EMAIL ROUTER] → Initial email handler (new ticket)")
                return await self.initial_email_handler.handle_new_email(email_data)
                
        except Exception as e:
            logger.error(f"Error routing email: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to route email"
            } 