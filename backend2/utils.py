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
    
    Uses database-validated sequential numbering to prevent duplicates.
    Queries Airtable to find the highest ticket number for today and increments by 1.
    
    Returns:
        Formatted ticket number like ARG-20250603-0001
    """
    try:
        today = datetime.now().strftime("%Y%m%d")
        logger.info(f"🎫 [TICKET GEN] Generating ticket number for date: {today}")
        
        # Query Airtable to find highest sequence number for today
        from .database import table
        
        # Search for all tickets with today's date pattern
        today_pattern = f"ARG-{today}-"
        
        try:
            # Get all records (we'll filter in memory since Airtable formula filtering is complex)
            all_records = table.all()
            logger.info(f"🎫 [TICKET GEN] Found {len(all_records)} total records in Airtable")
            
            # Filter for today's tickets and extract sequence numbers
            today_tickets = []
            for record in all_records:
                ticket_num = record.get('fields', {}).get('ticket_number', '')
                if ticket_num.startswith(today_pattern):
                    # Extract sequence number from ticket like "ARG-20250603-0001"
                    try:
                        sequence_part = ticket_num.split('-')[-1]  # Get "0001" part
                        sequence_number = int(sequence_part)
                        today_tickets.append(sequence_number)
                        logger.info(f"🎫 [TICKET GEN] Found existing ticket: {ticket_num} (sequence: {sequence_number})")
                    except (ValueError, IndexError):
                        logger.warning(f"⚠️ [TICKET GEN] Could not parse sequence from ticket: {ticket_num}")
                        continue
            
            # Determine next sequence number
            if today_tickets:
                next_sequence = max(today_tickets) + 1
                logger.info(f"🎫 [TICKET GEN] Highest existing sequence: {max(today_tickets)}, next: {next_sequence}")
            else:
                next_sequence = 1
                logger.info(f"🎫 [TICKET GEN] No existing tickets for today, starting with: {next_sequence}")
            
            # Format final ticket number
            ticket_number = f"ARG-{today}-{next_sequence:04d}"
            logger.info(f"🎫 [TICKET GEN] Generated candidate ticket number: {ticket_number}")
            
            # Double-check uniqueness (paranoid validation)
            if validate_ticket_uniqueness(ticket_number):
                logger.info(f"✅ [TICKET GEN] Confirmed unique ticket number: {ticket_number}")
                return ticket_number
            else:
                logger.error(f"❌ [TICKET GEN] Generated ticket already exists! This should not happen.")
                # Increment and try again (safety mechanism)
                retry_ticket = f"ARG-{today}-{next_sequence + 1:04d}"
                logger.warning(f"🔄 [TICKET GEN] Retrying with: {retry_ticket}")
                if validate_ticket_uniqueness(retry_ticket):
                    return retry_ticket
                else:
                    logger.error(f"❌ [TICKET GEN] Even retry failed! Falling back to microsecond-based.")
                    # Fall through to fallback
            
        except Exception as db_error:
            logger.error(f"❌ [TICKET GEN] Database error during ticket generation: {db_error}")
            # Fall through to fallback logic below
            
    except Exception as e:
        logger.error(f"❌ [TICKET GEN] Error generating ticket: {e}")
    
    # Fallback: Use microsecond-based numbering (much safer than old modulo approach)
    try:
        logger.warning("⚠️ [TICKET GEN] Using fallback microsecond-based numbering")
        import time
        
        today = datetime.now().strftime("%Y%m%d")
        # Use microseconds for much better collision resistance
        microseconds = int(time.time() * 1000000) % 10000
        fallback_ticket = f"ARG-{today}-{microseconds:04d}"
        
        logger.info(f"🔄 [TICKET GEN] Fallback ticket number: {fallback_ticket}")
        return fallback_ticket
        
    except Exception as fallback_error:
        logger.error(f"❌ [TICKET GEN] Even fallback failed: {fallback_error}")
        # Final emergency fallback
        today = datetime.now().strftime("%Y%m%d")
        return f"ARG-{today}-9999"


def validate_ticket_uniqueness(ticket_number: str) -> bool:
    """
    Validate that a ticket number doesn't already exist in Airtable
    
    Args:
        ticket_number: Ticket number to check (e.g., "ARG-20250603-0001")
        
    Returns:
        True if unique (safe to use), False if duplicate exists
    """
    try:
        logger.info(f"🔍 [TICKET VALIDATION] Checking uniqueness of: {ticket_number}")
        
        from .database import table
        from pyairtable.formulas import match
        
        # Search for existing ticket with this exact number
        existing_records = table.all(formula=match({"ticket_number": ticket_number}))
        
        if existing_records:
            logger.error(f"❌ [TICKET VALIDATION] DUPLICATE FOUND: {ticket_number} already exists!")
            logger.error(f"❌ [TICKET VALIDATION] Existing record ID: {existing_records[0]['id']}")
            return False
        else:
            logger.info(f"✅ [TICKET VALIDATION] Ticket number is unique: {ticket_number}")
            return True
            
    except Exception as e:
        logger.error(f"❌ [TICKET VALIDATION] Error validating ticket uniqueness: {e}")
        # Return False to be safe - don't use if we can't validate
        return False


def parse_multipart_form_data(raw_body: bytes) -> dict:
    """
    Parse multipart form data from SendGrid webhook
    
    Args:
        raw_body: Raw bytes from webhook request
        
    Returns:
        Dictionary with parsed form fields
    """
    try:
        # Simple parser for multipart form data with UTF-8 error handling
        try:
            decoded_body = raw_body.decode('utf-8')
        except UnicodeDecodeError as e:
            logger.warning(f"⚠️ [PARSER] UTF-8 decode error: {e}")
            logger.info(f"🔧 [PARSER] Attempting UTF-8 decode with error handling...")
            # Try with error handling - replace problematic bytes
            decoded_body = raw_body.decode('utf-8', errors='replace')
            logger.info(f"✅ [PARSER] Successfully decoded with character replacement")
        
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
        
        # Add debugging for problematic content
        for field_name, field_value in parsed_data.items():
            field_length = len(field_value) if field_value else 0
            logger.info(f"📋 [PARSER] Field '{field_name}': {field_length} characters")
            
            # Log first few characters of each field for debugging
            if field_value and field_length > 0:
                preview = field_value[:100] + "..." if field_length > 100 else field_value
                logger.info(f"📝 [PARSER] '{field_name}' preview: {repr(preview)}")
        
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
            # Add to processed set immediately to prevent race conditions
            _processed_message_ids.add(message_id)
            logger.info(f"📝 [DEDUPE] Marked as processed: {message_id}")
            logger.info(f"📊 [DEDUPE] Total processed emails: {len(_processed_message_ids)}")
        
    except Exception as e:
        logger.error(f"❌ [DEDUPE] Error marking as processed: {e}")


def mark_email_as_processing(message_id: str) -> bool:
    """
    Mark this Message-ID as currently being processed to prevent race conditions
    
    Args:
        message_id: Message-ID to mark as processing
        
    Returns:
        True if successfully marked (safe to proceed), False if already processing
    """
    try:
        if message_id == "unknown":
            return True  # Allow through if we can't identify
            
        if message_id in _processed_message_ids:
            logger.warning(f"🚫 [DEDUPE] Already processed/processing: {message_id}")
            return False
        else:
            # Immediately add to prevent other concurrent requests from processing
            _processed_message_ids.add(message_id)
            logger.info(f"🔒 [DEDUPE] Marked as processing: {message_id}")
            return True
            
    except Exception as e:
        logger.error(f"❌ [DEDUPE] Error marking as processing: {e}")
        return True  # Default to allowing through


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