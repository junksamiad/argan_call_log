"""
Database module for HR Email Management System - Backend2
Handles email ticket storage and retrieval using Airtable
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pyairtable import Api, Table
from pyairtable.formulas import match
from pydantic import BaseModel
from openai import OpenAI

logger = logging.getLogger(__name__)

# Airtable configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "argan_call_log"

# Initialize Airtable connection
api = Api(AIRTABLE_API_KEY)
table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

# Initialize OpenAI client for name extraction
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class SenderNameExtractionResponse(BaseModel):
    """Pydantic model for structured sender name extraction output"""
    sender_name: Optional[str] = None
    sender_first_name: Optional[str] = None
    sender_last_name: Optional[str] = None
    confidence: float = 0.0
    notes: Optional[str] = None


class SenderNameExtractor:
    """Simple AI agent for extracting sender names from email content"""
    
    def __init__(self):
        self.model = "gpt-4.1"  # Using the full model for better accuracy
    
    def extract_sender_name(self, email_content: str) -> SenderNameExtractionResponse:
        """
        Extract sender name from email content using AI
        
        Args:
            email_content: Email body text to analyze
            
        Returns:
            SenderNameExtractionResponse with extracted name or None
        """
        try:
            logger.info("🤖 [NAME EXTRACTOR] Analyzing email content for sender name...")
            
            system_prompt = """# Sender Name Extraction Agent

You are a specialist at extracting sender names from email content. Your job is to analyze email text and identify if the sender has included their name in the message.

## What to Look For:
- Names in email signatures, especially after "Best regards", "Sincerely", "Thanks", etc.
- Names that appear on separate lines after closing phrases
- Names followed by job titles or company information
- Names in introductions (e.g., "Hi, this is Mike calling about...")
- Names that appear to be the person signing off the email

## What NOT to Extract:
- Company names alone (e.g., "TechFlow Solutions Ltd")
- Generic titles without names (Manager, Director, etc.)
- Email addresses
- Phone numbers
- Names that appear to be other people being mentioned in the content

## Name Component Extraction:
- **sender_name**: Full name as it appears (e.g., "Rebecca Thompson")
- **sender_first_name**: First name only (e.g., "Rebecca") 
- **sender_last_name**: Last name only (e.g., "Thompson")
- If only first name found, leave last name as null
- If only last name found, leave first name as null

## Guidelines:
- Look carefully at the END of the email for signatures
- Names often appear after "Best regards,", "Sincerely,", "Thanks," etc.
- If you see a person's name followed by title/company info, extract the person's name
- Split names into first and last components when possible
- Set confidence to 1.0 if you find a clear signature, 0.8 for probable names, 0.0 if uncertain
- If no clear name found, return all fields as null

## Examples:
- "Thanks for your help.\n\nBest regards,\nJohn Smith" → sender_name: "John Smith", first: "John", last: "Smith"
- "Best regards,\n\nRebecca Thompson\nOperations Director" → sender_name: "Rebecca Thompson", first: "Rebecca", last: "Thompson"
- "Hi there, this is Sarah from ABC Corp..." → sender_name: "Sarah", first: "Sarah", last: null
- "Please contact our manager for assistance." → all null (no sender name)
"""

            user_prompt = f"""Analyze this email content and extract the sender's name.

IMPORTANT: Pay special attention to the END of the email where signatures typically appear.

EMAIL CONTENT:
{email_content}

Focus on finding:
- Names after "Best regards,", "Sincerely,", "Thanks," etc.
- Names on separate lines after closing phrases
- Names followed by titles or company information

Extract the sender's name if clearly identifiable, otherwise return null."""

            response = openai_client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=SenderNameExtractionResponse
            )
            
            result = response.output_parsed
            
            if result.sender_name:
                logger.info(f"✅ [NAME EXTRACTOR] Found sender name: '{result.sender_name}' (confidence: {result.confidence})")
            else:
                logger.info(f"ℹ️ [NAME EXTRACTOR] No sender name found in email content")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ [NAME EXTRACTOR] Error extracting sender name: {e}")
            return SenderNameExtractionResponse(
                sender_name=None,
                confidence=0.0,
                notes=f"Extraction failed: {str(e)}"
            )


