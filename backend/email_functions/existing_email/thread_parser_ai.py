"""
Thread Parser AI Agent
Specialized AI for parsing complex email threads and extracting individual messages
Handles email archaeology for conversation history reconstruction
"""

import logging
import hashlib
import json
import re
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
from pydantic import BaseModel
import os

logger = logging.getLogger(__name__)


class ParsedMessage(BaseModel):
    """Schema for a single parsed message from an email thread"""
    sender: str
    sender_name: str = ""
    timestamp: str
    subject: str = ""
    query: str  # AI-extracted message content
    message_type: str = "reply"  # initial, reply, forward


class ThreadParseResponse(BaseModel):
    """Schema for the complete thread parsing response"""
    messages: List[ParsedMessage]


class ThreadParserAI:
    def __init__(self):
        """Initialize the Thread Parser AI agent"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4.1"
        logger.info("🧵 [THREAD PARSER AI] Initialized")

    def _build_thread_parsing_prompt(self) -> str:
        """Build the system prompt for thread parsing"""
        return """# Email Thread Parser Agent

You are an expert email thread parsing system. Your job is to analyze email content and extract individual messages from email chains/threads.

## Your Task
Parse the provided email content and extract each individual message in the conversation thread. Email clients often include previous messages when replying, creating a chain of quoted content.

## What to Extract
For each message in the thread, extract:
1. **Sender information** (email, name if available)
2. **Timestamp** (when the message was sent)
3. **Subject line** 
4. **Message content** (the actual message body, not quoted/forwarded content)
5. **Message type** (initial, reply, forward)

## Common Email Thread Patterns
- **Gmail**: Uses "On [date] at [time], [sender] wrote:"
- **Outlook**: Uses "From: [sender], Sent: [date], To: [recipient], Subject: [subject]"
- **Generic**: Look for patterns like "-----Original Message-----", "> ", ">>", etc.

## Deduplication Rules
- Extract only unique message content
- Ignore auto-generated signatures, disclaimers, footers
- Focus on the actual human-written content
- Don't include quoted content unless it's part of the actual new message

## Important Parsing Rules
1. **Latest message first** - The most recent message is usually at the top
2. **Strip quoted content** - Don't include ">" prefixed content unless it's part of the actual message
3. **Preserve chronological order** - Arrange messages by timestamp (oldest first)
4. **Handle malformed content** - Some email clients mangle formatting
5. **Ignore signatures** - Filter out email signatures and legal disclaimers
6. **Extract sender emails** - Always include the email address, extract name if available
7. **Normalize timestamps** - Convert to ISO format (YYYY-MM-DDTHH:MM:SSZ)

## Message Types
- **initial**: The first message that started the conversation
- **reply**: A response to a previous message
- **forward**: A forwarded message

Extract ALL messages you can identify in the thread, even if formatting is inconsistent. If you can only find one message (the current one), return just that single message.

