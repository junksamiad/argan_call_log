# 📜 Conversation History Architecture

## Overview

The HR Email Management System implements sophisticated conversation history tracking to maintain complete context across email threads. This document outlines the architecture, design decisions, and implementation approach for managing complex email conversations.

## Core Concepts

### **1. Conversation History Structure**

Each ticket maintains a chronological conversation history stored as a JSON array in Airtable. Individual messages use a consistent 4-field structure:

```json
{
  "sender_email": "employee@company.com",
  "sender_email_date": "2024-06-01T15:30:00Z", 
  "sender_email_content": "The actual message content",
  "sender_name": "John Smith"
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

## Database Schema (Airtable Fields)

### Core Conversation Fields
1. **`initial_conversation_query`** *(Long Text)*
   - **Type**: JSON Object
   - **Purpose**: Stores the first customer email in a structured format
   - **Usage**: Used for auto-reply generation and quick customer query reference

2. **`conversation_history`** *(Long Text)*
   - **Type**: JSON Array
   - **Purpose**: Stores subsequent conversation messages (replies, follow-ups)
   - **Usage**: Threading support, conversation archaeology, full dialogue tracking

3. **`final_conversation_history`** *(Formula Field)*
   - **Type**: Computed JSON Array
   - **Purpose**: Combines initial_conversation_query + conversation_history into single array
   - **Formula**: 
   ```
   IF(
     OR(conversation_history = "", conversation_history = "[]"),
     "[" & initial_conversation_query & "]",
     "[" & initial_conversation_query & "," & MID(conversation_history, 2, LEN(conversation_history) - 2) & "]"
   )
   ```
   - **Usage**: Full conversation export, AI analysis, reporting

## Data Structure Formats

### `initial_conversation_query` Format
```json
{
  "sender_email": "customer@example.com",
  "sender_email_date": "Tue, 3 Jun 2025 10:25:14 +0100", 
  "sender_email_content": "Original customer message content...",
  "sender_name": "John Smith"
}
```

### `conversation_history` Format
```json
[
  {
    "sender_email": "customer@example.com",
    "sender_email_date": "2025-06-03T14:30:22.000Z",
    "sender_email_content": "Follow-up message content...",
    "sender_name": "Customer Name"
  }
]
```

### `final_conversation_history` Format (Computed)
```json
[
  {
    "sender_email": "customer@example.com",
    "sender_email_date": "Tue, 3 Jun 2025 10:25:14 +0100",
    "sender_email_content": "Original customer message...",
    "sender_name": "John Smith"
  },
  {
    "sender_email": "customer@example.com",
    "sender_email_date": "2025-06-03T14:30:22.000Z",
    "sender_email_content": "Follow-up question content...",
    "sender_name": "John Smith"
  }
]
```

## Implementation Details

### New Email Path
1. **Context Object** → `extract_email_data_from_context()`
2. **AI Classification** → Extract customer query using OpenAI GPT-4.1
3. **Build Initial Query** → `build_initial_conversation_query()`
4. **Store in Airtable** → Both fields populated, formula auto-calculates

### Existing Email Path  
1. **Email Thread** → `parse_conversation_thread()`
2. **AI Conversation Parsing** → Extract individual messages from thread
3. **Update Airtable** → Append to `conversation_history`, formula auto-updates

### Airtable Formula Logic
- **Single message**: Wraps `initial_conversation_query` in array brackets
- **Multiple messages**: Combines initial query + strips brackets from history array
- **Result**: Always valid JSON array with consistent 4-field structure

### Technical Threading Data
- **Conversation Data**: Simplified 4-field structure for human/AI consumption
- **Technical Data**: Message-IDs, References, In-Reply-To stored in `raw_headers` field
- **Header Evolution**: Each new email overwrites `raw_headers` with more complete threading map
- **Best of Both**: Clean conversation + complete technical threading preserved

## AI Agent Integration

### ConversationParsingAgent
- **Model**: OpenAI GPT-4.1 with structured outputs
- **Input**: Raw email thread content
- **Output**: Pydantic models ensuring schema compliance
- **Deduplication**: Content hashing prevents duplicate entries

### Benefits
1. **Schema Compliance**: Pydantic models guarantee valid JSON structure
2. **Robust Parsing**: Handles various email client formatting quirks
3. **Human Fallback**: Manual review possible when AI parsing fails
4. **Conversation Archaeology**: Reconstructs full dialogue from complex email threads

## Usage Examples

### Reading Full Conversation (Python)
```python
# Get the computed full conversation
record = airtable.find_ticket("ARG-20250603-1234")
full_conversation = json.loads(record['fields']['final_conversation_history'])

# Process chronologically
for entry in full_conversation:
    print(f"{entry['sender_name']} ({entry['sender_email']}): {entry['sender_email_content']}")
```

### API Export
```python
def export_conversation(ticket_number):
    record = airtable.find_ticket(ticket_number)
    return {
        "ticket_number": ticket_number,
        "full_conversation": json.loads(record['fields']['final_conversation_history']),
        "message_count": len(json.loads(record['fields']['final_conversation_history'])),
        "last_updated": record['fields'].get('Last Updated')
    }
```

## Technical Benefits

1. **Consistent Schema**: Both initial and follow-up messages use identical 4-field structure
2. **Simple Parsing**: No need to handle different field names across conversation entries
3. **AI-Friendly**: Clean, uniform structure for LLM processing and analysis
4. **Formula-Computed**: final_conversation_history auto-calculates from consistent structures
5. **Export Ready**: Single field contains complete conversation with uniform format
6. **Message-ID Tracking**: Technical threading data preserved separately in raw_headers field
7. **Header Evolution**: raw_headers grows richer with each email, containing full conversation map
8. **Future-Proof**: Consistent foundation for existing_email path implementation 