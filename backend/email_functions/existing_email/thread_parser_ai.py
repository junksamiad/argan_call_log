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
import os

logger = logging.getLogger(__name__)


class ThreadParserAI:
    def __init__(self):
        """Initialize the Thread Parser AI agent"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"
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

## Deduplication
- Extract only unique message content
- Ignore auto-generated signatures, disclaimers, footers
- Focus on the actual human-written content

## Output Format
Return a JSON array of message objects:
```json
[
  {
    "sender": "sender@example.com",
    "sender_name": "John Doe",
    "timestamp": "2024-06-01T15:30:00Z",
    "subject": "Original subject",
    "body_text": "The actual message content only",
    "message_type": "initial|reply|forward",
    "source": "extracted",
    "content_hash": "unique_hash",
    "thread_position": 1
  }
]
```

## Important Rules
1. **Latest message first** - The most recent message is usually at the top
2. **Strip quoted content** - Don't include ">" prefixed content unless it's part of the actual message
3. **Preserve chronological order** - Arrange messages by timestamp
4. **Handle malformed content** - Some email clients mangle formatting
5. **Ignore signatures** - Filter out email signatures and legal disclaimers

Extract ALL messages you can identify in the thread, even if formatting is inconsistent.
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
            parsed_messages = await self._call_openai_thread_parser(email_content)
            
            # Post-process and enhance the messages
            enhanced_messages = self._enhance_parsed_messages(parsed_messages, email_data)
            
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

BODY TEXT:
{email_data.get('body_text', 'No text content')}

BODY HTML (if different):
{email_data.get('body_html', 'No HTML content')}

PARSE THIS EMAIL THREAD AND EXTRACT ALL INDIVIDUAL MESSAGES.
"""

    async def _call_openai_thread_parser(self, thread_content: str) -> List[Dict[str, Any]]:
        """Call OpenAI to parse the email thread"""
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
                text_format="json"  # Request JSON output
            )
            
            # Parse the JSON response
            parsed_data = json.loads(response.output_parsed)
            return parsed_data if isinstance(parsed_data, list) else []
            
        except Exception as e:
            logger.error(f"🧵 [THREAD PARSER] OpenAI API error: {e}")
            return []

    def _enhance_parsed_messages(self, parsed_messages: List[Dict[str, Any]], email_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhance parsed messages with additional metadata"""
        enhanced = []
        
        for i, message in enumerate(parsed_messages):
            enhanced_message = {
                "message_id": self._generate_message_id(message, email_data),
                "timestamp": self._normalize_timestamp(message.get('timestamp')),
                "sender": message.get('sender', 'unknown@unknown.com'),
                "sender_name": message.get('sender_name', ''),
                "message_type": message.get('message_type', 'reply'),
                "source": "extracted",
                "extracted_from": email_data.get('message_id', ''),
                "subject": message.get('subject', email_data.get('subject', '')),
                "body_text": message.get('body_text', ''),
                "content_hash": self._generate_content_hash(message.get('body_text', '')),
                "thread_position": i + 1,  # Will be updated during merge
                "priority": "Normal"
            }
            enhanced.append(enhanced_message)
        
        return enhanced

    def _generate_message_id(self, message: Dict[str, Any], email_data: Dict[str, Any]) -> str:
        """Generate a unique message ID"""
        content = f"{message.get('sender', '')}{message.get('timestamp', '')}{message.get('body_text', '')[:100]}"
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
            # Add more parsing logic here as needed
            if isinstance(timestamp, str) and 'T' in timestamp:
                return timestamp  # Already ISO format
            else:
                # Fallback to current time
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
            "body_text": email_data.get('body_text', ''),
            "content_hash": self._generate_content_hash(email_data.get('body_text', '')),
            "thread_position": 1,
            "priority": "Normal"
        }] 