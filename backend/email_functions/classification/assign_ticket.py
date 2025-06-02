"""
Ticket number generation using Airtable as the database
"""
import logging
from datetime import datetime
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