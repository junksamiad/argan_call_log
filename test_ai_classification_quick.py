"""
Quick test for AI classification functionality
"""

from backend.email_functions.classification.email_classifier_agent import EmailClassifierAgent

def test_ai():
    print("🧪 Testing AI Classification...")
    
    classifier = EmailClassifierAgent()
    test_email = {
        'sender': 'test@example.com',
        'subject': 'Test email',
        'body_text': 'This is a test email message',
        'recipients': ['hr@company.com'],
        'email_date': '2025-05-31T20:30:00Z',
        'message_id': 'test-123'
    }
    
    try:
        # Call the sync version directly
        result = classifier._call_openai_classifier_sync(
            classifier._prepare_email_content(test_email)
        )
        print(f'✅ AI Classification: {result.EMAIL_CLASSIFICATION}')
        print(f'📊 Confidence: {result.confidence_score}')
        print(f'📝 Notes: {result.notes}')
        return True
    except Exception as e:
        print(f'❌ AI Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ai()
    if success:
        print('🎉 AI classification is working!')
    else:
        print('💥 AI classification failed') 