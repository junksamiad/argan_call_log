"""
Quick test to debug AI classification response structure
"""
import asyncio
import json
from backend.email_functions.classification.email_classifier_agent import EmailClassifierAgent

async def test_ai_response():
    """Test what the AI classifier actually returns"""
    
    # Sample email data
    email_data = {
        'sender': 'cvrcontractsltd@gmail.com',
        'subject': 'Concern Regarding Punctuality and Performance of Care Assistant',
        'body_text': '''Dear HR Team,

I hope you are well. I am writing to seek your advice on an ongoing issue with one of our care assistants, Ms Jane Smith, who has recently shown a pattern of late arrivals and noticeable decline in work performance. This has become a concern for both resident care and team morale.

Over the past three weeks, Ms Smith has arrived late to her shifts on five occasions, ranging from 15 to 45 minutes late. Additionally, I have received feedback from other staff members that she appears disengaged during shifts and has missed some important care tasks that were documented in resident care plans.

I have spoken with Ms Smith informally about these issues, and while she acknowledged the concerns, there has been no improvement. I believe we now need to escalate this matter through proper HR procedures.

Could you please advise on the appropriate next steps? Should we initiate a formal disciplinary process, and if so, what documentation do I need to prepare? I want to ensure we handle this sensitively but also maintain our high standards of care.

I would appreciate your guidance on this matter at your earliest convenience, as it is affecting the quality of care we provide to our residents.

Thank you for your time and assistance.

Best regards,
Sarah Williams
Home Manager
Sunshine Care Home
sarah.williams@sunshinecare.co.uk
01234 567890''',
        'recipients': ['email@email.adaptixinnovation.co.uk'],
        'message_id': 'test123',
        'email_date': '2024-06-01T12:00:00Z'
    }
    
    print("🧪 Testing AI Classification Response Structure...")
    print("=" * 60)
    
    try:
        classifier = EmailClassifierAgent()
        response = await classifier.classify_email(email_data)
        
        print("✅ AI Classification Response received")
        print(f"Type: {type(response)}")
        print()
        
        print("📋 TOP-LEVEL ATTRIBUTES:")
        for attr in dir(response):
            if not attr.startswith('_'):
                print(f"  {attr}: {getattr(response, attr, 'N/A')}")
        print()
        
        print("📊 EMAIL_DATA CONTENT:")
        if hasattr(response, 'EMAIL_DATA'):
            email_data_obj = response.EMAIL_DATA
            print(f"EMAIL_DATA Type: {type(email_data_obj)}")
            print()
            
            # Check if it has the fields we need
            fields_to_check = ['ai_summary', 'hr_category', 'sentiment_tone', 'urgency_keywords_list']
            
            for field in fields_to_check:
                if hasattr(email_data_obj, field):
                    value = getattr(email_data_obj, field)
                    print(f"✅ {field}: {value}")
                else:
                    print(f"❌ {field}: MISSING")
            
            print()
            print("🔍 ALL EMAIL_DATA ATTRIBUTES:")
            for attr in dir(email_data_obj):
                if not attr.startswith('_'):
                    value = getattr(email_data_obj, attr, 'N/A')
                    print(f"  {attr}: {str(value)[:100]}..." if len(str(value)) > 100 else f"  {attr}: {value}")
        else:
            print("❌ No EMAIL_DATA found in response")
        
        print()
        print("🔧 DICT CONVERSION TEST:")
        if hasattr(response, 'EMAIL_DATA'):
            try:
                email_data_dict = response.EMAIL_DATA.__dict__
                print(f"Dict keys: {list(email_data_dict.keys())}")
                for key, value in email_data_dict.items():
                    if key in ['ai_summary', 'hr_category']:
                        print(f"  {key}: {value}")
            except Exception as e:
                print(f"Dict conversion failed: {e}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_response()) 