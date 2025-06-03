"""
Main Email Processing Orchestrator - Backend2
Central hub for all email processing logic
"""

import logging
from typing import Dict, Any
from datetime import datetime
from .validator import validate_email_path
from .ai_agents import EmailPath

logger = logging.getLogger(__name__)


def create_context_object(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a flattened context object from raw SendGrid webhook payload
    
    Args:
        raw_payload: Raw multipart form data from SendGrid webhook
        
    Returns:
        Flattened context object with standardized field names
    """
    try:
        logger.info("📦 [CONTEXT] Creating context object from raw payload")
        
        # Extract key fields from the multipart form data
        context = {
            # Email content fields
            'subject': raw_payload.get('subject', ''),
            'text': raw_payload.get('text', ''),
            'from': raw_payload.get('from', ''),
            'to': raw_payload.get('to', ''),
            
            # Technical fields
            'sender_ip': raw_payload.get('sender_ip', ''),
            'spf': raw_payload.get('SPF', ''),
            'dkim': raw_payload.get('dkim', ''),
            'attachments': raw_payload.get('attachments', '0'),
            'charsets': raw_payload.get('charsets', '{}'),
            'envelope': raw_payload.get('envelope', '{}'),
            
            # Email headers (contains full header block)
            'headers': raw_payload.get('headers', ''),
            
            # Processing metadata
            'received_timestamp': datetime.utcnow().isoformat(),
            'processing_status': 'received',
            'raw_payload_keys': list(raw_payload.keys()),
            
            # Preserve original for debugging
            '_raw_payload': raw_payload
        }
        
        logger.info(f"📦 [CONTEXT] Context object created successfully")
        logger.info(f"📦 [CONTEXT] Subject: '{context['subject']}'")
        logger.info(f"📦 [CONTEXT] From: '{context['from']}'")
        logger.info(f"📦 [CONTEXT] To: '{context['to']}'")
        logger.info(f"📦 [CONTEXT] Raw payload fields: {len(raw_payload)} items")
        
        return context
        
    except Exception as e:
        logger.error(f"❌ [CONTEXT] Error creating context object: {e}")
        
        # Create minimal fallback context
        return {
            'subject': raw_payload.get('subject', 'EXTRACTION_FAILED'),
            'from': raw_payload.get('from', 'unknown@unknown.com'),
            'to': raw_payload.get('to', 'unknown'),
            'text': raw_payload.get('text', ''),
            'error': str(e),
            'received_timestamp': datetime.utcnow().isoformat(),
            'processing_status': 'error_creating_context',
            '_raw_payload': raw_payload
        }


async def process_new_email_path(context_object: Dict[str, Any], classifier_response: Any) -> Dict[str, Any]:
    """
    Process emails that are new inquiries (no existing ticket number)
    
    Args:
        context_object: Flattened context object
        classifier_response: AI classification response
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info("🆕 [NEW EMAIL PATH] Starting new email processing")
        logger.info(f"🆕 [NEW EMAIL PATH] Subject: {context_object.get('subject')}")
        logger.info(f"🆕 [NEW EMAIL PATH] From: {context_object.get('from')}")
        
        # ============================================================================
        # STEP 1: GENERATE NEW TICKET NUMBER
        # ============================================================================
        logger.info("🎫 [NEW EMAIL PATH] Generating new ticket number...")
        from .utils import generate_ticket_number
        
        ticket_number = generate_ticket_number()
        logger.info(f"🎫 [NEW EMAIL PATH] Generated ticket: {ticket_number}")
        
        # Add ticket number to context for downstream processing
        context_object['ticket_number'] = ticket_number
        context_object['processing_status'] = 'ticket_generated'
        # ============================================================================
        
        # ============================================================================
        # STEP 2: EXTRACT EMAIL DATA AND STORE IN AIRTABLE
        # ============================================================================
        logger.info("💾 [NEW EMAIL PATH] Extracting email data for Airtable...")
        from .database import extract_email_data_from_context, store_new_email
        
        # Extract all required fields from context object
        email_data = extract_email_data_from_context(context_object)
        
        # Store in Airtable
        logger.info("💾 [NEW EMAIL PATH] Storing email in Airtable...")
        airtable_success = store_new_email(email_data)
        
        if airtable_success:
            logger.info("✅ [NEW EMAIL PATH] Email stored in Airtable successfully")
            context_object['processing_status'] = 'stored_in_airtable'
        else:
            logger.error("❌ [NEW EMAIL PATH] Failed to store email in Airtable")
            context_object['processing_status'] = 'airtable_error'
        # ============================================================================
        
        # TODO: Implement remaining new email processing logic
        # This will include:
        # - Send auto-reply with ticket number
        
        result = {
            "success": True,
            "path_taken": "new_email",
            "ticket_number": ticket_number,
            "message": f"New email processed - ticket {ticket_number} generated",
            "context": context_object,
            "classifier_response": classifier_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("✅ [NEW EMAIL PATH] Processing complete")
        return result
        
    except Exception as e:
        logger.error(f"❌ [NEW EMAIL PATH] Error processing new email: {e}")
        return {
            "success": False,
            "path_taken": "new_email",
            "error": str(e),
            "message": "New email processing failed",
            "timestamp": datetime.utcnow().isoformat()
        }


async def process_existing_email_path(context_object: Dict[str, Any], classifier_response: Any) -> Dict[str, Any]:
    """
    Process emails that are replies to existing tickets
    
    Args:
        context_object: Flattened context object
        classifier_response: AI classification response
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info("💬 [EXISTING EMAIL PATH] Starting existing email processing")
        logger.info(f"💬 [EXISTING EMAIL PATH] Subject: {context_object.get('subject')}")
        logger.info(f"💬 [EXISTING EMAIL PATH] Ticket: {classifier_response.ticket_number_found}")
        
        # TODO: Implement existing email processing logic
        # This will include:
        # - Look up existing ticket in database
        # - Update conversation history
        # - Send notification to HR team
        # - Parse thread for new content
        
        result = {
            "success": True,
            "path_taken": "existing_email",
            "ticket_number": classifier_response.ticket_number_found,
            "message": "Existing email path processing started",
            "context": context_object,
            "classifier_response": classifier_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("✅ [EXISTING EMAIL PATH] Processing complete")
        return result
        
    except Exception as e:
        logger.error(f"❌ [EXISTING EMAIL PATH] Error processing existing email: {e}")
        return {
            "success": False,
            "path_taken": "existing_email",
            "error": str(e),
            "message": "Existing email processing failed",
            "timestamp": datetime.utcnow().isoformat()
        }


async def process_email(raw_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for email processing
    
    Args:
        raw_payload: Raw SendGrid webhook payload
        
    Returns:
        Processing result dictionary
    """
    try:
        logger.info("🚀 [MAIN ORCHESTRATOR] Starting email processing")
        logger.info("=" * 60)
        
        # Step 1: Create flattened context object from raw payload
        context_object = create_context_object(raw_payload)
        
        # ============================================================================
        # STEP 2: EMAIL DEDUPLICATION CHECK
        # ============================================================================
        # Extract Message-ID from headers for duplicate detection
        from .utils import extract_message_id_from_headers, is_duplicate_email, mark_email_as_processed
        
        logger.info("🔍 [MAIN ORCHESTRATOR] Checking for duplicate emails...")
        message_id = extract_message_id_from_headers(context_object.get('headers', ''))
        
        # Check if this email has already been processed
        if is_duplicate_email(message_id):
            logger.warning("🚫 [MAIN ORCHESTRATOR] DUPLICATE EMAIL DETECTED - SKIPPING PROCESSING")
            logger.info("=" * 60)
            return {
                "success": True,
                "status": "duplicate_skipped",
                "message": "Email already processed - duplicate detected",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info("✅ [MAIN ORCHESTRATOR] Email is new - proceeding with processing")
        # ============================================================================
        
        # Step 3: Use AI classifier to determine processing path
        logger.info("🔍 [MAIN ORCHESTRATOR] Running AI classification...")
        classifier_response = await validate_email_path(context_object)
        
        # Step 3: Route to appropriate processing path
        logger.info(f"🔀 [MAIN ORCHESTRATOR] Routing to: {classifier_response.path}")
        
        if classifier_response.path == EmailPath.NEW_EMAIL:
            result = await process_new_email_path(context_object, classifier_response)
        elif classifier_response.path == EmailPath.EXISTING_EMAIL:
            result = await process_existing_email_path(context_object, classifier_response)
        else:
            # Fallback to new email processing
            logger.warning(f"❓ [MAIN ORCHESTRATOR] Unknown path: {classifier_response.path}, defaulting to new_email")
            result = await process_new_email_path(context_object, classifier_response)
        
        # ============================================================================
        # STEP 5: MARK EMAIL AS PROCESSED (PREVENT FUTURE DUPLICATES)
        # ============================================================================
        logger.info("📝 [MAIN ORCHESTRATOR] Marking email as processed...")
        mark_email_as_processed(message_id)
        # ============================================================================
        
        logger.info("=" * 60)
        logger.info("✅ [MAIN ORCHESTRATOR] Email processing complete")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ [MAIN ORCHESTRATOR] Critical error in email processing: {e}")
        logger.info("=" * 60)
        
        return {
            "success": False,
            "error": str(e),
            "message": "Critical error in main orchestrator",
            "timestamp": datetime.utcnow().isoformat()
        } 