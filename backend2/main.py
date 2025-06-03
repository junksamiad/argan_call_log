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
        
        if not airtable_success:
            logger.error("❌ [NEW EMAIL PATH] Failed to store email in Airtable")
            context_object['processing_status'] = 'airtable_error'
            # Return error - don't proceed with auto-reply if storage failed
            return {
                "success": False,
                "path_taken": "new_email",
                "error": "Failed to store email in Airtable",
                "message": "New email processing failed at storage step",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info("✅ [NEW EMAIL PATH] Email stored in Airtable successfully")
        context_object['processing_status'] = 'stored_in_airtable'
        # ============================================================================
        
        # ============================================================================
        # STEP 3: SEND AUTO-REPLY EMAIL
        # ============================================================================
        logger.info("📤 [NEW EMAIL PATH] Sending auto-reply email...")
        from .email_service import email_service
        from .auto_reply_templates import template_generator, extract_sender_info_from_db_record
        
        try:
            # Extract sender information from stored data with name components
            sender_info = extract_sender_info_from_db_record(
                email_data['initial_conversation_query'],
                email_data['sender_first_name'],
                email_data['sender_last_name']
            )
            
            # Generate auto-reply content using first name for personalized greeting
            auto_reply_content = template_generator.generate_auto_reply_content(
                sender_first_name=sender_info['sender_first_name'],
                original_subject=email_data['subject'], 
                original_query=sender_info['original_content'],
                ticket_number=ticket_number,
                priority="Normal"  # Default priority for new emails
            )
            
            # Send auto-reply with CC to argan-bot (testing)
            cc_addresses = ["argan-bot@arganhrconsultancy.co.uk"]  # Will change to advice@ after testing
            
            auto_reply_result = await email_service.send_auto_reply_email(
                to_email=sender_info['sender_email'],
                subject=auto_reply_content['subject'],
                text_content=auto_reply_content['text_body'],
                html_content=auto_reply_content['html_body'],
                ticket_number=ticket_number,
                cc_addresses=cc_addresses
            )
            
            if auto_reply_result['success']:
                logger.info("✅ [NEW EMAIL PATH] Auto-reply sent successfully")
                context_object['processing_status'] = 'auto_reply_sent'
                context_object['auto_reply_status'] = 'sent'
                
                # Update Airtable record to mark initial_auto_reply_sent = True
                from .database import update_auto_reply_status
                update_success = update_auto_reply_status(ticket_number, True)
                if update_success:
                    logger.info("✅ [NEW EMAIL PATH] Airtable auto-reply status updated")
                else:
                    logger.warning("⚠️ [NEW EMAIL PATH] Failed to update Airtable auto-reply status")
                
            else:
                logger.error(f"❌ [NEW EMAIL PATH] Auto-reply failed: {auto_reply_result.get('message', 'Unknown error')}")
                context_object['processing_status'] = 'auto_reply_failed'
                context_object['auto_reply_status'] = 'failed'
                context_object['auto_reply_error'] = auto_reply_result.get('message', 'Unknown error')
                
                # Auto-reply failure shouldn't fail the entire process, but we log it
                logger.warning("⚠️ [NEW EMAIL PATH] Continuing despite auto-reply failure")
                
        except Exception as e:
            logger.error(f"❌ [NEW EMAIL PATH] Exception in auto-reply process: {e}")
            context_object['processing_status'] = 'auto_reply_exception'
            context_object['auto_reply_status'] = 'exception'
            context_object['auto_reply_error'] = str(e)
            # Continue processing despite auto-reply failure
        # ============================================================================
        
        # Determine overall success based on auto-reply status
        overall_success = True
        overall_message = f"New email processed - ticket {ticket_number} generated"
        
        if context_object.get('auto_reply_status') == 'sent':
            overall_message += " and auto-reply sent"
        elif context_object.get('auto_reply_status') in ['failed', 'exception']:
            overall_message += " but auto-reply failed"
            # Note: We still consider this a success since the ticket was created
        
        result = {
            "success": overall_success,
            "path_taken": "new_email",
            "ticket_number": ticket_number,
            "message": overall_message,
            "auto_reply_status": context_object.get('auto_reply_status', 'not_attempted'),
            "auto_reply_error": context_object.get('auto_reply_error'),
            "context": context_object,
            "classifier_response": classifier_response,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("✅ [NEW EMAIL PATH] Processing complete")
        logger.info(f"📊 [NEW EMAIL PATH] Final status: {context_object.get('processing_status', 'unknown')}")
        logger.info(f"📧 [NEW EMAIL PATH] Auto-reply status: {context_object.get('auto_reply_status', 'not_attempted')}")
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
        # Convert context_object to EmailContext for the handler
        from .models.email_context import EmailContext
        
        # Create EmailContext object from dict
        email_context = EmailContext(
            subject=context_object.get('subject', ''),
            text=context_object.get('text', ''),
            from_field=context_object.get('from', ''),
            to=context_object.get('to', ''),
            sender_ip=context_object.get('sender_ip', ''),
            spf=context_object.get('spf', ''),
            dkim=context_object.get('dkim', ''),
            attachments=context_object.get('attachments', '0'),
            charsets=context_object.get('charsets', '{}'),
            envelope=context_object.get('envelope', '{}'),
            headers=context_object.get('headers', ''),
            received_timestamp=context_object.get('received_timestamp', ''),
            processing_status=context_object.get('processing_status', 'received'),
            raw_payload_keys=context_object.get('raw_payload_keys', []),
            _raw_payload=context_object.get('_raw_payload', {})
        )
        
        # Import and use the new existing email handler
        from .email_functions.existing_email.existing_email_handler import process_existing_email_path as handler_process
        
        # Process with the sophisticated auto-reply detection
        handler_result = handler_process(email_context, classifier_response.ticket_number_found)
        
        # Convert handler result to our expected format
        result = {
            "success": True,
            "path_taken": "existing_email",
            "ticket_number": classifier_response.ticket_number_found,
            "processing_result": handler_result,
            "message": f"Existing email path - {handler_result['status']}",
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
        # STEP 2: EMAIL DEDUPLICATION CHECK WITH RACE CONDITION PROTECTION
        # ============================================================================
        # Extract Message-ID from headers for duplicate detection
        from .utils import extract_message_id_from_headers, mark_email_as_processing, mark_email_as_processed
        
        logger.info("🔍 [MAIN ORCHESTRATOR] Checking for duplicate emails...")
        message_id = extract_message_id_from_headers(context_object.get('headers', ''))
        
        # Mark as processing immediately to prevent race conditions
        if not mark_email_as_processing(message_id):
            logger.warning("🚫 [MAIN ORCHESTRATOR] DUPLICATE/CONCURRENT EMAIL DETECTED - SKIPPING PROCESSING")
            logger.info("=" * 60)
            return {
                "success": True,
                "status": "duplicate_skipped",
                "message": "Email already processed or currently processing - duplicate detected",
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        logger.info("✅ [MAIN ORCHESTRATOR] Email is new and marked for processing - proceeding")
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
        
        # Note: Email is already marked as processed during deduplication check
        # No need for additional marking here since we use immediate processing lock
        
        logger.info("=" * 60)
        logger.info("✅ [MAIN ORCHESTRATOR] Email processing complete")
        logger.info("✅ EMAIL PROCESSING SUCCESSFUL!")
        logger.info(f"🔀 Path taken: {result.get('path_taken', 'unknown')}")
        if result.get('auto_reply_status'):
            logger.info(f"📧 Auto-reply status: {result.get('auto_reply_status')}")
        logger.info("=" * 80)
        
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