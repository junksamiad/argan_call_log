# 📜 Conversation History Architecture

## Overview

The HR Email Management System implements sophisticated conversation history tracking to maintain complete context across email threads. This document outlines the architecture, design decisions, and implementation approach for managing complex email conversations.

## Core Concepts

### **1. Conversation History Structure**

Each ticket maintains a chronological conversation history stored as a JSON array in Airtable. Individual messages are structured objects containing:

```json
{
  "message_id": "abc123def456",
  "timestamp": "2024-06-01T15:30:00Z", 
  "sender": "employee@company.com",
  "sender_name": "John Smith",
  "message_type": "initial|reply|forward",
  "source": "direct|extracted",
  "extracted_from": "parent_message_id", 
  "subject": "Original subject line",
  "body_text": "The actual message content",
  "content_hash": "sha256_hash_16chars",
  "thread_position": 1,
  "ai_summary": "Optional AI summary",
  "priority": "Normal|High|Urgent"
}
```

### **2. Message Types & Sources**

- **Message Types**: `initial`, `reply`, `forward`
- **Sources**: 
  - `direct`: Received directly via webhook
  - `extracted`: Parsed from email thread by AI

### **3. Deduplication Strategy**

Multiple deduplication mechanisms prevent duplicate content:
- **Content Hash**: SHA-256 of normalized message content
- **Message ID**: Unique identifier based on sender/timestamp/content
- **Timestamp Correlation**: Prevents temporal duplicates

## Architecture Components

### **NEW_EMAIL Path (Implemented)**

For emails that create new tickets:

```python
# Simple conversation history construction
conversation_history = create_initial_conversation_entry(email_data, classification_data)
enhanced_email_data['conversation_history'] = json.dumps(conversation_history)
```

**Process Flow:**
1. Generate unique message ID
2. Extract metadata (sender, timestamp, subject, content)
3. Create initial conversation entry with `thread_position: 1`
4. Store in Airtable `Conversation History` field

### **EXISTING_EMAIL Path (Skeleton Implemented)**

For replies to existing tickets:

**Process Flow:**
1. **Ticket Identification**: Extract ticket number from AI classification
2. **Thread Parsing**: Use specialized Thread Parser AI to extract individual messages
3. **Conversation Retrieval**: Get existing conversation from Airtable
4. **Message Merging**: Combine new messages with existing, handling deduplication
5. **Position Updating**: Recalculate `thread_position` for chronological order
6. **Airtable Update**: Store updated conversation history

```python
# High-level flow
ticket_number = extract_ticket_number(classification_data)
existing_record = airtable.find_ticket(ticket_number)
parsed_messages = await thread_parser.parse_email_thread(email_data)
existing_conversation = get_existing_conversation(existing_record)
updated_conversation = merge_conversations(existing_conversation, parsed_messages)
airtable.update_conversation_advanced(ticket_number, updated_conversation, email_data)
```

## Thread Parser AI Agent

### **Purpose**
Specialized AI agent for "email archaeology" - extracting individual messages from complex email threads where multiple messages are quoted/forwarded together.

### **Capabilities**
- **Email Client Recognition**: Handles Gmail, Outlook, generic patterns
- **Quote Detection**: Identifies and separates quoted content from new content
- **Metadata Extraction**: Extracts sender, timestamp, subject for each message
- **Content Normalization**: Strips signatures, disclaimers, formatting artifacts
- **Fallback Handling**: Gracefully handles unparseable content

### **Parsing Patterns**
- **Gmail**: `"On [date] at [time], [sender] wrote:"`
- **Outlook**: `"From: [sender], Sent: [date], To: [recipient]"`
- **Generic**: `"-----Original Message-----"`, `"> "`, `">>"`

### **AI Prompt Strategy**
The Thread Parser uses a specialized system prompt that:
- Provides specific patterns for different email clients
- Emphasizes deduplication and content separation
- Requests structured JSON output
- Handles malformed/inconsistent formatting

## Deduplication & Merging

### **Multi-Level Deduplication**

1. **Content Hash Matching**
   ```python
   existing_hashes = {msg.get('content_hash') for msg in existing_messages}
   if content_hash in existing_hashes:
       continue  # Skip duplicate
   ```

