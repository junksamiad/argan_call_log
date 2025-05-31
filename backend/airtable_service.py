"""
Airtable Service for HR Email Management System
Handles all interactions with Airtable as the primary database
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pyairtable import Api
import json

logger = logging.getLogger(__name__)


class AirtableService:
    def __init__(self):
        """Initialize Airtable service"""
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME", "call_log")
        
        if not self.api_key or not self.base_id:
            raise ValueError("AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in environment variables")
        
        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, self.table_name)
        
        logger.info(f"📊 [AIRTABLE] Connected to base {self.base_id}, table {self.table_name}")
    
    def create_email_record(self, email_data: Dict[str, Any], ticket_number: str, 
                           classification_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new email record in Airtable
        
        Args:
            email_data: Email data from SendGrid
            ticket_number: Generated ticket number
            classification_data: AI classification results
            
        Returns:
            Created Airtable record
        """
        try:
            # Prepare the record data
            record_data = {
                "Ticket Number": ticket_number,
                "Sender Email": email_data.get('sender'),
                "Sender Name": email_data.get('sender_name', ''),
                "Subject": email_data.get('subject', ''),
                "Body Text": email_data.get('body_text', ''),
                "Body HTML": email_data.get('body_html', ''),
                "Message ID": email_data.get('message_id', ''),
                "Email Date": self._format_datetime(email_data.get('email_date')),
                "Recipients": json.dumps(email_data.get('recipients', [])),
                "CC Recipients": json.dumps(email_data.get('cc', [])),
                "Message Type": "Inbound",
                "Status": "Open",
                "Priority": "Normal",
                "Created At": datetime.utcnow().isoformat(),
                "DKIM Status": email_data.get('dkim', ''),
                "SPF Status": email_data.get('spf', '')
            }
            
            # Add AI classification data if available
            if classification_data:
                ai_data = classification_data.get('ai_extracted_data', {})
                record_data.update({
                    "AI Classification": classification_data.get('EMAIL_CLASSIFICATION', ''),
                    "AI Confidence": classification_data.get('confidence_score', 0),
                    "Urgency Keywords": json.dumps(ai_data.get('urgency_keywords', [])),
                    "Sentiment Tone": ai_data.get('sentiment_tone', ''),
                    "AI Processing Timestamp": self._format_datetime(classification_data.get('processing_timestamp')),
                    "AI Notes": classification_data.get('notes', '')
                })
            
            # Create the record
            created_record = self.table.create(record_data)
            
            logger.info(f"📊 [AIRTABLE] Created record for ticket {ticket_number}")
            return created_record
            
        except Exception as e:
            logger.error(f"📊 [AIRTABLE] Error creating record: {e}")
            raise
    
    def find_ticket(self, ticket_number: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing ticket by ticket number
        
        Args:
            ticket_number: Ticket number to search for
            
        Returns:
            Airtable record if found, None otherwise
        """
        try:
            records = self.table.all(formula=f"{{Ticket Number}} = '{ticket_number}'")
            
            if records:
                logger.info(f"📊 [AIRTABLE] Found existing ticket {ticket_number}")
                return records[0]
            else:
                logger.info(f"📊 [AIRTABLE] No existing ticket found for {ticket_number}")
                return None
                
        except Exception as e:
            logger.error(f"📊 [AIRTABLE] Error finding ticket {ticket_number}: {e}")
            return None
    
    def update_conversation(self, ticket_number: str, new_message_data: Dict[str, Any]) -> bool:
        """
        Update an existing ticket with new conversation data
        
        Args:
            ticket_number: Ticket number to update
            new_message_data: New message data to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find the existing record
            existing_record = self.find_ticket(ticket_number)
            if not existing_record:
                logger.warning(f"📊 [AIRTABLE] Cannot update - ticket {ticket_number} not found")
                return False
            
            record_id = existing_record['id']
            
            # Get existing conversation data
            existing_conversation = existing_record['fields'].get('Conversation History', '[]')
            try:
                conversation_list = json.loads(existing_conversation)
            except:
                conversation_list = []
            
            # Add new message to conversation
            new_message = {
                "timestamp": datetime.utcnow().isoformat(),
                "sender": new_message_data.get('sender'),
                "message_id": new_message_data.get('message_id'),
                "subject": new_message_data.get('subject'),
                "body_text": new_message_data.get('body_text'),
                "message_type": "Reply"
            }
            
            conversation_list.append(new_message)
            
            # Update the record
            updated_fields = {
                "Conversation History": json.dumps(conversation_list),
                "Last Updated": datetime.utcnow().isoformat(),
                "Message Count": len(conversation_list)
            }
            
            self.table.update(record_id, updated_fields)
            
            logger.info(f"📊 [AIRTABLE] Updated conversation for ticket {ticket_number}")
            return True
            
        except Exception as e:
            logger.error(f"📊 [AIRTABLE] Error updating conversation for {ticket_number}: {e}")
            return False
    
    def get_ticket_counter(self) -> int:
        """
        Get the next ticket number from Airtable
        This is a simple implementation - in production you might want a dedicated counter table
        """
        try:
            # Get all records and find the highest ticket number
            all_records = self.table.all()
            
            max_number = 0
            today = datetime.now().strftime("%Y%m%d")
            
            for record in all_records:
                ticket_num = record['fields'].get('Ticket Number', '')
                if ticket_num.startswith(f"ARG-{today}-"):
                    try:
                        number_part = int(ticket_num.split('-')[-1])
                        max_number = max(max_number, number_part)
                    except:
                        continue
            
            return max_number + 1
            
        except Exception as e:
            logger.error(f"📊 [AIRTABLE] Error getting ticket counter: {e}")
            return 1
    
    def _format_datetime(self, dt_input: Any) -> Optional[str]:
        """Format datetime for Airtable - returns None for empty/invalid dates"""
        if dt_input is None or dt_input == '' or dt_input == 'Unknown':
            return None  # Airtable accepts None for empty dateTime fields
        elif isinstance(dt_input, datetime):
            return dt_input.isoformat()
        elif isinstance(dt_input, str):
            # Try to parse and validate the string
            try:
                from dateutil import parser
                parsed_date = parser.parse(dt_input)
                return parsed_date.isoformat()
            except:
                # If string can't be parsed as date, return None
                logger.warning(f"📊 [AIRTABLE] Invalid date string: {dt_input}, using None")
                return None
        else:
            # For any other type, use current time as fallback
            return datetime.utcnow().isoformat()
    
    def health_check(self) -> bool:
        """Check if Airtable connection is working"""
        try:
            # Try to get table info
            table_info = self.table.schema()
            logger.info(f"📊 [AIRTABLE] Health check passed - table has {len(table_info['fields'])} fields")
            return True
        except Exception as e:
            logger.error(f"📊 [AIRTABLE] Health check failed: {e}")
            return False

    def find_ticket_by_number(self, ticket_number: str) -> Optional[Dict[str, Any]]:
        """
        Alias for find_ticket method for consistency
        
        Args:
            ticket_number: Ticket number to search for
            
        Returns:
            Airtable record if found, None otherwise
        """
        return self.find_ticket(ticket_number) 