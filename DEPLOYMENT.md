# Deployment Guide

## Backend Deployment Options

### Option 1: Deploy to Heroku

1. Install Heroku CLI
2. Create `Procfile`:
```
web: uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
worker: celery -A backend.services.celery_app worker --loglevel=info
beat: celery -A backend.services.celery_app beat --loglevel=info
```

3. Deploy:
```bash
heroku create argan-email-backend
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
heroku config:set EMAIL_PASSWORD=your-password
heroku config:set OPENAI_API_KEY=your-key
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

### Option 2: Deploy to AWS EC2

1. Launch EC2 instance (Ubuntu 22.04)
2. Install dependencies:
```bash
sudo apt update
sudo apt install python3-pip postgresql redis-server nginx
```

3. Set up systemd services for API and workers
4. Configure Nginx as reverse proxy

### Option 3: Deploy to Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Docker Compose setup:
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/argan
    depends_on:
      - db
      - redis
  
  worker:
    build: .
    command: celery -A backend.services.celery_app worker
    depends_on:
      - redis
      - db
  
  beat:
    build: .
    command: celery -A backend.services.celery_app beat
    depends_on:
      - redis
      - db
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=argan
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7
```

## Frontend Deployment (Vercel)

1. Build your frontend in v0
2. Connect to GitHub
3. Deploy to Vercel:
```bash
vercel
```

4. Set environment variables:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

## Production Checklist

### Security
- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS (SSL certificates)
- [ ] Configure CORS properly
- [ ] Set DEBUG=False
- [ ] Enable rate limiting
- [ ] Set up firewall rules

### Database
- [ ] Use PostgreSQL (not SQLite)
- [ ] Set up regular backups
- [ ] Configure connection pooling
- [ ] Set up read replicas if needed

### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Configure logging (CloudWatch/LogDNA)
- [ ] Set up uptime monitoring
- [ ] Configure alerts

### Performance
- [ ] Enable caching (Redis)
- [ ] Set up CDN for static assets
- [ ] Configure auto-scaling
- [ ] Optimize database queries

### Email
- [ ] Verify email sending limits
- [ ] Set up email bounce handling
- [ ] Configure SPF/DKIM records
- [ ] Monitor email reputation

## Environment Variables (Production)

```env
# Production settings
DEBUG=False
DATABASE_URL=postgresql://user:password@host/database
REDIS_URL=redis://redis-host:6379
SECRET_KEY=generate-strong-secret-key
EMAIL_PASSWORD=production-email-password
OPENAI_API_KEY=production-api-key

# Optional: Email alternatives
# Consider using email service like SendGrid/AWS SES for better deliverability
SMTP_SERVICE=sendgrid
SENDGRID_API_KEY=your-api-key
```

## Scaling Considerations

1. **Database**: Use connection pooling and read replicas
2. **API**: Deploy multiple instances behind load balancer
3. **Workers**: Scale Celery workers based on queue size
4. **Email**: Consider dedicated email service for high volume
5. **AI**: Monitor OpenAI API usage and costs

## Cost Optimization

1. Use reserved instances for predictable workloads
2. Set up auto-scaling to handle peak loads
3. Monitor OpenAI API usage to control costs
4. Use caching to reduce database queries
5. Consider serverless for variable workloads 