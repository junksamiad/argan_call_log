import logging
from typing import List, Dict, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType
import base64
from config.settings import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.EMAIL_ADDRESS
        
    def send_email(self, to: List[str], subject: str, body: str, 
                   cc: List[str] = None, thread_id: str = None, 
                   is_html: bool = False, attachments: List[Dict] = None) -> bool:
        """
        Send email via SendGrid API
        
        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (text or HTML)
            cc: Optional list of CC recipients
            thread_id: Optional thread ID to include in subject
            is_html: Whether body is HTML
            attachments: Optional list of attachments
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Add thread ID to subject if provided
            if thread_id:
                subject = f"[{thread_id}] {subject}"
            
            # Create mail object
            mail = Mail(
                from_email=Email(self.from_email),
                subject=subject
            )
            
            # Add recipients
            for recipient in to:
                mail.add_to(To(recipient))
                
            # Add CC recipients if provided
            if cc:
                for cc_recipient in cc:
                    mail.add_cc(Email(cc_recipient))
            
            # Add content
            if is_html:
                mail.add_content(Content("text/html", body))
            else:
                mail.add_content(Content("text/plain", body))
            
            # Add attachments if provided
            if attachments:
                for att in attachments:
                    attachment = Attachment()
                    attachment.file_content = FileContent(base64.b64encode(att['content']).decode())
                    attachment.file_type = FileType(att.get('content_type', 'application/octet-stream'))
                    attachment.file_name = FileName(att['filename'])
                    mail.add_attachment(attachment)
            
            # Send email
            response = self.sendgrid_client.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {', '.join(to)}. Status: {response.status_code}")
                return True
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}, Body: {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return False
    
    def send_reply(self, to: str, subject: str, body: str, 
                   thread_id: str, is_html: bool = False) -> bool:
        """
        Send a reply email for a specific thread
        """
        return self.send_email(
            to=[to],
            subject=subject,
            body=body,
            thread_id=thread_id,
            is_html=is_html
        ) 