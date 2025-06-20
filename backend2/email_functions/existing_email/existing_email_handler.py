import logging
from ...models.email_context import EmailContext
import re
import json
from typing import Dict, Any, List, Optional
from ...database import extract_email_date_from_headers
from ...ai_agents import ConversationParsingAgent1

logger = logging.getLogger(__name__)

def process_existing_email_path(context: EmailContext, ticket_number: str) -> dict:
    """
    Process emails that are replies/forwards to existing tickets
    """
    logger.info("💬 [EXISTING EMAIL PATH] Starting existing email processing")
    logger.info(f"💬 [EXISTING EMAIL PATH] Subject: {context.subject}")
    logger.info(f"💬 [EXISTING EMAIL PATH] Ticket: {ticket_number}")
    
    # Simple check: If FROM field is our domain, it's our auto-reply bouncing back
    if context.from_field and "email@email.adaptixinnovation.co.uk" in context.from_field:
        logger.info("🤖 [EXISTING EMAIL PATH] Detected our auto-reply bouncing back - ignoring")
        logger.info(f"🔍 [EXISTING EMAIL PATH] FROM field: {context.from_field}")
        return {
            "status": "ignored_auto_reply_bounce",
            "ticket_number": ticket_number,
            "message": "Our auto-reply bouncing back - safely ignored"
        }
    
    # If not our domain, it's a genuine response (customer or HR advisor)
    logger.info("📨 [EXISTING EMAIL PATH] Detected genuine response (customer or HR advisor)")
    logger.info(f"🔍 [EXISTING EMAIL PATH] FROM field: {context.from_field}")
    
    # Step 1: Retrieve existing record from database
    logger.info(f"🔍 [EXISTING EMAIL PATH] Retrieving existing record for ticket: {ticket_number}")
    existing_record = get_existing_record(ticket_number)
    
    if not existing_record:
        logger.error(f"❌ [EXISTING EMAIL PATH] No record found for ticket: {ticket_number}")
        return {
            "status": "error_record_not_found",
            "ticket_number": ticket_number,
            "message": f"No existing record found for ticket {ticket_number}"
        }
    
    logger.info(f"✅ [EXISTING EMAIL PATH] Found existing record: {existing_record.get('record_id', 'N/A')}")
    
    # Step 2: Parse conversation using ConversationParsingAgent
    logger.info("🧵 [EXISTING EMAIL PATH] Parsing conversation thread...")
    
    # Extract existing conversation history from the record
    existing_conversation_history = existing_record.get('fields', {}).get('conversation_history', '')
    
    # Debug: Log the existing conversation history details
    if existing_conversation_history and existing_conversation_history.strip():
        logger.info(f"📋 [EXISTING EMAIL PATH] Found existing conversation history: {len(existing_conversation_history)} characters")
        logger.info("📋 [EXISTING EMAIL PATH] Existing conversation history preview:")
        logger.info("-" * 50)
        # Show first 500 chars and last 500 chars to verify it's not truncated
        if len(existing_conversation_history) <= 1000:
            logger.info(existing_conversation_history)
        else:
            logger.info(f"FIRST 500 CHARS: {existing_conversation_history[:500]}")
            logger.info("...")
            logger.info(f"LAST 500 CHARS: {existing_conversation_history[-500:]}")
        logger.info("-" * 50)
    else:
        logger.info("📋 [EXISTING EMAIL PATH] No existing conversation history found in database")
    
    new_conversation_history = parse_conversation_thread(
        email_text=context.text,
        existing_conversation_history=existing_conversation_history
    )
    
    # Check if we should update the conversation_history field
    # Consider empty if: empty string, whitespace only, or just '[]'
    is_conversation_history_empty = (
        not existing_conversation_history or 
        not existing_conversation_history.strip() or 
        existing_conversation_history.strip() == '[]'
    )
    
    if is_conversation_history_empty:
        # Step 3: Update database record - no meaningful conversation history found
        logger.info("💾 [EXISTING EMAIL PATH] No meaningful conversation history - updating database record...")
        update_result = update_existing_record(
            ticket_number=ticket_number,
            new_conversation_history=new_conversation_history,
            new_raw_headers=context.headers,
            debug_raw_email_text=context.text  # Store raw email text for debugging
        )
        
        if update_result['success']:
            logger.info("✅ [EXISTING EMAIL PATH] Record updated successfully")
            return {
                "status": "conversation_updated",
                "ticket_number": ticket_number,
                "message": "Conversation history updated successfully",
                "conversation_entries_count": len(new_conversation_history) if isinstance(new_conversation_history, list) else 0
            }
        else:
            logger.error(f"❌ [EXISTING EMAIL PATH] Failed to update record: {update_result.get('error', 'Unknown error')}")
            return {
                "status": "error_update_failed",
                "ticket_number": ticket_number,
                "message": f"Failed to update record: {update_result.get('error', 'Unknown error')}"
            }
    else:
        # Meaningful conversation history found - run Agent 2 to merge and deduplicate
        logger.info("📋 [EXISTING EMAIL PATH] Meaningful conversation history found - running Agent 2 for merge/deduplication")
        
        # Import Agent 2
        from ...ai_agents import ConversationParsingAgent2
        
        # Initialize Agent 2
        agent2 = ConversationParsingAgent2()
        
        # Format the input for Agent 2: Agent 1's output + existing DB data
        agent2_input = f"NEW JSON:\n{new_conversation_history}\n\nEXISTING JSON:\n{existing_conversation_history}"
        
        logger.info(f"🤖 [AGENT 2] Running Agent 2 with NEW JSON ({len(str(new_conversation_history))} chars) + EXISTING JSON ({len(existing_conversation_history)} chars)")
        
        # Run Agent 2 to merge and deduplicate
        merged_conversation_history = agent2.parse_conversation_thread_sync(
            full_email_content=agent2_input,
            existing_conversation_history=""  # Not used by Agent 2
        )
        
        # Convert JSON string back to list for processing
        import json
        try:
            merged_conversation_list = json.loads(merged_conversation_history)
        except json.JSONDecodeError as e:
            logger.error(f"❌ [AGENT 2] Failed to parse Agent 2 output as JSON: {e}")
            merged_conversation_list = []
        
        # Step 3: Update database record with Agent 2's merged output
        logger.info("💾 [EXISTING EMAIL PATH] Updating database with Agent 2's merged conversation history...")
        update_result = update_existing_record(
            ticket_number=ticket_number,
            new_conversation_history=merged_conversation_list,
            new_raw_headers=context.headers,
            debug_raw_email_text=context.text  # Store raw email text for debugging
        )
        
        if update_result['success']:
            logger.info("✅ [EXISTING EMAIL PATH] Record updated successfully with merged conversation history")
            return {
                "status": "conversation_merged",
                "ticket_number": ticket_number,
                "message": "Conversation history merged and updated successfully",
                "conversation_entries_count": len(merged_conversation_list) if isinstance(merged_conversation_list, list) else 0
            }
        else:
            logger.error(f"❌ [EXISTING EMAIL PATH] Failed to update record: {update_result.get('error', 'Unknown error')}")
            return {
                "status": "error_merge_failed",
                "ticket_number": ticket_number,
                "message": f"Failed to update merged record: {update_result.get('error', 'Unknown error')}"
            }

