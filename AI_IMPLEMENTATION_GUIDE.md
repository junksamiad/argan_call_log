# HR Email Management System - AI Implementation Guide

## 1. AI Component Overview

### 1.1 AI Processing Pipeline
```
Incoming Email → Email Parser → AI Analyzer → Response Generator → Database Storage
      ↓              ↓             ↓              ↓               ↓
   Raw Email    Structured    AI Analysis    Suggested       Complete
   Content      Data         Results        Response        Record
```

### 1.2 AI Capabilities Required
- **Email Classification**: Determine query type (leave, benefits, policy, etc.)
- **Data Extraction**: Extract staff details, urgency level, key information
- **Sentiment Analysis**: Assess tone and urgency of the query
- **Response Generation**: Create contextually appropriate responses
- **Content Summarization**: Generate concise summaries for HR staff

## 2. OpenAI Integration Architecture

### 2.1 API Configuration
```python
# config/ai_settings.py
import openai
from pydantic import BaseSettings

class AISettings(BaseSettings):
    openai_api_key: str
    ai_model: str = "gpt-4"
    max_tokens: int = 1000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"

ai_settings = AISettings()
openai.api_key = ai_settings.openai_api_key
```

### 2.2 AI Service Layer
```python
# backend/services/ai_service.py
from typing import Dict, Any, Optional
import json
import openai
from datetime import datetime

class EmailAIProcessor:
    def __init__(self):
        self.model = ai_settings.ai_model
        self.max_tokens = ai_settings.max_tokens
        
    async def analyze_email(self, email_content: str, subject: str, sender: str) -> Dict[str, Any]:
        """
        Comprehensive AI analysis of incoming email
        """
        analysis_prompt = self._build_analysis_prompt(email_content, subject, sender)
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": analysis_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,  # Lower temperature for consistent analysis
                functions=[self._get_analysis_function_schema()],
                function_call={"name": "analyze_hr_email"}
            )
            
            function_call = response.choices[0].message.function_call
            analysis_result = json.loads(function_call.arguments)
            
            return {
                "success": True,
                "analysis": analysis_result,
                "tokens_used": response.usage.total_tokens,
                "model": self.model
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": self._get_fallback_analysis()
            }
    
    def _get_system_prompt(self) -> str:
        return """
        You are an AI assistant for Argan HR Consultancy, specializing in analyzing HR-related emails.
        Your role is to:
        1. Extract key information from employee queries
        2. Classify the type of HR request
        3. Assess urgency and sentiment
        4. Identify required actions
        5. Generate appropriate response suggestions
        
        Always maintain professionalism and confidentiality.
        """
    
    def _build_analysis_prompt(self, content: str, subject: str, sender: str) -> str:
        return f"""
        Please analyze this HR email and extract structured information:
        
        FROM: {sender}
        SUBJECT: {subject}
        CONTENT: {content}
        
        Analyze and extract:
        1. Employee details (name, department if mentioned)
        2. Query type and category
        3. Urgency level (1-5 scale)
        4. Key issues or requests
        5. Required actions
        6. Sentiment analysis
        7. Suggested response approach
        """
    
    def _get_analysis_function_schema(self) -> Dict[str, Any]:
        return {
            "name": "analyze_hr_email",
            "description": "Analyze HR email and extract structured information",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_name": {
                        "type": "string",
                        "description": "Employee's full name if identifiable"
                    },
                    "employee_department": {
                        "type": "string",
                        "description": "Employee's department if mentioned"
                    },
                    "query_type": {
                        "type": "string",
                        "enum": ["leave_request", "benefits_inquiry", "policy_question", 
                                "complaint", "general_inquiry", "technical_issue", "other"],
                        "description": "Primary category of the HR query"
                    },
                    "urgency_level": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "description": "Urgency level: 1=Low, 2=Normal, 3=Medium, 4=High, 5=Critical"
                    },
                    "key_issues": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of main issues or requests mentioned"
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "negative", "frustrated", "urgent"],
                        "description": "Overall sentiment of the email"
                    },
                    "requires_immediate_attention": {
                        "type": "boolean",
                        "description": "Whether this requires immediate HR attention"
                    },
                    "suggested_response_tone": {
                        "type": "string",
                        "enum": ["formal", "friendly", "empathetic", "urgent", "informational"],
                        "description": "Recommended tone for response"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of the email content"
                    },
                    "recommended_actions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of recommended actions for HR team"
                    }
                },
                "required": ["query_type", "urgency_level", "sentiment", "summary"]
            }
        }
```

## 3. Response Generation System

