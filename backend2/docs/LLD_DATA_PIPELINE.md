# Low-Level Design - Data Pipeline

## Overview

The **Data Pipeline** manages all database operations for the HR email management system using Airtable as the primary database with PyAirtable as the client library.

## Core Components

### 1. Database Connection
- Airtable API integration with environment-based configuration
- Connection validation and schema verification
- Error handling for connection failures

### 2. Data Storage Operations
- New email record creation with complete ticket information
- Conversation history updates for existing tickets  
- Auto-reply status tracking and updates

### 3. Data Retrieval Operations
- Ticket lookup by ticket number with formula-based queries
- Conversation history retrieval for existing tickets
- Record existence validation

### 4. AI-Enhanced Data Extraction
- Sender name extraction using OpenAI GPT-4.1
- Care home name detection from email content
- Fallback mechanisms for AI extraction failures

### 5. Data Processing
- Email content parsing and field extraction
- JSON conversation structure building
- Date formatting and consistency management

## Performance Characteristics

- **Record Creation:** 300-800ms (Airtable API dependent)
- **Record Retrieval:** 200-600ms (single record lookup)  
- **AI Name Extraction:** 2-4 seconds (OpenAI API dependent)
- **Conversation Building:** 100-200ms (JSON construction)
- **API Rate Limit:** 5 requests per second (Airtable)

## Key Features

- **AI Integration:** OpenAI-powered name and care home extraction
- **Robust Error Handling:** Fallback mechanisms for all operations
- **JSON Management:** Structured conversation history storage
- **Rate Limiting:** Built-in Airtable API limit handling
- **Data Validation:** Field validation and sanitization

## Configuration

### **Environment Variables**
```bash
# Airtable Configuration
AIRTABLE_API_KEY=pat_your_api_key_here
AIRTABLE_BASE_ID=app_your_base_id_here

# OpenAI for AI Extraction
OPENAI_API_KEY=sk-your_openai_key_here

# Database Settings
TABLE_NAME=argan_call_log
DATABASE_TIMEOUT=30
MAX_RETRY_ATTEMPTS=3
```

### **Data Validation Rules**
```python
# Required fields for new records
REQUIRED_FIELDS = ['ticket_number', 'status', 'subject', 'original_sender']

# Field length limits
MAX_SUBJECT_LENGTH = 500
MAX_EMAIL_BODY_LENGTH = 50000
MAX_CONVERSATION_HISTORY_LENGTH = 100000

# Date format validation
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
```

## Monitoring & Alerting

### **Key Metrics**
- Database connection success rate
- Record creation/update success rate
- AI extraction success rate
- Average operation latency
- API rate limit utilization

### **Alert Conditions**
- Database connection failures
- Record operation failure rate >2%
- AI extraction failure rate >10%
- API rate limit exceeded
- Operation latency >5 seconds

### **Logging Strategy**
```python
logger.info("📊 [AIRTABLE] Initializing Airtable connection...")
logger.info(f"💾 [AIRTABLE] Ticket {ticket_number} saved with record ID: {record_id}")
logger.info(f"🤖 [NAME EXTRACTOR] Found sender name: '{sender_name}' (confidence: {confidence})")
logger.info(f"🏠 [CARE HOME EXTRACTOR] Found care home name: '{care_home_name}'")
logger.info(f"✅ [DATABASE] Successfully updated record {record_id}")
``` 