def detect_auto_reply_forward(context: EmailContext) -> bool:
    """
    Detect if an EXISTING_EMAIL is our own auto-reply being forwarded back
    vs a genuine customer response.
    
    Returns:
        True if this is our auto-reply being forwarded back
        False if this is a genuine customer response
    """
    logger.info("🔍 [AUTO-REPLY DETECTION] Analyzing email characteristics...")
    
    # Primary detection signals
    signals = {
        "from_our_domain": False,
        "auto_reply_content": False, 
        "auto_reply_subject": False,
        "reply_to_customer": False,
        "our_dkim": False
    }
    
    # 1. Check FROM field - our auto-replies come from our domain
    if context.from_field and "email@email.adaptixinnovation.co.uk" in context.from_field:
        signals["from_our_domain"] = True
        logger.info("✅ [AUTO-REPLY DETECTION] FROM field matches our domain")
    else:
        logger.info("❌ [AUTO-REPLY DETECTION] FROM field is NOT our domain")
    
    # 2. Check content for auto-reply patterns
    if context.text:
        auto_reply_patterns = [
            r"Thank you for contacting Argan HR Consultancy",
            r"We have received your enquiry and assigned it ticket number",
            r"Hi \w+,\s*\r?\n\r?\nThank you for contacting",
            r"┌─+┐",  # Our formatted content box
            r"Original Subject:",
            r"Argan HR Consultancy - Auto Reply"
        ]
        
        for pattern in auto_reply_patterns:
            if re.search(pattern, context.text, re.IGNORECASE | re.MULTILINE):
                signals["auto_reply_content"] = True
                logger.info(f"✅ [AUTO-REPLY DETECTION] Found auto-reply pattern: {pattern}")
                break
        
        if not signals["auto_reply_content"]:
            logger.info("❌ [AUTO-REPLY DETECTION] No auto-reply content patterns found")
    
    # 3. Check subject for auto-reply pattern
    if context.subject:
        # Our auto-reply subject: "[TICKET] Argan HR Consultancy - Call Logged"
        # Customer response would likely be: "Re: [TICKET] Argan HR Consultancy - Call Logged"
        auto_reply_subject_pattern = r"\[ARG-\d{8}-\d{4}\]\s+Argan HR Consultancy - Call Logged$"
        if re.search(auto_reply_subject_pattern, context.subject):
            signals["auto_reply_subject"] = True
            logger.info("✅ [AUTO-REPLY DETECTION] Subject matches auto-reply pattern")
        else:
            logger.info("❌ [AUTO-REPLY DETECTION] Subject does NOT match auto-reply pattern")
    
    # 4. Check for Reply-To header pointing to customer
    headers_text = getattr(context, 'headers', '')
    if headers_text and re.search(r"Reply-To:.*@(?!.*adaptixinnovation\.co\.uk)", headers_text):
        signals["reply_to_customer"] = True
        logger.info("✅ [AUTO-REPLY DETECTION] Reply-To points to customer email")
    
    # 5. Check DKIM for our domain
    if hasattr(context, 'dkim') and context.dkim and "email.adaptixinnovation.co.uk" in context.dkim:
        signals["our_dkim"] = True
        logger.info("✅ [AUTO-REPLY DETECTION] DKIM authenticated from our domain")
    
    # Decision logic
    confidence_score = sum(signals.values())
    total_signals = len(signals)
    
    logger.info("📊 [AUTO-REPLY DETECTION] Detection signals:")
    for signal_name, detected in signals.items():
        status = "✅" if detected else "❌"
        logger.info(f"   {status} {signal_name}: {detected}")
    
    logger.info(f"📊 [AUTO-REPLY DETECTION] Confidence score: {confidence_score}/{total_signals}")
    
    # Strong indicators: from_our_domain + auto_reply_content + auto_reply_subject
    strong_indicators = signals["from_our_domain"] and signals["auto_reply_content"] and signals["auto_reply_subject"]
    
    if strong_indicators:
        logger.info("🤖 [AUTO-REPLY DETECTION] VERDICT: Auto-reply forward detected (strong indicators)")
        return True
    elif confidence_score >= 3:
        logger.info("🤖 [AUTO-REPLY DETECTION] VERDICT: Auto-reply forward detected (high confidence)")
        return True
    else:
        logger.info("📨 [AUTO-REPLY DETECTION] VERDICT: Genuine customer response detected")
        return False

