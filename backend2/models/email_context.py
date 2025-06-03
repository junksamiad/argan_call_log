"""
Email Context Model - Data structure for email processing
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class EmailContext:
    """
    Structured representation of email data for processing
    """
    # Core email fields
    subject: str
    text: str
    from_field: str
    to: str
    
    # Technical fields
    sender_ip: str
    spf: str
    dkim: str
    attachments: str
    charsets: str
    envelope: str
    headers: str
    
    # Processing metadata
    received_timestamp: str
    processing_status: str
    raw_payload_keys: List[str]
    _raw_payload: Dict[str, Any]
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure raw_payload_keys is a list
        if not isinstance(self.raw_payload_keys, list):
            self.raw_payload_keys = []
        
        # Ensure _raw_payload is a dict
        if not isinstance(self._raw_payload, dict):
            self._raw_payload = {} 