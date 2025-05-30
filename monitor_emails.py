#!/usr/bin/env python3
"""
Monitor the database for incoming emails
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import EmailThread, EmailMessage
from datetime import datetime
import time
import json

# Create database connection
engine = create_engine("sqlite:///argan_email.db")
Session = sessionmaker(bind=engine)

def monitor_emails():
    """Monitor for new emails"""
    print("=== Email Monitor Started ===")
    print("Watching for new emails...")
    print("Press Ctrl+C to stop\n")
    
    seen_threads = set()
    
    while True:
        try:
            session = Session()
            
            # Get all threads
            threads = session.query(EmailThread).order_by(EmailThread.created_at.desc()).all()
            
            for thread in threads:
                if thread.id not in seen_threads:
                    seen_threads.add(thread.id)
                    
                    # New thread found!
                    print(f"\n{'='*60}")
                    print(f"NEW EMAIL THREAD: {thread.ticket_number}")
                    print(f"{'='*60}")
                    print(f"Subject: {thread.subject}")
                    print(f"From: {thread.sender_email}")
                    print(f"Status: {thread.status}")
                    print(f"Created: {thread.created_at}")
                    
                    if thread.staff_name:
                        print(f"\nAI Analysis:")
                        print(f"Staff Member: {thread.staff_name}")
                        print(f"Query Type: {thread.query_type}")
                        print(f"Urgency: {thread.urgency}")
                        print(f"Summary: {thread.executive_summary}")
                        
                        if thread.key_points:
                            points = json.loads(thread.key_points)
                            print(f"Key Points:")
                            for point in points:
                                print(f"  - {point}")
                    
                    # Get messages
                    messages = session.query(EmailMessage).filter(
                        EmailMessage.thread_id == thread.id
                    ).order_by(EmailMessage.created_at).all()
                    
                    print(f"\nMessages ({len(messages)}):")
                    for msg in messages:
                        print(f"  [{msg.direction}] {msg.sender} → {', '.join(msg.recipients or [])}")
                        if msg.body_text:
                            preview = msg.body_text[:100].replace('\n', ' ')
                            print(f"    Preview: {preview}...")
            
            session.close()
            time.sleep(2)  # Check every 2 seconds
            
        except KeyboardInterrupt:
            print("\nMonitor stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_emails() 