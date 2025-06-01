"""
Auto Reply Email Sender
Handles sending auto-reply emails with CC support and tracking
"""

import logging
from typing import Dict, List, Optional, Any
from .email_service import EmailService
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoReplySender:
    def __init__(self):
        self.email_service = EmailService()
        # TEMPORARILY DISABLED FOR TESTING - Comment out CC functionality
        # self.default_cc_addresses = ["advice@arganconsultancy.co.uk"]  # Default CC recipients
        self.default_cc_addresses = []  # Disabled during testing
    
    async def send_auto_reply(
        self,
        to_email: str,
        subject: str,
        content_text: str,
        content_html: str,
        ticket_number: str,
        cc_addresses: Optional[List[str]] = None,
        delay_seconds: float = 0.5
    ) -> Dict[str, Any]:
        """
        Send an auto-reply email with optional CC recipients and connection delay
        
        Args:
            to_email: Primary recipient
            subject: Email subject (will be formatted with ticket number)
            content_text: Plain text content
            content_html: HTML content
            ticket_number: Ticket number for tracking
            cc_addresses: Optional list of CC email addresses
            delay_seconds: Delay before sending to prevent connection conflicts
            
        Returns:
            Dict with success status and details
        """
        try:
            # Add small delay to prevent connection conflicts
            if delay_seconds > 0:
                logger.info(f"📤 [AUTO REPLY] Waiting {delay_seconds}s before sending to {to_email}")
                await asyncio.sleep(delay_seconds)
                
            # TEMPORARILY DISABLED FOR TESTING - Comment out CC functionality
            # Use provided CC addresses or default ones
            # cc_list = cc_addresses or self.default_cc_addresses
            cc_list = []  # Disabled during testing
            
            # Send the main email
            result = await self.email_service.send_hr_response(
                to_email=to_email,
                subject=subject,
                content_text=content_text,
                content_html=content_html,
                ticket_number=ticket_number
            )
            
            # Log detailed results
            if not result.get('success'):
                logger.error(f"Email service returned failure for {to_email}")
                logger.error(f"Failure details: {result}")
            
            # TEMPORARILY DISABLED FOR TESTING - Comment out CC sending
            logger.info(f"📧 [AUTO REPLY] CC functionality temporarily disabled for testing")
            
            return result
            
        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
            logger.error(f"Error sending auto-reply: {error_msg}")
            logger.error(f"Exception details - Type: {type(e).__name__}, Args: {e.args}")
            
            return {
                "success": False,
                "error": error_msg,
                "message": f"Failed to send auto-reply: {error_msg}",
                "exception_type": type(e).__name__
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


# Standalone function for easy import
_auto_reply_sender = None

async def send_auto_reply(recipient, ticket_number, original_subject, sender_name="", 
                         priority="Normal", ai_summary=None, original_email_body=None):
    """
    Send auto-reply email with ticket confirmation
    
    Args:
        recipient: Email address to send reply to
        ticket_number: Generated ticket number
        original_subject: Subject of original email
        sender_name: Name of the sender (if available)
        priority: Priority level (Normal, High, Urgent)
        ai_summary: AI-generated summary (optional)
        original_email_body: Original email content for human review (optional)
    """
    try:
        logger.info(f"📤 [AUTO REPLY] Preparing auto-reply for {recipient}")
        
        # Use sender name if available, otherwise fall back to email address
        display_name = sender_name.strip() if sender_name and sender_name.strip() else recipient.split('@')[0]
        
        # Ensure proper greeting format - using "Hi" for a more casual, friendly tone
        greeting = f"Hi {display_name},"
        
        # Build email content
        text_content = f"""{greeting}

Thank you for contacting Argan Consultancy HR. We have received your enquiry and assigned it ticket number {ticket_number}.

Original Subject: {original_subject}
Priority: {priority}
Ticket Number: {ticket_number}

We will review your request and respond within our standard timeframe:

• Urgent matters: Within 4 hours
• High priority: Within 24 hours  
• Normal requests: Within 2-3 business days

If you need to follow up on this matter, please reference ticket number {ticket_number} in your subject line.

Thank you for your patience.

Best regards,
Argan Consultancy HR Team"""

        # Add original email body for human review if provided
        if original_email_body and original_email_body.strip():
            text_content += f"""

------- ORIGINAL ENQUIRY -------
{original_email_body.strip()}
--------------------------------"""

        # HTML version with better formatting
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2c5aa0;">Argan Consultancy HR - Auto Reply</h2>
            
            <p>{greeting}</p>
            
            <p>Thank you for contacting Argan Consultancy HR. We have received your enquiry and assigned it ticket number <strong>{ticket_number}</strong>.</p>
            
            <div style="background-color: #f0f7ff; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
                <p><strong>Original Subject:</strong> {original_subject}</p>
                <p><strong>Priority:</strong> <span style="color: #28a745;">{priority}</span></p>
                <p><strong>Ticket Number:</strong> {ticket_number}</p>
            </div>
            
            <p>We will review your request and respond within our standard timeframe:</p>
            
            <ul>
                <li><strong>Urgent matters:</strong> Within 4 hours</li>
                <li><strong>High priority:</strong> Within 24 hours</li>
                <li><strong>Normal requests:</strong> Within 2-3 business days</li>
            </ul>
            
            <p><em>If you need to follow up on this matter, please reference ticket number {ticket_number} in your subject line.</em></p>"""

        # Add original email content for human review if provided
        if original_email_body and original_email_body.strip():
            html_content += f"""
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;">
                <h4 style="color: #495057; margin-top: 0;">Original Enquiry (for reference):</h4>
                <div style="font-family: 'Courier New', monospace; font-size: 12px; background-color: #ffffff; padding: 10px; border-radius: 3px; white-space: pre-wrap;">{original_email_body.strip()}</div>
            </div>"""

        html_content += """
            <p>Thank you for your patience.</p>
            
            <p>Best regards,<br>
            <strong>Argan Consultancy HR Team</strong></p>
        </body>
        </html>
        """
        
        global _auto_reply_sender
        
        if _auto_reply_sender is None:
            _auto_reply_sender = AutoReplySender()
        
        # Send the auto-reply
        return await _auto_reply_sender.send_auto_reply(
            to_email=recipient,
            subject=f"[{ticket_number}] Thank you for contacting Argan Consultancy HR",
            content_text=text_content,
            content_html=html_content,
            ticket_number=ticket_number
        )
        
    except Exception as e:
        logger.error(f"❌ [AUTO REPLY] Error in standalone function: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to send auto-reply: {str(e)}"
        } 