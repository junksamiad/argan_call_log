"""
AI Agents for HR Email Management System - Backend2
Base agent class and specific agents for email processing
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import List
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmailPath(str, Enum):
    """Email routing paths"""
    NEW_EMAIL = "new_email"
    EXISTING_EMAIL = "existing_email"


class TicketClassificationResponse(BaseModel):
    """Structured response from ticket classification agent"""
    ticket_number_present_in_subject: bool
    path: EmailPath
    confidence_score: float
    ticket_number_found: Optional[str] = None
    analysis_notes: Optional[str] = None


class ConversationEntry(BaseModel):
    """Single conversation entry with sender, date, content, and name"""
    sender_email: str
    sender_email_date: str
    sender_email_content: str
    sender_name: str


class ConversationParsingResponse(BaseModel):
    """Structured response from conversation parsing agent"""
    conversation_entries: List[ConversationEntry]


class BaseAIAgent(ABC):
    """Base class for all AI agents in the system"""
    
    def __init__(self, model: str = "gpt-4.1"):
        """Initialize the AI agent with OpenAI client"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        logger.info(f"🤖 [AI AGENT] Initialized {self.__class__.__name__} with model {model}")
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this specific agent"""
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Any:
        """Process input data and return structured output"""
        pass


class TicketClassificationAgent(BaseAIAgent):
    """
    AI Agent to classify emails by detecting Argan ticket numbers in subject lines
    """
    
    def __init__(self):
        super().__init__()
        self.ticket_pattern = "ARG-YYYYMMDD-NNNN"  # e.g., ARG-20250531-0001
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for ticket classification"""
        return f"""# Argan HR Ticket Classification Agent

You are an expert email classifier for Argan Consultancy HR system. Your job is to analyze email subject lines to detect the presence of Argan ticket numbers.

## Argan Ticket Number Format
- Pattern: {self.ticket_pattern}
- Examples: ARG-20250531-0001, ARG-20241215-0123, ARG-20250603-0456
- May appear with prefixes like: "Re: ARG-20250531-0001", "[ARG-20250531-0001]", "Ticket: ARG-20250531-0001"
- Case insensitive matching
- May have slight formatting variations but core pattern is ARG-[8 digits]-[4 digits]

## Classification Rules
- **NEW_EMAIL**: Subject line does NOT contain any Argan ticket number
- **EXISTING_EMAIL**: Subject line DOES contain an Argan ticket number

## Analysis Requirements
- Examine the subject line carefully for ticket number patterns
- If you find a ticket number, extract it exactly as it appears
- Provide high confidence scores only when certain
- Include brief analysis notes explaining your decision

## Output Requirements
You must respond with a JSON object that matches the TicketClassificationResponse schema exactly:
- ticket_number_present_in_subject: boolean (true/false)
- path: "new_email" or "existing_email" 
- confidence_score: float between 0.0 and 1.0
- ticket_number_found: the exact ticket number if found, null otherwise
- analysis_notes: brief explanation of your decision
"""

    async def process(self, input_data: Dict[str, Any]) -> TicketClassificationResponse:
        """
        Classify an email subject line for ticket number presence
        
        Args:
            input_data: Dict containing 'subject' field to analyze
            
        Returns:
            TicketClassificationResponse with classification results
        """
        try:
            subject = input_data.get('subject', '')
            logger.info(f"🎫 [TICKET CLASSIFIER] Analyzing subject: '{subject}'")
            
            # Prepare input for AI analysis
            user_content = f"""
EMAIL SUBJECT TO ANALYZE:
"{subject}"

Please analyze this subject line for the presence of an Argan ticket number and classify accordingly.
"""
            
            # Call OpenAI with structured output
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": self._build_system_prompt()
                    },
                    {
                        "role": "user", 
                        "content": user_content
                    }
                ],
                text_format=TicketClassificationResponse
            )
            
            result = response.output_parsed
            logger.info(f"🎫 [TICKET CLASSIFIER] Classification: {result.path}, Ticket found: {result.ticket_number_found}")
            
            return result
            
        except Exception as e:
            logger.error(f"🎫 [TICKET CLASSIFIER] Error during classification: {e}")
            # Return fallback classification
            return self._create_fallback_response(input_data.get('subject', ''), str(e))
    
    def _create_fallback_response(self, subject: str, error_msg: str) -> TicketClassificationResponse:
        """Create a fallback response when AI classification fails"""
        logger.warning(f"🎫 [TICKET CLASSIFIER] Creating fallback response due to error: {error_msg}")
        
        # Simple regex fallback for ticket detection
        import re
        ticket_pattern = r'ARG-\d{8}-\d{4}'
        match = re.search(ticket_pattern, subject.upper())
        
        has_ticket = match is not None
        ticket_found = match.group(0) if match else None
        
        return TicketClassificationResponse(
            ticket_number_present_in_subject=has_ticket,
            path=EmailPath.EXISTING_EMAIL if has_ticket else EmailPath.NEW_EMAIL,
            confidence_score=0.8 if has_ticket else 0.7,  # Regex is fairly reliable
            ticket_number_found=ticket_found,
            analysis_notes=f"Fallback regex classification due to AI error: {error_msg}"
        )


