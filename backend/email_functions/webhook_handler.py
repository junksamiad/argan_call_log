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
            
            # Normalize the email data structure
            normalized_data = {
                'sender': sender_email,  # Now contains just the email address
                'sender_full': raw_sender,  # Full "Name <email>" format
                'sender_name': sender_name,
                'recipients': email_data.get('to', []),
                'cc': email_data.get('cc', []),
                'bcc': email_data.get('bcc', []),
                'subject': email_data.get('subject', ''),
                'body_text': email_data.get('text', ''),
                'body_html': email_data.get('html', ''),
                'message_id': email_data.get('message_id', ''),
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