# Keep the existing debugging function for development
def debug_existing_email_analysis(context: EmailContext, ticket_number: str):
    """Enhanced debugging output for existing email analysis"""
    logger.info("🔍 [EXISTING EMAIL PATH] === DEBUGGING OUTPUT START ===")
    logger.info("=" * 80)
    
    # Key fields analysis
    original_sender = extract_original_sender(context)
    message_id = extract_message_id(context)
    
    logger.info("📋 [ANALYSIS] KEY FIELDS SUMMARY:")
    logger.info(f"   🎫 Ticket Number: {ticket_number}")
    logger.info(f"   📧 From Field: {context.from_field}")
    logger.info(f"   📧 To Field: {context.to}")
    logger.info(f"   📧 Original Sender: {original_sender}")
    logger.info(f"   🆔 Message-ID: {message_id}")
    logger.info(f"   📬 Subject: {context.subject}")
    logger.info(f"   📅 Received: {context.received_timestamp}")
    logger.info(f"   🔗 SPF: {getattr(context, 'spf', 'N/A')}")
    logger.info(f"   🔐 DKIM: {getattr(context, 'dkim', 'N/A')}")
    logger.info(f"   📎 Attachments: {getattr(context, 'attachments', 'N/A')}")
    
    # Email content preview
    text_length = len(context.text) if context.text else 0
    html_content = getattr(context, '_raw_payload', {}).get('html', '')
    html_length = len(html_content) if html_content else 0
    
    logger.info("📄 [ANALYSIS] EMAIL CONTENT PREVIEW:")
    logger.info(f"   📝 Text content length: {text_length} characters")
    logger.info(f"   🌐 HTML content length: {html_length} characters")
    if context.text:
        preview = context.text[:200] + "..." if len(context.text) > 200 else context.text
        logger.info(f"   📝 Text preview: '{preview}'")
    
    # Headers analysis
    headers = getattr(context, 'headers', '')
    if headers:
        logger.info("📋 [ANALYSIS] HEADERS ANALYSIS:")
        logger.info(f"   📄 Headers length: {len(headers)} characters")
        
        # Extract key headers
        key_headers = ['DKIM-Signature', 'Date', 'Envelope-To', 'From', 'Message-ID', 'Reply-To', 'Subject', 'To']
        logger.info("   🔑 Key headers found:")
        for header_name in key_headers:
            pattern = rf'{header_name}:\s*(.+?)(?=\n[A-Z]|\n\n|\Z)'
            match = re.search(pattern, headers, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Truncate very long values
                if len(value) > 200:
                    value = value[:200] + "..."
                logger.info(f"       {header_name}: {value}")
    
    # Raw payload structure
    raw_payload = getattr(context, '_raw_payload', {})
    if raw_payload:
        logger.info("📦 [ANALYSIS] RAW SENDGRID PAYLOAD STRUCTURE:")
        logger.info(f"   📄 Payload keys: {list(raw_payload.keys())}")
        logger.info("📦 [ANALYSIS] Formatted payload (truncated):")
        logger.info("   {")
        for key, value in raw_payload.items():
            if isinstance(value, str):
                if len(value) > 200:
                    truncated_value = value[:200] + f"... [TRUNCATED - Full length: {len(value)} chars]"
                else:
                    truncated_value = value
                logger.info(f'     "{key}": "{truncated_value}",')
            else:
                logger.info(f'     "{key}": {value},')
        logger.info("   }")
    
    # Context object summary
    context_dict = context.__dict__ if hasattr(context, '__dict__') else {}
    logger.info("🎯 [ANALYSIS] CONTEXT OBJECT SUMMARY:")
    logger.info(f"   📄 Context keys: {list(context_dict.keys())}")
    logger.info(f"   🔍 Processing status: {getattr(context, 'processing_status', 'unknown')}")
    
    # Auto-reply detection clues
    logger.info("🤖 [ANALYSIS] AUTO-REPLY DETECTION CLUES:")
    from_our_domain = original_sender and "email.adaptixinnovation.co.uk" in original_sender
    content_suggests_auto_reply = context.text and any(phrase in context.text.lower() for phrase in [
        "thank you for contacting argan hr consultancy",
        "we have received your enquiry", 
        "assigned it ticket number"
    ])
    
    logger.info(f"   🎯 Original sender from our domain: {from_our_domain}")
    logger.info(f"   📝 Content suggests auto-reply: {content_suggests_auto_reply}")
    logger.info(f"   ⏰ Processing timestamp: {context.received_timestamp}")
    
    logger.info("=" * 80)
    logger.info("🔍 [EXISTING EMAIL PATH] === DEBUGGING OUTPUT END ===")

def extract_original_sender(context: EmailContext) -> str:
    """Extract the original sender from the email context"""
    # Try different methods to find the original sender
    if hasattr(context, 'from_field') and context.from_field:
        # Extract email from "Name <email@domain.com>" format
        import re
        match = re.search(r'<([^>]+)>', context.from_field)
        if match:
            return match.group(1)
        # If no angle brackets, assume the whole thing is the email
        if '@' in context.from_field:
            return context.from_field
    
    # Fallback to other fields if available
    raw_payload = getattr(context, '_raw_payload', {})
    if 'from' in raw_payload:
        match = re.search(r'<([^>]+)>', raw_payload['from'])
        if match:
            return match.group(1)
        return raw_payload['from']
    
    return "unknown"

def extract_message_id(context: EmailContext) -> str:
    """Extract Message-ID from headers"""
    headers = getattr(context, 'headers', '')
    if headers:
        match = re.search(r'Message-ID:\s*(.+)', headers, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "unknown"

def get_existing_record(ticket_number: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve existing record from Airtable using ticket number
    
    Args:
        ticket_number: The ticket number to search for
        
    Returns:
        Dictionary containing the record data or None if not found
    """
    try:
        logger.info(f"🔍 [DATABASE] Searching for existing record with ticket: {ticket_number}")
        
        # Import database functions
        from ...database import table
        
        # Search using the ticket_number field
        records = table.all(formula=f"{{ticket_number}}='{ticket_number}'")
        
        if not records:
            logger.warning(f"⚠️ [DATABASE] No record found for ticket: {ticket_number}")
            return None
        
        if len(records) > 1:
            logger.warning(f"⚠️ [DATABASE] Multiple records found for ticket {ticket_number}, using first one")
        
        record = records[0]
        logger.info(f"✅ [DATABASE] Found record: {record['id']}")
        
        # Return both the record ID and fields for easy access
        return {
            'record_id': record['id'],
            'fields': record['fields']
        }
        
    except Exception as e:
        logger.error(f"❌ [DATABASE] Error retrieving record for ticket {ticket_number}: {e}")
        return None

def parse_conversation_thread(email_text: str, existing_conversation_history: str) -> List[Dict[str, Any]]:
    """
    Parse conversation thread using ConversationParsingAgent
    
    Args:
        email_text: The full email text content
        existing_conversation_history: Existing conversation history in JSON format
        
    Returns:
        List of conversation entries as dictionaries
    """
    try:
        logger.info("🤖 [CONVERSATION] Initializing ConversationParsingAgent...")
        
        # ==================== DEBUGGING: FULL INPUT ANALYSIS ====================
        logger.info("=" * 100)
        logger.info("🔍 [DEBUG] RAW EMAIL TEXT BEING PASSED TO AI AGENT:")
        logger.info("=" * 100)
        logger.info(f"📏 Total length: {len(email_text)} characters")
        logger.info(f"📄 Line count: {len(email_text.splitlines()) if email_text else 0}")
        logger.info("")
        logger.info("📄 FULL CONTENT:")
        logger.info("-" * 50)
        if email_text:
            # Split into lines for better readability
            lines = email_text.splitlines()
            for i, line in enumerate(lines, 1):
                logger.info(f"{i:3d}: {line}")
        else:
            logger.info("(EMPTY OR NONE)")
        logger.info("-" * 50)
        logger.info("=" * 100)
        # ========================================================================
        
        # Import the conversation parsing agent
        from ...ai_agents import ConversationParsingAgent1
        
        # Initialize agent
        agent = ConversationParsingAgent1()
        
        # Parse the conversation thread
        logger.info(f"🧵 [CONVERSATION] Parsing {len(email_text)} characters of email content...")
        conversation_json = agent.parse_conversation_thread_sync(email_text, existing_conversation_history)
        
        # ==================== DEBUGGING: AI OUTPUT ANALYSIS ====================
        logger.info("=" * 100)
        logger.info("🤖 [DEBUG] AI AGENT OUTPUT ANALYSIS:")
        logger.info("=" * 100)
        logger.info(f"📄 JSON Response length: {len(conversation_json)} characters")
        logger.info("")
        logger.info("📄 RAW JSON RESPONSE:")
        logger.info("-" * 50)
        logger.info(conversation_json)
        logger.info("-" * 50)
        logger.info("=" * 100)
        # ========================================================================
        
        # Parse JSON response
        conversation_entries = json.loads(conversation_json)
        
        # ==================== DEBUGGING: PARSED ENTRIES ANALYSIS ====================
        logger.info("=" * 100)
        logger.info("📋 [DEBUG] PARSED CONVERSATION ENTRIES ANALYSIS:")
        logger.info("=" * 100)
        logger.info(f"📊 Total entries found: {len(conversation_entries)}")
        logger.info("")
        
        for i, entry in enumerate(conversation_entries, 1):
            logger.info(f"📧 ENTRY {i}:")
            logger.info(f"   👤 Sender Email: {entry.get('sender_email', 'N/A')}")
            logger.info(f"   👤 Sender Name: {entry.get('sender_name', 'N/A')}")
            logger.info(f"   📅 Date: {entry.get('sender_email_date', 'N/A')}")
            logger.info(f"   📏 Content Length: {len(entry.get('sender_content', ''))}")
            
            # Show first few lines of content
            content = entry.get('sender_content', '')
            if content:
                content_lines = content.splitlines()[:3]  # First 3 lines
                logger.info(f"   📄 Content Preview:")
                for line_num, line in enumerate(content_lines, 1):
                    logger.info(f"      {line_num}: {line}")
                if len(content.splitlines()) > 3:
                    logger.info(f"      ... (+{len(content.splitlines()) - 3} more lines)")
            logger.info("")
        
        logger.info("=" * 100)
        # ================================================================================
        
        logger.info(f"✅ [CONVERSATION] Successfully parsed {len(conversation_entries)} conversation entries")
        return conversation_entries
        
    except Exception as e:
        logger.error(f"❌ [CONVERSATION] Error parsing conversation thread: {e}")
        return []  # Return empty list on error

def update_existing_record(ticket_number: str, new_conversation_history: List[Dict[str, Any]], new_raw_headers: str, debug_raw_email_text: str = None) -> Dict[str, Any]:
    """
    Update existing Airtable record with new conversation history and raw headers
    
    Args:
        ticket_number: The ticket number to update
        new_conversation_history: List of conversation entries
        new_raw_headers: Raw email headers string
        
    Returns:
        Dictionary with success status and any error message
    """
    try:
        logger.info(f"💾 [DATABASE] Updating record for ticket: {ticket_number}")
        
        # Get the existing record first
        existing_record = get_existing_record(ticket_number)
        if not existing_record:
            return {'success': False, 'error': 'Record not found'}
        
        record_id = existing_record['record_id']
        
        # Import database functions
        from ...database import table
        
        # Prepare update data
        update_data = {
            'conversation_history': json.dumps(new_conversation_history, ensure_ascii=False),
            'raw_headers': new_raw_headers
        }
        
        # Add debug raw email text if provided (for analysis)
        # NOTE: Commented out until debug_raw_email_text field is created in Airtable
        # if debug_raw_email_text:
        #     update_data['debug_raw_email_text'] = debug_raw_email_text
        #     logger.info(f"📝 [DATABASE] Including debug raw email text ({len(debug_raw_email_text)} chars)")
        
        logger.info(f"📝 [DATABASE] Updating record {record_id} with {len(new_conversation_history)} conversation entries")
        logger.info(f"📝 [DATABASE] Raw headers length: {len(new_raw_headers)} characters")
        
        # Update the record
        table.update(record_id, update_data)
        
        logger.info(f"✅ [DATABASE] Successfully updated record {record_id}")
        return {'success': True}
        
    except Exception as e:
        logger.error(f"❌ [DATABASE] Error updating record for ticket {ticket_number}: {e}")
        return {'success': False, 'error': str(e)} 