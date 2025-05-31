"""
Initial Email Content Templates
Defines the structure and content for auto-reply emails to new queries
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class InitialEmailContent:
    def __init__(self):
        self.company_name = "Argan Consultancy HR Services"
        self.company_color = "#2c5aa0"
    
    def generate_auto_reply_content(self, ticket_number: str, original_sender: str, original_subject: str = "", original_body: str = "") -> Dict[str, str]:
        """
        Generate the content for the auto-reply email to new queries
        """
        # Clean up the original body for display
        original_content = original_body.strip() if original_body else "No message content"
        if len(original_content) > 500:
            original_content = original_content[:500] + "..."
        
        text_content = self._generate_text_content(ticket_number, original_subject, original_content)
        html_content = self._generate_html_content(ticket_number, original_subject, original_content)
        
        return {
            "text": text_content,
            "html": html_content
        }
    
    def _generate_text_content(self, ticket_number: str, original_subject: str, original_content: str) -> str:
        """Generate plain text version of the auto-reply"""
        return f"""Dear Colleague,

Thank you for contacting {self.company_name}.

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
    
    def _generate_html_content(self, ticket_number: str, original_subject: str, original_content: str) -> str:
        """Generate HTML version of the auto-reply"""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px;">
    <div style="background-color: {self.company_color}; color: white; padding: 20px; text-align: center;">
        <h2 style="margin: 0;">{self.company_name}</h2>
    </div>
    
    <div style="padding: 20px; background-color: #f8f9fa;">
        <p>Dear Colleague,</p>
        
        <p>Thank you for contacting {self.company_name}.</p>
        
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
    
    def format_reply_subject(self, original_subject: str, ticket_number: str) -> str:
        """
        Format the reply subject with ticket number for auto-replies
        """
        import re
        
        # Remove common reply prefixes
        subject = re.sub(r'^(Re:|RE:|Fwd:|FWD:)\s*', '', original_subject, flags=re.IGNORECASE).strip()
        
        # Check if ticket number already exists in subject
        if ticket_number.upper() in subject.upper():
            return f"Re: {subject}"
        
        # Add ticket number to subject
        return f"Re: [{ticket_number}] {subject}" 