"""
Auto-reply template system for HR Email Management System - Backend2
Generates professional acknowledgment emails with ticket numbers and personalized content
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AutoReplyTemplateGenerator:
    """
    Generates auto-reply email templates for new HR inquiries
    
    Based on the email format requirements:
    - Personalized greeting using sender name
    - Ticket number in subject and body
    - Original query included for reference
    - Professional formatting with priority information
    - Response timeframe details
    """
    
    def __init__(self):
        """Initialize template generator"""
        self.company_name = "Argan HR Consultancy"
        self.team_name = "Argan HR Consultancy Team"
        
    def generate_auto_reply_content(
        self,
        sender_first_name: str,
        original_subject: str,
        original_query: str,
        ticket_number: str,
        priority: str = "Normal"
    ) -> Dict[str, str]:
        """
        Generate auto-reply email content (both text and HTML)
        
        Args:
            sender_first_name: First name of the person who sent the original email
            original_subject: Subject line of the original email
            original_query: Body content of the original email
            ticket_number: Generated ticket number (e.g., ARG-20250603-7955)
            priority: Priority level (Normal, High, Urgent)
            
        Returns:
            Dictionary with 'subject', 'text_body', and 'html_body' keys
        """
        try:
            logger.info(f"📝 [TEMPLATE] Generating auto-reply for {sender_first_name}, ticket {ticket_number}")
            
            # Generate subject line with ticket number prefix
            subject = f"[{ticket_number}] {self.company_name} - Call Logged"
            
            # Generate personalized greeting using first name
            greeting = self._generate_greeting(sender_first_name)
            
            # Generate response timeframe based on priority
            response_timeframe = self._get_response_timeframe(priority)
            
            # Build text body
            text_body = f"""{greeting},

Thank you for contacting {self.company_name}. We have received your enquiry and assigned it ticket number {ticket_number}.

┌─────────────────────────────────────────────────────────────────┐
│ Original Subject: {original_subject:<45} │
│ Priority: {priority:<53} │
│ Ticket Number: {ticket_number:<47} │
└─────────────────────────────────────────────────────────────────┘

We will review your request and respond within our standard timeframe:

• Urgent matters: Within 4 hours
• High priority: Within 24 hours  
• Normal requests: Within 2-3 business days

If you need to follow up on this matter, please reference ticket number {ticket_number} in your subject line.

Original Enquiry (for reference):

{self._format_original_query(original_query)}

Thank you for your patience.

Best regards,
{self.team_name}

