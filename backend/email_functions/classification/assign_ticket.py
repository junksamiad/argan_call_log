"""
Database setup utilities for automatic ticket number generation
"""
from sqlalchemy import event, text
from sqlalchemy.orm import Session
from backend.database import EmailThread, TicketCounter
import logging
from datetime import datetime
import os
from backend.airtable_service import AirtableService

logger = logging.getLogger(__name__)


def generate_ticket_number_standalone() -> str:
    """
    Generate a ticket number using Airtable for counter management
    
    Returns:
        Formatted ticket number like ARG-20250531-0001
    """
    try:
        today = datetime.now().strftime("%Y%m%d")
        
        # Use Airtable to get the next ticket number for today
        airtable = AirtableService()
        
        # Count existing tickets for today to determine next number
        # Search for tickets that start with today's date
        all_records = airtable.table.all()
        
        # Filter tickets created today
        today_tickets = []
        for record in all_records:
            ticket_num = record['fields'].get('Ticket Number', '')
            if ticket_num.startswith(f"ARG-{today}-"):
                today_tickets.append(ticket_num)
        
        # Determine next number
        if today_tickets:
            # Extract numbers and find the highest
            numbers = []
            for ticket in today_tickets:
                try:
                    # Extract the last 4 digits
                    num_part = ticket.split('-')[-1]
                    numbers.append(int(num_part))
                except:
                    continue
            
            next_number = max(numbers) + 1 if numbers else 1
        else:
            next_number = 1
        
        # Format ticket number with leading zeros
        ticket_number = f"ARG-{today}-{next_number:04d}"
        logger.info(f"🎫 [TICKET GEN] Generated ticket number: {ticket_number}")
        
        return ticket_number
        
    except Exception as e:
        logger.error(f"❌ [TICKET GEN] Error generating ticket: {e}")
        # Fallback to timestamp-based numbering
        import time
        fallback_number = int(time.time()) % 10000
        today = datetime.now().strftime("%Y%m%d")
        return f"ARG-{today}-{fallback_number:04d}"


# Alias for backward compatibility
generate_ticket_number = generate_ticket_number_standalone


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