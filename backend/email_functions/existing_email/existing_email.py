"""
Existing Email Handler for HR Email Management System
Handles replies to existing tickets and conversation threading
"""

import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.airtable_service import AirtableService

logger = logging.getLogger(__name__)


class ExistingEmailHandler:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    async def handle_reply_email(self, email_data: Dict[str, Any], ticket_number: str) -> Dict[str, Any]:
        """
        Handle a reply to an existing ticket
        
        Args:
            email_data: Email data (possibly AI-enhanced) from router
            ticket_number: Extracted ticket number from AI classification
            
        Returns:
            Dict with processing results
        """
        try:
            sender = email_data.get('sender')
            subject = email_data.get('subject', 'No Subject')
            
            logger.info(f"🔄 [EXISTING EMAIL] Processing reply for ticket: {ticket_number}")
            logger.info(f"🔄 [EXISTING EMAIL] From: {sender}")
            
            # Check if we have AI-extracted data
            ai_data = email_data.get('ai_extracted_data', {})
            if ai_data:
                logger.info(f"🤖 [EXISTING EMAIL] AI Confidence: {ai_data.get('ai_confidence', 'N/A')}")
                logger.info(f"🤖 [EXISTING EMAIL] Sentiment: {ai_data.get('sentiment_tone', 'N/A')}")
                urgency_keywords = ai_data.get('urgency_keywords', [])
                if urgency_keywords:
                    logger.info(f"⚡ [EXISTING EMAIL] Urgency indicators found: {urgency_keywords}")
            
            # TODO: Implement reply handling logic
            # This will include:
            # - Finding the existing thread in the database using ticket_number
            # - Adding the new message to the thread with AI metadata
            # - Analyzing if urgent response is needed based on AI sentiment/keywords
            # - Potentially sending acknowledgment or routing to HR staff
            # - Updating thread status if needed
            # - Storing conversation history with AI-extracted context
            
            # For now, return success with enhanced data
            return {
                "success": True,
                "ticket_number": ticket_number,
                "sender": sender,
                "subject": subject,
                "message": f"Reply processed for ticket {ticket_number}",
                "action": "added_to_existing_thread",
                "ai_enhanced": bool(ai_data),
                "urgency_detected": len(ai_data.get('urgency_keywords', [])) > 0 if ai_data else False,
                "sentiment": ai_data.get('sentiment_tone') if ai_data else None
            }
            
        except Exception as e:
            logger.error(f"❌ [EXISTING EMAIL] Error processing reply: {e}")
            return {
                "success": False,
                "error": str(e),
                "ticket_number": ticket_number,
                "message": f"Failed to process reply for ticket {ticket_number}"
            }


async def process_existing_email(email_data: Dict[str, Any], classification_data=None) -> Dict[str, Any]:
    """
    Process a reply to an existing ticket (standalone function)
    
    Args:
        email_data: Email data from webhook
        classification_data: AI classification results with ticket number
        
    Returns:
        Dict with processing results
    """
    try:
        # Extract ticket number from classification
        ticket_number = None
        if classification_data and hasattr(classification_data, 'EMAIL_DATA'):
            ticket_number = classification_data.EMAIL_DATA.ticket_number
        
        if not ticket_number:
            logger.error("❌ [EXISTING EMAIL] No ticket number found in classification data")
            return {
                "success": False,
                "error": "No ticket number found",
                "message": "Cannot process existing email without ticket number"
            }
        
        logger.info(f"🔄 [EXISTING EMAIL] Processing reply for ticket: {ticket_number}")
        logger.info(f"🔄 [EXISTING EMAIL] From: {email_data.get('sender')}")
        
        # Initialize Airtable service
        airtable = AirtableService()
        
        # Find existing ticket
        existing_ticket = airtable.find_ticket_by_number(ticket_number)
        if not existing_ticket:
            logger.warning(f"⚠️ [EXISTING EMAIL] Ticket {ticket_number} not found in Airtable")
            return {
                "success": False,
                "error": f"Ticket {ticket_number} not found",
                "message": f"Cannot find existing ticket {ticket_number}"
            }
        
        # Update conversation in Airtable
        updated_record = airtable.update_conversation(
            ticket_number=ticket_number,
            new_message_data=email_data,
            classification_data=classification_data
        )
        
        logger.info(f"✅ [EXISTING EMAIL] Updated conversation for ticket {ticket_number}")
        
        return {
            "success": True,
            "ticket_number": ticket_number,
            "sender": email_data.get('sender'),
            "subject": email_data.get('subject'),
            "message": f"Reply processed for ticket {ticket_number}",
            "action": "updated_existing_thread",
            "airtable_record_id": updated_record.get('id') if updated_record else None,
            "ai_enhanced": bool(classification_data)
        }
        
    except Exception as e:
        logger.error(f"❌ [EXISTING EMAIL] Error processing reply: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to process existing email: {str(e)}"
        } 