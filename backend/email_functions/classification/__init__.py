"""
Email Classification Package
Contains AI classification agents and ticket assignment logic
"""

from .email_classifier_agent import EmailClassifierAgent
from .email_classification_schema import EmailClassificationResponse, EmailClassification

__all__ = ['EmailClassifierAgent', 'EmailClassificationResponse', 'EmailClassification'] 