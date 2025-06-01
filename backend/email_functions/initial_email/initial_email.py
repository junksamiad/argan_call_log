"""
Initial Email Handler with AI Enhancement and Airtable Integration
Processes new emails, generates tickets, extracts AI metadata, and stores in Airtable
"""

import logging
import asyncio
import json
import hashlib
from datetime import datetime
from backend.email_functions.classification.assign_ticket import generate_ticket_number_standalone
from backend.airtable_service import AirtableService
from backend.email_functions.auto_reply import send_auto_reply

logger = logging.getLogger(__name__)


def generate_message_id(email_data):
    """Generate a unique message ID for conversation tracking"""
    content = f"{email_data.get('sender', '')}{email_data.get('message_id', '')}{email_data.get('email_date', '')}"
    return hashlib.md5(content.encode()).hexdigest()[:12]


def generate_content_hash(content):
    """Generate content hash for deduplication"""
    if not content:
        return ""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def create_initial_conversation_entry(email_data, classification_data=None):
    """
    Create the initial conversation history entry for a new email
    
    Args:
        email_data: Raw email data from webhook
        classification_data: AI classification results
        
    Returns:
        List with single conversation entry
    """
    # Extract AI summary if available
    ai_summary = None
    if classification_data:
        # Handle object format (MockClassificationData with EMAIL_DATA attribute)
        if hasattr(classification_data, 'EMAIL_DATA'):
            ai_summary = classification_data.EMAIL_DATA.ai_summary
        # Handle dictionary format (with ai_extracted_data key)
        elif isinstance(classification_data, dict) and 'ai_extracted_data' in classification_data:
            ai_summary = classification_data['ai_extracted_data'].get('ai_summary')
    
    # Create the initial conversation entry
    conversation_entry = {
        "message_id": generate_message_id(email_data),
        "timestamp": email_data.get('email_date') or datetime.utcnow().isoformat(),
        "sender": email_data.get('sender', 'unknown@unknown.com'),
        "sender_name": email_data.get('sender_name', ''),
        "message_type": "initial",
        "source": "direct",
        "extracted_from": None,
        "subject": email_data.get('subject', ''),
        "body_text": email_data.get('body_text', ''),
        "content_hash": generate_content_hash(email_data.get('body_text', '')),
        "thread_position": 1,
        "ai_summary": ai_summary,
        "priority": "Normal"
    }
    
    logger.info(f"📜 [CONVERSATION] Created initial conversation entry for {email_data.get('sender')}")
    return [conversation_entry]


