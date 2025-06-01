"""
Enhanced Email Router with AI Classification and Airtable Integration
Routes emails based on AI classification and processes them accordingly
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from .classification.email_classifier_agent import EmailClassifierAgent
from .initial_email.initial_email import process_initial_email
from .existing_email.existing_email import process_existing_email
from .classification.email_classification_schema import EmailClassification
import json

logger = logging.getLogger(__name__)


class EmailRouter:
    def __init__(self):
        """Initialize the email router with AI classifier"""
        self.ai_classifier = EmailClassifierAgent()
        logger.info("📬 [EMAIL ROUTER] Initialized with AI classification")
    
    async def route_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an email based on AI classification
        
        Args:
            email_data: Email data from SendGrid webhook
            
        Returns:
            Processing result dictionary
        """
        try:
            sender = email_data.get('sender', 'Unknown')
            subject = email_data.get('subject', 'No Subject')
            
            logger.info(f"📬 [EMAIL ROUTER] Routing email from {sender} with subject: {subject}")
            
            # Step 1: AI Classification
            logger.info("🤖 [EMAIL ROUTER] Starting AI classification...")
            classification_result = await self.ai_classifier.classify_email(email_data)
            
            classification = classification_result.EMAIL_CLASSIFICATION
            confidence = classification_result.confidence_score
            
            logger.info(f"🤖 [EMAIL ROUTER] AI Classification: {classification}")
            logger.info(f"🤖 [EMAIL ROUTER] Confidence: {confidence}")
            
            # Convert to dict for compatibility with handlers
            classification_dict = self._convert_classification_to_dict(classification_result)
            
            # Step 2: Route based on classification
            if classification == EmailClassification.NEW_EMAIL:
                logger.info("🆕 [EMAIL ROUTER] → Initial email handler (new ticket)")
                return await process_initial_email(email_data, classification_dict)
                
            elif classification == EmailClassification.EXISTING_EMAIL:
                logger.info("💬 [EMAIL ROUTER] → Existing email handler (reply)")
                return await process_existing_email(email_data, classification_dict)
                
            else:
                logger.warning(f"❓ [EMAIL ROUTER] Unknown classification: {classification}")
                # Default to new email processing
                logger.info("🆕 [EMAIL ROUTER] → Defaulting to initial email handler")
                return await process_initial_email(email_data, classification_dict)
                
        except Exception as e:
            logger.error(f"❌ [EMAIL ROUTER] Error routing email: {e}")
            
            # Fallback: try to process as new email
            try:
                logger.info("🚨 [EMAIL ROUTER] Attempting fallback processing...")
                return await process_initial_email(email_data, None)
            except Exception as fallback_error:
                logger.error(f"❌ [EMAIL ROUTER] Fallback also failed: {fallback_error}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "Email routing failed completely"
                }
    
    def _convert_classification_to_dict(self, classification_result) -> Dict[str, Any]:
        """
        Convert Pydantic classification result to dictionary for handlers
        
        Args:
            classification_result: EmailClassificationResponse from AI
            
        Returns:
            Dictionary representation of the classification
        """
        try:
            # Convert the main classification
            result_dict = {
                "EMAIL_CLASSIFICATION": classification_result.EMAIL_CLASSIFICATION.value,
                "confidence_score": classification_result.confidence_score,
                "processing_timestamp": classification_result.processing_timestamp,
                "notes": classification_result.notes
            }
            
            # Convert the email data if present
            if classification_result.EMAIL_DATA:
                email_data = classification_result.EMAIL_DATA
                
                # Parse JSON list fields
                try:
                    urgency_keywords = json.loads(email_data.urgency_keywords_list) if email_data.urgency_keywords_list else []
                except:
                    urgency_keywords = []
                
                try:
                    deadline_mentions = json.loads(email_data.deadline_mentions_list) if email_data.deadline_mentions_list else []
                except:
                    deadline_mentions = []
                
                try:
                    recipients = json.loads(email_data.recipients_list) if email_data.recipients_list else []
                except:
                    recipients = []
                
                result_dict["ai_extracted_data"] = {
                    "sender_email": email_data.sender_email,
                    "sender_name": email_data.sender_name,
                    "sender_domain": email_data.sender_domain,
                    "recipients_list": recipients,
                    "subject": email_data.subject,
                    "body_text": email_data.body_text,
                    "body_html": email_data.body_html,
                    "message_id": email_data.message_id,
                    "email_date": email_data.email_date,
                    "ticket_number": email_data.ticket_number,
                    "ticket_confidence": email_data.ticket_confidence,
                    "urgency_keywords": urgency_keywords,
                    "sentiment_tone": email_data.sentiment_tone,
                    "deadline_mentions": deadline_mentions,
                    "ai_summary": email_data.ai_summary,
                    "hr_category": email_data.hr_category,
                    "dkim_status": email_data.dkim_status,
                    "spf_status": email_data.spf_status,
                    "ai_confidence": classification_result.confidence_score
                }
            
            return result_dict
            
        except Exception as e:
            logger.error(f"🤖 [EMAIL ROUTER] Error converting classification: {e}")
            return {
                "EMAIL_CLASSIFICATION": "NEW_EMAIL",
                "confidence_score": 0.1,
                "notes": f"Conversion error: {e}"
            }


# Global router instance
email_router = EmailRouter()


async def route_email_async(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async function to route an email - used by the main server
    
    Args:
        email_data: Email data from SendGrid
        
    Returns:
        Processing result
    """
    return await email_router.route_email(email_data) 