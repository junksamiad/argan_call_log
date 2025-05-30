# Argan HR Email Management System

An automated email processing system for HR queries with AI-powered analysis, response suggestions, and approval workflows.

## Features

- **Email Integration**: Automatically fetches emails from IONOS email account
- **AI Processing**: 
  - Extracts structured information from emails using GPT-4
  - Generates executive summaries and action items
  - Suggests professional responses
- **Thread Management**: Tracks conversation threads with unique ticket numbers
- **Approval Workflow**: Routes queries through ops managers for approval
- **Dashboard API**: RESTful API for frontend integration

## System Architecture

```
Email Account (IONOS) → IMAP Fetch → AI Processing Pipeline → Database → API → Frontend
                                          ↓
                                   - Parse & Extract
                                   - Summarize
                                   - Generate Response
```

## How the System Works

1. **Email arrives** → System checks for existing ticket number in subject line (e.g., `[ARG-00001]`)
2. **Thread detection**:
   - If ticket exists → Add to existing thread
   - If new email → Process as new thread
3. **AI Processing** (for new threads):
   - Extract structured data (staff name, query type, urgency)
   - Generate executive summary
   - Create suggested response
4. **Database Storage**:
   - Create EmailThread record
   - Database auto-generates unique ticket number (`ARG-00001`, `ARG-00002`, etc.)
   - Store all extracted data and AI suggestions
5. **Dashboard Access**:
   - HR staff can view threads and messages
   - Review AI-suggested responses
   - Edit and send responses
   - Route to ops manager for approval
6. **Reply Sent**:
   - Ticket number automatically added to subject: `[ARG-00001] Original Subject`
   - Links future responses to the same thread

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL (or SQLite for development)
- Redis (for background tasks)
- OpenAI API key

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd argan_call_log

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the root directory:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/argan_email_db

# Email Configuration (Already set in config/settings.py)
# Modify if needed

# Redis Configuration
REDIS_URL=redis://localhost:6379
```

### 4. Database Setup

```bash
# Initialize database tables
python -c "from backend.utils.database import init_db; init_db()"
```

### 5. Running the Application

#### Start the API Server:

```bash
cd backend/api
python main.py
```

The API will be available at `http://localhost:8000`

#### Start Celery Worker (for background email processing):

```bash
celery -A backend.services.celery_app worker --loglevel=info
```

#### Start Celery Beat (for scheduled email checks):

```bash
celery -A backend.services.celery_app beat --loglevel=info
```

## API Endpoints

### Email Threads

- `GET /api/v1/threads` - List all email threads with pagination
- `GET /api/v1/threads/{thread_id}` - Get specific thread details
- `GET /api/v1/threads/{thread_id}/messages` - Get all messages in a thread
- `POST /api/v1/threads/{thread_id}/reply` - Send a reply
- `PUT /api/v1/threads/{thread_id}/status` - Update thread status

### Email Processing

- `POST /api/v1/process-emails` - Manually trigger email processing

### Authentication

- `POST /api/v1/auth/token` - Login and get access token
- `POST /api/v1/auth/register` - Register new user

## Email Processing Flow

1. **Email Reception**: System checks for new emails every 60 seconds
2. **Thread Detection**: Checks subject line for existing ticket numbers `[ARG-XXXXX]`
3. **AI Processing**:
   - Extracts: staff name, email, query type, urgency level
   - Generates: executive summary, key points, action items
   - Creates: suggested response
4. **Database Storage**: All data stored with unique ticket number
5. **Dashboard Access**: HR staff can view, respond, and manage queries

## Testing Email Connection

Run the test script to verify email connection:

```bash
python test_email_connection.py
```

## Development

### Project Structure

```
argan_call_log/
├── backend/
│   ├── api/           # FastAPI routes
│   ├── models/        # Database models & schemas
│   ├── services/      # Business logic
│   └── utils/         # Helper functions
├── config/            # Configuration
├── tests/             # Test files
└── frontend/          # Frontend application (to be built)
```

### Adding New Features

1. Create/modify models in `backend/models/`
2. Add business logic in `backend/services/`
3. Expose via API in `backend/api/`
4. Update schemas in `backend/models/schemas.py`

## Security Notes

- Change default passwords before production deployment
- Use environment variables for sensitive data
- Configure CORS appropriately for production
- Implement rate limiting for API endpoints
- Regular security audits recommended

## Troubleshooting

### Email Connection Issues

- Verify IONOS email credentials
- Check IMAP/SMTP server settings
- Ensure ports 993 (IMAP) and 465 (SMTP) are not blocked

### Database Issues

- Ensure PostgreSQL is running
- Check DATABASE_URL in configuration
- Run database migrations if needed

### AI Processing Issues

- Verify OpenAI API key is valid
- Check API rate limits
- Monitor token usage

## Support

For issues or questions, please contact the development team. 