async def process_initial_email(email_data, classification_data=None):
    """
    Process a new email with AI classification data and store in Airtable
    
    Args:
        email_data: Raw email data from webhook
        classification_data: AI classification results (optional)
    """
    try:
        logger.info(f"📧 [INITIAL EMAIL] Processing new email from {email_data.get('sender')}")
        
        # Initialize Airtable service
        airtable = AirtableService()
        
        # DEDUPLICATION: Check if this email already exists
        message_id = email_data.get('message_id', '')
        sender = email_data.get('sender', '')
        subject = email_data.get('subject', '')
        
        if message_id or (sender and subject):
            # Search for existing records with same identifiers
            existing_records = airtable.table.all()
            for record in existing_records:
                fields = record['fields']
                existing_message_id = fields.get('Message ID', '')
                existing_sender = fields.get('Sender Email', '')
                existing_subject = fields.get('Subject', '')
                
                # Check for exact match by message ID or sender+subject combination
                if (message_id and existing_message_id == message_id) or \
                   (sender == existing_sender and subject == existing_subject):
                    logger.warning(f"🔄 [DEDUP] Found existing record {fields.get('Ticket Number', 'Unknown')} for this email")
                    
                    # If this record doesn't have AI data but we have it now, update it
                    if classification_data and not fields.get('AI Summary'):
                        logger.info(f"🔄 [DEDUP] Updating existing record with AI classification data")
                        
                        # Extract proper sender name and email body for auto-reply
                        sender_name = extract_sender_name_for_auto_reply(email_data, classification_data)
                        original_email_body = extract_email_body_for_auto_reply(email_data)
                        
                        # Update the record with AI data
                        ai_data = classification_data.get('ai_extracted_data', {}) if isinstance(classification_data, dict) else {}
                        
                        update_fields = {
                            'AI Summary': ai_data.get('ai_summary', ''),
                            'AI Classification': classification_data.get('EMAIL_CLASSIFICATION', ''),
                            'AI Confidence': classification_data.get('confidence_score', 0),
                            'Query Type': ai_data.get('hr_category', ''),
                            'AI Processing Timestamp': classification_data.get('processing_timestamp', ''),
                            'Urgency Keywords': json.dumps(ai_data.get('urgency_keywords', [])),
                            'Sentiment Tone': ai_data.get('sentiment_tone', '')
                        }
                        
                        # Remove empty fields to avoid Airtable errors
                        update_fields = {k: v for k, v in update_fields.items() if v}
                        
                        try:
                            airtable.table.update(record['id'], update_fields)
                            logger.info(f"✅ [DEDUP] Updated record {fields.get('Ticket Number')} with AI data")
                        except Exception as update_error:
                            logger.error(f"❌ [DEDUP] Failed to update record: {update_error}")
                        
                        # Send auto-reply if not already sent
                        if not fields.get('Auto Reply Sent', False):
                            logger.info(f"📤 [DEDUP] Sending auto-reply for existing ticket {fields.get('Ticket Number')}")
                            
                            try:
                                auto_reply_success = await send_auto_reply(
                                    recipient=email_data.get('sender'),
                                    ticket_number=fields.get('Ticket Number'),
                                    original_subject=email_data.get('subject', ''),
                                    sender_name=sender_name,
                                    priority=extract_priority_from_classification(classification_data),
                                    ai_summary=extract_ai_summary(classification_data),
                                    original_email_body=original_email_body
                                )
                                
                                if auto_reply_success:
                                    # Update record to mark auto-reply sent
                                    airtable.table.update(record['id'], {
                                        "Auto Reply Sent": True,
                                        "Auto Reply Timestamp": datetime.utcnow().isoformat()
                                    })
                                    logger.info(f"✅ [DEDUP] Auto-reply sent for existing ticket")
                                
                            except Exception as reply_error:
                                logger.error(f"❌ [DEDUP] Failed to send auto-reply: {reply_error}")
                    
                    # Return the existing record info
                    return {
                        "success": True,
                        "ticket_number": fields.get('Ticket Number'),
                        "airtable_record_id": record['id'],
                        "message": f"Email already processed as ticket {fields.get('Ticket Number')}",
                        "ai_classification": classification_data.get('EMAIL_CLASSIFICATION') if classification_data else None,
                        "ai_confidence": classification_data.get('confidence_score') if classification_data else None,
                        "duplicate_detected": True
                    }
        
        # If we get here, it's a genuinely new email - proceed with normal processing
        logger.info(f"✅ [DEDUP] Confirmed new email - proceeding with ticket creation")
        
        # Generate ticket number
        ticket_number = generate_ticket_number_standalone()
        logger.info(f"🎫 [TICKET GEN] Generated ticket number: {ticket_number}")
        
        # Create conversation history
        conversation_history = create_initial_conversation_entry(email_data, classification_data)
        
        # Prepare enhanced email data with AI metadata and conversation history
        enhanced_email_data = prepare_enhanced_email_data(email_data, classification_data)
        enhanced_email_data['conversation_history'] = json.dumps(conversation_history)
        
        # Create record in Airtable
        airtable_record = airtable.create_email_record(
            email_data=enhanced_email_data,
            ticket_number=ticket_number,
            classification_data=classification_data
        )
        
        logger.info(f"🎫 [INITIAL EMAIL] New ticket created: {ticket_number}")
        logger.info(f"📊 [AIRTABLE] Record created with ID: {airtable_record['id']}")
        
        # Extract proper sender name and email body for auto-reply
        sender_name = extract_sender_name_for_auto_reply(email_data, classification_data)
        original_email_body = extract_email_body_for_auto_reply(email_data)
        
        logger.info(f"📤 [AUTO REPLY] Using sender name: '{sender_name}' and body length: {len(original_email_body) if original_email_body else 0}")
        
        # Send auto-reply with ticket number
        try:
            auto_reply_success = await send_auto_reply(
                recipient=email_data.get('sender'),
                ticket_number=ticket_number,
                original_subject=email_data.get('subject', ''),
                sender_name=sender_name,
                priority=extract_priority_from_classification(classification_data),
                ai_summary=extract_ai_summary(classification_data),
                original_email_body=original_email_body
            )
            
            if auto_reply_success:
                # Update Airtable record to mark auto-reply sent
                airtable.table.update(airtable_record['id'], {
                    "Auto Reply Sent": True,
                    "Auto Reply Timestamp": datetime.utcnow().isoformat()
                })
                logger.info(f"✅ [AUTO REPLY] Sent confirmation to {email_data.get('sender')}")
            
        except Exception as e:
            logger.error(f"❌ [AUTO REPLY] Failed to send auto-reply: {e}")
        
        return {
            "success": True,
            "ticket_number": ticket_number,
            "airtable_record_id": airtable_record['id'],
            "message": f"New ticket created: {ticket_number}",
            "ai_classification": classification_data.get('EMAIL_CLASSIFICATION') if classification_data else None,
            "ai_confidence": classification_data.get('confidence_score') if classification_data else None
        }
        
    except Exception as e:
        logger.error(f"Error processing new email: {e}")
        raise Exception(f"Failed to process new email: {e}")


