# Argan Call Log - Auto-Reply System

🎯 **Simple, focused email auto-reply system for Argan Consultancy HR**

## What It Does

When someone sends an email to your HR address, this system:

1. **Receives the email** via SendGrid webhook
2. **Generates a unique ticket number** (format: `ARG-YYYYMMDD-XXXX`)
3. **Sends an auto-reply** to the sender with the ticket number
4. **CCs advice@arganconsultancy.co.uk** on the reply
5. **Stores everything** in a database for tracking

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create a `.env` file:
```env
# SendGrid Configuration
SENDGRID_API_KEY=your_sendgrid_api_key_here
EMAIL_ADDRESS=your_from_email@arganconsultancy.co.uk

# Database (SQLite by default)
DATABASE_URL=sqlite:///argan_email.db
```

### 3. Test the System
```bash
# Test core functionality (no email sending)
python test_ticket_generation.py

# Test with sample email processing
python email_auto_reply_handler.py --test
```

### 4. Run the Server
```bash
python main.py
```

The server will start on `http://localhost:8000`

### 5. Set Up SendGrid Webhook

1. **Expose your local server** (for testing):
   ```bash
   ngrok http 8000
   ```

2. **Configure SendGrid Inbound Parse**:
   - Go to SendGrid → Settings → Inbound Parse
   - Add your ngrok URL: `https://your-ngrok-url.ngrok.io/webhook/inbound`
   - Set destination email (e.g., `support@email.adaptixinnovation.co.uk`)

### 6. Test Live Email Processing

Send an email to your configured address and watch the magic happen! ✨

## System Architecture

```
Email → SendGrid → Webhook → Auto-Reply System → Database
                              ↓
                         Auto-Reply Email → Sender + CC
```

## File Structure

```
argan_call_log/
├── main.py                           # FastAPI application
├── email_auto_reply_handler.py       # Standalone email handler
├── test_ticket_generation.py         # Test script
├── backend/
│   ├── services/
│   │   ├── auto_reply_service.py     # Core auto-reply logic
│   │   └── email_service.py          # SendGrid email sending
│   ├── models/
│   │   ├── database.py               # Database models
│   │   └── schemas.py                # Pydantic schemas
│   ├── api/endpoints/
│   │   └── webhook.py                # SendGrid webhook endpoint
│   └── utils/
│       └── database.py               # Database utilities
├── config/
│   └── settings.py                   # Configuration
└── requirements.txt                  # Dependencies
```

## Features

✅ **Unique Ticket Generation** - `ARG-YYYYMMDD-XXXX` format  
✅ **Professional Auto-Replies** - HTML + text versions  
✅ **Thread Tracking** - Handles follow-up emails  
✅ **Database Storage** - SQLite (easily switchable)  
✅ **SendGrid Integration** - Reliable email delivery  
✅ **Webhook Processing** - Real-time email handling  
✅ **Clean Architecture** - Easy to maintain and extend  

## API Endpoints

- `GET /` - System status
- `GET /health` - Health check
- `GET /webhook/test` - Test webhook connectivity
- `POST /webhook/inbound` - SendGrid email webhook

## Testing

### Test Core Functionality
```bash
python test_ticket_generation.py
```

### Test Email Handler
```bash
python email_auto_reply_handler.py --test
```

### Test Specific Email
```bash
python email_auto_reply_handler.py \
  --sender "test@example.com" \
  --subject "Test Question" \
  --body "This is a test email"
```

## Configuration

All configuration is in `config/settings.py` and can be overridden with environment variables:

- `SENDGRID_API_KEY` - Your SendGrid API key
- `EMAIL_ADDRESS` - From email address
- `DATABASE_URL` - Database connection string
- `TICKET_PREFIX` - Ticket number prefix (default: "ARG")

## Deployment

For production deployment:

1. Set up a proper domain and SSL
2. Configure SendGrid with your production webhook URL
3. Use a production database (PostgreSQL recommended)
4. Set up monitoring and logging

## Future Enhancements

- 🔄 Airtable integration for ticket management
- 🤖 AI-powered email analysis and categorization
- 📊 Dashboard for ticket tracking
- 📱 Mobile notifications
- 🔐 Authentication and user management

## Support

For issues or questions, contact the development team or check the logs in the application output.

---

**Built with ❤️ for Argan Consultancy HR Team** 