Return the messages in chronological order (oldest first).
"""

    async def parse_email_thread(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse an email thread and extract individual messages
        
        Args:
            email_data: Raw email data containing the thread
            
        Returns:
            List of individual message objects
        """
        try:
            logger.info(f"🧵 [THREAD PARSER] Starting thread analysis for {email_data.get('sender')}")
            
            # Prepare content for AI analysis
            email_content = self._prepare_thread_content(email_data)
            
            # Call OpenAI to parse the thread
            parsed_response = await self._call_openai_thread_parser(email_content)
            
            # Post-process and enhance the messages
            enhanced_messages = self._enhance_parsed_messages(parsed_response.messages, email_data)
            
            logger.info(f"🧵 [THREAD PARSER] Extracted {len(enhanced_messages)} messages from thread")
            return enhanced_messages
            
        except Exception as e:
            logger.error(f"🧵 [THREAD PARSER] Error parsing thread: {e}")
            # Fallback: treat as single message
            return self._create_fallback_message(email_data)

    def _prepare_thread_content(self, email_data: Dict[str, Any]) -> str:
        """Prepare email content for thread parsing"""
        return f"""
EMAIL THREAD TO PARSE:

HEADERS:
From: {email_data.get('sender', 'Unknown')}
To: {email_data.get('recipients', [])}
Subject: {email_data.get('subject', 'No Subject')}
Date: {email_data.get('email_date', 'Unknown')}

BODY HTML:
{email_data.get('body_html', 'No HTML content')}

PARSE THIS EMAIL THREAD AND EXTRACT ALL INDIVIDUAL MESSAGES.
"""

    async def _call_openai_thread_parser(self, thread_content: str) -> ThreadParseResponse:
        """Call OpenAI to parse the email thread using structured outputs"""
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": self._build_thread_parsing_prompt()
                    },
                    {
                        "role": "user",
                        "content": thread_content
                    }
                ],
                text_format=ThreadParseResponse
            )
            
            return response.output_parsed
            
        except Exception as e:
            logger.error(f"🧵 [THREAD PARSER] OpenAI API error: {e}")
            # Return empty response that will trigger fallback
            return ThreadParseResponse(messages=[])

    def _enhance_parsed_messages(self, parsed_messages: List[ParsedMessage], email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance parsed messages with additional metadata"""
        enhanced = []
        
        for i, message in enumerate(parsed_messages):
            enhanced_message = {
                "message_id": self._generate_message_id(message.dict(), email_data),
                "timestamp": self._normalize_timestamp(message.timestamp),
                "sender": message.sender,
                "sender_name": message.sender_name,
                "message_type": message.message_type,
                "source": "extracted",
                "extracted_from": email_data.get('message_id', ''),
                "subject": message.subject or email_data.get('subject', ''),
                "query": message.query,  # AI-extracted content
                "content_hash": self._generate_content_hash(message.query),
                "thread_position": i + 1,  # Will be updated during merge
                "priority": "Normal"
            }
            enhanced.append(enhanced_message)
        
        return enhanced

    def _generate_message_id(self, message: Dict[str, Any], email_data: Dict[str, Any]) -> str:
        """Generate a unique message ID"""
        content = f"{message.get('sender', '')}{message.get('timestamp', '')}{message.get('query', '')[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _generate_content_hash(self, content: str) -> str:
        """Generate content hash for deduplication"""
        if not content:
            return ""
        # Normalize content for hashing (remove whitespace variations)
        normalized = re.sub(r'\s+', ' ', content.strip())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _normalize_timestamp(self, timestamp: str) -> str:
        """Normalize timestamp to ISO format"""
        if not timestamp:
            return datetime.utcnow().isoformat()
        
        # Try to parse and normalize various timestamp formats
        try:
            if isinstance(timestamp, str) and 'T' in timestamp:
                return timestamp  # Already ISO format
            else:
                # Try to parse common formats and convert to ISO
                # Add more sophisticated parsing if needed
                return datetime.utcnow().isoformat()
        except:
            return datetime.utcnow().isoformat()

    def _create_fallback_message(self, email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fallback message when parsing fails"""
        logger.warning("🧵 [THREAD PARSER] Using fallback - treating as single message")
        
        return [{
            "message_id": hashlib.md5(f"{email_data.get('sender', '')}{email_data.get('message_id', '')}".encode()).hexdigest()[:12],
            "timestamp": email_data.get('email_date', datetime.utcnow().isoformat()),
            "sender": email_data.get('sender', 'unknown@unknown.com'),
            "sender_name": email_data.get('sender_name', ''),
            "message_type": "reply",
            "source": "direct",
            "extracted_from": None,
            "subject": email_data.get('subject', ''),
            "query": "AI_THREAD_PARSE_FAILED",  # Use query with diagnostic message
            "content_hash": self._generate_content_hash("AI_THREAD_PARSE_FAILED"),
            "thread_position": 1,
            "priority": "Normal"
        }] 