#!/usr/bin/env python3
"""
Test script to verify automatic ticket number generation
"""
import sys
sys.path.append('.')

from backend.utils.database import init_db, SessionLocal
from backend.models.database import EmailThread
from backend.models.schemas import ThreadStatus


def test_ticket_generation():
    """Test automatic ticket number generation"""
    print("Testing Automatic Ticket Number Generation")
    print("=" * 50)
    
    # Initialize database
    print("\n1. Initializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Create test threads
    with SessionLocal() as db:
        print("\n2. Creating test email threads...")
        
        # Create first thread
        thread1 = EmailThread(
            subject="Test Query 1",
            staff_email="test1@example.com",
            staff_name="Test User 1",
            status=ThreadStatus.OPEN.value
        )
        db.add(thread1)
        db.flush()
        print(f"✓ Thread 1 created with ticket: {thread1.ticket_number}")
        
        # Create second thread
        thread2 = EmailThread(
            subject="Test Query 2",
            staff_email="test2@example.com",
            staff_name="Test User 2",
            status=ThreadStatus.OPEN.value
        )
        db.add(thread2)
        db.flush()
        print(f"✓ Thread 2 created with ticket: {thread2.ticket_number}")
        
        # Create third thread
        thread3 = EmailThread(
            subject="Test Query 3",
            staff_email="test3@example.com",
            staff_name="Test User 3",
            status=ThreadStatus.OPEN.value
        )
        db.add(thread3)
        db.flush()
        print(f"✓ Thread 3 created with ticket: {thread3.ticket_number}")
        
        # Verify sequential numbering
        print("\n3. Verifying ticket numbers...")
        assert thread1.ticket_number == "ARG-00001", f"Expected ARG-00001, got {thread1.ticket_number}"
        assert thread2.ticket_number == "ARG-00002", f"Expected ARG-00002, got {thread2.ticket_number}"
        assert thread3.ticket_number == "ARG-00003", f"Expected ARG-00003, got {thread3.ticket_number}"
        print("✓ Ticket numbers are sequential and properly formatted")
        
        # Verify uniqueness
        print("\n4. Verifying uniqueness...")
        all_threads = db.query(EmailThread).all()
        ticket_numbers = [t.ticket_number for t in all_threads]
        assert len(ticket_numbers) == len(set(ticket_numbers)), "Duplicate ticket numbers found!"
        print(f"✓ All {len(ticket_numbers)} ticket numbers are unique")
        
        # Don't commit - this is just a test
        db.rollback()
        print("\n✓ Test completed successfully (rolled back test data)")


if __name__ == "__main__":
    try:
        test_ticket_generation()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        sys.exit(1) 