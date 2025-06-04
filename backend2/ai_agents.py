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
from pydantic import BaseModel, Field
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
    sender_name: str
    sender_email_date: str = Field(
        description="Date and time when the sender's email was sent in DD/MM/YYYY HH:MM BST format",
        examples=["03/06/2025 17:37 BST", "15/12/2024 09:30 BST"]
    )
    sender_content: str
    chronological_order: int


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


class ConversationParsingAgent1(BaseAIAgent):
    """
    AI Agent for parsing email conversation threads
    
    This agent takes quoted email content and structures it into 
    individual conversation entries with sender, date, and content.
    Much more robust than regex-based parsing for handling various
    email client formats and edge cases.
    """
    
    def __init__(self):
        super().__init__()
        self.agent_name = "ConversationParsingAgent1"
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for conversation parsing with full business context"""
        return """Context: You are an ai agent employed by a HR consultancy company called Argan HR Consultancy. They have built a complex automated email system that processes email threads that are passed to it, and extracts the back and forth conversations on the thread into a single conversational json of entries with attributes. 

Generally, the story works like this. Argan's client emails with a query, the query gets forwarded to the system and it provides a ticket number and an auto reply to the client, CC'ing in advice@arganhrconsultancy.co.uk in the process. The Argan HR adviser and their client (or other stakeholders in the conversation) will have a back and forth conversation (outside of our system). Every time the client replies to the Argan advisor, this response (which may or may not include the other parts of the conversation in the thread) gets forwarded to our system.