---
This is an automated response. Please do not reply to this email.
"""

            # Generate HTML content with professional styling
            html_body = self._generate_html_content(
                greeting, 
                original_subject, 
                original_query, 
                ticket_number, 
                priority
            )

            logger.info(f"✅ [TEMPLATE] Auto-reply content generated successfully")
            logger.info(f"📝 [TEMPLATE] Subject: {subject}")
            logger.info(f"📝 [TEMPLATE] Greeting: {greeting}")
            logger.info(f"📝 [TEMPLATE] Priority: {priority}")
            logger.info(f"📝 [TEMPLATE] HTML content: {len(html_body)} characters")
            
            return {
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body
            }
            
        except Exception as e:
            logger.error(f"❌ [TEMPLATE] Error generating auto-reply content: {e}")
            # Return fallback template
            return self._generate_fallback_template(ticket_number, original_subject)
    
    def _generate_greeting(self, sender_first_name: str) -> str:
        """
        Generate personalized greeting using first name only
        
        Args:
            sender_first_name: First name extracted from email or fallback
            
        Returns:
            Formatted greeting string
        """
        try:
            if not sender_first_name or sender_first_name.strip() == "":
                return "Hello"
            
            # Clean the first name
            clean_name = sender_first_name.strip()
            
            # Handle email address fallback case
            if "@" in clean_name:
                clean_name = clean_name.split("@")[0]
            
            # Capitalize properly
            if clean_name.lower() in ["unknown", "user", "customer"]:
                return "Hello"
            
            # Format name properly (use first name only for more personal greeting)
            formatted_name = clean_name.title() if clean_name.islower() else clean_name
            
            return f"Hi {formatted_name}"
            
        except Exception as e:
            logger.warning(f"⚠️ [TEMPLATE] Error generating greeting for '{sender_first_name}': {e}")
            return "Hello"
    
    def _get_response_timeframe(self, priority: str) -> str:
        """
        Get response timeframe text based on priority
        
        Args:
            priority: Priority level string
            
        Returns:
            Response timeframe description
        """
        priority_map = {
            "urgent": "within 4 hours",
            "high": "within 24 hours", 
            "normal": "within 2-3 business days"
        }
        
        return priority_map.get(priority.lower(), "within 2-3 business days")
    
    def _format_original_query(self, original_query: str) -> str:
        """
        Format the original query for inclusion in auto-reply
        
        Args:
            original_query: Original email body content
            
        Returns:
            Formatted query text with proper indentation
        """
        try:
            if not original_query or original_query.strip() == "":
                return "    [No content provided]"
            
            # Clean up the query text
            clean_query = original_query.strip()
            
            # No length limit - include full original query for customer reference
            
            # Add indentation to each line for better formatting
            lines = clean_query.split('\n')
            indented_lines = ["    " + line for line in lines]
            
            return '\n'.join(indented_lines)
            
        except Exception as e:
            logger.warning(f"⚠️ [TEMPLATE] Error formatting original query: {e}")
            return "    [Error formatting original message]"
    
    def _format_original_query_html(self, original_query: str) -> str:
        """
        Format the original query for inclusion in HTML auto-reply with proper escaping
        
        Args:
            original_query: Original email body content
            
        Returns:
            HTML-safe formatted query text with line breaks converted to <br> tags
        """
        try:
            if not original_query or original_query.strip() == "":
                return "[No content provided]"
            
            # Clean up the query text
            clean_query = original_query.strip()
            
            # HTML escape special characters first
            import html
            escaped_query = html.escape(clean_query)
            
            # Convert line breaks to HTML <br> tags for better email client compatibility
            html_formatted = escaped_query.replace('\n', '<br>')
            
            return html_formatted
            
        except Exception as e:
            logger.warning(f"⚠️ [TEMPLATE] Error formatting HTML original query: {e}")
            return "[Error formatting original message]"
    
    def _generate_fallback_template(self, ticket_number: str, original_subject: str) -> Dict[str, str]:
        """
        Generate fallback template in case of errors
        
        Args:
            ticket_number: Ticket number
            original_subject: Original email subject
            
        Returns:
            Dictionary with basic subject, text_body, and html_body
        """
        logger.warning(f"⚠️ [TEMPLATE] Using fallback template for ticket {ticket_number}")
        
        subject = f"[{ticket_number}] {self.company_name} - Call Logged"
        
        text_body = f"""Hello,

Thank you for contacting {self.company_name}. We have received your enquiry and assigned it ticket number {ticket_number}.

We will review your request and respond within 2-3 business days.

If you need to follow up on this matter, please reference ticket number {ticket_number} in your subject line.

Thank you for your patience.

Best regards,
{self.team_name}

---
This is an automated response. Please do not reply to this email.
"""

        html_body = f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c5aa0;">{self.company_name} - Auto Reply</h2>
    
    <p>Hello,</p>
    
    <p>Thank you for contacting {self.company_name}. We have received your enquiry and assigned it ticket number <strong>{ticket_number}</strong>.</p>
    
    <p>We will review your request and respond within 2-3 business days.</p>
    
    <p><em>If you need to follow up on this matter, please reference ticket number {ticket_number} in your subject line.</em></p>
    
    <p>Thank you for your patience.</p>
    
    <p>Best regards,<br>
    <strong>{self.team_name}</strong></p>
    
    <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">This is an automated response. Please do not reply to this email.</p>
</body>
</html>"""
        
        return {
            "subject": subject,
            "text_body": text_body,
            "html_body": html_body
        }

    def _generate_html_content(
        self,
        greeting: str,
        original_subject: str,
        original_query: str,
        ticket_number: str,
        priority: str
    ) -> str:
        """
        Generate HTML content for the auto-reply email with professional styling
        Matches the original backend's design with colors and formatting
        
        Args:
            greeting: Personalized greeting
            original_subject: Original email subject
            original_query: Original email body content
            ticket_number: Generated ticket number
            priority: Priority level
            
        Returns:
            HTML formatted content
        """
        try:
            # Generate priority color based on priority level
            priority_color = "#28a745"  # Green for Normal
            if priority.lower() == "high":
                priority_color = "#ffc107"  # Amber for High
            elif priority.lower() == "urgent":
                priority_color = "#dc3545"  # Red for Urgent
            
            # Generate HTML content with professional styling matching original backend
            html_content = f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c5aa0;">{self.company_name} - Auto Reply</h2>
    
    <p>{greeting}</p>
    
    <p>Thank you for contacting {self.company_name}. We have received your enquiry and assigned it ticket number <strong>{ticket_number}</strong>.</p>
    
    <div style="background-color: #f0f7ff; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
        <p><strong>Original Subject:</strong> {original_subject}</p>
        <p><strong>Priority:</strong> <span style="color: {priority_color};">{priority}</span></p>
        <p><strong>Ticket Number:</strong> {ticket_number}</p>
    </div>
    
    <p>We will review your request and respond within our standard timeframe:</p>
    
    <ul>
        <li><strong>Urgent matters:</strong> Within 4 hours</li>
        <li><strong>High priority:</strong> Within 24 hours</li>
        <li><strong>Normal requests:</strong> Within 2-3 business days</li>
    </ul>
    
    <p><em>If you need to follow up on this matter, please reference ticket number {ticket_number} in your subject line.</em></p>
    
    <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px;">
        <h4 style="color: #495057; margin-top: 0;">Original Enquiry (for reference):</h4>
        <div style="font-family: 'Courier New', monospace; font-size: 12px; background-color: #ffffff; padding: 10px; border-radius: 3px; line-height: 1.4;">{self._format_original_query_html(original_query)}</div>
    </div>
    
    <p>Thank you for your patience.</p>
    
    <p>Best regards,<br>
    <strong>{self.team_name}</strong></p>
    
    <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
    <p style="font-size: 12px; color: #666;">This is an automated response. Please do not reply to this email.</p>
