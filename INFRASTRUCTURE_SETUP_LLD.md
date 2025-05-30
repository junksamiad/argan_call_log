# HR Email Management System - Infrastructure Setup (LLD)

## 1. DNS Configuration

### 1.1 Domain Structure
```
adaptixinnovation.co.uk (Main Domain)
├── MX Records: mx1.hostinger.com, mx2.hostinger.com
└── email.adaptixinnovation.co.uk (Email Subdomain)
    └── MX Record: mx.sendgrid.net (Priority: 10)
```

### 1.2 MX Record Configuration

#### Current Configuration (Working)
```dns
; MX Record for email subdomain
email.adaptixinnovation.co.uk.    300    IN    MX    10 mx.sendgrid.net.
```

#### Legacy SendGrid Records (Deprecated - Do Not Use)
```dns
; These records no longer exist and will cause email failures
email.adaptixinnovation.co.uk.    300    IN    MX    10 mxa.sendgrid.net.
email.adaptixinnovation.co.uk.    300    IN    MX    20 mxb.sendgrid.net.
```

#### DNS Verification Commands
```bash
# Check current MX records
dig MX email.adaptixinnovation.co.uk

# Verify SendGrid server resolution
dig A mx.sendgrid.net

# Check DNS propagation globally
nslookup -type=MX email.adaptixinnovation.co.uk 8.8.8.8
```

### 1.3 DNS Provider Setup Steps

#### For Most DNS Providers:
1. **Access DNS Management**
   - Log into your domain registrar/DNS provider
   - Navigate to DNS Records or Domain Management

2. **Remove Old Records**
   ```
   DELETE: mxa.sendgrid.net
   DELETE: mxb.sendgrid.net
   ```

3. **Add New MX Record**
   ```
   Type: MX
   Host: email (or email.adaptixinnovation.co.uk)
   Priority: 10
   Value: mx.sendgrid.net
   TTL: 300 (or default)
   ```

4. **Verify Configuration**
   - Wait 5-15 minutes for propagation
   - Test with `dig MX email.adaptixinnovation.co.uk`

## 2. SendGrid Configuration

### 2.1 Account Setup

#### Authentication Status
```
✅ em8479.email.adaptixinnovation.co.uk - Verified
❌ em9019.adaptixinnovation.co.uk - Failed (Removed)
```

#### Domain Authentication Records
SendGrid requires these DNS records for domain verification:
```dns
; CNAME records for domain authentication
em8479._domainkey.email.adaptixinnovation.co.uk    CNAME    em8479.dkim.sendgrid.net
s1._domainkey.email.adaptixinnovation.co.uk        CNAME    s1.domainkey.u8479.wl134.sendgrid.net
s2._domainkey.email.adaptixinnovation.co.uk        CNAME    s2.domainkey.u8479.wl134.sendgrid.net
```

### 2.2 Inbound Parse Configuration

#### Current Settings
```
Host: email.adaptixinnovation.co.uk
URL: https://d41e-86-163-177-54.ngrok-free.app/inbound
Send Raw: ✅ Enabled
Spam Check: ❌ Disabled
```

#### Webhook Data Format (Raw Mode)
SendGrid sends multipart/form-data with these fields:
```
email: Full raw email content (SMTP headers + body)
to: Recipient email address
from: Sender email address  
subject: Email subject line
dkim: DKIM verification result
SPF: SPF verification result
sender_ip: Originating IP address
envelope: JSON with routing information
charsets: Character encoding information
```

### 2.3 SendGrid API Configuration

#### Required Environment Variables
```bash
# SendGrid API Key (for sending emails)
SENDGRID_API_KEY=SG.your-api-key-here

# Webhook verification (optional)
SENDGRID_WEBHOOK_VERIFICATION_KEY=your-verification-key
```

#### API Endpoints Used
- **Inbound Parse API**: For webhook management
- **Mail Send API**: For sending responses
- **Domain Authentication API**: For domain verification

## 3. ngrok Configuration

### 3.1 Installation and Setup

#### Installation (macOS)
```bash
# Install via Homebrew
brew install ngrok

# Or download from https://ngrok.com/download
```

