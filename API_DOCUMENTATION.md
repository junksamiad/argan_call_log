# Argan HR Email Management System - API Documentation

Base URL: `http://localhost:8000`

## Authentication

Most endpoints require authentication. Use the `/api/v1/auth/token` endpoint to get an access token.

### Login
```
POST /api/v1/auth/token
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

Use the token in subsequent requests:
```
Authorization: Bearer <access_token>
```

## Email Thread Endpoints

### List Email Threads

Get paginated list of email threads.

```
GET /api/v1/threads?page=1&page_size=20&status=open&priority=high
```

Query Parameters:
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20)
- `status` (string): Filter by status (open, pending_approval, closed)
- `priority` (string): Filter by priority (low, normal, high, urgent)

Response:
```json
{
  "threads": [
    {
      "id": 1,
      "thread_id": "550e8400-e29b-41d4-a716-446655440000",
      "ticket_number": "ARG-00001",
      "subject": "Leave Request Query",
      "status": "open",
      "priority": "normal",
      "staff_email": "john.doe@client.com",
      "staff_name": "John Doe",
      "query_type": "leave_request",
      "department": "Sales",
      "summary": "Employee requesting clarification on annual leave policy",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:45:00Z",
      "message_count": 3,
      "last_message_date": "2024-01-15T14:45:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20
}
```

### Get Thread Details

```
GET /api/v1/threads/{thread_id}
```

Response: Single thread object (same structure as list item)

### Get Thread Messages

```
GET /api/v1/threads/{thread_id}/messages
```

Response:
```json
[
  {
    "id": 1,
    "thread_id": 1,
    "message_id": "<message-id@mail.server>",
    "sender": "john.doe@client.com",
    "recipients": ["argan-bot@arganhrconsultancy.co.uk"],
    "cc": [],
    "subject": "Leave Request Query",
    "body_text": "Hello, I have a question about...",
    "body_html": "<html>...",
    "message_type": "inbound",
    "direction": "in",
    "suggested_response": "Dear John,\n\nThank you for your query...",
    "requires_approval": true,
    "approved_by": null,
    "approved_at": null,
    "email_date": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-15T10:31:00Z"
  }
]
```

### Send Reply

```
POST /api/v1/threads/{thread_id}/reply
Content-Type: application/json

{
  "body": "Dear John,\n\nThank you for your query regarding annual leave...",
  "recipients": ["john.doe@client.com"],
  "cc": ["ops.manager@client.com"],
  "requires_approval": false,
  "is_html": false
}
```

Response:
```json
{
  "message": "Reply sent successfully",
  "thread_id": 1
}
```

### Update Thread Status

```
PUT /api/v1/threads/{thread_id}/status
Content-Type: application/json

{
  "status": "closed"
}
```

Status values: `open`, `pending_approval`, `closed`

Response:
```json
{
  "message": "Status updated",
  "thread_id": 1,
  "status": "closed"
}
```

## Email Processing

### Manually Trigger Email Processing

```
POST /api/v1/process-emails
```

This endpoint triggers the email processing pipeline in the background.

Response:
```json
{
  "message": "Email processing started"
}
```

## Message Management

### Approve Message

```
PUT /api/v1/messages/{message_id}/approve
Content-Type: application/json

{
  "approved_by": "jane.manager@company.com"
}
```

Response:
```json
{
  "message": "Message approved",
  "message_id": 5
}
```

## WebSocket Support (Future)

For real-time updates, connect to:
```
ws://localhost:8000/ws
```

Events:
- `new_thread`: New email thread created
- `thread_updated`: Thread status or content updated
- `new_message`: New message in existing thread

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

API endpoints are rate-limited to:
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users

## CORS

CORS is enabled for all origins in development. Configure appropriately for production.

## Interactive Documentation

Visit `http://localhost:8000/docs` for Swagger UI interactive documentation.
Visit `http://localhost:8000/redoc` for ReDoc documentation. 