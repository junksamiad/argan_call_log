"""
Email Classifier Agent
Uses OpenAI's GPT-4.1 with structured outputs to classify emails and extract data
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI
from .email_classification_schema import EmailClassificationResponse

logger = logging.getLogger(__name__)


class EmailClassifierAgent:
    def __init__(self):
        """Initialize the AI classifier with OpenAI client"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1"  # Updated to use gpt-4.1 as requested
        
        # Ticket pattern for prompt context
        self.ticket_pattern = "ARG-YYYYMMDD-XXXX"  # e.g., ARG-20250531-0003
        
    def _build_classification_prompt(self) -> str:
        """Build the system prompt for email classification"""
        return f"""# Email Classification Agent

You are an expert HR email classification system for Argan Consultancy. Your job is to analyze incoming emails and:

1. **CLASSIFY** the email as either NEW_EMAIL or EXISTING_EMAIL
2. **EXTRACT** all relevant data and metadata in a structured format

## Classification Rules

**NEW_EMAIL**: Email does NOT contain any existing ticket number reference
**EXISTING_EMAIL**: Email DOES contain a ticket number reference in subject or body

## Ticket Number Format
- Pattern: {self.ticket_pattern}
- Examples: ARG-20250531-0001, ARG-20250531-0123, ARG-20241215-0456
- May appear as: [ARG-20250531-0001], Ticket: ARG-20250531-0001, Re: ARG-20250531-0001, etc.
- Case insensitive matching
- May have slight formatting variations

## Context Awareness
- Look for ticket numbers in subject line AND email body
- Consider context - is this genuinely a reply to an existing ticket?
- Distinguish between real replies vs coincidental number matches
- Check for "Re:", "Reply:", "Fwd:" patterns indicating replies

## Data Extraction Requirements
- Extract ALL available contact information
- Parse email metadata thoroughly
- Identify urgency indicators (urgent, ASAP, emergency, deadline words)
- Detect deadline mentions and time-sensitive language
- Extract attachment information
- Analyze email structure and threading depth
- Assess sentiment and tone
- Flatten complex data into simple key-value pairs for easier parsing

## Output Quality
- Be thorough in data extraction
- Use high confidence scores only when certain
- Include context around ticket number findings
- Note any unusual patterns or concerns

You must respond with valid JSON that matches the EmailClassificationResponse schema exactly.
"""

    async def classify_email(self, email_data: Dict[str, Any]) -> EmailClassificationResponse:
        """
        Classify an email and extract structured data
        
        Args:
            email_data: Raw email data from SendGrid
            
        Returns:
            EmailClassificationResponse with classification and extracted data
        """
        try:
            logger.info(f"🤖 [AI CLASSIFIER] Starting classification for email from {email_data.get('sender')}")
            
            # Prepare email content for AI analysis
            email_content = self._prepare_email_content(email_data)
            
            # Call OpenAI with structured output (sync version)
            response = self._call_openai_classifier_sync(email_content)
            
            logger.info(f"🤖 [AI CLASSIFIER] Classification complete: {response.EMAIL_CLASSIFICATION}")
            
            return response
            
        except Exception as e:
            logger.error(f"🤖 [AI CLASSIFIER] Error during classification: {e}")
            # Return fallback classification
            return self._create_fallback_response(email_data, str(e))
    
    def _prepare_email_content(self, email_data: Dict[str, Any]) -> str:
        """Prepare email content for AI analysis"""
        return f"""
EMAIL TO CLASSIFY:

SUBJECT: {email_data.get('subject', 'No Subject')}

FROM: {email_data.get('sender', 'Unknown')}

TO: {email_data.get('recipients', ['Unknown'])}

CC: {email_data.get('cc', [])}

MESSAGE ID: {email_data.get('message_id', 'Unknown')}

EMAIL DATE: {email_data.get('email_date', 'Unknown')}

BODY TEXT:
{email_data.get('body_text', 'No text content')}

BODY HTML:
{email_data.get('body_html', 'No HTML content')}

TECHNICAL METADATA:
- DKIM: {email_data.get('dkim', 'Unknown')}
- SPF: {email_data.get('spf', 'Unknown')}
- Sender IP: {email_data.get('sender_ip', 'Unknown')}
- Envelope: {email_data.get('envelope', 'Unknown')}

ATTACHMENTS: {email_data.get('attachments', 'None')}
"""
    
    def _call_openai_classifier_sync(self, email_content: str) -> EmailClassificationResponse:
        """Call OpenAI API with structured output using Responses API (synchronous)"""
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": self._build_classification_prompt()
                    },
                    {
                        "role": "user", 
                        "content": email_content
                    }
                ],
                text_format=EmailClassificationResponse
            )
            
            return response.output_parsed
            
        except Exception as e:
            logger.error(f"🤖 [AI CLASSIFIER] OpenAI API error: {e}")
            raise

    async def _call_openai_classifier(self, email_content: str) -> EmailClassificationResponse:
        """Call OpenAI API with structured output using Responses API"""
        # Use sync version for now since async was hanging
        return self._call_openai_classifier_sync(email_content)
    
    def _create_fallback_response(self, email_data: Dict[str, Any], error_msg: str) -> EmailClassificationResponse:
        """Create a fallback response when AI classification fails"""
        logger.warning(f"🤖 [AI CLASSIFIER] Creating fallback response due to error: {error_msg}")
        
        # Simple fallback logic - check for basic ticket patterns
        subject = email_data.get('subject', '').upper()
        body = email_data.get('body_text', '').upper()
        
        # Basic regex fallback for ticket detection
        import re
        ticket_pattern = r'ARG-\d{8}-\d{4}'
        
        has_ticket = bool(re.search(ticket_pattern, subject) or re.search(ticket_pattern, body))
        
        from .email_classification_schema import EmailClassification, FlattenedEmailData
        
        return EmailClassificationResponse(
            EMAIL_CLASSIFICATION=EmailClassification.EXISTING_EMAIL if has_ticket else EmailClassification.NEW_EMAIL,
            EMAIL_DATA=FlattenedEmailData(
                sender_email=email_data.get('sender', 'unknown@unknown.com'),
                sender_name=email_data.get('sender_name'),
                sender_domain=email_data.get('sender', '').split('@')[-1] if '@' in email_data.get('sender', '') else None,
                recipients_list=json.dumps(email_data.get('recipients', [])),
                subject=email_data.get('subject', 'No Subject'),
                body_text=email_data.get('body_text', ''),
                body_html=email_data.get('body_html'),
                message_id=email_data.get('message_id', ''),
                email_date=str(email_data.get('email_date', datetime.utcnow())),
                ticket_number=None,  # Fallback doesn't extract ticket
                ticket_confidence=0.0,
                dkim_status=email_data.get('dkim'),
                spf_status=email_data.get('spf')
            ),
            processing_timestamp=datetime.utcnow().isoformat(),
            confidence_score=0.1,  # Low confidence for fallback
            notes=f"Fallback classification due to error: {error_msg}"
        ) 