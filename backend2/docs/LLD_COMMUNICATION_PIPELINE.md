# Low-Level Design - Communication Pipeline

## Overview

The **Communication Pipeline** manages all outbound email communications including auto-reply generation, template processing, and email delivery through SendGrid. It ensures reliable delivery with retry logic and professional formatting.

## Core Components

### 1. Email Service (`email_service.py`)
- SendGrid API integration with timeout and retry configurations
- Auto-reply email delivery with CC functionality
- Connection testing and API key validation
- Exponential backoff retry logic for failed deliveries

### 2. Auto-Reply Template Generator (`auto_reply_templates.py`)
- Professional email template generation with personalization
- HTML and text content generation for multi-format support
- Ticket number integration and original query inclusion
- Priority-based response timeframe communication

### 3. Sender Information Extraction
- Database record parsing for sender details
- Name component extraction and formatting
- Email address validation and cleaning
- Fallback handling for missing information

## Key Features

### **Template Generation**
- **Personalized Greetings:** "Hi {first_name}" with fallback to "Hello"
- **Ticket Integration:** Clear ticket number reference throughout
- **Original Query Inclusion:** Full customer message for reference
- **Professional Formatting:** Branded design with company styling
- **Multi-Format Output:** Both text and HTML versions

### **Email Delivery**
- **SendGrid Integration:** RESTful API with proper authentication
- **Retry Logic:** 3 attempts with exponential backoff (2s, 4s, 6s)
- **CC Functionality:** advice@arganhrconsultancy.co.uk for visibility
- **Reply-To Handling:** Replies directed back to original sender
- **Error Handling:** Graceful degradation with detailed logging

### **Performance Characteristics**
- **Template Generation:** 100-200ms (text processing)
- **Email Delivery:** 500-1500ms (SendGrid API dependent)
- **Retry Logic:** Up to 12 seconds total with backoff
- **Success Rate:** >98% delivery reliability

## Configuration

### **SendGrid Settings**
```bash
SENDGRID_API_KEY=SG.your_api_key
FROM_EMAIL=email@email.adaptixinnovation.co.uk
```

### **Template Settings**
```bash
COMPANY_NAME="Argan HR Consultancy"
TEAM_NAME="Argan HR Consultancy Team"
AUTO_REPLY_CC_ADDRESSES=advice@arganhrconsultancy.co.uk
```

### **Retry Configuration**
```bash
MAX_RETRIES=3
BASE_DELAY=2  # seconds
INITIAL_DELAY=0.5  # seconds
```

## Sample Auto-Reply Output

```
Subject: [ARG-20250603-0001] Argan HR Consultancy - Call Logged

Hi John,

Thank you for contacting Argan HR Consultancy. We have received your enquiry 
and assigned it ticket number ARG-20250603-0001.

┌─────────────────────────────────────────────────────────────────┐
│ Original Subject: HR Policy Question                           │
│ Priority: Normal                                               │
│ Ticket Number: ARG-20250603-0001                              │
└─────────────────────────────────────────────────────────────────┘

We will review your request and respond within our standard timeframe:
• Urgent matters: Within 4 hours
• High priority: Within 24 hours  
• Normal requests: Within 2-3 business days

Original Enquiry (for reference):
    Hi, I need help with HR policy regarding staff breaks...

Best regards,
Argan HR Consultancy Team
``` 