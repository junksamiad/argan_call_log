"""
Email service module for HR Email Management System - Backend2
Handles sending auto-reply emails using SendGrid API with retry logic
"""

import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending auto-reply emails via SendGrid API
    
    Features:
    - SendGrid API integration
    - Retry logic with exponential backoff
    - Auto-reply template support
    - CC functionality
    - Error handling and logging
    """
    
    def __init__(self):
        """Initialize email service with SendGrid configuration"""
        self.api_key = os.getenv("SENDGRID_API_KEY", "")
        self.from_email = os.getenv("FROM_EMAIL", "email@email.adaptixinnovation.co.uk")
        
        # Retry configuration
        self.max_retries = 3
        self.base_delay = 2  # Base delay for exponential backoff
        self.initial_delay = 0.5  # Initial delay to prevent connection conflicts
        
        if not self.api_key:
            logger.error("❌ [EMAIL SERVICE] SENDGRID_API_KEY not found in environment variables")
            
        if not self.from_email:
            logger.error("❌ [EMAIL SERVICE] FROM_EMAIL not found in environment variables")
        
        logger.info(f"📧 [EMAIL SERVICE] Initialized with from_email: {self.from_email}")
        
        # Configure HTTPX client with timeout settings
        self.client_config = {
            "timeout": httpx.Timeout(
                connect=10.0,  # Connection timeout
                read=30.0,     # Read timeout
                write=10.0,    # Write timeout
                pool=5.0       # Pool timeout
            ),
            "limits": httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5
            )
        }
    
    async def send_auto_reply(
        self,
        to_email: str,
        subject: str,
        content_text: str,
        ticket_number: str,
        cc_addresses: Optional[List[str]] = None,
        delay_seconds: float = 0.5,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Send auto-reply email with retry logic
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            content_text: Email body content (plain text)
            ticket_number: Ticket number for subject prefix
            cc_addresses: List of CC email addresses
            delay_seconds: Initial delay before sending (prevents connection conflicts)
            max_retries: Maximum number of retry attempts
            
        Returns:
            Dictionary with success status and details
        """
        
        # Add initial delay to prevent connection conflicts
        if delay_seconds > 0:
            logger.info(f"📤 [AUTO REPLY] Waiting {delay_seconds}s before sending to {to_email}")
            await asyncio.sleep(delay_seconds)
        
        logger.info(f"📤 [AUTO REPLY] Starting auto-reply send to {to_email}")
        logger.info(f"🎫 [AUTO REPLY] Ticket: {ticket_number}")
        
        for attempt in range(max_retries + 1):
            try:
                # Validate and clean email address
                to_email_clean = to_email.strip()
                if not to_email_clean or '@' not in to_email_clean:
                    raise ValueError(f"Invalid email address: {to_email}")
                
                # Format subject with ticket number prefix
                formatted_subject = f"[{ticket_number}] {subject}"
                
                # Build email payload for SendGrid API
                personalization = {
                    "to": [{"email": to_email_clean}]
                }
                
                # Add CC addresses if provided
                if cc_addresses:
                    cc_list = [{"email": cc_email.strip()} for cc_email in cc_addresses if cc_email.strip()]
                    if cc_list:
                        personalization["cc"] = cc_list
                        logger.info(f"📧 [AUTO REPLY] Adding CC recipients: {[cc['email'] for cc in cc_list]}")
                
                payload = {
                    "personalizations": [personalization],
                    "from": {
                        "email": self.from_email,
                        "name": "Argan HR Consultancy"
                    },
                    "reply_to": {
                        "email": to_email_clean,  # Reply-to goes back to original sender
                        "name": "Original Sender"
                    },
                    "subject": formatted_subject,
                    "content": [
                        {
                            "type": "text/plain",
                            "value": content_text.encode('utf-8').decode('utf-8')
                        }
                    ]
                }
                
                # Log attempt details
                if attempt > 0:
                    logger.info(f"🔄 [AUTO REPLY] Retry attempt {attempt + 1} for {to_email_clean}")
                else:
                    logger.info(f"📤 [AUTO REPLY] Sending to: {to_email_clean}")
                    logger.info(f"📤 [AUTO REPLY] Subject: {formatted_subject}")
                    logger.info(f"📤 [AUTO REPLY] From: {self.from_email}")
                
                # Send via SendGrid API
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json; charset=utf-8"
                }
                
                async with httpx.AsyncClient(**self.client_config) as client:
                    response = await client.post(
                        "https://api.sendgrid.com/v3/mail/send",
                        headers=headers,
                        json=payload
                    )
                
                if response.status_code == 202:
                    logger.info(f"✅ [AUTO REPLY] Email sent successfully to: {to_email_clean}")
                    logger.info(f"📧 [AUTO REPLY] Subject: {formatted_subject}")
                    logger.info(f"📧 [AUTO REPLY] SendGrid response headers: {dict(response.headers)}")
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "message": "Auto-reply sent successfully",
                        "recipient": to_email_clean,
                        "subject": formatted_subject,
                        "ticket_number": ticket_number,
                        "attempts": attempt + 1,
                        "cc_addresses": cc_addresses or []
                    }
                else:
                    error_msg = f"SendGrid API error. Status: {response.status_code}, Body: {response.text}"
                    logger.error(f"❌ [AUTO REPLY] {error_msg}")
                    
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": f"Failed to send auto-reply. Status: {response.status_code}",
                        "error": response.text,
                        "attempts": attempt + 1
                    }
                    
            except (httpx.ConnectTimeout, httpx.TimeoutException, httpx.ConnectError) as e:
                error_msg = f"Connection error: {type(e).__name__}: {str(e) if str(e) else 'Network timeout'}"
                
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6 seconds
                    logger.warning(f"🔄 [AUTO REPLY] {error_msg} for {to_email_clean}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ [AUTO REPLY] Final attempt failed for {to_email_clean}: {error_msg}")
                    return {
                        "success": False,
                        "message": f"Auto-reply failed after {max_retries + 1} attempts: {error_msg}",
                        "error": error_msg,
                        "exception_type": type(e).__name__,
                        "attempts": attempt + 1
                    }
                    
            except Exception as e:
                error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
                logger.error(f"❌ [AUTO REPLY] Error sending auto-reply to {to_email_clean}: {error_msg}")
                logger.error(f"❌ [AUTO REPLY] Exception details - Type: {type(e).__name__}, Args: {e.args}")
                
                return {
                    "success": False,
                    "message": f"Error sending auto-reply: {error_msg}",
                    "error": error_msg,
                    "exception_type": type(e).__name__,
                    "exception_args": str(e.args),
                    "attempts": attempt + 1
                }
        
        # This should never be reached due to the loop structure, but just in case
        return {
            "success": False,
            "message": "Unexpected error in retry loop",
            "attempts": max_retries + 1
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test SendGrid connection and API key validity
        
        Returns:
            Dictionary with connection test results
        """
        try:
            logger.info("🧪 [EMAIL SERVICE] Testing SendGrid connection...")
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with a simple API call (get user info)
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.get(
                    "https://api.sendgrid.com/v3/user/account",
                    headers=headers
                )
            
            if response.status_code == 200:
                logger.info("✅ [EMAIL SERVICE] SendGrid connection successful")
                return {
                    "success": True,
                    "message": "SendGrid connection successful",
                    "status_code": response.status_code
                }
            else:
                logger.error(f"❌ [EMAIL SERVICE] SendGrid connection failed with status {response.status_code}")
                return {
                    "success": False,
                    "message": f"SendGrid connection failed with status {response.status_code}",
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except Exception as e:
            error_msg = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
            logger.error(f"❌ [EMAIL SERVICE] SendGrid connection error: {error_msg}")
            return {
                "success": False,
                "message": f"SendGrid connection error: {error_msg}",
                "error": error_msg,
                "exception_type": type(e).__name__
            }

    async def send_auto_reply_email(
        self, 
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str = None,
        ticket_number: str = None,
        cc_addresses: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send auto-reply acknowledgment email with retry logic
        
        Args:
            to_email: Recipient email address
            subject: Email subject line 
            text_content: Plain text email content
            html_content: HTML email content for rich formatting
            ticket_number: Optional ticket number for tracking
            cc_addresses: Optional list of CC recipients
            
        Returns:
            Dictionary with success status and details
        """
        for attempt in range(self.max_retries + 1):
            try:
                # Add initial delay for connection conflict prevention
                if attempt == 0 and self.initial_delay > 0:
                    logger.info(f"📤 [EMAIL] Adding {self.initial_delay}s delay before sending to {to_email}")
                    await asyncio.sleep(self.initial_delay)
                
                logger.info(f"📤 [EMAIL] Attempting to send auto-reply to {to_email} (attempt {attempt + 1})")
                
                # Build personalization with to/cc recipients
                personalization = {
                    "to": [{"email": to_email.strip()}]
                }
                
                # Add CC recipients if provided
                if cc_addresses:
                    cc_list = [{"email": cc.strip()} for cc in cc_addresses if cc.strip()]
                    if cc_list:
                        personalization["cc"] = cc_list
                        logger.info(f"📧 [EMAIL] Adding CC recipients: {[cc['email'] for cc in cc_list]}")
                
                # Build email payload
                payload = {
                    "personalizations": [personalization],
                    "from": {
                        "email": self.from_email,
                        "name": "Argan HR Consultancy"
                    },
                    "reply_to": {
                        "email": to_email.strip()  # Reply goes back to original sender
                    },
                    "subject": subject,
                    "content": [
                        {
                            "type": "text/plain",
                            "value": text_content
                        }
                    ]
                }
                
                # Add HTML content if provided
                if html_content:
                    payload["content"].append({
                        "type": "text/html", 
                        "value": html_content
                    })
                    logger.info(f"📧 [EMAIL] Including HTML content in email")
                
                # Send request to SendGrid API
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"📤 [EMAIL] Sending to SendGrid API...")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.sendgrid.com/v3/mail/send",
                        headers=headers,
                        json=payload
                    )
                
                # Check response
                if response.status_code == 202:
                    logger.info(f"✅ [EMAIL] Auto-reply sent successfully to {to_email}")
                    logger.info(f"📧 [EMAIL] Subject: {subject}")
                    logger.info(f"📧 [EMAIL] Response: {response.status_code}")
                    
                    return {
                        "success": True,
                        "status_code": response.status_code,
                        "message": "Auto-reply sent successfully",
                        "recipient": to_email,
                        "subject": subject,
                        "attempts": attempt + 1,
                        "cc_addresses": cc_addresses or []
                    }
                else:
                    error_msg = f"SendGrid API error: {response.status_code} - {response.text}"
                    logger.error(f"❌ [EMAIL] {error_msg}")
                    
                    return {
                        "success": False,
                        "status_code": response.status_code,
                        "message": error_msg,
                        "error": response.text,
                        "attempts": attempt + 1
                    }
                    
            except (httpx.ConnectTimeout, httpx.TimeoutException, httpx.NetworkError) as e:
                error_msg = f"Network error: {type(e).__name__}: {str(e)}"
                
                if attempt < self.max_retries:
                    wait_time = self.base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"🔄 [EMAIL] {error_msg}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries + 1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ [EMAIL] Final attempt failed: {error_msg}")
                    return {
                        "success": False,
                        "message": f"Email failed after {self.max_retries + 1} attempts: {error_msg}",
                        "error": error_msg,
                        "attempts": attempt + 1
                    }
                    
            except Exception as e:
                error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
                logger.error(f"❌ [EMAIL] {error_msg}")
                
                return {
                    "success": False,
                    "message": error_msg,
                    "error": error_msg,
                    "attempts": attempt + 1
                }
        
        # Fallback return (should not reach here)
        return {
            "success": False,
            "message": "Unexpected end of retry loop",
            "attempts": self.max_retries + 1
        }


# Initialize global email service instance
email_service = EmailService() 