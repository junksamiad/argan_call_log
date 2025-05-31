"""
Email Service for HR Email Management System
Handles sending emails through SendGrid API
"""

import os
import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent, Attachment, FileContent, FileName, FileType, Disposition

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("EMAIL_ADDRESS", "support@email.adaptixinnovation.co.uk")
        
        # Initialize SendGrid client
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
        Send an HR response email using direct HTTP request to SendGrid API
        """
        try:
            # Validate and clean email address
            to_email = to_email.strip()
            if not to_email or '@' not in to_email:
                raise ValueError(f"Invalid email address: {to_email}")
            
            # Clean and validate subject
            subject = subject.strip()
            if not subject:
                subject = "HR System Response"
            
            # Format subject with ticket number
            if ticket_number and not f"[{ticket_number}]" in subject:
                formatted_subject = f"[{ticket_number}] {subject}"
            else:
                formatted_subject = subject
            
            # Clean content
            content_text = content_text.strip()
            if content_html:
                content_html = content_html.strip()
            
            # Build email payload
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": to_email}]
                    }
                ],
                "from": {
                    "email": self.from_email,
                    "name": "Argan HR Consultancy"
                },
                "reply_to": {
                    "email": self.from_email,
                    "name": "Argan HR Consultancy"
                },
                "subject": formatted_subject,
                "content": [
                    {
                        "type": "text/plain",
                        "value": content_text.encode('utf-8').decode('utf-8')
                    }
                ]
            }
            
            # Add HTML content if provided
            if content_html:
                payload["content"].append({
                    "type": "text/html",
                    "value": content_html.encode('utf-8').decode('utf-8')
                })
            
            # Debug: Log the payload (without API key)
            logger.info(f"📤 [EMAIL SERVICE] Email payload - To: {to_email}, From: {self.from_email}, Subject: {formatted_subject}")
            
            # Send via HTTP request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json; charset=utf-8"
            }
            
            logger.info(f"📤 [EMAIL SERVICE] Sending email to: {to_email}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
            
            if response.status_code == 202:
                logger.info(f"✅ [EMAIL SERVICE] Email sent successfully to: {to_email}")
                logger.info(f"📧 [EMAIL SERVICE] Subject: {formatted_subject}")
                logger.info(f"📧 [EMAIL SERVICE] From: {self.from_email}")
                logger.info(f"📧 [EMAIL SERVICE] Response headers: {dict(response.headers)}")
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "message": "Email sent successfully",
                    "recipient": to_email,
                    "subject": formatted_subject,
                    "from_email": self.from_email,
                    "response_headers": dict(response.headers)
                }
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}, Body: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": f"Failed to send email. Status: {response.status_code}",
                    "error": response.text
                }
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return {
                "success": False,
                "message": f"Error sending email: {str(e)}",
                "error": str(e)
            }
    
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