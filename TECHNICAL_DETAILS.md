# Technical Implementation Details

## Automatic Ticket Number Generation

The system uses database-driven automatic ticket number generation to ensure:
- **Uniqueness**: No duplicate ticket numbers
- **Sequential ordering**: Numbers increment sequentially
- **Thread safety**: Multiple concurrent requests won't create duplicates
- **Database portability**: Works with both SQLite and PostgreSQL

### How It Works

1. **TicketCounter Table**: Maintains the last used ticket number
   ```sql
   CREATE TABLE ticket_counter (
       id INTEGER PRIMARY KEY CHECK (id = 1),
       last_number INTEGER DEFAULT 0
   );
   ```

2. **SQLAlchemy Event Listener**: Intercepts new EmailThread inserts
   ```python
   @event.listens_for(EmailThread, 'before_insert')
   def generate_ticket_number(mapper, connection, target):
       # Atomically increment counter and get new number
       # Generates format: ARG-00001, ARG-00002, etc.
   ```

3. **Database-Specific Implementation**:
   - **SQLite**: Uses separate UPDATE and SELECT statements
   - **PostgreSQL**: Uses UPDATE...RETURNING for atomic operation

### Ticket Number Format

- Pattern: `ARG-XXXXX` (e.g., ARG-00001, ARG-00002)
- Prefix: Configurable via `TICKET_PREFIX` setting (default: "ARG")
- Number: 5-digit zero-padded sequential number
- Maximum: 99,999 tickets (can be extended)

### Benefits

1. **No Manual Tracking**: Database handles all numbering
2. **Crash Recovery**: Counter persists in database
3. **Concurrent Safety**: Database transactions ensure no duplicates
4. **Easy Reset**: Can reset counter by updating ticket_counter table

### Testing

Run the ticket generation test:
```bash
python test_ticket_generation.py
```

This will:
- Initialize the database
- Create test threads
- Verify sequential numbering
- Check uniqueness
- Roll back test data

### Customization

To change the ticket prefix:
```python
# In config/settings.py or .env
TICKET_PREFIX=HR  # Changes format to HR-00001

# In backend/utils/database_setup.py
target.ticket_number = f"{settings.TICKET_PREFIX}-{next_number:05d}"
```

### Database Queries

View current ticket counter:
```sql
SELECT * FROM ticket_counter;
```

Reset counter (use with caution):
```sql
UPDATE ticket_counter SET last_number = 0 WHERE id = 1;
```

Find highest ticket number in use:
```sql
SELECT MAX(CAST(SUBSTR(ticket_number, 5) AS INTEGER)) 
FROM email_threads 
WHERE ticket_number LIKE 'ARG-%';
``` 