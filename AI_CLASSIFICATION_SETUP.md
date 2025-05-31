# AI Email Classification System Setup

## Overview
The email system now uses OpenAI's GPT-4.1 with structured outputs to intelligently classify emails as either NEW_EMAIL or EXISTING_EMAIL, replacing the previous regex-based approach.

## Setup Instructions

### 1. Environment Configuration
Copy the example environment file and configure your API keys:

```bash
cp env.example .env
```

Edit `.env` and add your OpenAI API key:
```bash
# OpenAI Configuration (REQUIRED FOR AI CLASSIFICATION)
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 2. Dependencies
The required packages are already installed, but if needed:
```bash
pip install openai pydantic python-dotenv
```

### 3. Directory Structure
The new AI classification system is organized as follows:
```
backend/email_functions/
├── classification/
│   ├── __init__.py
│   ├── email_classifier_agent.py      # Main AI classifier
│   ├── email_classification_schema.py # Pydantic schemas
│   └── assign_ticket.py              # Ticket generation logic
├── email_router.py                   # Updated router using AI
├── initial_email/                    # New email handlers
└── existing_email/                   # Reply handlers
```

## How It Works

### 1. Email Classification Flow
```
Incoming Email → AI Classifier → Structured Output → Route to Handler
```

### 2. AI Classifier Features
- **Smart Ticket Detection**: Finds ticket numbers in subject AND body text
- **Context Awareness**: Distinguishes real replies vs coincidental matches
- **Data Extraction**: Extracts contact info, urgency keywords, sentiment
- **Structured Output**: Returns flattened data for easy parsing
- **Fallback**: Graceful degradation to regex-based routing if AI fails

### 3. Structured Output Schema
The AI returns:
```python
{
    "EMAIL_CLASSIFICATION": "NEW_EMAIL" | "EXISTING_EMAIL",
    "EMAIL_DATA": {
        "sender_email": "...",
        "subject": "...",
        "ticket_number": "ARG-YYYYMMDD-XXXX",
        "urgency_keywords_list": "[...]",
        "sentiment_tone": "...",
        # ... more fields
    },
    "confidence_score": 0.95,
    "notes": "AI observations"
}
```

## Testing

### Run Basic AI Classifier Test
```bash
python test_ai_classifier.py
```

### Run Full Integration Test
```bash
python test_email_routing_integration.py
```

## Benefits

### ✅ Improvements Over Regex
- **Smarter Detection**: Finds tickets in body text, handles variations
- **Context Aware**: Understands when ticket references are genuine replies
- **Rich Metadata**: Extracts urgency, sentiment, contact details
- **Future Ready**: Easy to extend with more AI capabilities

### ✅ Graceful Fallbacks
- **Robust**: Falls back to regex routing if AI fails
- **Reliable**: Multiple layers of error handling
- **Observable**: Comprehensive logging with emojis

## Configuration

### Model Selection
Currently using `gpt-4.1` for best accuracy. To change:
```python
# In email_classifier_agent.py
self.model = "gpt-4o-mini"  # For faster/cheaper processing
```

### Prompt Tuning
The classification prompt can be customized in:
```python
EmailClassifierAgent._build_classification_prompt()
```

## Monitoring

Look for these log messages:
- `🤖 [AI CLASSIFIER]` - AI classification events
- `📬 [EMAIL ROUTER]` - Routing decisions
- `🆕 [EMAIL ROUTER]` - New ticket creation
- `🔄 [EMAIL ROUTER]` - Existing ticket handling

## Cost Considerations

- **GPT-4.1**: ~$0.03 per 1K input tokens, ~$0.12 per 1K output tokens
- **Typical email**: ~500 tokens input, ~200 tokens output = ~$0.04 per email
- **Monthly estimate**: 1000 emails = ~$40/month

## Troubleshooting

### API Key Issues
```bash
# Check if key is loaded
python -c "import os; print('API Key:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

### Import Issues
```bash
# Test imports
python -c "import sys; sys.path.append('backend'); from backend.email_functions.classification import EmailClassifierAgent; print('✅ Imports working')"
```

### Debug Mode
Set `DEBUG=True` in `.env` for verbose logging.

## Next Steps

1. **Phase 2**: Add AI metadata extraction for initial emails
2. **Phase 3**: Implement AI summarization and categorization  
3. **Phase 4**: Build conversation threading with AI parsing
4. **Optimization**: Consider downgrading to smaller models for cost efficiency 