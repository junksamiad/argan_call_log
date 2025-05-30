from pyairtable import Api
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

# Airtable connection
airtable_api = None
email_table = None

def init_airtable():
    """Initialize Airtable connection"""
    global airtable_api, email_table
    
    try:
        airtable_api = Api(settings.AIRTABLE_API_KEY)
        
        # Get the base and table
        base = airtable_api.base(settings.AIRTABLE_BASE_ID)
        email_table = base.table(settings.AIRTABLE_TABLE_NAME)
        
        logger.info("Airtable connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing Airtable: {str(e)}")
        raise

def get_airtable_api():
    """Get Airtable API instance"""
    if airtable_api is None:
        init_airtable()
    return airtable_api

def get_email_table():
    """Get email table"""
    if email_table is None:
        init_airtable()
    return email_table

# For compatibility with existing code
engine = None
Base = None 