Task: You will be passed the email forwarded into our system. In the email you may see a 'source of truth original query' from the client, and then multiple other conversation entries that followed after. You must extract the conversation entries (always ignoring the source of truth query) and produce a structured output as per the response output json schema. Also ignore any queries that pertain to be part of the auto-reply response. The schema will show you what to include. Your final response should order all the conversation entries in chronological order. If you cannot find a timestamp for a certain email entry, then set it's time stamp to be the same as the previous entry you have processed in the chronology. Once you have your final chronological list of entries, number them accordingly with the lowest number being the earliest entry."""

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
            
            user_prompt = f"""{quoted_content}"""

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
    
    def parse_conversation_thread_sync(self, full_email_content: str, existing_conversation_history: str = "") -> str:
        """
        Synchronous version of conversation parsing using structured outputs
        
        Args:
            full_email_content: The complete email content (not preprocessed)
            existing_conversation_history: Existing conversation history from DB in JSON format
            
        Returns:
            JSON string containing array of conversation entries
        """
        try:
            logger.info("🤖 [CONVERSATION AI] Starting structured conversation parsing...")
            logger.info(f"📧 [CONVERSATION AI] Processing {len(full_email_content)} characters of full email content")
            
            # Check if we have existing conversation history
            if existing_conversation_history and existing_conversation_history.strip():
                logger.info(f"📋 [CONVERSATION AI] Found existing conversation history: {len(existing_conversation_history)} characters")
                task_mode = "Task 1 only (email only - ignoring DB entries)"
            else:
                logger.info("📋 [CONVERSATION AI] No existing conversation history - processing email only")
                task_mode = "Task 1 only (email only)"
            
            # ==================== DEBUGGING: FULL INPUT ANALYSIS ====================
            logger.info("=" * 100)
            logger.info("🔍 [AI DEBUG] FULL EMAIL CONTENT BEING SENT TO AI:")
            logger.info("=" * 100)
            logger.info(f"📏 Total content length: {len(full_email_content)} characters")
            logger.info(f"📄 Line count: {len(full_email_content.splitlines()) if full_email_content else 0}")
            logger.info(f"🎯 Task mode: {task_mode}")
            logger.info("")
            logger.info("📄 FULL EMAIL CONTENT:")
            logger.info("-" * 50)
            if full_email_content:
                # Split into lines for better readability
                lines = full_email_content.splitlines()
                for i, line in enumerate(lines, 1):
                    logger.info(f"{i:3d}: {line}")
            else:
                logger.info("(EMPTY OR NONE)")
            logger.info("-" * 50)
            logger.info("=" * 100)
            # ========================================================================
            
            # Prepare the user prompt - only use email content, ignore existing conversation history
            user_prompt = full_email_content

            # ==================== DEBUGGING: COMPLETE PROMPT ANALYSIS ====================
            logger.info("=" * 100)
            logger.info("🔍 [AI DEBUG] COMPLETE USER PROMPT BEING SENT TO AI AGENT:")
            logger.info("=" * 100)
            logger.info(f"📏 Total prompt length: {len(user_prompt)} characters")
            logger.info(f"📄 Line count: {len(user_prompt.splitlines()) if user_prompt else 0}")
            logger.info("")
            logger.info("📄 COMPLETE USER PROMPT:")
            logger.info("-" * 50)
            if user_prompt:
                # Split into lines for better readability
                lines = user_prompt.splitlines()
                for i, line in enumerate(lines, 1):
                    logger.info(f"{i:3d}: {line}")
            else:
                logger.info("(EMPTY OR NONE)")
            logger.info("-" * 50)
            logger.info("=" * 100)
            # ========================================================================

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
            
            # Apply date fallback logic before converting to JSON
            processed_entries = self._apply_date_fallback_logic(parsed_response.conversation_entries)
            
            # Convert to the expected JSON format (array of conversation entries)
            import json
            conversation_array = [entry.model_dump() for entry in processed_entries]
            
            logger.info(f"✅ [CONVERSATION AI] Successfully parsed {len(conversation_array)} conversation entries using structured outputs")
            return json.dumps(conversation_array, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ [CONVERSATION AI] Error in structured conversation parsing: {e}")
            return "[]"  # Return empty array on error
    
    def _apply_date_fallback_logic(self, entries: List[ConversationEntry]) -> List[ConversationEntry]:
        """
        Apply +5 second fallback logic for missing dates to maintain chronological order
        
        Args:
            entries: List of conversation entries from AI parsing
            
        Returns:
            List of conversation entries with date fallbacks applied
        """
        from datetime import datetime, timedelta
        import re
        
        try:
            logger.info(f"📅 [DATE FALLBACK] Processing {len(entries)} entries for date consistency...")
            
            processed_entries = []
            
            for i, entry in enumerate(entries):
                # Check if date is missing or empty
                if not entry.sender_email_date or entry.sender_email_date.strip() == "":
                    if i == 0:
                        # First entry with no date - use current timestamp as fallback
                        fallback_date = datetime.now().strftime("%d/%m/%Y %H:%M BST")
                        entry.sender_email_date = fallback_date
                        logger.info(f"📅 [DATE FALLBACK] Entry {i+1}: Used current timestamp as fallback")
                    else:
                        # Use previous entry's date + 5 seconds
                        prev_entry = processed_entries[i-1]
                        fallback_date = self._add_seconds_to_date(prev_entry.sender_email_date, 5)
                        entry.sender_email_date = fallback_date
                        logger.info(f"📅 [DATE FALLBACK] Entry {i+1}: Used previous date + 5 seconds")
                else:
                    logger.info(f"📅 [DATE FALLBACK] Entry {i+1}: Date present, no fallback needed")
                
                processed_entries.append(entry)
            
            logger.info(f"✅ [DATE FALLBACK] Successfully processed all {len(processed_entries)} entries")
            return processed_entries
            
        except Exception as e:
            logger.error(f"❌ [DATE FALLBACK] Error applying date fallback logic: {e}")
            return entries  # Return original entries on error
    
    def _add_seconds_to_date(self, date_string: str, seconds_to_add: int) -> str:
        """
        Add seconds to a date string in various formats
        
        Args:
            date_string: Original date string
            seconds_to_add: Number of seconds to add
            
        Returns:
            New date string with added seconds
        """
        from datetime import datetime, timedelta
        import re
        
        try:
            # Try to parse various date formats and add seconds
            date_formats = [
                "%d/%m/%Y %H:%M BST",      # "03/06/2025 17:37 BST"
                "%d/%m/%Y %H:%M",          # "03/06/2025 17:37"
                "%d %b %Y, at %H:%M",      # "3 Jun 2025, at 17:44"
                "%a, %d %b %Y %H:%M:%S %z", # "Tue, 3 Jun 2025 17:36:45 +0100"
                "%Y-%m-%d %H:%M:%S",       # "2025-06-03 17:37:00"
                "%Y-%m-%dT%H:%M:%S",       # "2025-06-03T17:37:00"
            ]
            
            parsed_date = None
            original_format = None
            
            # Try to parse the date with various formats
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string.strip(), date_format)
                    original_format = date_format
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                # If parsing fails, append "+Xs" to original string
                return f"{date_string} +{seconds_to_add}s"
            
            # Add seconds and format back to original format
            new_date = parsed_date + timedelta(seconds=seconds_to_add)
            
            # Return in the same format as input
            return new_date.strftime(original_format)
            
        except Exception as e:
            logger.warning(f"⚠️ [DATE FALLBACK] Could not parse date '{date_string}': {e}")
            # Fallback: append "+Xs" to original string
            return f"{date_string} +{seconds_to_add}s"


