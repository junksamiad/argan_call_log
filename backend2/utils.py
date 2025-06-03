"""
Utility Functions for HR Email Management System - Backend2
Contains helper functions like ticket number generation
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_ticket_number() -> str:
    """
    Generate a ticket number using the Argan format: ARG-YYYYMMDD-NNNN
    
    Returns:
        Formatted ticket number like ARG-20250603-0001
    """
    try:
        today = datetime.now().strftime("%Y%m%d")
        
        # TODO: In production, this should check existing tickets in database
        # For now, use a simple timestamp-based numbering
        import time
        sequence_number = int(time.time()) % 10000
        
        # Format ticket number with leading zeros
        ticket_number = f"ARG-{today}-{sequence_number:04d}"
        logger.info(f"🎫 [TICKET GEN] Generated ticket number: {ticket_number}")
        
        return ticket_number
        
    except Exception as e:
        logger.error(f"❌ [TICKET GEN] Error generating ticket: {e}")
        # Fallback to timestamp-based numbering
        import time
        fallback_number = int(time.time()) % 10000
        today = datetime.now().strftime("%Y%m%d")
        return f"ARG-{today}-{fallback_number:04d}"


def parse_multipart_form_data(raw_body: bytes) -> dict:
    """
    Parse multipart form data from SendGrid webhook
    
    Args:
        raw_body: Raw bytes from webhook request
        
    Returns:
        Dictionary with parsed form fields
    """
    try:
        # Simple parser for multipart form data
        decoded_body = raw_body.decode('utf-8')
        
        # Find boundary
        if '--xYzZY' in decoded_body:
            boundary = 'xYzZY'
        else:
            # Try to extract boundary from content-type header if available
            boundary = 'unknown'
        
        # Split by boundary
        parts = decoded_body.split(f'--{boundary}')
        
        parsed_data = {}
        
        for part in parts:
            if 'Content-Disposition: form-data' in part:
                lines = part.strip().split('\n')
                
                # Extract field name
                field_name = None
                for line in lines:
                    if 'name="' in line:
                        start = line.find('name="') + 6
                        end = line.find('"', start)
                        field_name = line[start:end]
                        break
                
                # Extract field value (skip headers)
                if field_name:
                    content_start = False
                    field_value = []
                    
                    for line in lines:
                        if content_start:
                            field_value.append(line)
                        elif line.strip() == '':
                            content_start = True
                    
                    parsed_data[field_name] = '\n'.join(field_value).strip()
        
        logger.info(f"📧 [PARSER] Parsed {len(parsed_data)} form fields")
        return parsed_data
        
    except Exception as e:
        logger.error(f"❌ [PARSER] Error parsing multipart data: {e}")
        return {}


# ================================================================================
# EMAIL DEDUPLICATION FUNCTIONS
# ================================================================================

# In-memory storage for processed Message-IDs (upgrade to Redis/DB in production)
_processed_message_ids = set()

def extract_message_id_from_headers(headers: str) -> str:
    """
    Extract Message-ID from email headers for deduplication
    
    Args:
        headers: Raw email headers string from SendGrid
        
    Returns:
        Message-ID string, or 'unknown' if not found
    """
    try:
        lines = headers.split('\n')
        
        for line in lines:
            # Look for Message-Id or Message-ID header
            if line.startswith('Message-Id:') or line.startswith('Message-ID:'):
                # Extract the ID part after the colon
                message_id = line.split(':', 1)[1].strip()
                logger.info(f"📧 [DEDUPE] Extracted Message-ID: {message_id}")
                return message_id
        
        logger.warning("⚠️ [DEDUPE] No Message-ID found in headers")
        return "unknown"
        
    except Exception as e:
        logger.error(f"❌ [DEDUPE] Error extracting Message-ID: {e}")
        return "unknown"


def is_duplicate_email(message_id: str) -> bool:
    """
    Check if this Message-ID has already been processed
    
    Args:
        message_id: Message-ID from email headers
        
    Returns:
        True if duplicate, False if new
    """
    try:
        if message_id == "unknown":
            # If we can't extract Message-ID, don't block (false negative is safer than false positive)
            logger.warning("⚠️ [DEDUPE] Unknown Message-ID, allowing through")
            return False
        
        if message_id in _processed_message_ids:
            logger.warning(f"🚫 [DEDUPE] DUPLICATE DETECTED: {message_id}")
            return True
        else:
            logger.info(f"✅ [DEDUPE] New email: {message_id}")
            return False
            
    except Exception as e:
        logger.error(f"❌ [DEDUPE] Error checking duplicate: {e}")
        return False  # Default to allowing email through


def mark_email_as_processed(message_id: str) -> None:
    """
    Mark this Message-ID as processed to prevent future duplicates
    
    Args:
        message_id: Message-ID to mark as processed
    """
    try:
        if message_id != "unknown":
            _processed_message_ids.add(message_id)
            logger.info(f"📝 [DEDUPE] Marked as processed: {message_id}")
            logger.info(f"📊 [DEDUPE] Total processed emails: {len(_processed_message_ids)}")
        
    except Exception as e:
        logger.error(f"❌ [DEDUPE] Error marking as processed: {e}")


def extract_original_sender_from_forwarded_email(headers: str) -> str:
    """
    Extract the original sender from forwarded email headers
    
    Args:
        headers: Email headers string from SendGrid
        
    Returns:
        Original sender email address
    """
    try:
        # Look for the original 'From:' line in headers
        lines = headers.split('\n')
        
        for line in lines:
            if line.startswith('From:'):
                # Extract email from "Name <email@domain.com>" format
                if '<' in line and '>' in line:
                    start = line.find('<') + 1
                    end = line.find('>')
                    original_sender = line[start:end]
                    logger.info(f"📧 [FORWARD PARSER] Found original sender: {original_sender}")
                    return original_sender
                else:
                    # Simple email format
                    parts = line.split(':')
                    if len(parts) > 1:
                        original_sender = parts[1].strip()
                        logger.info(f"📧 [FORWARD PARSER] Found original sender: {original_sender}")
                        return original_sender
        
        logger.warning("⚠️ [FORWARD PARSER] Could not extract original sender from headers")
        return "unknown@unknown.com"
        
    except Exception as e:
        logger.error(f"❌ [FORWARD PARSER] Error extracting original sender: {e}")
        return "unknown@unknown.com" 