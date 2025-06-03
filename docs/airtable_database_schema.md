# Airtable Database Schema - HR Email Management System

## Table: `argan_call_log`

**Purpose:** Store and manage email tickets for the HR Email Management System
**Base Type:** Airtable Base
**Access:** Backend2 application via pyairtable SDK

---

## Field Definitions

### 🎫 Ticket Tracking Fields

#### `ticket_number`
- **Type:** Single Line Text
- **Required:** Yes (Unique)
- **Format:** `ARG-YYYYMMDD-NNNN`
- **Example:** `ARG-20250603-0001`
- **Description:** Unique ticket identifier generated for each new email inquiry
- **Usage:** Primary identifier for tracking email conversations and responses
- **Constraints:** Must be unique across all records

#### `status`
- **Type:** Single Select
- **Required:** Yes
- **Default:** `new`
- **Options:**
  - `new` (Red) - Newly received email, not yet processed
  - `in_progress` (Yellow) - HR team is working on the inquiry
  - `resolved` (Green) - Issue resolved, awaiting closure
  - `closed` (Gray) - Ticket closed and archived
- **Description:** Current processing status of the email ticket
- **Usage:** Workflow management and reporting

#### `created_at`
- **Type:** Date & Time
- **Required:** Yes
- **Include Time:** Yes
- **Format:** ISO 8601 (YYYY-MM-DDTHH:MM:SS.sssZ)
- **Example:** `2025-06-03T14:30:45.123Z`
- **Description:** Timestamp when the email was received and processed by the system
- **Usage:** Tracking, reporting, SLA monitoring

---

### 📧 Email Content Fields

#### `subject`
- **Type:** Single Line Text
- **Required:** No
- **Max Length:** ~1000 characters (Airtable limit)
- **Example:** `"Question about holiday policy"`
- **Description:** Email subject line as received from the sender
- **Usage:** Display in UI, searching, classification

#### `email_body`
- **Type:** Long Text
- **Required:** No
- **Max Length:** ~100,000 characters (Airtable limit)
- **Content:** Plain text or HTML content
- **Description:** Full email body content after text/HTML processing
- **Usage:** AI analysis, HR review, response generation
- **Note:** Will be processed through text/HTML logic (to be implemented)

#### `original_sender`
- **Type:** Email
- **Required:** No
- **Format:** Valid email address
- **Example:** `user@company.com`
- **Description:** Original sender's email address, extracted from forwarded email headers
- **Usage:** Auto-reply routing, contact management
- **Note:** Extracted from forwarded email headers using header parsing logic

---

### 🔧 Technical Fields

#### `message_id`
- **Type:** Single Line Text
- **Required:** No (Unique when present)
- **Format:** RFC 2822 Message-ID
- **Example:** `<256304D3-3BE0-4EC0-91A0-EF12F7C3463C@gmail.com>`
- **Description:** Email Message-ID header for deduplication and thread tracking
- **Usage:** Prevent duplicate processing, conversation threading
- **Constraints:** Should be unique when not "unknown"

#### `raw_headers`
- **Type:** Long Text
- **Required:** No
- **Content:** Email headers in raw format
- **Description:** Conversation-relevant headers (Message-ID, In-Reply-To, References)
- **Usage:** Email thread reconstruction, debugging, compliance
- **Example:**
  ```
  Message-Id: <ABC123@gmail.com>
  In-Reply-To: <XYZ789@gmail.com>
  References: <DEF456@gmail.com> <XYZ789@gmail.com>
  ```

---

### 🔒 Security Fields

#### `spf_result`
- **Type:** Single Line Text
- **Required:** No
- **Values:** `pass`, `fail`, `neutral`, `softfail`, `temperror`, `permerror`
- **Example:** `pass`
- **Description:** SPF (Sender Policy Framework) validation result from SendGrid
- **Usage:** Email authentication verification, security analysis

#### `dkim_result`
- **Type:** Single Line Text
- **Required:** No
- **Format:** JSON or simple text
- **Example:** `{@gmail.com : pass}`
- **Description:** DKIM (DomainKeys Identified Mail) validation result from SendGrid
- **Usage:** Email authentication verification, security analysis

---

### 📎 Attachment Fields

#### `has_attachments`
- **Type:** Checkbox
- **Required:** Yes
- **Default:** `false`
- **Description:** Boolean flag indicating if the email contains attachments
- **Usage:** UI display, processing workflows, attachment handling

