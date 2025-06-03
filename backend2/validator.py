"""
Email Validator for HR Email Management System - Backend2
Handles AI classification and email routing validation
"""

import logging
from typing import Dict, Any
from .ai_agents import TicketClassificationAgent, TicketClassificationResponse

logger = logging.getLogger(__name__)


class EmailValidator:
    """
    Validates and classifies incoming emails using AI agents
    """
    
    def __init__(self):
        """Initialize the validator with AI agents"""
        self.ticket_classifier = TicketClassificationAgent()
        logger.info("✅ [EMAIL VALIDATOR] Initialized with AI agents")
    
    async def classify_email_path(self, context_object: Dict[str, Any]) -> TicketClassificationResponse:
        """
        Classify an email to determine its processing path
        
        Args:
            context_object: Flattened context object containing raw email payload
            
        Returns:
            TicketClassificationResponse with classification results
        """
        try:
            logger.info("🔍 [EMAIL VALIDATOR] Starting email path classification")
            
            # Extract subject from context object for classification
            subject = context_object.get('subject', '')
            logger.info(f"🔍 [EMAIL VALIDATOR] Subject to classify: '{subject}'")
            
            # Use AI classifier to analyze subject line
            classifier_input = {'subject': subject}
            classifier_response = await self.ticket_classifier.process(classifier_input)
            
            logger.info(f"🔍 [EMAIL VALIDATOR] Classification complete:")
            logger.info(f"   📋 Path: {classifier_response.path}")
            logger.info(f"   🎫 Ticket found: {classifier_response.ticket_number_found}")
            logger.info(f"   📊 Confidence: {classifier_response.confidence_score}")
            logger.info(f"   🧠 AI Reasoning: {classifier_response.analysis_notes}")
            
            return classifier_response
            
        except Exception as e:
            logger.error(f"❌ [EMAIL VALIDATOR] Error during classification: {e}")
            
            # Create fallback response
            from .ai_agents import EmailPath
            return TicketClassificationResponse(
                ticket_number_present_in_subject=False,
                path=EmailPath.NEW_EMAIL,
                confidence_score=0.1,
                ticket_number_found=None,
                analysis_notes=f"Validator error, defaulting to new_email: {str(e)}"
            )


# Global validator instance
email_validator = EmailValidator()


async def validate_email_path(context_object: Dict[str, Any]) -> TicketClassificationResponse:
    """
    Convenience function to validate email path using the global validator
    
    Args:
        context_object: Flattened context object containing raw email payload
        
    Returns:
        TicketClassificationResponse with classification results
    """
    return await email_validator.classify_email_path(context_object) 