def prepare_enhanced_email_data(email_data, classification_data=None):
    """
    Enhance email data with AI classification results and metadata
    
    Args:
        email_data: Original email data
        classification_data: AI classification results
        
    Returns:
        Enhanced email data dictionary
    """
    # Start with original email data
    enhanced_data = email_data.copy()
    
    # Ensure email_date is properly set with fallback to current time
    if not enhanced_data.get('email_date') or enhanced_data.get('email_date') == '':
        enhanced_data['email_date'] = datetime.utcnow().isoformat()
        logger.info(f"📅 [EMAIL DATE] Set fallback email date: {enhanced_data['email_date']}")
    else:
        logger.info(f"📅 [EMAIL DATE] Using provided email date: {enhanced_data.get('email_date')}")
    
    # Add AI-extracted metadata if available
    if classification_data and hasattr(classification_data, 'EMAIL_DATA'):
        ai_data = classification_data.EMAIL_DATA
        
        # Enhance with AI-extracted fields
        enhanced_data.update({
            'sender_name': ai_data.sender_name or email_data.get('sender_name', ''),
            'sender_domain': ai_data.sender_domain,
            'urgency_keywords': ai_data.urgency_keywords,
            'sentiment_tone': ai_data.sentiment_tone,
            'mentioned_people': ai_data.mentioned_people,
            'mentioned_departments': ai_data.mentioned_departments,
            'deadline_mentions': ai_data.deadline_mentions,
            'policy_references': ai_data.policy_references,
            'contact_phone': ai_data.contact_phone,
            'contact_address': ai_data.contact_address,
            'ai_summary': ai_data.ai_summary,
            'ai_processing_timestamp': classification_data.processing_timestamp
        })
        
        logger.info(f"🤖 [AI ENHANCEMENT] Enhanced email data with AI extraction")
        
        # Log extracted insights
        if ai_data.urgency_keywords:
            logger.info(f"🚨 [AI INSIGHTS] Urgency keywords detected: {ai_data.urgency_keywords}")
        if ai_data.sentiment_tone:
            logger.info(f"😊 [AI INSIGHTS] Sentiment: {ai_data.sentiment_tone}")
        if ai_data.deadline_mentions:
            logger.info(f"⏰ [AI INSIGHTS] Deadlines mentioned: {ai_data.deadline_mentions}")
    
    return enhanced_data


