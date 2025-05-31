"""
Initial Email Handler with AI Enhancement and Airtable Integration
Processes new emails, generates tickets, extracts AI metadata, and stores in Airtable
"""

import logging
import asyncio
from datetime import datetime
from backend.email_functions.classification.assign_ticket import generate_ticket_number_standalone
from backend.airtable_service import AirtableService
from backend.email_functions.auto_reply import send_auto_reply

logger = logging.getLogger(__name__)


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
        
        # Generate ticket number
        ticket_number = generate_ticket_number_standalone()
        logger.info(f"🎫 [TICKET GEN] Generated ticket number: {ticket_number}")
        
        # Prepare enhanced email data with AI metadata
        enhanced_email_data = prepare_enhanced_email_data(email_data, classification_data)
        
        # Create record in Airtable
        airtable_record = airtable.create_email_record(
            email_data=enhanced_email_data,
            ticket_number=ticket_number,
            classification_data=classification_data
        )
        
        logger.info(f"🎫 [INITIAL EMAIL] New ticket created: {ticket_number}")
        logger.info(f"📊 [AIRTABLE] Record created with ID: {airtable_record['id']}")
        
        # Send auto-reply with ticket number
        try:
            auto_reply_success = await send_auto_reply(
                recipient=email_data.get('sender'),
                ticket_number=ticket_number,
                original_subject=email_data.get('subject', ''),
                sender_name=email_data.get('sender_name', ''),
                priority=extract_priority_from_classification(classification_data),
                ai_summary=extract_ai_summary(classification_data)
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


# Keep backward compatibility
process_new_email = process_initial_email 