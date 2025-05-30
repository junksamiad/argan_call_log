# HR Email Management System - High-Level Design (HLD)

## 1. System Overview

The HR Email Management System is designed to automatically process HR queries sent via email, generate AI-powered responses, and provide a dashboard for HR staff to review and send approved responses.

### 1.1 Business Requirements
- **Automatic Email Processing**: Capture emails sent to `argan-bot@arganhrconsultancy.co.uk`
- **AI-Powered Analysis**: Extract structured data and generate suggested responses
- **Ticket Management**: Auto-generate unique ticket numbers (ARG-00001, ARG-00002, etc.)
- **Approval Workflow**: HR staff review and approve responses before sending
- **Thread Tracking**: Link email conversations using ticket numbers in subject lines

### 1.2 Key Features
- Real-time email ingestion via SendGrid Inbound Parse
- OpenAI GPT-4 integration for content analysis and response generation
- RESTful API backend with FastAPI
- Database storage with SQLAlchemy (SQLite/PostgreSQL)
- Background processing with Celery
- Web dashboard for HR staff management

## 2. System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Email Sender  │───▶│   SendGrid   │───▶│   ngrok Tunnel  │
│  (Staff/Client) │    │ Inbound Parse│    │ (Development)   │
└─────────────────┘    └──────────────┘    └─────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                FastAPI Backend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Webhook    │  │   API       │  │   Authentication    │ │
│  │  Endpoint   │  │ Endpoints   │  │     & Security      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenAI API    │    │   Database      │    │   Celery        │
│   (GPT-4)       │    │ (SQLite/PgSQL)  │    │ Background      │
│                 │    │                 │    │ Workers         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────────────┐
                    │     Frontend Dashboard  │
                    │    (React/Vue/v0)       │
                    │                         │
                    └─────────────────────────┘
```

## 3. Component Architecture

### 3.1 Email Ingestion Layer
- **SendGrid Inbound Parse**: Receives emails and forwards to webhook
- **DNS Configuration**: MX records route emails to SendGrid
- **ngrok Tunnel**: Exposes local development server to internet

### 3.2 API Layer (FastAPI)
- **Webhook Endpoint** (`/inbound`): Receives emails from SendGrid
- **Authentication**: JWT-based user authentication
- **CRUD Operations**: Thread and message management
- **File Handling**: Attachment processing and storage

### 3.3 Data Processing Layer
- **Email Parser**: Extracts metadata, content, and attachments
- **AI Integration**: OpenAI GPT-4 for analysis and response generation
- **Ticket Generator**: Auto-incremental ticket numbering system
- **Thread Linking**: Subject line parsing for conversation tracking

### 3.4 Data Storage Layer
- **Primary Database**: SQLite (development) / PostgreSQL (production)
- **Models**: EmailThread, EmailMessage, EmailAttachment, User, TicketCounter
- **File Storage**: Local filesystem (development) / Cloud storage (production)

### 3.5 Background Processing
- **Celery Workers**: Async email processing and AI analysis
- **Redis**: Message broker and caching
- **Scheduled Tasks**: Periodic cleanup and maintenance

## 4. Data Flow

### 4.1 Inbound Email Processing
1. **Email Reception**: Staff sends email to `argan-bot@arganhrconsultancy.co.uk`
2. **DNS Routing**: MX record routes to `mx.sendgrid.net`
3. **SendGrid Processing**: Parses email and sends to webhook
4. **Webhook Reception**: FastAPI receives multipart/form-data
5. **Ticket Generation**: Check subject for existing ticket or create new
6. **Database Storage**: Store email thread and message data
7. **AI Processing**: Queue for background analysis
8. **Dashboard Update**: Real-time updates for HR staff

### 4.2 Response Generation Flow
1. **AI Analysis**: Extract query type, urgency, staff details
2. **Response Generation**: Create suggested response using GPT-4
3. **Database Update**: Store AI analysis and suggested response
4. **Notification**: Alert HR staff of new query
5. **Review Process**: HR staff review and edit response
6. **Approval**: Manager approves response
7. **Email Sending**: Send response with ticket number in subject

## 5. Security Architecture

### 5.1 Authentication & Authorization
- **JWT Tokens**: Secure API access
- **Role-Based Access**: Admin, HR Staff, Manager roles
- **Session Management**: Secure session handling

### 5.2 Data Security
- **Input Validation**: Pydantic models for data validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **File Upload Security**: Type and size validation
- **Environment Variables**: Secure credential storage

### 5.3 Communication Security
- **HTTPS**: All API communications encrypted
- **Webhook Verification**: SendGrid signature validation
- **CORS Configuration**: Controlled cross-origin requests

## 6. Scalability Considerations

### 6.1 Horizontal Scaling
- **Stateless API**: Enables multiple server instances
- **Database Connection Pooling**: Efficient resource utilization
- **Celery Workers**: Scalable background processing
- **Load Balancing**: Distribute traffic across instances

### 6.2 Performance Optimization
- **Database Indexing**: Optimized query performance
- **Caching Strategy**: Redis for frequently accessed data
- **Async Processing**: Non-blocking email handling
- **File Compression**: Efficient attachment storage

## 7. Monitoring & Observability

### 7.1 Logging
- **Structured Logging**: JSON format for analysis
- **Log Levels**: Debug, Info, Warning, Error, Critical
- **Request Tracing**: Track email processing pipeline
- **Error Tracking**: Comprehensive error reporting

### 7.2 Metrics
- **Email Volume**: Track incoming email rates
- **Processing Time**: Monitor response times
- **Error Rates**: Track failed processing attempts
- **User Activity**: Dashboard usage analytics

## 8. Deployment Architecture

### 8.1 Development Environment
- **Local FastAPI**: uvicorn development server
- **SQLite Database**: File-based storage
- **ngrok Tunnel**: External access for webhooks
- **Local Redis**: Background task processing

### 8.2 Production Environment
- **Container Deployment**: Docker containers
- **PostgreSQL**: Production database
- **Reverse Proxy**: nginx for load balancing
- **Cloud Storage**: S3/GCS for file attachments
- **Monitoring**: Prometheus + Grafana

## 9. Integration Points

### 9.1 External Services
- **SendGrid**: Email processing and delivery
- **OpenAI API**: AI analysis and response generation
- **DNS Provider**: MX record management
- **Cloud Provider**: Hosting and storage

### 9.2 Internal Integrations
- **Database**: SQLAlchemy ORM
- **Background Tasks**: Celery + Redis
- **Authentication**: JWT + bcrypt
- **File Storage**: Local/Cloud abstraction layer

## 10. Future Enhancements

### 10.1 Planned Features
- **Multi-language Support**: Internationalization
- **Advanced Analytics**: Reporting dashboard
- **Mobile App**: iOS/Android applications
- **Integration APIs**: Third-party system connections

### 10.2 Scalability Roadmap
- **Microservices**: Service decomposition
- **Event-Driven Architecture**: Async messaging
- **Multi-tenant Support**: Organization isolation
- **Global Deployment**: Multi-region hosting

---

**Document Version**: 1.0  
**Last Updated**: May 30, 2025  
**Author**: System Architecture Team 