2. **Message ID Matching**
   ```python
   existing_message_ids = {msg.get('message_id') for msg in existing_messages}
   if message_id in existing_message_ids:
       continue  # Skip duplicate
   ```

3. **Temporal Deduplication**
   - Compare timestamps and sender combinations
   - Handle slight timestamp variations from email client differences

### **Merge Process**

```python
def merge_conversations(existing_messages, new_messages):
    # 1. Filter duplicates using content hash and message ID
    unique_new_messages = filter_duplicates(new_messages, existing_messages)
    
    # 2. Combine and sort chronologically
    all_messages = existing_messages + unique_new_messages
    all_messages.sort(key=lambda x: x.get('timestamp', ''))
    
    # 3. Update thread positions
    for i, message in enumerate(all_messages, 1):
        message['thread_position'] = i
    
    return all_messages
```

## Database Schema

### **Airtable Fields**

- **Conversation History** (`multilineText`): JSON array of all messages
- **Message Count** (`number`): Total number of messages in conversation
- **Last Message Date** (`dateTime`): Timestamp of most recent message
- **Is Initial Email** (`checkbox`): Whether this was the original inquiry

### **Field Updates on Reply**

When processing existing email replies:
```python
update_data = {
    "Conversation History": json.dumps(updated_conversation),
    "Last Updated": datetime.utcnow().isoformat(),
    "Status": "In Progress",  # New activity updates status
    "Last Message Date": email_data.get('email_date'),
    "Message Count": len(updated_conversation)
}
```

## Error Handling & Fallbacks

### **Thread Parser Failures**
If AI thread parsing fails:
```python
# Fallback: treat as single message
return self._create_fallback_message(email_data)
```

### **Ticket Not Found**
If existing ticket lookup fails:
```python
# Fallback: process as new email
from backend.email_functions.initial_email.initial_email import process_initial_email
return await process_initial_email(email_data, classification_data)
```

### **Airtable Update Failures**
Graceful error handling with detailed logging and return status indicators.

## Performance Considerations

### **Content Hash Optimization**
```python
# Normalize content before hashing to catch minor variations
normalized = re.sub(r'\s+', ' ', content.strip())
return hashlib.sha256(normalized.encode()).hexdigest()[:16]
```

### **Batch Operations**
- Single Airtable update per conversation (not per message)
- JSON storage minimizes database round trips
- Efficient duplicate checking using Python sets

### **AI Usage Optimization**
- Thread Parser only called for existing email replies
- Fallback to simple processing when AI fails
- Structured prompts minimize token usage

## Future Enhancements

### **Phase 4 Considerations**
- **Thread Visualization**: UI for displaying conversation timeline
- **Search Integration**: Full-text search across conversation history
- **Analytics**: Conversation metrics (response times, message counts)
- **Smart Threading**: ML-based conversation grouping beyond ticket numbers

### **Advanced Features**
- **Attachment Threading**: Track attachments across conversation
- **Participant Tracking**: Multi-party conversation support
- **Response Templates**: Context-aware auto-reply suggestions
- **Escalation Triggers**: Automatic escalation based on conversation patterns

## Implementation Status

### ✅ **Completed (NEW_EMAIL Path)**
- Basic conversation history construction
- Initial message entry creation
- Airtable integration with conversation storage
- Auto-reply integration

### 🔧 **Skeleton Implemented (EXISTING_EMAIL Path)**
- Thread Parser AI agent structure
- Conversation merging logic
- Airtable update methods
- Error handling framework

### ⏳ **Ready for Implementation**
- OpenAI API integration for Thread Parser
- Real-world thread parsing testing
- Performance optimization
- UI integration for conversation display

## Testing Strategy

### **Unit Tests**
- Message ID generation consistency
- Content hash deduplication accuracy
- Timestamp normalization
- JSON serialization/deserialization

### **Integration Tests**
- End-to-end conversation flow (new → reply → reply)
- Thread Parser accuracy with real email samples
- Airtable field updates and retrieval
- Error handling scenarios

### **Performance Tests**
- Large conversation history handling
- Complex thread parsing performance
- Concurrent email processing

---

**Note**: This architecture provides a robust foundation for comprehensive email conversation management while maintaining flexibility for future enhancements. The skeleton implementation ensures all components are ready for seamless activation when needed. 