</body>
</html>"""

            return html_content
            
        except Exception as e:
            logger.error(f"❌ [TEMPLATE] Error generating HTML content: {e}")
            return "<p>Error generating HTML content</p>"


def extract_sender_info_from_db_record(
    initial_conversation_query: str, 
    sender_first_name: str = "", 
    sender_last_name: str = ""
) -> Dict[str, str]:
    """
    Extract sender information from the database record's initial_conversation_query field
    
    Args:
        initial_conversation_query: JSON string from database containing sender info
        sender_first_name: First name from database sender_first_name field
        sender_last_name: Last name from database sender_last_name field
        
    Returns:
        Dictionary with sender_name, sender_first_name, sender_email, original_subject, and original_content
    """
    try:
        logger.info("📋 [TEMPLATE] Extracting sender info from database record...")
        
        # Parse the JSON string
        conversation_data = json.loads(initial_conversation_query)
        
        # Extract required fields with fallbacks
        sender_name = conversation_data.get("sender_name", "")
        sender_email = conversation_data.get("sender_email", "unknown@unknown.com")
        sender_email_content = conversation_data.get("sender_email_content", "")
        sender_email_date = conversation_data.get("sender_email_date", "")
        
        # Use database fields for first/last name with JSON fallback
        first_name = sender_first_name.strip() if sender_first_name else ""
        last_name = sender_last_name.strip() if sender_last_name else ""
        
        # If database fields are empty, try to extract from sender_name
        if not first_name and sender_name:
            name_parts = sender_name.strip().split()
            if len(name_parts) >= 1:
                first_name = name_parts[0]
            if len(name_parts) >= 2:
                last_name = " ".join(name_parts[1:])
        
        logger.info(f"✅ [TEMPLATE] Extracted sender info:")
        logger.info(f"📧 [TEMPLATE] Full Name: '{sender_name}'")
        logger.info(f"📧 [TEMPLATE] First Name: '{first_name}'")
        logger.info(f"📧 [TEMPLATE] Last Name: '{last_name}'")
        logger.info(f"📧 [TEMPLATE] Email: {sender_email}")
        logger.info(f"📧 [TEMPLATE] Content length: {len(sender_email_content)} chars")
        
        return {
            "sender_name": sender_name,
            "sender_first_name": first_name,
            "sender_last_name": last_name,
            "sender_email": sender_email,
            "original_content": sender_email_content,
            "original_date": sender_email_date
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ [TEMPLATE] JSON decode error in initial_conversation_query: {e}")
        return {
            "sender_name": "",
            "sender_first_name": "",
            "sender_last_name": "",
            "sender_email": "unknown@unknown.com", 
            "original_content": "",
            "original_date": ""
        }
    except Exception as e:
        logger.error(f"❌ [TEMPLATE] Error extracting sender info: {e}")
        return {
            "sender_name": "",
            "sender_first_name": "",
            "sender_last_name": "",
            "sender_email": "unknown@unknown.com",
            "original_content": "", 
            "original_date": ""
        }


# Initialize global template generator
template_generator = AutoReplyTemplateGenerator() 