# Initialize name extractor
name_extractor = SenderNameExtractor()

def init_database():
    """
    Initialize the Airtable connection and verify table access
    """
    try:
        logger.info("📊 [AIRTABLE] Initializing Airtable connection...")
        
        # Test connection by getting table schema
        schema = table.schema()
        logger.info(f"✅ [AIRTABLE] Connected to table '{TABLE_NAME}' successfully")
        logger.info(f"📋 [AIRTABLE] Table has {len(schema.fields)} fields")
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error connecting to Airtable: {e}")
        logger.error(f"❌ [AIRTABLE] Check your AIRTABLE_API_KEY and AIRTABLE_BASE_ID in .env")
        raise


def extract_email_data_from_context(context_object: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract email data from context object for database storage
    
    Args:
        context_object: Flattened context object from main.py
        
    Returns:
        Dictionary with extracted data ready for database insertion
    """
    try:
        logger.info("📦 [DATABASE] Extracting email data from context...")
        
        # Extract basic fields
        extracted_data = {
            # Ticket tracking
            'ticket_number': context_object.get('ticket_number', ''),
            'status': 'new',  # Always 'new' for new emails
            'created_at': context_object.get('received_timestamp', datetime.utcnow().isoformat()),
            
            # Email content
            'subject': context_object.get('subject', ''),
            'email_body': extract_email_body(context_object),
            'original_sender': extract_original_sender(context_object),
            
            # Technical fields
            'message_id': extract_message_id_for_db(context_object),
            'raw_headers': extract_conversation_headers(context_object),
            
            # Security fields
            'spf_result': context_object.get('spf', ''),
            'dkim_result': context_object.get('dkim', ''),
            
            # Attachment scaffolding
            'has_attachments': int(context_object.get('attachments', '0')) > 0,
            'attachment_count': int(context_object.get('attachments', '0')),
            'attachment_info': '{}',  # Empty JSON for now
            
            # Auto-reply tracking
            'initial_auto_reply_sent': False,  # Will be updated after auto-reply is sent
            
            # Sender name components (extracted from AI parsing)
            'sender_first_name': '',  # Will be populated during conversation building
            'sender_last_name': '',   # Will be populated during conversation building
            
            # Conversation tracking - get name components from conversation building
            'initial_conversation_query': '',  # Will be set below
            'conversation_history': '[]'  # Empty array for new emails
        }
        
        # Build conversation query and get name components
        conversation_json, first_name, last_name = build_initial_conversation_query(context_object)
        extracted_data['initial_conversation_query'] = conversation_json
        extracted_data['sender_first_name'] = first_name
        extracted_data['sender_last_name'] = last_name
        
        logger.info("📦 [AIRTABLE] Email data extracted successfully")
        logger.info(f"📦 [AIRTABLE] Ticket: {extracted_data['ticket_number']}")
        logger.info(f"📦 [AIRTABLE] Original sender: {extracted_data['original_sender']}")
        logger.info(f"📦 [AIRTABLE] Attachments: {extracted_data['attachment_count']}")
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error extracting email data: {e}")
        raise


def extract_email_body(context_object: Dict[str, Any]) -> str:
    """
    Extract email body content using bulletproof parsing strategy
    
    Strategy:
    1. Always check 'text' field first (plain text)
    2. If text is empty/missing, fall back to 'html' field
    3. If both are empty, return empty string
    
    Args:
        context_object: Context object containing email payload
        
    Returns:
        Email body content as string
    """
    try:
        # Step 1: Check for plain text field first
        body_plain = context_object.get("text", "").strip()
        
        if body_plain:
            logger.info(f"📄 [EMAIL BODY] Using plain text field ({len(body_plain)} chars)")
            return body_plain
        
        # Step 2: Fall back to HTML field if text is empty/missing
        body_html = context_object.get("html", "").strip()
        
        if body_html:
            logger.info(f"📄 [EMAIL BODY] Using HTML field ({len(body_html)} chars) - text was empty")
            # TODO: Future enhancement - strip HTML tags if needed
            return body_html
        
        # Step 3: Both fields are empty - handle edge case
        logger.warning("⚠️ [EMAIL BODY] Both text and html fields are empty")
        return ""
        
    except Exception as e:
        logger.error(f"❌ [EMAIL BODY] Error extracting body: {e}")
        # Fallback to whatever we can get
        return context_object.get("text", context_object.get("html", ""))


def extract_original_sender(context_object: Dict[str, Any]) -> str:
    """
    Extract the original sender from forwarded email headers
    
    Args:
        context_object: Context object containing headers
        
    Returns:
        Original sender email address
    """
    try:
        # Use the utility function from utils.py
        try:
            from .utils import extract_original_sender_from_forwarded_email
        except ImportError:
            # Handle direct execution case
            from utils import extract_original_sender_from_forwarded_email
        headers = context_object.get('headers', '')
        
        original_sender = extract_original_sender_from_forwarded_email(headers)
        logger.info(f"📧 [AIRTABLE] Extracted original sender: {original_sender}")
        
        return original_sender
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error extracting original sender: {e}")
        return context_object.get('from', 'unknown@unknown.com')


def extract_message_id_for_db(context_object: Dict[str, Any]) -> str:
    """
    Extract Message-ID for database storage
    
    Args:
        context_object: Context object containing headers
        
    Returns:
        Message-ID string
    """
    try:
        try:
            from .utils import extract_message_id_from_headers
        except ImportError:
            from utils import extract_message_id_from_headers
        headers = context_object.get('headers', '')
        
        message_id = extract_message_id_from_headers(headers)
        return message_id
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error extracting Message-ID: {e}")
        return "unknown"


def extract_conversation_headers(context_object: Dict[str, Any]) -> str:
    """
    Extract headers that link conversations (Message-ID, In-Reply-To, References)
    
    Args:
        context_object: Context object containing headers
        
    Returns:
        Relevant headers as string
    """
    try:
        headers = context_object.get('headers', '')
        conversation_headers = []
        
        # Extract conversation-relevant headers
        lines = headers.split('\n')
        for line in lines:
            if any(header in line for header in ['Message-Id:', 'Message-ID:', 'In-Reply-To:', 'References:']):
                conversation_headers.append(line.strip())
        
        result = '\n'.join(conversation_headers)
        logger.info(f"📧 [AIRTABLE] Extracted conversation headers ({len(conversation_headers)} lines)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error extracting conversation headers: {e}")
        return context_object.get('headers', '')


def build_initial_conversation_query(context_object: Dict[str, Any]) -> tuple[str, str, str]:
    """
    Build structured JSON for the initial customer query
    
    This creates the first conversation entry containing:
    - sender_email: Original sender's email
    - sender_email_date: When the email was sent  
    - sender_email_content: The email body content
    - sender_name: AI-extracted sender name or fallback to email username
    
    Args:
        context_object: Context object containing email payload
        
    Returns:
        Tuple of (json_string, sender_first_name, sender_last_name)
    """
    try:
        logger.info("📝 [CONVERSATION] Building initial conversation query...")
        
        # Step 1: Get the original sender email
        original_sender = extract_original_sender(context_object)
        
        # Step 2: Get the email date from headers
        email_date = extract_email_date_from_headers(context_object)
        
        # Step 3: Get the email body content
        email_content = extract_email_body(context_object)
        
        # Step 4: AI extraction of sender name from email content
        logger.info("🤖 [CONVERSATION] Extracting sender name using AI...")
        ai_result = name_extractor.extract_sender_name(email_content)
        
        # Determine final sender name with fallback logic
        if ai_result.sender_name and ai_result.sender_name.strip():
            sender_name = ai_result.sender_name.strip()
            sender_first_name = ai_result.sender_first_name.strip() if ai_result.sender_first_name else ""
            sender_last_name = ai_result.sender_last_name.strip() if ai_result.sender_last_name else ""
            logger.info(f"✅ [CONVERSATION] Using AI-extracted sender name: '{sender_name}' (first: '{sender_first_name}', last: '{sender_last_name}')")
        else:
            # Fallback: use email username part
            sender_name = original_sender.split('@')[0] if '@' in original_sender else original_sender
            sender_first_name = sender_name  # Use email username as first name fallback
            sender_last_name = ""
            logger.info(f"🔄 [CONVERSATION] Using fallback sender name from email: '{sender_name}'")
        
        # Build the structured conversation entry (now with 4 fields)
        initial_query = {
            "sender_email": original_sender,
            "sender_email_date": email_date, 
            "sender_email_content": email_content,
            "sender_name": sender_name
        }
        
        # Convert to JSON string
        import json
        json_string = json.dumps(initial_query, indent=2, ensure_ascii=False)
        
        logger.info("✅ [CONVERSATION] Initial conversation query built successfully")
        logger.info(f"📝 [CONVERSATION] Sender Email: {original_sender}")
        logger.info(f"📝 [CONVERSATION] Sender Name: '{sender_name}'")
        logger.info(f"📝 [CONVERSATION] Date: {email_date}")
        logger.info(f"📝 [CONVERSATION] Content length: {len(email_content)} chars")
        
        return json_string, sender_first_name, sender_last_name
        
    except Exception as e:
        logger.error(f"❌ [CONVERSATION] Error building initial conversation query: {e}")
        # Return empty structure on error with 4 fields
        fallback_email = "unknown@unknown.com"
        fallback_name = fallback_email.split('@')[0]
        fallback_json = json.dumps({
            "sender_email": fallback_email,
            "sender_email_date": datetime.utcnow().isoformat(),
            "sender_email_content": "",
            "sender_name": fallback_name
        }, indent=2)
        return fallback_json, fallback_name, ""


def extract_email_date_from_headers(context_object: Dict[str, Any]) -> str:
    """
    Extract the email date from headers
    
    Args:
        context_object: Context object containing headers
        
    Returns:
        Email date string from Date header
    """
    try:
        headers = context_object.get('headers', '')
        
        # Parse headers to find the Date field
        lines = headers.split('\n')
        for line in lines:
            if line.lower().startswith('date:'):
                # Extract everything after 'Date: '
                date_str = line[5:].strip()  # Remove 'Date:' and whitespace
                logger.info(f"📅 [EMAIL DATE] Found date header: {date_str}")
                return date_str
        
        # Fallback: use received timestamp or current time
        fallback_date = context_object.get('received_timestamp', datetime.utcnow().isoformat())
        logger.warning(f"⚠️ [EMAIL DATE] No Date header found, using fallback: {fallback_date}")
        return fallback_date
        
    except Exception as e:
        logger.error(f"❌ [EMAIL DATE] Error extracting date: {e}")
        return datetime.utcnow().isoformat()


def parse_conversation_thread(text_content: str, payload_from: str, payload_headers: str) -> str:
    """
    Parse a full conversation thread from forwarded email text
    
    This function is designed for the existing_email path where we receive
    emails containing full conversation history with quoted replies.
    
    Strategy:
    1. Extract latest message (before first "> On ... wrote:" marker)
    2. Get latest sender from payload["from"] 
    3. Get latest date from first "Date:" in payload["headers"]
    4. Parse older messages from quoted blocks in text
    5. Build JSON array with all conversation entries
    
    Args:
        text_content: Full text content containing conversation thread
        payload_from: The "from" field from the webhook payload
        payload_headers: The "headers" field from the webhook payload
        
    Returns:
        JSON string containing array of conversation entries
    """
    try:
        logger.info("🧵 [CONVERSATION] Parsing conversation thread...")
        
        # TODO: Implement conversation thread parsing
        # This will be needed for the existing_email path
        
        conversation_entries = []
        
        # Step 1: Extract latest message content (before first quoted block)
        latest_content = extract_latest_message_content(text_content)
        
        # Step 2: Get latest sender email from payload
        latest_sender = extract_sender_from_payload_from(payload_from)
        
        # Step 3: Get latest date from headers
        latest_date = extract_date_from_payload_headers(payload_headers)
        
        # Step 4: Build latest message entry
        latest_entry = {
            "sender_email": latest_sender,
            "sender_email_date": latest_date,
            "sender_email_content": latest_content
        }
        conversation_entries.append(latest_entry)
        
        # Step 5: Parse older quoted messages using AI agent (much more robust than regex)
        older_entries = parse_quoted_messages_with_ai(text_content)
        conversation_entries.extend(older_entries)
        
        import json
        return json.dumps(conversation_entries, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ [CONVERSATION] Error parsing conversation thread: {e}")
        return "[]"  # Return empty array on error


def extract_latest_message_content(text_content: str) -> str:
    """
    Extract the latest message content from conversation thread text
    
    Strategy: Split at first "> On ... wrote:" marker to get the top message
    
    Args:
        text_content: Full conversation text
        
    Returns:
        Latest message content as string
    """
    try:
        # Find first quoted block marker
        lines = text_content.split('\n')
        latest_lines = []
        
        for line in lines:
            if line.strip().startswith('> On ') and 'wrote:' in line:
                # Found first quoted block, stop here
                break
            latest_lines.append(line)
        
        latest_content = '\n'.join(latest_lines).strip()
        logger.info(f"📄 [LATEST MESSAGE] Extracted {len(latest_content)} chars")
        
        return latest_content
        
    except Exception as e:
        logger.error(f"❌ [LATEST MESSAGE] Error extracting latest content: {e}")
        return text_content  # Return full text as fallback


def extract_sender_from_payload_from(payload_from: str) -> str:
    """
    Extract sender email from payload "from" field
    
    Example: "cvrcontractsltd <cvrcontractsltd@gmail.com>" -> "cvrcontractsltd@gmail.com"
    
    Args:
        payload_from: The "from" field from webhook payload
        
    Returns:
        Extracted email address
    """
    try:
        import re
        # Extract email from format like "Name <email@domain.com>"
        email_match = re.search(r'<([^>]+)>', payload_from)
        if email_match:
            return email_match.group(1)
        
        # If no angle brackets, assume it's just the email
        return payload_from.strip()
        
    except Exception as e:
        logger.error(f"❌ [SENDER EXTRACT] Error extracting sender: {e}")
        return payload_from


def extract_date_from_payload_headers(payload_headers: str) -> str:
    """
    Extract date from payload headers
    
    Args:
        payload_headers: Headers string from webhook payload
        
    Returns:
        Date string from first Date header
    """
    try:
        lines = payload_headers.split('\n')
        for line in lines:
            if line.lower().startswith('date:'):
                date_str = line[5:].strip()
                return date_str
        
        # Fallback to current time
        return datetime.utcnow().isoformat()
        
    except Exception as e:
        logger.error(f"❌ [DATE EXTRACT] Error extracting date: {e}")
        return datetime.utcnow().isoformat()


def parse_quoted_messages_with_ai(text_content: str) -> list:
    """
    Parse older conversation messages using AI agent (much more robust than regex)
    
    This finds the first quoted section and passes it to the AI agent
    to extract all conversation entries with proper handling of various
    email client formats and edge cases.
    
    Args:
        text_content: Full conversation text containing quoted blocks
        
    Returns:
        List of conversation entry dictionaries
    """
    try:
        logger.info("🤖 [AI PARSING] Starting AI-based conversation parsing...")
        
        # Find the start of quoted content (first "> On ... wrote:" line)
        lines = text_content.split('\n')
        quoted_start_index = -1
        
        for i, line in enumerate(lines):
            if line.strip().startswith('> On ') and 'wrote:' in line:
                quoted_start_index = i
                break
        
        if quoted_start_index == -1:
            logger.info("📜 [AI PARSING] No quoted content found in email")
            return []
        
        # Extract everything from first quoted line onwards
        quoted_content = '\n'.join(lines[quoted_start_index:])
        
        if not quoted_content.strip():
            logger.info("📜 [AI PARSING] Quoted content is empty")
            return []
        
        logger.info(f"🤖 [AI PARSING] Sending {len(quoted_content)} chars to AI agent...")
        
        # Use AI agent to parse the quoted content
        try:
            from .ai_agents import ConversationParsingAgent
        except ImportError:
            from ai_agents import ConversationParsingAgent
        
        ai_agent = ConversationParsingAgent()
        conversation_json = ai_agent.parse_conversation_thread_sync(quoted_content)
        
        # Parse the JSON response
        import json
        try:
            conversation_entries = json.loads(conversation_json)
            logger.info(f"✅ [AI PARSING] Successfully parsed {len(conversation_entries)} conversation entries")
            return conversation_entries
        except json.JSONDecodeError as e:
            logger.error(f"❌ [AI PARSING] Failed to parse AI response as JSON: {e}")
            return []
        
    except Exception as e:
        logger.error(f"❌ [AI PARSING] Error in AI conversation parsing: {e}")
        return []


# Note: Removed regex-based parsing functions in favor of AI agent approach
# The ConversationParsingAgent in ai_agents.py now handles all conversation parsing


def store_new_email(email_data: Dict[str, Any]) -> bool:
    """
    Store new email data in Airtable
    
    Args:
        email_data: Extracted email data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("💾 [AIRTABLE] Storing new email in Airtable...")
        
        # Prepare Airtable record format
        airtable_record = {
            "ticket_number": email_data['ticket_number'],
            "status": email_data['status'],
            "created_at": email_data['created_at'],
            "subject": email_data['subject'],
            "email_body": email_data['email_body'],
            "original_sender": email_data['original_sender'],
            "message_id": email_data['message_id'],
            "raw_headers": email_data['raw_headers'],
            "spf_result": email_data['spf_result'],
            "dkim_result": email_data['dkim_result'],
            "has_attachments": email_data['has_attachments'],
            "attachment_count": email_data['attachment_count'],
            "attachment_info": email_data['attachment_info'],
            "initial_auto_reply_sent": email_data['initial_auto_reply_sent'],
            "sender_first_name": email_data['sender_first_name'],
            "sender_last_name": email_data['sender_last_name'],
            "initial_conversation_query": email_data['initial_conversation_query'],
            "conversation_history": email_data['conversation_history']
        }
        
        # Create record in Airtable
        created_record = table.create(airtable_record)
        
        logger.info("✅ [AIRTABLE] Email stored successfully")
        logger.info(f"💾 [AIRTABLE] Ticket {email_data['ticket_number']} saved with record ID: {created_record['id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error storing email: {e}")
        return False


def update_auto_reply_status(ticket_number: str, auto_reply_sent: bool) -> bool:
    """
    Update the auto-reply status for a ticket in Airtable
    
    Args:
        ticket_number: Ticket number to update
        auto_reply_sent: Whether auto-reply was sent successfully
        
    Returns:
        True if update successful, False otherwise
    """
    try:
        logger.info(f"🔄 [AIRTABLE] Updating auto-reply status for ticket {ticket_number}")
        
        # Find the record by ticket number
        records = table.all(formula=match({"ticket_number": ticket_number}))
        
        if not records:
            logger.error(f"❌ [AIRTABLE] No record found for ticket {ticket_number}")
            return False
        
        if len(records) > 1:
            logger.warning(f"⚠️ [AIRTABLE] Multiple records found for ticket {ticket_number}, updating first one")
        
        record = records[0]
        record_id = record['id']
        
        # Update the auto-reply status
        update_data = {
            "initial_auto_reply_sent": auto_reply_sent
        }
        
        table.update(record_id, update_data)
        
        logger.info(f"✅ [AIRTABLE] Updated auto-reply status for ticket {ticket_number} to {auto_reply_sent}")
        return True
        
    except Exception as e:
        logger.error(f"❌ [AIRTABLE] Error updating auto-reply status for ticket {ticket_number}: {e}")
        return False


# Initialize Airtable connection on module import
try:
    init_database()
except Exception as e:
    logger.error(f"❌ [AIRTABLE] Failed to initialize Airtable connection: {e}") 