#### Authentication Setup
```bash
# Add your authtoken (one-time setup)
ngrok config add-authtoken 2qbrFxgjqCECJJmL3YkXJhXV7CJ_4coZiEKXqFBZt7exjyEC2

# Verify configuration
ngrok config check
```

### 3.2 Tunnel Configuration

#### Basic HTTP Tunnel
```bash
# Expose local port 8000 to internet
ngrok http 8000
```

#### Current Tunnel Details
```
Public URL: https://d41e-86-163-177-54.ngrok-free.app
Local URL: http://localhost:8000
Region: Europe (eu)
Account: junksamiad (Plan: Free)
```

#### ngrok Configuration File
Location: `~/.ngrok2/ngrok.yml`
```yaml
version: "2"
authtoken: 2qbrFxgjqCECJJmL3YkXJhXV7CJ_4coZiEKXqFBZt7exjyEC2
tunnels:
  hr-system:
    proto: http
    addr: 8000
    hostname: your-custom-domain.ngrok.io  # Pro feature
    inspect: true
```

### 3.3 ngrok Monitoring

#### Web Interface
- **URL**: http://127.0.0.1:4040
- **Features**: Request inspection, replay, response analysis
- **Real-time Traffic**: Monitor webhook calls from SendGrid

#### Traffic Analysis
```
Request Headers:
- User-Agent: SendGrid Event API
- Content-Type: multipart/form-data
- X-Forwarded-For: SendGrid IP ranges

Response Monitoring:
- 200 OK: Successful webhook processing
- 422 Unprocessable Entity: Data validation errors
- 500 Internal Server Error: Application errors
```

## 4. FastAPI Webhook Implementation

### 4.1 Endpoint Configuration

#### Webhook URL Structure
```
Production: https://your-domain.com/inbound
Development: https://d41e-86-163-177-54.ngrok-free.app/inbound
Testing: http://localhost:8000/inbound
```

#### Request Processing Flow
```python
@router.post("/inbound")
async def inbound_parse(
    email: str = Form(None),           # Raw email content
    to: str = Form(...),               # Required recipient
    from_email: str = Form(..., alias="from"),  # Required sender
    subject: str = Form(None),         # Email subject
    dkim: str = Form(None),           # DKIM verification
    SPF: str = Form(None),            # SPF verification
    sender_ip: str = Form(None),      # Sender IP
    envelope: str = Form(None),       # Routing info
    # ... file attachments
):
```

### 4.2 Data Validation and Processing

#### Input Validation
```python
# Pydantic models for data validation
class EmailWebhookData(BaseModel):
    email: Optional[str] = None
    to: str
    from_email: str = Field(alias="from")
    subject: Optional[str] = None
    dkim: Optional[str] = None
    spf: Optional[str] = Field(alias="SPF")
    sender_ip: Optional[str] = None
    envelope: Optional[str] = None
```

#### Error Handling
```python
try:
    # Process email data
    result = process_inbound_email(webhook_data)
    return PlainTextResponse("OK")
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    return PlainTextResponse("OK")  # Still return OK to avoid retries
except Exception as e:
    logger.error(f"Processing error: {e}")
    return PlainTextResponse("OK")
```

## 5. Development Environment Setup

### 5.1 Local Development Stack

#### Required Services
```bash
# 1. FastAPI Server (Terminal 1)
cd backend/api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. ngrok Tunnel (Terminal 2)
ngrok http 8000

# 3. Redis Server (Terminal 3) - Optional for background tasks
redis-server

# 4. Celery Worker (Terminal 4) - Optional for async processing
celery -A backend.services.celery_app worker --loglevel=info
```

#### Environment Variables
```bash
# .env file
DATABASE_URL=sqlite:///argan_email.db
OPENAI_API_KEY=your-openai-api-key
SENDGRID_API_KEY=your-sendgrid-api-key
SECRET_KEY=your-secret-key
DEBUG=True
```

### 5.2 Testing Workflow

#### Email Testing Process
1. **Start Local Server**: `uvicorn main:app --reload`
2. **Start ngrok Tunnel**: `ngrok http 8000`
3. **Update SendGrid Webhook**: Use ngrok URL
4. **Send Test Email**: To `test@email.adaptixinnovation.co.uk`
5. **Monitor Logs**: Check backend console and ngrok dashboard
6. **Verify Processing**: Confirm 200 OK response