### 3.1 Response Generator
```python
# backend/services/response_generator.py
class ResponseGenerator:
    def __init__(self):
        self.model = ai_settings.ai_model
        
    async def generate_response(self, 
                              analysis: Dict[str, Any], 
                              email_content: str,
                              company_policies: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate contextually appropriate response based on analysis
        """
        response_prompt = self._build_response_prompt(analysis, email_content, company_policies)
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_response_system_prompt()},
                    {"role": "user", "content": response_prompt}
                ],
                max_tokens=800,
                temperature=0.7,
                functions=[self._get_response_function_schema()],
                function_call={"name": "generate_hr_response"}
            )
            
            function_call = response.choices[0].message.function_call
            response_data = json.loads(function_call.arguments)
            
            return {
                "success": True,
                "response": response_data,
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": self._get_fallback_response(analysis)
            }
    
    def _get_response_system_prompt(self) -> str:
        return """
        You are an HR response assistant for Argan HR Consultancy.
        Generate professional, helpful, and empathetic responses to employee queries.
        
        Guidelines:
        - Always maintain professional tone
        - Be empathetic and understanding
        - Provide clear, actionable information
        - Include relevant policy references when applicable
        - Suggest next steps or follow-up actions
        - Use appropriate greeting and closing
        """
    
    def _build_response_prompt(self, analysis: Dict, email_content: str, policies: str = None) -> str:
        policy_context = f"\n\nRelevant Policies:\n{policies}" if policies else ""
        
        return f"""
        Generate a professional HR response based on this analysis:
        
        ANALYSIS:
        - Query Type: {analysis.get('query_type', 'general_inquiry')}
        - Urgency: {analysis.get('urgency_level', 3)}/5
        - Sentiment: {analysis.get('sentiment', 'neutral')}
        - Key Issues: {', '.join(analysis.get('key_issues', []))}
        - Recommended Tone: {analysis.get('suggested_response_tone', 'friendly')}
        
        ORIGINAL EMAIL CONTENT:
        {email_content}
        {policy_context}
        
        Generate an appropriate response that addresses the employee's concerns.
        """
    
    def _get_response_function_schema(self) -> Dict[str, Any]:
        return {
            "name": "generate_hr_response",
            "description": "Generate professional HR response email",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject_line": {
                        "type": "string",
                        "description": "Appropriate subject line for the response"
                    },
                    "greeting": {
                        "type": "string",
                        "description": "Professional greeting"
                    },
                    "main_content": {
                        "type": "string",
                        "description": "Main body of the response addressing the query"
                    },
                    "next_steps": {
                        "type": "string",
                        "description": "Clear next steps or actions for the employee"
                    },
                    "closing": {
                        "type": "string",
                        "description": "Professional closing"
                    },
                    "requires_follow_up": {
                        "type": "boolean",
                        "description": "Whether this response requires follow-up"
                    },
                    "follow_up_timeline": {
                        "type": "string",
                        "description": "When to follow up if required"
                    }
                },
                "required": ["subject_line", "greeting", "main_content", "closing"]
            }
        }
```

## 4. Enhanced Webhook with AI Processing

### 4.1 Updated Webhook Implementation
```python
# backend/api/endpoints/webhook.py (Enhanced Version)
from backend.services.ai_service import EmailAIProcessor
from backend.services.response_generator import ResponseGenerator
from backend.services.ticket_service import TicketService

@router.post("/inbound")
async def inbound_parse(
    email: str = Form(None),
    to: str = Form(...),
    from_email: str = Form(..., alias="from"),
    subject: str = Form(None),
    dkim: str = Form(None),
    SPF: str = Form(None),
    sender_ip: str = Form(None),
    envelope: str = Form(None),
    # ... file attachments
):
    """
    Enhanced webhook with AI processing
    """
    try:
        # Initialize services
        ai_processor = EmailAIProcessor()
        response_generator = ResponseGenerator()
        ticket_service = TicketService()
        
        # Extract email content for AI processing
        email_content = email or "No content available"
        
        # Check for existing ticket in subject
        ticket_number = ticket_service.extract_ticket_from_subject(subject)
        is_new_thread = ticket_number is None
        
        if is_new_thread:
            # Generate new ticket number
            ticket_number = ticket_service.generate_ticket_number()
            
            # AI Analysis for new emails
            print("🤖 Starting AI analysis...")
            ai_analysis = await ai_processor.analyze_email(
                email_content=email_content,
                subject=subject or "No Subject",
                sender=from_email
            )
            
            if ai_analysis["success"]:
                print("✅ AI Analysis completed:")
                analysis_data = ai_analysis["analysis"]
                print(f"   📊 Query Type: {analysis_data.get('query_type')}")
                print(f"   🚨 Urgency: {analysis_data.get('urgency_level')}/5")
                print(f"   😊 Sentiment: {analysis_data.get('sentiment')}")
                print(f"   📝 Summary: {analysis_data.get('summary')}")
                
                # Generate suggested response
                print("🤖 Generating suggested response...")
                response_suggestion = await response_generator.generate_response(
                    analysis=analysis_data,
                    email_content=email_content
                )
                
                if response_suggestion["success"]:
                    print("✅ Response generated successfully")
                    response_data = response_suggestion["response"]
                    print(f"   📧 Subject: {response_data.get('subject_line')}")
                else:
                    print(f"❌ Response generation failed: {response_suggestion.get('error')}")
                    response_data = None
            else:
                print(f"❌ AI Analysis failed: {ai_analysis.get('error')}")
                analysis_data = ai_analysis["analysis"]  # Fallback data
                response_data = None
        else:
            print(f"📧 Reply to existing ticket: {ticket_number}")
            analysis_data = None
            response_data = None
        
        # Log the processed email
        print("=" * 60)
        print("🚀 EMAIL PROCESSED WITH AI")
        print("=" * 60)
        print(f"📧 From: {from_email}")
        print(f"📬 To: {to}")
        print(f"📝 Subject: {subject}")
        print(f"🎫 Ticket: {ticket_number}")
        print(f"🔄 Type: {'New Thread' if is_new_thread else 'Reply'}")
        if analysis_data:
            print(f"🤖 AI Analysis: ✅ Complete")
            print(f"   📊 Query Type: {analysis_data.get('query_type')}")
            print(f"   🚨 Urgency: {analysis_data.get('urgency_level')}/5")
        if response_data:
            print(f"💬 Response: ✅ Generated")
        print("=" * 60)
        
        # TODO: Save to database when database is restored
        # await save_email_with_ai_data(
        #     ticket_number=ticket_number,
        #     email_data={...},
        #     ai_analysis=analysis_data,
        #     suggested_response=response_data
        # )
        
        return PlainTextResponse("OK - Email processed with AI!")
        
    except Exception as e:
        print(f"❌ ERROR processing email: {e}")
        logger.error(f"Error processing inbound email: {e}")
        return PlainTextResponse("OK")
```

