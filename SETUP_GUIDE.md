# Argan HR Email Management System - Setup Guide

## Important: Email Authentication Issue

The email authentication is currently failing with the provided credentials. This is likely because:

1. **Password needs to be changed**: The IONOS email instructions mentioned "please change your password the first time you log in"
2. You need to log in to https://mail.ionos.co.uk/ and set a new password

## Quick Start Steps

### 1. Update Email Password

1. Go to https://mail.ionos.co.uk/
2. Log in with:
   - Email: argan-bot@arganhrconsultancy.co.uk
   - Password: Dashboard2025!
3. Change the password when prompted
4. Note down the new password

### 2. Update Configuration

Update the password in `config/settings.py`:

```python
EMAIL_PASSWORD: str = "your-new-password-here"
```

Or better, use environment variables:

```python
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "default-password")
```

Then create a `.env` file:

```
EMAIL_PASSWORD=your-new-password-here
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=sqlite:///argan_email.db
```

### 3. Test Email Connection

Run the test script to verify the connection works:

```bash
python test_email_connection.py
```

You should see:
- ✓ IMAP Connection: PASSED
- ✓ SMTP Connection: PASSED

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the System

For development, use the provided script:

```bash
./start_dev.sh
```

Or manually:

```bash
# Initialize database
python -c "from backend.utils.database import init_db; init_db()"

# Start API server
cd backend/api
python main.py
```

### 6. Start Background Workers (Optional)

In separate terminals:

```bash
# Email checking worker
celery -A backend.services.celery_app worker --loglevel=info

# Scheduled tasks
celery -A backend.services.celery_app beat --loglevel=info
```

## API Access

- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Default admin login: username=`admin`, password=`admin123`

## Troubleshooting

### Email Connection Fails

1. **Check password**: Ensure you've updated the password after first login
2. **Check server settings**: 
   - IMAP: imap.ionos.com:993 (SSL/TLS)
   - SMTP: smtp.ionos.com:465 (SSL/TLS)
3. **Try alternative SMTP port**: If port 465 is blocked, try 587 with STARTTLS
4. **Check firewall**: Ensure ports 993 and 465/587 are not blocked

### Database Issues

If using PostgreSQL instead of SQLite:

```bash
# Install PostgreSQL
# Create database
createdb argan_email_db

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@localhost/argan_email_db
```

### Missing OpenAI Key

The AI features require an OpenAI API key:

1. Get a key from https://platform.openai.com/
2. Add to `.env`: `OPENAI_API_KEY=sk-...`

## Next Steps

Once the backend is running:

1. Use the API to build your frontend in v0
2. Deploy the frontend to Vercel
3. Configure CORS in production
4. Set up proper authentication
5. Configure production database
6. Set up monitoring and logging

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   IONOS Email   │────▶│  Backend API    │────▶│   Frontend UI   │
│     Account      │     │   (FastAPI)     │     │    (v0/Vercel)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   PostgreSQL    │
                        │    Database     │
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   AI Pipeline   │
                        │   (OpenAI)      │
                        └─────────────────┘
```

## Security Checklist

- [ ] Change default admin password
- [ ] Update email password
- [ ] Set strong SECRET_KEY for JWT
- [ ] Configure CORS for production
- [ ] Use HTTPS in production
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates 