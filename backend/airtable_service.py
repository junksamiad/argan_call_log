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
                "Body HTML": email_data.get('body_html', ''),
                "Message ID": email_data.get('message_id', ''),
                "Email Date": self._format_datetime(email_data.get('email_date')),
                "Recipients": json.dumps(email_data.get('recipients', [])),
                "CC Recipients": json.dumps(email_data.get('cc', [])),
                "Conversation History": email_data.get('conversation_history', '[]'),
                "Message Type": "Inbound",
                "Status": "Open",
                "Priority": "Normal",
                "Created At": datetime.utcnow().isoformat(),
                "DKIM Status": email_data.get('dkim', ''),
                "SPF Status": email_data.get('spf', '')
            }
            
            # DEBUG: Log the Message ID being stored
            message_id = email_data.get('message_id', '')
            logger.info(f"🐛 [AIRTABLE DEBUG] Message ID to store: '{message_id}' (length: {len(message_id)})")
            if not message_id:
                logger.warning(f"🐛 [AIRTABLE DEBUG] ⚠️ Message ID is empty! Email data keys: {list(email_data.keys())}")
            else:
                logger.info(f"🐛 [AIRTABLE DEBUG] ✅ Message ID found: {message_id}")
            
            # Process attachment data
            attachments = email_data.get('attachments', [])
            attachment_count = 0
            attachment_names = []
            
            if attachments:
                try:
                    # Handle attachments count (SendGrid sends as string)
                    if isinstance(attachments, str) and attachments.isdigit():
                        attachment_count = int(attachments)
                    elif isinstance(attachments, list):
                        attachment_count = len(attachments)
                        attachment_names = [att.get('filename', 'unnamed') for att in attachments if isinstance(att, dict)]
                    
                    # Look for attachment-info field with metadata
                    attachment_info = email_data.get('attachment-info', '')
                    if attachment_info:
                        try:
                            if isinstance(attachment_info, str):
                                attachment_metadata = json.loads(attachment_info)
                            else:
                                attachment_metadata = attachment_info
                            
                            # Extract filenames from attachment metadata
                            for key, info in attachment_metadata.items():
                                if isinstance(info, dict) and 'filename' in info:
                                    attachment_names.append(info['filename'])
                            
                            # Update count if we got more info from metadata
                            if len(attachment_names) > attachment_count:
                                attachment_count = len(attachment_names)
                                
                        except json.JSONDecodeError:
                            logger.warning(f"📎 [ATTACHMENTS] Failed to parse attachment-info: {attachment_info}")
                    
                    logger.info(f"📎 [ATTACHMENTS] Found {attachment_count} attachments: {attachment_names}")
                    
                except Exception as e:
                    logger.error(f"📎 [ATTACHMENTS] Error processing attachments: {e}")
            
            # Add attachment data to record
            record_data.update({
                "Has Attachments": attachment_count > 0,
                "Attachment Count": attachment_count,
                "Attachment Names": json.dumps(attachment_names) if attachment_names else "[]"
            })
            
            # Add AI classification data if available
            if classification_data:
                # DEBUG: Log the classification data structure
                logger.info(f"🐛 [AIRTABLE] DEBUG - Classification data type: {type(classification_data)}")
                logger.info(f"🐛 [AIRTABLE] DEBUG - Classification data keys: {list(classification_data.keys()) if isinstance(classification_data, dict) else 'Not a dict'}")
                
                # Get AI data from the correct key (email router creates 'ai_extracted_data')
                ai_data = {}
                if 'ai_extracted_data' in classification_data:
                    # Data comes from email router as ai_extracted_data
                    logger.info(f"🐛 [AIRTABLE] DEBUG - Found ai_extracted_data (from email router)")
                    ai_data = classification_data.get('ai_extracted_data', {})
                elif hasattr(classification_data, 'EMAIL_DATA'):
                    # Handle direct Pydantic model object
                    logger.info(f"🐛 [AIRTABLE] DEBUG - Found EMAIL_DATA attribute (Pydantic model)")
                    ai_data = classification_data.EMAIL_DATA.__dict__
                elif isinstance(classification_data.get('EMAIL_DATA'), dict):
                    # Handle dict object with EMAIL_DATA key
                    logger.info(f"🐛 [AIRTABLE] DEBUG - Found EMAIL_DATA in dict")
                    ai_data = classification_data.get('EMAIL_DATA', {})
                else:
                    logger.warning(f"🐛 [AIRTABLE] DEBUG - No ai_extracted_data or EMAIL_DATA found, ai_data will be empty")
                
                # DEBUG: Log what we extracted
                logger.info(f"🐛 [AIRTABLE] DEBUG - ai_data keys: {list(ai_data.keys()) if isinstance(ai_data, dict) else 'Not a dict'}")
                logger.info(f"🐛 [AIRTABLE] DEBUG - ai_summary: {ai_data.get('ai_summary', 'MISSING')}")
                logger.info(f"🐛 [AIRTABLE] DEBUG - hr_category: {ai_data.get('hr_category', 'MISSING')}")
                
                # Validate HR category - don't set if empty to avoid Airtable select field errors
                hr_category = ai_data.get('hr_category', '').strip()
                query_type_data = {}
                if hr_category and hr_category != '':
                    query_type_data["Query Type"] = hr_category
                    logger.info(f"🐛 [AIRTABLE] DEBUG - Setting Query Type: {hr_category}")
                else:
                    logger.warning(f"🐛 [AIRTABLE] DEBUG - HR category empty or missing, not setting Query Type")
                
                record_data.update({
                    "AI Classification": classification_data.get('EMAIL_CLASSIFICATION', ''),
                    "AI Confidence": classification_data.get('confidence_score', 0),
                    "AI Summary": ai_data.get('ai_summary', ''),  # Now should get the AI summary
                    "Query": ai_data.get('query', ''),  # AI-extracted clean customer query
                    "Urgency Keywords": json.dumps(ai_data.get('urgency_keywords_list', ai_data.get('urgency_keywords', []))),
                    "Sentiment Tone": ai_data.get('sentiment_tone', ''),
                    "AI Processing Timestamp": self._format_datetime(classification_data.get('processing_timestamp')),
                    "AI Notes": classification_data.get('notes', '')
                })
                
                # DEBUG: Log what we're setting
                logger.info(f"🐛 [AIRTABLE] DEBUG - Setting AI Summary: {ai_data.get('ai_summary', 'EMPTY')}")
                
                # Add Query Type separately to handle validation
                record_data.update(query_type_data)
            
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
            logger.info(f"🔍 [AIRTABLE] Searching for ticket: {ticket_number}")
            
            # Search for the ticket
            records = self.table.all(formula=f"{{Ticket Number}} = '{ticket_number}'")
            
            if records:
                logger.info(f"✅ [AIRTABLE] Found ticket {ticket_number}")
                return records[0]  # Return the first (should be only) match
            else:
                logger.warning(f"⚠️ [AIRTABLE] Ticket {ticket_number} not found")
                return None
                
        except Exception as e:
            logger.error(f"❌ [AIRTABLE] Error finding ticket {ticket_number}: {e}")
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
                "query": new_message_data.get('query', 'AI_EXTRACTION_FAILED'),
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
            logger.info(f"📊 [AIRTABLE] Health check passed - table has {len(table_info.fields)} fields")
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

    def update_conversation_advanced(self, ticket_number, conversation_history, email_data):
        """
        Update conversation history for an existing ticket with advanced features
        
        Args:
            ticket_number: Ticket number to update
            conversation_history: Updated conversation history (list of messages)
            email_data: Raw email data for metadata updates
            
        Returns:
            Updated record or None if failed
        """
        try:
            logger.info(f"💬 [AIRTABLE] Updating conversation for ticket {ticket_number}")
            
            # Find the existing record
            existing_record = self.find_ticket(ticket_number)
            if not existing_record:
                logger.error(f"❌ [AIRTABLE] Cannot update conversation - ticket {ticket_number} not found")
                return None
            
            # Get current Message ID field value
            current_message_ids = existing_record['fields'].get('Message ID', '')
            
            # Extract new Message-ID from email_data
            new_message_id = email_data.get('message_id', '') if email_data else ''
            
            # Append new Message-ID if it exists and isn't already in the list
            updated_message_ids = current_message_ids
            if new_message_id and new_message_id not in current_message_ids:
                if current_message_ids:
                    updated_message_ids = f"{current_message_ids}, {new_message_id}"
                else:
                    updated_message_ids = new_message_id
                logger.info(f"📧 [MESSAGE-ID] Appending new Message-ID: {new_message_id}")
            
            # Prepare update data (only include fields that exist in Airtable schema)
            update_data = {
                "Conversation History": json.dumps(conversation_history),
                "Last Updated": datetime.utcnow().isoformat(),
                "Status": "In Progress",  # Update status since there's new activity
                "Message Count": len(conversation_history),
                "Message ID": updated_message_ids  # Append new Message-ID to existing list
            }
            
            # Update the record
            updated_record = self.table.update(existing_record['id'], update_data)
            logger.info(f"✅ [AIRTABLE] Updated conversation for ticket {ticket_number}")
            
            return updated_record
            
        except Exception as e:
            logger.error(f"❌ [AIRTABLE] Error updating conversation for {ticket_number}: {e}")
            return None

    def get_conversation_history(self, ticket_number):
        """Get conversation history for a ticket"""
        try:
            record = self.find_ticket(ticket_number)
            if record:
                conversation_json = record['fields'].get('Conversation History', '[]')
                return json.loads(conversation_json)
            return []
        except Exception as e:
            logger.error(f"❌ [AIRTABLE] Error getting conversation for {ticket_number}: {e}")
            return []

    def get_full_conversation_history(self, ticket_number):
        """
        Get the complete conversation history from the computed formula field
        This includes both initial_conversation_query and conversation_history combined
        
        Args:
            ticket_number: Ticket number to retrieve full conversation for
            
        Returns:
            List of conversation entries in chronological order, or empty list if not found
        """
        try:
            record = self.find_ticket(ticket_number)
            if record:
                # Get the computed formula field that combines both conversation fields
                full_conversation_json = record['fields'].get('final_conversation_history', '[]')
                full_conversation = json.loads(full_conversation_json)
                
                logger.info(f"📜 [AIRTABLE] Retrieved full conversation for {ticket_number}: {len(full_conversation)} messages")
                return full_conversation
            
            logger.warning(f"📜 [AIRTABLE] Ticket {ticket_number} not found")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ [AIRTABLE] JSON decode error for {ticket_number}: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ [AIRTABLE] Error getting full conversation for {ticket_number}: {e}")
            return []

    def export_conversation_data(self, ticket_number):
        """
        Export complete conversation data for a ticket including metadata
        
        Args:
            ticket_number: Ticket number to export
            
        Returns:
            Dict with complete conversation data and metadata
        """
        try:
            record = self.find_ticket(ticket_number)
            if not record:
                return None
            
            fields = record['fields']
            full_conversation = self.get_full_conversation_history(ticket_number)
            
            return {
                "ticket_number": ticket_number,
                "airtable_record_id": record['id'],
                "full_conversation": full_conversation,
                "message_count": len(full_conversation),
                "ticket_created": fields.get('Created At'),
                "last_updated": fields.get('Last Updated'),
                "status": fields.get('Status'),
                "sender_email": fields.get('Sender Email'),
                "sender_name": fields.get('Sender Name'),
                "subject": fields.get('Subject'),
                "ai_classification": fields.get('AI Classification'),
                "ai_summary": fields.get('AI Summary'),
                "query_type": fields.get('Query Type'),
                "priority": fields.get('Priority')
            }
            
        except Exception as e:
            logger.error(f"❌ [AIRTABLE] Error exporting conversation data for {ticket_number}: {e}")
            return None

    # Backward compatibility
    def find_ticket_by_number(self, ticket_number):
        """Backward compatibility method"""
        return self.find_ticket(ticket_number)

    def update_conversation(self, ticket_number, new_message_data, classification_data=None):
        """Simple conversation update (backward compatibility)"""
        try:
            # Get existing conversation
            existing_conversation = self.get_conversation_history(ticket_number)
            
            # Create new message entry
            new_message = {
                "message_id": f"msg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": new_message_data.get('email_date', datetime.utcnow().isoformat()),
                "sender": new_message_data.get('sender', ''),
                "query": new_message_data.get('query', 'AI_EXTRACTION_FAILED'),
                "message_type": "reply",
                "thread_position": len(existing_conversation) + 1
            }
            
            # Add to conversation
            existing_conversation.append(new_message)
            
            # Update using advanced method
            return self.update_conversation_advanced(ticket_number, existing_conversation, new_message_data)
            
        except Exception as e:
            logger.error(f"❌ [AIRTABLE] Error in simple conversation update: {e}")
            return None 