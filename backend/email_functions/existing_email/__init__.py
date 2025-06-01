"""
Existing Email Handling Package
Handles replies to existing tickets and conversation threading
"""

from .existing_email import process_existing_email, process_reply_email

__all__ = ['process_existing_email', 'process_reply_email'] 