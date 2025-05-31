"""
Initial Email Handling Package
Handles new email queries and ticket generation
"""

from .initial_email import process_initial_email, prepare_enhanced_email_data, extract_priority_from_classification, extract_ai_summary
from .initial_email_content import InitialEmailContent

__all__ = ['process_initial_email', 'prepare_enhanced_email_data', 'extract_priority_from_classification', 'extract_ai_summary', 'InitialEmailContent'] 