## 5. Database Schema for AI Data

### 5.1 Enhanced Database Models
```python
# backend/models/database.py (Enhanced)
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base

class EmailThread(Base):
    __tablename__ = "email_threads"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, index=True)
    subject = Column(String(500))
    status = Column(String(50), default="open")
    priority = Column(Integer, default=3)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI Analysis Fields
    ai_query_type = Column(String(100))
    ai_urgency_level = Column(Integer)
    ai_sentiment = Column(String(50))
    ai_summary = Column(Text)
    ai_analysis_data = Column(JSON)  # Full AI analysis
    
    # Response Management
    suggested_response = Column(JSON)  # AI-generated response
    approved_response = Column(Text)   # HR-approved response
    response_sent = Column(Boolean, default=False)
    response_sent_at = Column(DateTime)

class EmailMessage(Base):
    __tablename__ = "email_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id"))
    direction = Column(String(20))  # "inbound" or "outbound"
    sender_email = Column(String(255))
    recipient_email = Column(String(255))
    subject = Column(String(500))
    content_text = Column(Text)
    content_html = Column(Text)
    raw_email = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # AI Processing
    ai_processed = Column(Boolean, default=False)
    ai_processing_time = Column(Float)  # Processing time in seconds
    ai_tokens_used = Column(Integer)
    ai_model_used = Column(String(50))

class AIProcessingLog(Base):
    __tablename__ = "ai_processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("email_messages.id"))
    processing_type = Column(String(50))  # "analysis", "response_generation"
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    processing_time = Column(Float)
    success = Column(Boolean)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 6. AI Service Integration

### 6.1 Ticket Service
```python
# backend/services/ticket_service.py
import re
from datetime import datetime
from typing import Optional

class TicketService:
    def __init__(self):
        self.ticket_prefix = "ARG"
        self.ticket_pattern = rf'\[({self.ticket_prefix}-\d+)\]'
    
    def extract_ticket_from_subject(self, subject: str) -> Optional[str]:
        """Extract ticket number from email subject"""
        if not subject:
            return None
            
        match = re.search(self.ticket_pattern, subject)
        return match.group(1) if match else None
    
    def generate_ticket_number(self) -> str:
        """Generate new sequential ticket number"""
        # TODO: Implement database-backed counter
        timestamp = int(datetime.now().timestamp())
        return f"{self.ticket_prefix}-{timestamp % 100000:05d}"
    
    def format_subject_with_ticket(self, original_subject: str, ticket_number: str) -> str:
        """Add ticket number to subject line"""
        if self.extract_ticket_from_subject(original_subject):
            return original_subject  # Already has ticket
        return f"[{ticket_number}] {original_subject}"
```

## 7. Configuration and Environment Setup

### 7.1 Environment Variables
```bash
# .env file additions for AI
OPENAI_API_KEY=sk-your-openai-api-key-here
AI_MODEL=gpt-4
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.7

