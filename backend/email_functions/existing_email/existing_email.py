"""
Existing Email Handler with Thread Parsing and Conversation History Management
Processes replies to existing tickets, extracts thread history, and updates conversation
"""

import logging
import json
import asyncio
from datetime import datetime
from backend.airtable_service import AirtableService
from backend.email_functions.auto_reply import send_auto_reply
from .thread_parser_ai import ThreadParserAI

logger = logging.getLogger(__name__)


async def process_existing_email(email_data, classification_data=None):
    """
    Process a reply to an existing ticket
    
    Args:
        email_data: Raw email data from webhook
        classification_data: AI classification results with ticket number
    """
    try:
        ticket_number = extract_ticket_number(classification_data)
        logger.info(f"💬 [EXISTING EMAIL] Processing reply for ticket {ticket_number}")
        
        # Initialize services
        airtable = AirtableService()
        thread_parser = ThreadParserAI()
        
        # Find existing ticket
        existing_record = airtable.find_ticket(ticket_number)
        if not existing_record:
            logger.warning(f"🚨 [EXISTING EMAIL] Ticket {ticket_number} not found, treating as new email")
            # Fallback to new email processing
            from backend.email_functions.initial_email.initial_email import process_initial_email
            return await process_initial_email(email_data, classification_data)
        
        # Parse email thread to extract individual messages
        logger.info(f"🧵 [THREAD PARSER] Parsing email thread for ticket {ticket_number}")
        parsed_messages = await thread_parser.parse_email_thread(email_data)
        
        # Get existing conversation history
        existing_conversation = get_existing_conversation(existing_record)
        
        # Merge new messages with existing conversation (deduplication)
        updated_conversation = merge_conversations(existing_conversation, parsed_messages)
        
        # Update Airtable record
        update_result = airtable.update_conversation_advanced(
            ticket_number, 
            updated_conversation,
            email_data
        )
        
        if update_result:
            logger.info(f"✅ [EXISTING EMAIL] Updated conversation for ticket {ticket_number}")
            
            # Send auto-reply for the new message
            await send_reply_confirmation(email_data, ticket_number, existing_record)
            
            return {
                "success": True,
                "ticket_number": ticket_number,
                "message": f"Updated existing ticket: {ticket_number}",
                "new_messages_count": len(parsed_messages),
                "total_messages": len(updated_conversation)
            }
        else:
            logger.error(f"❌ [EXISTING EMAIL] Failed to update conversation for {ticket_number}")
            return {
                "success": False,
                "error": "Failed to update conversation",
                "ticket_number": ticket_number
            }
            
    except Exception as e:
        logger.error(f"❌ [EXISTING EMAIL] Error processing existing email: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to process existing email: {str(e)}"
        }


def extract_ticket_number(classification_data):
    """Extract ticket number from AI classification data"""
    if not classification_data:
        return None
    
    # Check if it's in the ai_extracted_data
    if 'ai_extracted_data' in classification_data:
        return classification_data['ai_extracted_data'].get('ticket_number')
    
    # Check if it's a direct attribute
    if hasattr(classification_data, 'EMAIL_DATA'):
        return classification_data.EMAIL_DATA.ticket_number
    
    return None


def get_existing_conversation(airtable_record):
    """Get existing conversation history from Airtable record"""
    try:
        conversation_json = airtable_record['fields'].get('Conversation History', '[]')
        return json.loads(conversation_json)
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"📜 [CONVERSATION] Error parsing existing conversation: {e}")
        return []


def merge_conversations(existing_messages, new_messages):
    """
    Merge new messages with existing conversation, handling deduplication
    
    Args:
        existing_messages: List of existing conversation entries
        new_messages: List of newly parsed messages
        
    Returns:
        Merged and deduplicated conversation list
    """
    logger.info(f"📜 [CONVERSATION] Merging {len(new_messages)} new messages with {len(existing_messages)} existing")
    
    # Create lookup sets for deduplication
    existing_hashes = {msg.get('content_hash') for msg in existing_messages if msg.get('content_hash')}
    existing_message_ids = {msg.get('message_id') for msg in existing_messages if msg.get('message_id')}
    
    # Filter out duplicates
    unique_new_messages = []
    for message in new_messages:
        content_hash = message.get('content_hash')
        message_id = message.get('message_id')
        
        # Skip if we've seen this content or message before
        if content_hash in existing_hashes or message_id in existing_message_ids:
            logger.debug(f"🔄 [DEDUP] Skipping duplicate message: {message_id}")
            continue
            
        unique_new_messages.append(message)
    
    # Combine and sort by timestamp
    all_messages = existing_messages + unique_new_messages
    all_messages.sort(key=lambda x: x.get('timestamp', ''))
    
    # Update thread positions
    for i, message in enumerate(all_messages, 1):
        message['thread_position'] = i
    
    logger.info(f"📜 [CONVERSATION] Merged conversation: {len(all_messages)} total messages ({len(unique_new_messages)} new)")
    return all_messages


async def send_reply_confirmation(email_data, ticket_number, existing_record):
    """Send auto-reply confirmation for reply to existing ticket"""
    try:
        # Extract sender information
        sender = email_data.get('sender')
        sender_name = email_data.get('sender_name', '')
        subject = email_data.get('subject', '')
        
        # Send confirmation auto-reply
        await send_auto_reply(
            recipient=sender,
            ticket_number=ticket_number,
            original_subject=subject,
            sender_name=sender_name,
            priority="Normal",
            ai_summary=f"Reply received for existing ticket {ticket_number}",
            original_email_body=email_data.get('body_text', '')  # Include for human review
        )
        
        logger.info(f"✅ [AUTO REPLY] Sent reply confirmation for {ticket_number} to {sender}")
        
    except Exception as e:
        logger.error(f"❌ [AUTO REPLY] Failed to send reply confirmation: {e}")


# Keep backward compatibility
process_reply_email = process_existing_email 