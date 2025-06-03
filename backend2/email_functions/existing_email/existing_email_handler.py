import logging
from ..models.email_context import EmailContext
from ..models.email_path import EmailPath
import re

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
    
    # TODO: Implement genuine response handling
    return {
        "status": "genuine_response_detected", 
        "ticket_number": ticket_number,
        "message": "Genuine response detected - processing not yet implemented"
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