class ConversationParsingAgent(BaseAIAgent):
    """
    AI Agent for parsing email conversation threads
    
    This agent takes quoted email content and structures it into 
    individual conversation entries with sender, date, and content.
    Much more robust than regex-based parsing for handling various
    email client formats and edge cases.
    """
    
    def __init__(self):
        super().__init__()
        self.agent_name = "ConversationParsingAgent"
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for conversation parsing with structured outputs"""
        return """# Email Conversation Thread Parser

You are a specialist in parsing email conversation threads. Your job is to extract individual conversation entries from quoted email content and return them in the specified structured format.

## Your Task
1. Identify each separate conversation entry from quoted blocks
2. Extract sender email, date, and content for each entry
3. Handle various email client formats and date formats
4. Clean up content by removing quote markers while preserving structure
5. Extract FIRST NAME ONLY for sender_name, with email fallback

## Input Patterns to Look For
- "> On [date], [sender] wrote:"
- ">> On [date] [sender] wrote:" 
- Other email client quote formats

## Date Format Examples
- "3 Jun 2025, at 06:12"
- "03/06/2025 05:55 BST"
- "Mon, 5 Jun 2025 14:30:15 +0100"

## Email Address and Name Processing
Extract email and first name from these patterns:

**Name Extraction Examples:**
- "Rebecca Thompson <rebecca@company.com>" → email: "rebecca@company.com", sender_name: "Rebecca"
- "John Smith <john.doe@company.com>" → email: "john.doe@company.com", sender_name: "John"
- "Argan HR <argan-bot@arganhrconsultancy.co.uk>" → email: "argan-bot@arganhrconsultancy.co.uk", sender_name: "Argan"
- "cvrcontractsltd <cvrcontractsltd@gmail.com>" → email: "cvrcontractsltd@gmail.com", sender_name: "cvrcontractsltd@gmail.com" (no clear first name, use email)
- "john.doe@company.com" → email: "john.doe@company.com", sender_name: "john.doe@company.com" (no display name, use email)

**sender_name Logic:**
- If display name contains clear first name (like "Rebecca Thompson"), extract FIRST NAME ONLY ("Rebecca")
- If display name is unclear/corporate (like "Argan HR", "cvrcontractsltd"), use the full display name
- If display name looks like a single word that could be a first name, use it
- If no display name or unclear, use the full email address as fallback

## Content Processing Rules
- Remove leading ">" quote markers from content lines
- Preserve original message text and line breaks
- Stop content extraction at the next conversation marker
- **IMPORTANT**: Order entries by DATE chronologically (oldest first, newest/latest last)

## Chronological Ordering
- Parse all conversation entries first, then sort by actual date/time
- The OLDEST message should be FIRST in the array (index 0)
- The NEWEST/LATEST message should be LAST in the array (final index)
- This creates a proper conversation timeline from earliest to most recent

## Important Notes
- Extract exact email addresses (remove display names in angle brackets)
- For sender_name: prioritize extracting first names, fallback to email when unclear
- Preserve original date strings as found
- Be flexible with email client formatting variations
- If no conversation entries found, return empty conversation_entries array
- Always include sender_name field following the first name extraction logic"""

    async def process(self, input_data: Dict[str, Any]) -> str:
        """
        Parse quoted email content into structured conversation entries
        
        Args:
            input_data: Dict containing 'quoted_content' field to parse
            
        Returns:
            JSON string containing array of conversation entries
        """
        try:
            quoted_content = input_data.get('quoted_content', '')
            logger.info(f"🧵 [CONVERSATION AI] Parsing {len(quoted_content)} chars of quoted content...")
            
            user_prompt = f"""Please parse the following quoted email content into individual conversation entries:

{quoted_content}

Return the structured JSON array of conversation entries following the format specified."""

            # Use OpenAI Responses API for structured parsing
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=ConversationParsingResponse
            )
            
            # Extract the structured response
            parsed_response = response.output_parsed
            
            # Convert to the expected JSON format (array of conversation entries)
            import json
            conversation_array = [entry.model_dump() for entry in parsed_response.conversation_entries]
            
            logger.info(f"✅ [CONVERSATION AI] Successfully parsed {len(conversation_array)} conversation entries")
            return json.dumps(conversation_array, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ [CONVERSATION AI] Error parsing conversation: {e}")
            return "[]"  # Return empty array on error
    
    def parse_conversation_thread_sync(self, quoted_email_content: str) -> str:
        """
        Synchronous version of conversation parsing using structured outputs
        
        Args:
            quoted_email_content: The portion of email starting from first "> On ... wrote:" marker
            
        Returns:
            JSON string containing array of conversation entries
        """
        try:
            logger.info("🤖 [CONVERSATION AI] Starting structured conversation parsing...")
            
            user_prompt = f"""Please parse the following quoted email content into individual conversation entries:

{quoted_email_content}"""

            # Use OpenAI Responses API with structured outputs for guaranteed schema compliance
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=ConversationParsingResponse
            )
            
            # Extract the structured response
            parsed_response = response.output_parsed
            
            # Convert to the expected JSON format (array of conversation entries)
            import json
            conversation_array = [entry.model_dump() for entry in parsed_response.conversation_entries]
            
            logger.info(f"✅ [CONVERSATION AI] Successfully parsed {len(conversation_array)} conversation entries using structured outputs")
            return json.dumps(conversation_array, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ [CONVERSATION AI] Error in structured conversation parsing: {e}")
            return "[]"  # Return empty array on error 