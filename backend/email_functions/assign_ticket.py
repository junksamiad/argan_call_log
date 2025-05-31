"""
Database setup utilities for automatic ticket number generation
"""
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from backend.database import EmailThread, TicketCounter
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@event.listens_for(EmailThread, 'before_insert')
def generate_ticket_number(mapper, connection, target):
    """
    Automatically generate ticket number before inserting a new EmailThread
    """
    if target.ticket_number is None:
        # Check if SQLite (doesn't support RETURNING)
        dialect_name = connection.dialect.name
        
        if dialect_name == 'sqlite':
            # SQLite approach
            connection.execute(text(
                "UPDATE ticket_counter SET last_number = last_number + 1 WHERE id = 1"
            ))
            result = connection.execute(text(
                "SELECT last_number FROM ticket_counter WHERE id = 1"
            ))
            row = result.fetchone()
            
            if row is None:
                # First time - initialize counter
                connection.execute(text(
                    "INSERT INTO ticket_counter (id, last_number) VALUES (1, 1)"
                ))
                next_number = 1
            else:
                next_number = row[0]
        else:
            # PostgreSQL and others that support RETURNING
            result = connection.execute(text(
                "UPDATE ticket_counter SET last_number = last_number + 1 WHERE id = 1 RETURNING last_number"
            ))
            row = result.fetchone()
            
            if row is None:
                # First time - initialize counter
                connection.execute(text(
                    "INSERT INTO ticket_counter (id, last_number) VALUES (1, 1)"
                ))
                next_number = 1
            else:
                next_number = row[0]
            
        # Format ticket number with leading zeros
        today = datetime.now().strftime("%Y%m%d")
        ticket_number = f"ARG-{today}-{next_number:04d}"
        target.ticket_number = ticket_number
        logger.info(f"🎫 [TICKET ASSIGN] Generated ticket number: {target.ticket_number}")


def init_ticket_counter(db_session):
    """
    Initialize the ticket counter if it doesn't exist
    """
    counter = db_session.query(TicketCounter).first()
    if not counter:
        counter = TicketCounter(last_number=0)
        db_session.add(counter)
        db_session.commit()
        logger.info("🎫 [TICKET COUNTER] Ticket counter initialized") 