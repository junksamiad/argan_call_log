from celery import Celery
from celery.schedules import crontab
from config.settings import settings
from backend.utils.database import SessionLocal
from backend.services.email_processor import EmailProcessor
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    'argan_email_processor',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'check-emails': {
            'task': 'backend.services.celery_app.check_and_process_emails',
            'schedule': settings.EMAIL_CHECK_INTERVAL,  # Every 60 seconds
        },
    }
)


@celery_app.task(name='backend.services.celery_app.check_and_process_emails')
def check_and_process_emails():
    """Background task to check and process new emails"""
    logger.info("Starting email check task")
    
    try:
        with SessionLocal() as db:
            processor = EmailProcessor(db)
            processor.process_new_emails()
            logger.info("Email processing completed")
    except Exception as e:
        logger.error(f"Error in email processing task: {str(e)}")
        raise


@celery_app.task(name='backend.services.celery_app.send_email_async')
def send_email_async(thread_id: int, body: str, recipients: list, cc: list = None):
    """Asynchronously send an email"""
    try:
        with SessionLocal() as db:
            processor = EmailProcessor(db)
            success = processor.send_reply(
                thread_id=thread_id,
                body=body,
                recipients=recipients,
                cc=cc
            )
            if success:
                logger.info(f"Email sent successfully for thread {thread_id}")
            else:
                logger.error(f"Failed to send email for thread {thread_id}")
            return success
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise 