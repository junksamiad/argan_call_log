"""
Webhook Handler for HR Email Management System
Handles incoming email webhooks from SendGrid and routes them to appropriate processors
"""

import logging
import json
from typing import Dict, Any
from .email_router import route_email_async
from fastapi import Request

logger = logging.getLogger(__name__)


class WebhookHandler:
    def __init__(self):
        """Initialize the webhook handler"""
        self.processed_messages = set()  # To avoid duplicate processing
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming email webhook from SendGrid
        
        Args:
            webhook_data: Raw webhook data from SendGrid
            
        Returns:
            Dict with processing results
        """
        try:
            logger.info("📧 [WEBHOOK] Processing incoming email webhook")
            
            # Extract email data from webhook
            email_data = self._extract_email_data(webhook_data)
            
            # Check for duplicates
            message_id = email_data.get('message_id', '')
            if message_id in self.processed_messages:
                logger.warning(f"⚠️ [WEBHOOK] Duplicate message detected: {message_id}")
                return {
                    "success": True,
                    "message": "Duplicate message ignored",
                    "message_id": message_id
                }
            
            # Mark as processed
            if message_id:
                self.processed_messages.add(message_id)
            
            # Route the email through our AI-enhanced system
            result = await route_email_async(email_data)
            
            logger.info(f"✅ [WEBHOOK] Email processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Error processing webhook: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to process webhook: {str(e)}"
            }
    
    async def parse_webhook(self, request: Request) -> Dict[str, Any]:
        """
        Parse webhook data from FastAPI Request object
        
        Args:
            request: FastAPI Request object from SendGrid webhook
            
        Returns:
            Parsed and normalized email data
        """
        try:
            # Get the raw body content
            body = await request.body()
            
            # Try to parse as JSON
            try:
                webhook_data = json.loads(body)
            except json.JSONDecodeError:
                # If not JSON, try to parse as form data
                form = await request.form()
                webhook_data = dict(form)
            
            logger.info("📧 [WEBHOOK] Parsing webhook data from SendGrid")
            
            # Extract and normalize email data
            email_data = self._extract_email_data(webhook_data)
            
            return email_data
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Error parsing webhook: {e}")
            return None
    
    def _extract_email_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and normalize email data from SendGrid webhook
        
        Args:
            webhook_data: Raw webhook data
            
        Returns:
            Normalized email data dict
        """
        try:
            # DEBUG: Log all webhook data to understand structure
            logger.info("🐛 [DEBUG] Raw webhook data keys:")
            for key in webhook_data.keys():
                logger.info(f"🐛 [DEBUG] Key: {key} = {str(webhook_data[key])[:100]}...")
            
            # Handle both single email and batch webhook formats
            if isinstance(webhook_data, list):
                # Take the first email if it's a batch
                email_data = webhook_data[0] if webhook_data else {}
            else:
                email_data = webhook_data
            
            # Extract sender information
            raw_sender = email_data.get('from', '')
            sender_email = self._extract_email_address(raw_sender)
            sender_name = self._extract_sender_name(raw_sender)
            
            # Extract body content - try multiple field names first, then parse raw email
            body_text = (
                email_data.get('text', '') or 
                email_data.get('body_text', '') or 
                email_data.get('plain', '') or
                email_data.get('body', '') or
                ''
            )
            
            body_html = (
                email_data.get('html', '') or 
                email_data.get('body_html', '') or 
                email_data.get('htmlbody', '') or
                ''
            )
            
            # If no body found in standard fields, try to parse from raw email
            if not body_text and not body_html and email_data.get('email'):
                try:
                    raw_email = email_data.get('email', '')
                    parsed_body = self._parse_raw_email(raw_email)
                    body_text = parsed_body.get('text', '')
                    body_html = parsed_body.get('html', '')
                    logger.info(f"🐛 [DEBUG] Parsed from raw email - Text: {len(body_text)}, HTML: {len(body_html)}")
                except Exception as parse_error:
                    logger.error(f"🐛 [DEBUG] Failed to parse raw email: {parse_error}")
            
            # DEBUG: Log body content extraction
            logger.info(f"🐛 [DEBUG] Body text found: {len(body_text)} characters")
            logger.info(f"🐛 [DEBUG] Body HTML found: {len(body_html)} characters")
            if body_text:
                logger.info(f"🐛 [DEBUG] Body text preview: {body_text[:200]}...")
            
            # Normalize the email data structure
            normalized_data = {
                'sender': sender_email,  # Now contains just the email address
                'sender_full': raw_sender,  # Full "Name <email>" format
                'sender_name': sender_name,
                'recipients': email_data.get('to', []),
                'cc': email_data.get('cc', []),
                'bcc': email_data.get('bcc', []),
                'subject': email_data.get('subject', ''),
                'body_text': body_text,
                'body_html': body_html,
                'message_id': self._extract_message_id(email_data),
                'email_date': email_data.get('date', ''),
                'attachments': email_data.get('attachments', []),
                'dkim': email_data.get('dkim', 'unknown'),
                'spf': email_data.get('spf', 'unknown'),
                'sender_ip': email_data.get('sender_ip', ''),
                'envelope': email_data.get('envelope', {}),
                'webhook_timestamp': email_data.get('timestamp', '')
            }
            
            logger.info(f"📧 [WEBHOOK] Extracted email from: {normalized_data['sender']}")
            logger.info(f"📧 [WEBHOOK] Subject: {normalized_data['subject']}")
            
            return normalized_data
            
        except Exception as e:
            logger.error(f"❌ [WEBHOOK] Error extracting email data: {e}")
            raise Exception(f"Failed to extract email data: {str(e)}")
    
    def _extract_email_address(self, from_field: str) -> str:
        """
        Extract just the email address from the 'from' field
        
        Args:
            from_field: Email from field (e.g., "John Doe <john@example.com>" or "john@example.com")
            
        Returns:
            Just the email address (e.g., "john@example.com")
        """
        try:
            if '<' in from_field and '>' in from_field:
                # Format: "Name <email@domain.com>" - extract the email part
                email_part = from_field.split('<')[1].split('>')[0].strip()
                return email_part
            else:
                # Just email address, return as is
                return from_field.strip()
        except Exception:
            # Fallback: return the original string
            return from_field.strip()
    
    def _extract_sender_name(self, from_field: str) -> str:
        """
        Extract sender name from email 'from' field
        
        Args:
            from_field: Email from field (e.g., "John Doe <john@example.com>")
            
        Returns:
            Extracted sender name or empty string
        """
        try:
            if '<' in from_field and '>' in from_field:
                # Format: "Name <email@domain.com>"
                name_part = from_field.split('<')[0].strip()
                # Remove quotes if present
                return name_part.strip('"').strip("'")
            else:
                # Just email address, no name
                return ""
        except Exception:
            return ""
    
    def _parse_raw_email(self, raw_email: str) -> Dict[str, str]:
        """
        Parse raw email content to extract body text and HTML
        
        Args:
            raw_email: Raw email message from SendGrid
            
        Returns:
            Dict with 'text' and 'html' keys
        """
        try:
            import email
            from email import policy
            
            # Parse the raw email
            msg = email.message_from_string(raw_email, policy=policy.default)
            
            body_text = ""
            body_html = ""
            
            # Handle multipart messages
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue
                    
                    if content_type == "text/plain":
                        body_text = part.get_content()
                    elif content_type == "text/html":
                        body_html = part.get_content()
            else:
                # Single part message
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    body_text = msg.get_content()
                elif content_type == "text/html":
                    body_html = msg.get_content()
            
            return {
                'text': body_text or "",
                'html': body_html or ""
            }
            
        except Exception as e:
            logger.error(f"❌ [EMAIL PARSER] Error parsing raw email: {e}")
            return {'text': "", 'html': ""}
    
    def _extract_message_id(self, email_data: Dict[str, Any]) -> str:
        """
        Extract Message-ID from email headers
        
        Args:
            email_data: Email data from SendGrid webhook
            
        Returns:
            Message-ID if found, empty string otherwise
        """
        try:
            # DEBUG: Log all available fields in email_data
            logger.info(f"🐛 [MESSAGE-ID DEBUG] Available email_data keys: {list(email_data.keys())}")
            
            # First check if there's a direct message_id field (unlikely with SendGrid)
            if email_data.get('message_id'):
                logger.info(f"📧 [WEBHOOK] Found direct message_id field: {email_data.get('message_id')}")
                return email_data.get('message_id', '')
            
            # SendGrid provides the raw email in the 'email' field - extract Message-ID from there
            raw_email = email_data.get('email', '')
            if raw_email:
                logger.info(f"🐛 [MESSAGE-ID DEBUG] Raw email content length: {len(raw_email)}")
                
                # Look for Message-ID in the raw email headers
                import re
                
                # Try multiple Message-ID patterns to handle different email providers
                patterns = [
                    # Standard format with angle brackets: Message-ID: <abc123@gmail.com>
                    r'Message-ID:\s*<([^>]+)>',
                    # Without angle brackets: Message-ID: abc123@gmail.com
                    r'Message-ID:\s*([^\r\n\s<>]+)',
                    # Case variations and extra whitespace
                    r'message-id:\s*<([^>]+)>',
                    r'message-id:\s*([^\r\n\s<>]+)',
                    # X-Message-ID (sometimes used)
                    r'X-Message-ID:\s*<([^>]+)>',
                    r'X-Message-ID:\s*([^\r\n\s<>]+)'
                ]
                
                for i, pattern in enumerate(patterns):
                    match = re.search(pattern, raw_email, re.IGNORECASE | re.MULTILINE)
                    if match:
                        message_id = match.group(1).strip()
                        # Clean up common formatting issues
                        message_id = message_id.strip('<>').strip()
                        logger.info(f"📧 [WEBHOOK] ✅ Extracted Message-ID (pattern {i+1}): {message_id}")
                        
                        # Log the email provider for debugging
                        if '@gmail.com' in message_id:
                            logger.info(f"📧 [PROVIDER] Detected Gmail Message-ID")
                        elif '@outlook.com' in message_id or '@hotmail.com' in message_id:
                            logger.info(f"📧 [PROVIDER] Detected Microsoft Message-ID")
                        elif '@yahoo.com' in message_id:
                            logger.info(f"📧 [PROVIDER] Detected Yahoo Message-ID")
                        else:
                            logger.info(f"📧 [PROVIDER] Message-ID from: {message_id.split('@')[-1] if '@' in message_id else 'Unknown'}")
                        
                        return message_id
                
                logger.warning("📧 [WEBHOOK] ⚠️ No Message-ID found in raw email content")
            else:
                logger.warning("📧 [WEBHOOK] ⚠️ No raw email content available for Message-ID extraction")
            
            # Fallback: Check for headers field (legacy support)
            headers = email_data.get('headers', '')
            if headers:
                logger.info(f"🐛 [MESSAGE-ID DEBUG] Found headers field, length: {len(str(headers))}")
                match = re.search(r'Message-ID:\s*<([^>]+)>', str(headers), re.IGNORECASE)
                if match:
                    message_id = match.group(1).strip()
                    logger.info(f"📧 [WEBHOOK] ✅ Extracted Message-ID from headers: {message_id}")
                    return message_id
            
            logger.warning("📧 [WEBHOOK] ⚠️ No Message-ID found in any available source")
            return ""
            
        except Exception as e:
            logger.error(f"📧 [WEBHOOK] ❌ Error extracting Message-ID: {e}")
            return ""
    
    def clear_processed_cache(self):
        """Clear the processed messages cache"""
        self.processed_messages.clear()
        logger.info("🧹 [WEBHOOK] Cleared processed messages cache")


# Singleton instance for easy access
_webhook_handler = None

async def process_webhook(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Standalone function to process webhooks
    
    Args:
        webhook_data: Raw webhook data from SendGrid
        
    Returns:
        Processing results
    """
    global _webhook_handler
    
    if _webhook_handler is None:
        _webhook_handler = WebhookHandler()
    
    return await _webhook_handler.process_webhook(webhook_data) 