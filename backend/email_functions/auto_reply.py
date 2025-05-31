"""
Auto Reply Email Sender
Handles sending auto-reply emails with CC support and tracking
"""

import logging
from typing import Dict, List, Optional, Any
from .email_service import EmailService

logger = logging.getLogger(__name__)


class AutoReplySender:
    def __init__(self):
        self.email_service = EmailService()
        self.default_cc_addresses = ["advice@arganconsultancy.co.uk"]  # Default CC recipients
    
    async def send_auto_reply(
        self,
        to_email: str,
        subject: str,
        content_text: str,
        content_html: str,
        ticket_number: str,
        cc_addresses: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send an auto-reply email with optional CC recipients
        
        Args:
            to_email: Primary recipient
            subject: Email subject (will be formatted with ticket number)
            content_text: Plain text content
            content_html: HTML content
            ticket_number: Ticket number for tracking
            cc_addresses: Optional list of CC email addresses
            
        Returns:
            Dict with success status and details
        """
        try:
            # Use provided CC addresses or default ones
            cc_list = cc_addresses or self.default_cc_addresses
            
            # Send the main email
            result = await self.email_service.send_hr_response(
                to_email=to_email,
                subject=subject,
                content_text=content_text,
                content_html=content_html,
                ticket_number=ticket_number
            )
            
            # If main email succeeded and we have CC addresses, send copies
            if result.get('success') and cc_list:
                for cc_email in cc_list:
                    try:
                        cc_subject = f"Copy: {subject}"
                        cc_text = f"This is a copy of the auto-reply sent to {to_email}\n\n{content_text}"
                        cc_html = f"<p><em>This is a copy of the auto-reply sent to {to_email}</em></p>{content_html}"
                        
                        await self.email_service.send_hr_response(
                            to_email=cc_email,
                            subject=cc_subject,
                            content_text=cc_text,
                            content_html=cc_html,
                            ticket_number=ticket_number
                        )
                        logger.info(f"📋 [AUTO REPLY] CC copy sent to: {cc_email} (Ticket: {ticket_number})")
                    except Exception as e:
                        logger.warning(f"Failed to send CC copy to {cc_email}: {e}")
                        # Don't fail the main operation if CC fails
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending auto-reply: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to send auto-reply: {str(e)}"
            }
    
    def add_default_cc(self, email: str):
        """Add an email to the default CC list"""
        if email not in self.default_cc_addresses:
            self.default_cc_addresses.append(email)
    
    def remove_default_cc(self, email: str):
        """Remove an email from the default CC list"""
        if email in self.default_cc_addresses:
            self.default_cc_addresses.remove(email)
    
    def get_default_cc_addresses(self) -> List[str]:
        """Get the current default CC addresses"""
        return self.default_cc_addresses.copy() 