#### Debugging Tools
```bash
# Test webhook endpoint directly
curl -X GET https://your-ngrok-url.ngrok-free.app/test

# Manual webhook test
curl -X POST "https://your-ngrok-url.ngrok-free.app/inbound" \
  -F "from=test@example.com" \
  -F "to=email@email.adaptixinnovation.co.uk" \
  -F "subject=Test Email" \
  -F "email=Raw email content here"

# DNS verification
dig MX email.adaptixinnovation.co.uk
dig A mx.sendgrid.net
```

## 6. Production Deployment Considerations

### 6.1 Infrastructure Requirements

#### Server Specifications
```
Minimum Requirements:
- CPU: 2 vCPUs
- RAM: 4GB
- Storage: 20GB SSD
- Network: 1Gbps

Recommended Production:
- CPU: 4 vCPUs
- RAM: 8GB
- Storage: 100GB SSD
- Network: 10Gbps
```

#### Domain and SSL
```
Domain: hr-system.arganhrconsultancy.co.uk
SSL Certificate: Let's Encrypt or commercial
Webhook URL: https://hr-system.arganhrconsultancy.co.uk/inbound
```

### 6.2 Security Hardening

#### Webhook Security
```python
# Verify SendGrid webhook signature
def verify_sendgrid_signature(payload, signature, timestamp):
    expected_signature = base64.b64encode(
        hmac.new(
            SENDGRID_WEBHOOK_KEY.encode(),
            (timestamp + payload).encode(),
            hashlib.sha256
        ).digest()
    )
    return hmac.compare_digest(signature, expected_signature)
```

#### Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/inbound")
@limiter.limit("100/minute")  # Limit webhook calls
async def inbound_parse(...):
```

## 7. Monitoring and Alerting

### 7.1 Health Checks

#### Endpoint Monitoring
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": check_database_connection(),
        "redis": check_redis_connection()
    }
```

#### External Monitoring
```bash
# Uptime monitoring
curl -f https://your-domain.com/health || alert_team

# DNS monitoring
dig MX email.adaptixinnovation.co.uk | grep mx.sendgrid.net || alert_dns_team
```

### 7.2 Logging Configuration

#### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Log webhook events
logger.info(
    "webhook_received",
    sender=from_email,
    recipient=to,
    subject=subject,
    timestamp=datetime.utcnow(),
    processing_time_ms=processing_time
)
```

## 8. Troubleshooting Guide

### 8.1 Common Issues

#### Email Not Reaching Webhook
```bash
# Check DNS resolution
dig MX email.adaptixinnovation.co.uk
# Should return: mx.sendgrid.net

# Check SendGrid server
dig A mx.sendgrid.net
# Should return multiple IP addresses

# Check ngrok tunnel
curl https://your-ngrok-url.ngrok-free.app/test
# Should return 200 OK
```

#### Webhook Returning 422 Errors
```python
# Common causes:
1. Missing required fields (to, from)
2. Incorrect field aliases (from vs from_email)
3. Data type mismatches
4. Pydantic validation errors

# Solution: Check FastAPI logs for validation details
```

#### SendGrid Authentication Issues
```bash
# Verify domain authentication
curl -X GET "https://api.sendgrid.com/v3/whitelabel/domains" \
  -H "Authorization: Bearer $SENDGRID_API_KEY"

# Check inbound parse settings
curl -X GET "https://api.sendgrid.com/v3/user/webhooks/parse/settings" \
  -H "Authorization: Bearer $SENDGRID_API_KEY"
```

### 8.2 Performance Optimization

#### Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_email_threads_ticket_number ON email_threads(ticket_number);
CREATE INDEX idx_email_messages_thread_id ON email_messages(thread_id);
CREATE INDEX idx_email_messages_created_at ON email_messages(created_at);
```

#### Caching Strategy
```python
# Redis caching for frequent queries
@cache.memoize(timeout=300)
def get_thread_by_ticket(ticket_number):
    return db.query(EmailThread).filter_by(ticket_number=ticket_number).first()
```

---

**Document Version**: 1.0  
**Last Updated**: May 30, 2025  
**Author**: Infrastructure Team  
**Review Date**: June 30, 2025 