from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from backend.models.database import Base
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    try:
        # Import here to ensure event listeners are registered
        from backend.utils import database_setup
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize ticket counter
        with SessionLocal() as db:
            database_setup.init_ticket_counter(db)
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 