class ConversationParsingAgent2(BaseAIAgent):
    """
    AI Agent for parsing email conversation threads - Version 2
    
    This agent takes quoted email content and structures it into 
    individual conversation entries with sender, date, and content.
    Much more robust than regex-based parsing for handling various
    email client formats and edge cases.
    """
    
    def __init__(self):
        super().__init__()
        self.agent_name = "ConversationParsingAgent2"
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt for conversation parsing with full business context"""
        return """Context: You are an ai agent employed by a HR consultancy company called Argan HR Consultancy. They have built a complex automated email system that processes email threads that are passed to it, and extracts the back and forth conversations on the thread into a single conversational json of entries with attributes.   A previous agent (Agent 1) has parsed all the conversation entries in an email thread, and stored them in a db as a single conversational JSON of entries with attributes (ie the EXISTING JSON).  But another email has now just arrived into the system. Agent 1 has just parsed this new email, extracted the conversation entries from it, and constructed another json (ie the NEW JSON).  Your task is to analyse both JSON (the existing JSON and the new JSON), remove any duplicate conversation entries (or what appear to be duplicate conversation entries) and create a single final JSON in chronological order, as per your response output json schema. 

If you cannot find a timestamp for a certain email entry, then set it's time stamp to be the same as the previous entry you have processed in the chronology. Once you have your final chronological list of entries, number them accordingly with the lowest number being the earliest entry.  A source of truth rule of thumb is that any unique entries in the NEW JSON should always follow the entries in the EXISTING JSON."""
    
    async def process(self, input_data: Dict[str, Any]) -> str:
        """
        Required abstract method - not used for Agent 2, we use parse_conversation_thread_sync instead
        
        Args:
            input_data: Dict containing input data (not used)
            
        Returns:
            Empty JSON array
        """
        logger.info("⚠️ [CONVERSATION AI 2] process() method called - this agent uses parse_conversation_thread_sync() instead")
        return "[]"
    
    def parse_conversation_thread_sync(self, full_email_content: str, existing_conversation_history: str = "") -> str:
        """
        Synchronous version of conversation parsing using structured outputs
        
        Args:
            full_email_content: The complete email content (not preprocessed)
            existing_conversation_history: Existing conversation history from DB in JSON format
            
        Returns:
            JSON string containing array of conversation entries
        """
        try:
            logger.info("🤖 [CONVERSATION AI] Starting structured conversation parsing...")
            logger.info(f"📧 [CONVERSATION AI] Processing {len(full_email_content)} characters of full email content")
            
            # Check if we have existing conversation history
            if existing_conversation_history and existing_conversation_history.strip():
                logger.info(f"📋 [CONVERSATION AI] Found existing conversation history: {len(existing_conversation_history)} characters")
                task_mode = "Task 1 only (email only - ignoring DB entries)"
            else:
                logger.info("📋 [CONVERSATION AI] No existing conversation history - processing email only")
                task_mode = "Task 1 only (email only)"
            
            # ==================== DEBUGGING: FULL INPUT ANALYSIS ====================
            logger.info("=" * 100)
            logger.info("🔍 [AI DEBUG] FULL EMAIL CONTENT BEING SENT TO AI:")
            logger.info("=" * 100)
            logger.info(f"📏 Total content length: {len(full_email_content)} characters")
            logger.info(f"📄 Line count: {len(full_email_content.splitlines()) if full_email_content else 0}")
            logger.info(f"🎯 Task mode: {task_mode}")
            logger.info("")
            logger.info("📄 FULL EMAIL CONTENT:")
            logger.info("-" * 50)
            if full_email_content:
                # Split into lines for better readability
                lines = full_email_content.splitlines()
                for i, line in enumerate(lines, 1):
                    logger.info(f"{i:3d}: {line}")
            else:
                logger.info("(EMPTY OR NONE)")
            logger.info("-" * 50)
            logger.info("=" * 100)
            # ========================================================================
            
            # Prepare the user prompt - only use email content, ignore existing conversation history
            user_prompt = full_email_content

            # ==================== DEBUGGING: COMPLETE PROMPT ANALYSIS ====================
            logger.info("=" * 100)
            logger.info("🔍 [AI DEBUG] COMPLETE USER PROMPT BEING SENT TO AI AGENT:")
            logger.info("=" * 100)
            logger.info(f"📏 Total prompt length: {len(user_prompt)} characters")
            logger.info(f"📄 Line count: {len(user_prompt.splitlines()) if user_prompt else 0}")
            logger.info("")
            logger.info("📄 COMPLETE USER PROMPT:")
            logger.info("-" * 50)
            if user_prompt:
                # Split into lines for better readability
                lines = user_prompt.splitlines()
                for i, line in enumerate(lines, 1):
                    logger.info(f"{i:3d}: {line}")
            else:
                logger.info("(EMPTY OR NONE)")
            logger.info("-" * 50)
            logger.info("=" * 100)
            # ========================================================================
            
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
            
            # Apply date fallback logic before converting to JSON
            processed_entries = self._apply_date_fallback_logic(parsed_response.conversation_entries)
            
            # Convert to the expected JSON format (array of conversation entries)
            import json
            conversation_array = [entry.model_dump() for entry in processed_entries]
            
            logger.info(f"✅ [CONVERSATION AI] Successfully parsed {len(conversation_array)} conversation entries using structured outputs")
            return json.dumps(conversation_array, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"❌ [CONVERSATION AI] Error in structured conversation parsing: {e}")
            return "[]"  # Return empty array on error
    
    def _apply_date_fallback_logic(self, entries: List[ConversationEntry]) -> List[ConversationEntry]:
        """
        Apply +5 second fallback logic for missing dates to maintain chronological order
        
        Args:
            entries: List of conversation entries from AI parsing
            
        Returns:
            List of conversation entries with date fallbacks applied
        """
        from datetime import datetime, timedelta
        import re
        
        try:
            logger.info(f"📅 [DATE FALLBACK] Processing {len(entries)} entries for date consistency...")
            
            processed_entries = []
            
            for i, entry in enumerate(entries):
                # Check if date is missing or empty
                if not entry.sender_email_date or entry.sender_email_date.strip() == "":
                    if i == 0:
                        # First entry with no date - use current timestamp as fallback
                        fallback_date = datetime.now().strftime("%d/%m/%Y %H:%M BST")
                        entry.sender_email_date = fallback_date
                        logger.info(f"📅 [DATE FALLBACK] Entry {i+1}: Used current timestamp as fallback")
                    else:
                        # Use previous entry's date + 5 seconds
                        prev_entry = processed_entries[i-1]
                        fallback_date = self._add_seconds_to_date(prev_entry.sender_email_date, 5)
                        entry.sender_email_date = fallback_date
                        logger.info(f"📅 [DATE FALLBACK] Entry {i+1}: Used previous date + 5 seconds")
                else:
                    logger.info(f"📅 [DATE FALLBACK] Entry {i+1}: Date present, no fallback needed")
                
                processed_entries.append(entry)
            
            logger.info(f"✅ [DATE FALLBACK] Successfully processed all {len(processed_entries)} entries")
            return processed_entries
            
        except Exception as e:
            logger.error(f"❌ [DATE FALLBACK] Error applying date fallback logic: {e}")
            return entries  # Return original entries on error
    
    def _add_seconds_to_date(self, date_string: str, seconds_to_add: int) -> str:
        """
        Add seconds to a date string in various formats
        
        Args:
            date_string: Original date string
            seconds_to_add: Number of seconds to add
            
        Returns:
            New date string with added seconds
        """
        from datetime import datetime, timedelta
        import re
        
        try:
            # Try to parse various date formats and add seconds
            date_formats = [
                "%d/%m/%Y %H:%M BST",      # "03/06/2025 17:37 BST"
                "%d/%m/%Y %H:%M",          # "03/06/2025 17:37"
                "%d %b %Y, at %H:%M",      # "3 Jun 2025, at 17:44"
                "%a, %d %b %Y %H:%M:%S %z", # "Tue, 3 Jun 2025 17:36:45 +0100"
                "%Y-%m-%d %H:%M:%S",       # "2025-06-03 17:37:00"
                "%Y-%m-%dT%H:%M:%S",       # "2025-06-03T17:37:00"
            ]
            
            parsed_date = None
            original_format = None
            
            # Try to parse the date with various formats
            for date_format in date_formats:
                try:
                    parsed_date = datetime.strptime(date_string.strip(), date_format)
                    original_format = date_format
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                # If parsing fails, append "+Xs" to original string
                return f"{date_string} +{seconds_to_add}s"
            
            # Add seconds and format back to original format
            new_date = parsed_date + timedelta(seconds=seconds_to_add)
            
            # Return in the same format as input
            return new_date.strftime(original_format)
            
        except Exception as e:
            logger.warning(f"⚠️ [DATE FALLBACK] Could not parse date '{date_string}': {e}")
            # Fallback: append "+Xs" to original string
            return f"{date_string} +{seconds_to_add}s"