#### `attachment_count`
- **Type:** Number
- **Required:** Yes
- **Default:** `0`
- **Precision:** 0 (integers only)
- **Range:** 0 to 999+
- **Description:** Number of attachments in the original email
- **Usage:** Attachment processing, UI display, storage planning

#### `attachment_info`
- **Type:** Long Text
- **Required:** No
- **Default:** `{}`
- **Format:** JSON string
- **Description:** Detailed attachment metadata (filenames, sizes, types)
- **Usage:** Attachment processing, security scanning, storage management
- **Future Structure:**
  ```json
  {
    "attachments": [
      {
        "filename": "document.pdf",
        "size": 1024000,
        "content_type": "application/pdf",
        "stored_path": "/attachments/ARG-20250603-0001/document.pdf"
      }
    ]
  }
  ```

---

### 📤 Auto-Reply Tracking

#### `initial_auto_reply_sent`
- **Type:** Checkbox
- **Required:** Yes
- **Default:** `false`
- **Description:** Whether the initial auto-reply with ticket number was sent to the original sender
- **Usage:** Preventing duplicate auto-replies, debugging email flow
- **Note:** Only tracks the first auto-reply; conversation replies tracked separately

---

## Relationships & Indexing

### Primary Keys
- **Airtable Record ID:** Automatic unique identifier
- **Business Key:** `ticket_number` (unique)

### Unique Constraints
- `ticket_number` - Business identifier
- `message_id` - Prevents duplicate email processing (when not "unknown")

### Indexes (Airtable Views)
Recommended views for efficient querying:
- **By Status:** Group by `status` field
- **By Date:** Sort by `created_at` descending
- **By Sender:** Group by `original_sender`
- **Unprocessed:** Filter where `initial_auto_reply_sent = false`

---

## Data Flow

### New Email Processing
1. Email received via SendGrid webhook
2. AI classification determines this is a new email
3. Ticket number generated (`ARG-YYYYMMDD-NNNN`)
4. Data extracted from context object
5. Record created in Airtable with `status = "new"`
6. Auto-reply sent, `initial_auto_reply_sent = true`

### Existing Email Processing
1. Email received via SendGrid webhook  
2. AI classification finds existing ticket number
3. Look up existing record by `ticket_number`
4. Update conversation history (future implementation)
5. Notify HR team of new response

---

## API Usage Examples

### Create New Record
```python
from pyairtable import Table

table = Table(api_key, base_id, "argan_call_log")

record = table.create({
    "ticket_number": "ARG-20250603-0001",
    "status": "new",
    "subject": "Holiday policy question",
    "original_sender": "user@company.com",
    "initial_auto_reply_sent": False
})
```

### Query Records
```python
# Get all new tickets
new_tickets = table.all(formula="status = 'new'")

# Find by ticket number
ticket = table.first(formula=f"ticket_number = 'ARG-20250603-0001'")

# Get recent tickets
recent = table.all(
    sort=["created_at"],
    max_records=50
)
```

### Update Record
```python
table.update(record_id, {
    "status": "in_progress",
    "initial_auto_reply_sent": True
})
```

---

## Future Enhancements

### Conversation History
- **Table:** `conversation_history` (separate table)
- **Relationship:** Links to `argan_call_log` via `ticket_number`
- **Purpose:** Store email thread/conversation chain

### Attachment Storage
- **Integration:** File storage service (S3, Google Drive, etc.)
- **Metadata:** Enhanced `attachment_info` JSON structure
- **Security:** Virus scanning, content filtering

### HR Assignment
- **Field:** `assigned_to` (Link to HR staff table)
- **Workflow:** Auto-assignment rules based on content/category

### Analytics Fields
- **Fields:** `response_time`, `resolution_time`, `customer_satisfaction`
- **Purpose:** Performance metrics and reporting

---

## Security & Compliance

### Data Protection
- All email content stored securely in Airtable
- Access controlled via Airtable permissions
- API keys managed via environment variables

### Retention Policy
- Consider implementing data retention policies
- Archive old tickets based on business requirements
- GDPR/privacy compliance for email content

### Audit Trail
- Airtable automatically tracks record creation/modification
- Additional audit logging in application logs
- Version history available in Airtable interface 