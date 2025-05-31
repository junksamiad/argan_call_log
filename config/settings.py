from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from typing import Optional

# Load .env file explicitly - this ensures .env takes priority
load_dotenv()

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///argan_email.db")
    
    # Email Configuration - SendGrid
    EMAIL_ADDRESS: str = os.getenv("EMAIL_ADDRESS", "support@email.adaptixinnovation.co.uk")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_WEBHOOK_VERIFICATION_KEY: Optional[str] = os.getenv("SENDGRID_WEBHOOK_VERIFICATION_KEY", None)
    PARSE_DOMAIN: str = os.getenv("PARSE_DOMAIN", "email.adaptixinnovation.co.uk")
    
    # Airtable Configuration (for future use)
    AIRTABLE_API_KEY: str = os.getenv("AIRTABLE_API_KEY", "")
    AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "")
    AIRTABLE_TABLE_NAME: str = os.getenv("AIRTABLE_TABLE_NAME", "call_log")
    
    # App Configuration
    TICKET_PREFIX: str = os.getenv("TICKET_PREFIX", "ARG")
    
    class Config:
        case_sensitive = True


settings = Settings() 