# AI Processing Settings
ENABLE_AI_ANALYSIS=true
ENABLE_RESPONSE_GENERATION=true
AI_PROCESSING_TIMEOUT=30

# Cost Management
DAILY_TOKEN_LIMIT=50000
MONTHLY_TOKEN_LIMIT=1000000
```

### 7.2 AI Settings Configuration
```python
# config/ai_settings.py
from pydantic import BaseSettings
from typing import Optional

class AISettings(BaseSettings):
    # OpenAI Configuration
    openai_api_key: str
    ai_model: str = "gpt-4"
    ai_max_tokens: int = 1000
    ai_temperature: float = 0.7
    
    # Processing Controls
    enable_ai_analysis: bool = True
    enable_response_generation: bool = True
    ai_processing_timeout: int = 30
    
    # Cost Management
    daily_token_limit: int = 50000
    monthly_token_limit: int = 1000000
    
    # Fallback Settings
    fallback_query_type: str = "general_inquiry"
    fallback_urgency_level: int = 3
    fallback_sentiment: str = "neutral"
    
    class Config:
        env_file = ".env"

ai_settings = AISettings()
```

## 8. Testing and Validation

### 8.1 AI Testing Framework
```python
# tests/test_ai_processing.py
import pytest
from backend.services.ai_service import EmailAIProcessor
from backend.services.response_generator import ResponseGenerator

class TestAIProcessing:
    @pytest.fixture
    def ai_processor(self):
        return EmailAIProcessor()
    
    @pytest.fixture
    def response_generator(self):
        return ResponseGenerator()
    
    @pytest.mark.asyncio
    async def test_leave_request_analysis(self, ai_processor):
        email_content = """
        Hi HR Team,
        
        I would like to request annual leave from June 15th to June 25th.
        I have checked with my manager and the timing works well for our project schedule.
        
        Please let me know if you need any additional information.
        
        Best regards,
        John Smith
        """
        
        result = await ai_processor.analyze_email(
            email_content=email_content,
            subject="Annual Leave Request",
            sender="john.smith@company.com"
        )
        
        assert result["success"] is True
        analysis = result["analysis"]
        assert analysis["query_type"] == "leave_request"
        assert analysis["urgency_level"] <= 3
        assert "John Smith" in analysis.get("employee_name", "")
    
    @pytest.mark.asyncio
    async def test_urgent_complaint_analysis(self, ai_processor):
        email_content = """
        URGENT: I need to speak with someone immediately about harassment
        in my department. This is affecting my ability to work and I need
        this addressed as soon as possible.
        """
        
        result = await ai_processor.analyze_email(
            email_content=email_content,
            subject="URGENT: Workplace Issue",
            sender="employee@company.com"
        )
        
        assert result["success"] is True
        analysis = result["analysis"]
        assert analysis["query_type"] == "complaint"
        assert analysis["urgency_level"] >= 4
        assert analysis["requires_immediate_attention"] is True
```

## 9. Monitoring and Analytics

### 9.1 AI Performance Metrics
```python
# backend/services/ai_analytics.py
from typing import Dict, List
from datetime import datetime, timedelta

class AIAnalytics:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_processing_stats(self, days: int = 7) -> Dict:
        """Get AI processing statistics"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query processing logs
        logs = self.db.query(AIProcessingLog).filter(
            AIProcessingLog.created_at >= start_date
        ).all()
        
        total_requests = len(logs)
        successful_requests = len([l for l in logs if l.success])
        total_tokens = sum(l.tokens_used for l in logs if l.tokens_used)
        avg_processing_time = sum(l.processing_time for l in logs) / total_requests if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "total_tokens_used": total_tokens,
            "average_processing_time": avg_processing_time,
            "cost_estimate": self.estimate_cost(total_tokens)
        }
    
    def estimate_cost(self, tokens: int) -> float:
        """Estimate OpenAI API cost based on token usage"""
        # GPT-4 pricing (approximate)
        cost_per_1k_tokens = 0.03  # Input tokens
        return (tokens / 1000) * cost_per_1k_tokens
```

## 10. Next Steps for Implementation

### 10.1 Phase 1: Basic AI Integration
1. **Set up OpenAI API key** in environment
2. **Implement basic email analysis** with simple prompts
3. **Test with sample emails** to validate responses
4. **Add AI data to webhook logging** (without database)

### 10.2 Phase 2: Enhanced Processing
1. **Restore database functionality** with AI fields
2. **Implement response generation** system
3. **Add ticket management** with AI analysis
4. **Create AI analytics dashboard**

### 10.3 Phase 3: Production Optimization
1. **Implement cost controls** and token limits
2. **Add error handling** and fallback mechanisms
3. **Optimize prompts** for better accuracy
4. **Add performance monitoring**

---

**Document Version**: 1.0  
**Last Updated**: May 30, 2025  
**Author**: AI Development Team  
**Next Review**: June 15, 2025 