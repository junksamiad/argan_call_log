"""
Email Service for HR Email Management System
Handles sending emails through SendGrid API
"""

import os
import logging
from typing import Optional, List, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent, Attachment, FileContent, FileName, FileType, Disposition
from config.settings import settings

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = settings.sendgrid_api_key
        self.from_email = settings.email_address
        self.sg = SendGridAPIClient(api_key=self.api_key)
    
    async def send_hr_response(
        self,
        to_email: str,
        subject: str,
        content_text: str,
        content_html: Optional[str] = None,
        ticket_number: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send an HR response email
        
        Args:
            to_email: Recipient email address
            subject: Email subject (ticket number will be added if provided)
            content_text: Plain text content
            content_html: HTML content (optional)
            ticket_number: Ticket number to include in subject
            attachments: List of attachment dictionaries
            
        Returns:
            Dict with success status and details
        """
        try:
            # Format subject with ticket number
            if ticket_number and not f"[{ticket_number}]" in subject:
                formatted_subject = f"[{ticket_number}] {subject}"
            else:
                formatted_subject = subject
            
            # Create the email
            message = Mail(
                from_email=From(self.from_email, "Argan HR Consultancy"),
                to_emails=To(to_email),
                subject=Subject(formatted_subject),
                plain_text_content=PlainTextContent(content_text)
            )
            
            # Add HTML content if provided
            if content_html:
                message.content = [
                    PlainTextContent(content_text),
                    HtmlContent(content_html)
                ]
            
            # Add attachments if provided
            if attachments:
                for attachment_data in attachments:
                    attachment = Attachment(
                        FileContent(attachment_data.get('content')),
                        FileName(attachment_data.get('filename')),
                        FileType(attachment_data.get('type', 'application/octet-stream')),
                        Disposition('attachment')
                    )
                    message.attachment = attachment
            
            # Send the email
            logger.info(f"Sending email to {to_email} with subject: {formatted_subject}")
            response = self.sg.send(message)
            
            if response.status_code == 202:
                logger.info(f"Email sent successfully to {to_email}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "Email sent successfully",
                    "recipient": to_email,
                    "subject": formatted_subject
                }
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": f"Failed to send email. Status: {response.status_code}",
                    "error": response.body
                }
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return {
                "success": False,
                "message": f"Error sending email: {str(e)}",
                "error": str(e)
            }
    
    async def send_notification_email(
        self,
        to_email: str,
        notification_type: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send notification emails to HR staff
        
        Args:
            to_email: HR staff email
            notification_type: Type of notification (new_query, urgent_query, etc.)
            data: Data for the notification
            
        Returns:
            Dict with success status and details
        """
        try:
            # Generate notification content based on type
            if notification_type == "new_query":
                subject = f"New HR Query - {data.get('ticket_number', 'Unknown')}"
                content = self._generate_new_query_notification(data)
            elif notification_type == "urgent_query":
                subject = f"🚨 URGENT HR Query - {data.get('ticket_number', 'Unknown')}"
                content = self._generate_urgent_query_notification(data)
            else:
                subject = f"HR System Notification - {data.get('ticket_number', 'Unknown')}"
                content = self._generate_generic_notification(data)
            
            return await self.send_hr_response(
                to_email=to_email,
                subject=subject,
                content_text=content["text"],
                content_html=content["html"]
            )
            
        except Exception as e:
            logger.error(f"Error sending notification to {to_email}: {e}")
            return {
                "success": False,
                "message": f"Error sending notification: {str(e)}",
                "error": str(e)
            }
    
    def _generate_new_query_notification(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate content for new query notification"""
        ticket_number = data.get('ticket_number', 'Unknown')
        sender = data.get('sender', 'Unknown')
        subject = data.get('subject', 'No Subject')
        query_type = data.get('query_type', 'general_inquiry')
        urgency = data.get('urgency_level', 3)
        summary = data.get('summary', 'No summary available')
        
        text_content = f"""
New HR Query Received

Ticket Number: {ticket_number}
From: {sender}
Subject: {subject}
Query Type: {query_type.replace('_', ' ').title()}
Urgency Level: {urgency}/5

Summary:
{summary}

Please review and respond through the HR dashboard.

Best regards,
Argan HR System
        """
        
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c5aa0;">📧 New HR Query Received</h2>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Ticket Number:</strong> {ticket_number}</p>
        <p><strong>From:</strong> {sender}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Query Type:</strong> {query_type.replace('_', ' ').title()}</p>
        <p><strong>Urgency Level:</strong> {urgency}/5</p>
    </div>
    
    <h3>Summary:</h3>
    <p style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107;">
        {summary}
    </p>
    
    <p style="margin-top: 30px;">
        Please review and respond through the HR dashboard.
    </p>
    
    <p>
        Best regards,<br>
        <strong>Argan HR System</strong>
    </p>
</body>
</html>
        """
        
        return {"text": text_content.strip(), "html": html_content}
    
    def _generate_urgent_query_notification(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate content for urgent query notification"""
        ticket_number = data.get('ticket_number', 'Unknown')
        sender = data.get('sender', 'Unknown')
        subject = data.get('subject', 'No Subject')
        summary = data.get('summary', 'No summary available')
        
        text_content = f"""
🚨 URGENT HR Query Requires Immediate Attention

Ticket Number: {ticket_number}
From: {sender}
Subject: {subject}

This query has been flagged as urgent and requires immediate attention.

Summary:
{summary}

Please respond as soon as possible.

Best regards,
Argan HR System
        """
        
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
        <h2 style="margin: 0; color: white;">🚨 URGENT HR Query</h2>
        <p style="margin: 5px 0 0 0; color: white;">Requires Immediate Attention</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p><strong>Ticket Number:</strong> {ticket_number}</p>
        <p><strong>From:</strong> {sender}</p>
        <p><strong>Subject:</strong> {subject}</p>
    </div>
    
    <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
        <p><strong>This query has been flagged as urgent and requires immediate attention.</strong></p>
    </div>
    
    <h3>Summary:</h3>
    <p style="background-color: #f8d7da; padding: 10px; border-left: 4px solid #dc3545;">
        {summary}
    </p>
    
    <p style="margin-top: 30px; font-weight: bold; color: #dc3545;">
        Please respond as soon as possible.
    </p>
    
    <p>
        Best regards,<br>
        <strong>Argan HR System</strong>
    </p>
</body>
</html>
        """
        
        return {"text": text_content.strip(), "html": html_content}
    
    def _generate_generic_notification(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate content for generic notification"""
        ticket_number = data.get('ticket_number', 'Unknown')
        message = data.get('message', 'No message provided')
        
        text_content = f"""
HR System Notification

Ticket Number: {ticket_number}

{message}

Best regards,
Argan HR System
        """
        
        html_content = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #2c5aa0;">📢 HR System Notification</h2>
    
    <p><strong>Ticket Number:</strong> {ticket_number}</p>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
        {message}
    </div>
    
    <p>
        Best regards,<br>
        <strong>Argan HR System</strong>
    </p>
</body>
</html>
        """
        
        return {"text": text_content.strip(), "html": html_content}
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test SendGrid connection and permissions"""
        try:
            # Try to get user information (basic API test)
            response = self.sg.client.user.get()
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "SendGrid connection successful",
                    "status_code": response.status_code
                }
            else:
                return {
                    "success": False,
                    "message": f"SendGrid connection failed with status {response.status_code}",
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"SendGrid connection error: {str(e)}",
                "error": str(e)
            } 