def extract_priority_from_classification(classification_data):
    """Extract priority level from AI classification data"""
    if not classification_data or not hasattr(classification_data, 'EMAIL_DATA'):
        return "Normal"
    
    urgency_keywords = classification_data.EMAIL_DATA.urgency_keywords
    if not urgency_keywords:
        return "Normal"
    
    # Convert to list if it's a JSON string
    if isinstance(urgency_keywords, str):
        try:
            import json
            urgency_keywords = json.loads(urgency_keywords)
        except:
            urgency_keywords = []
    
    # Determine priority based on urgency keywords
    urgent_keywords = ['urgent', 'emergency', 'asap', 'immediate', 'critical']
    high_keywords = ['important', 'priority', 'deadline', 'soon']
    
    if any(keyword.lower() in [uk.lower() for uk in urgency_keywords] for keyword in urgent_keywords):
        return "Urgent"
    elif any(keyword.lower() in [uk.lower() for uk in urgency_keywords] for keyword in high_keywords):
        return "High"
    else:
        return "Normal"


def extract_ai_summary(classification_data):
    """Extract AI summary for auto-reply personalization"""
    if not classification_data or not hasattr(classification_data, 'EMAIL_DATA'):
        return None
    
    return classification_data.EMAIL_DATA.ai_summary


def extract_sender_name_for_auto_reply(email_data, classification_data=None):
    """
    Extract the best available sender name for auto-reply greeting
    Priority: AI extracted name > original sender_name > email username part
    Returns only the first name for a more personal greeting
    """
    # Try AI-extracted sender name first
    ai_sender_name = None
    if classification_data:
        if hasattr(classification_data, 'EMAIL_DATA'):
            if classification_data.EMAIL_DATA.sender_name:
                ai_sender_name = classification_data.EMAIL_DATA.sender_name.strip()
        elif isinstance(classification_data, dict):
            if 'ai_extracted_data' in classification_data:
                ai_data = classification_data.get('ai_extracted_data', {})
                ai_sender_name = ai_data.get('sender_name', '').strip()
    
    # Try original email data sender_name
    original_sender_name = email_data.get('sender_name', '').strip()
    
    # Use the best available name
    full_name = None
    if ai_sender_name and ai_sender_name != '':
        full_name = ai_sender_name
        logger.info(f"📤 [AUTO REPLY] Using AI-extracted sender name: {ai_sender_name}")
    elif original_sender_name and original_sender_name != '':
        full_name = original_sender_name
        logger.info(f"📤 [AUTO REPLY] Using original sender name: {original_sender_name}")
    else:
        # Fall back to email username part
        sender_email = email_data.get('sender', 'unknown@unknown.com')
        full_name = sender_email.split('@')[0]
        logger.info(f"📤 [AUTO REPLY] Using fallback name from email: {full_name}")
    
    # Extract just the first name for more personal greeting
    if full_name:
        # Split by space and take the first part
        first_name = full_name.split()[0]
        logger.info(f"📤 [AUTO REPLY] Using first name for greeting: '{first_name}' (from '{full_name}')")
        return first_name
    
    return "there"  # Fallback greeting like "Hi there," if no name found


def extract_email_body_for_auto_reply(email_data):
    """
    Extract the email body content for inclusion in auto-reply
    Priority: body_text > text > fallback message
    """
    # Try different possible keys for email body
    body_options = ['body_text', 'text', 'body', 'message']
    
    for key in body_options:
        body_content = email_data.get(key, '').strip()
        if body_content:
            logger.info(f"📤 [AUTO REPLY] Found email body using key '{key}' (length: {len(body_content)})")
            return body_content
    
    # Fallback message if no body found
    logger.warning(f"📤 [AUTO REPLY] No email body content found in keys: {body_options}")
    return "Original email content was not available."


# Keep backward compatibility
process_new_email = process_initial_email 