import openai
import json
from typing import Dict, Optional, List
import logging
from backend.models.schemas import ParsedEmailQuery, EmailSummary, QueryType, Priority
from config.settings import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        
    def parse_email_query(self, email_body: str, subject: str) -> ParsedEmailQuery:
        """Extract structured information from email using AI"""
        try:
            prompt = f"""
            Analyze the following HR query email and extract structured information.
            
            Subject: {subject}
            Body: {email_body}
            
            Extract and return the following information in JSON format:
            - staff_name: The name of the person making the query
            - staff_email: Their email address (extract from the email content or sender info)
            - department: Their department if mentioned
            - query_type: Categorize as one of: leave_request, policy_question, complaint, general_inquiry, payroll, benefits, training, other
            - urgency_level: Assess as one of: low, normal, high, urgent
            - query_summary: A brief one-line summary of the query
            - detailed_description: A detailed description of the issue
            - mentioned_dates: List of any dates mentioned
            - mentioned_people: List of any people mentioned
            - policy_references: Any company policies or procedures referenced
            - sentiment: The overall sentiment (positive, neutral, negative, frustrated, etc.)
            - requires_ops_approval: Boolean - whether this needs ops manager approval (default true for HR queries)
            - suggested_actions: List of recommended next steps
            
            Return only valid JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an HR assistant specialized in parsing and categorizing employee queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            parsed_data = json.loads(response.choices[0].message.content)
            
            # Validate and convert to Pydantic model
            return ParsedEmailQuery(**parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing email with AI: {str(e)}")
            # Return a basic parsed structure on error
            return ParsedEmailQuery(
                staff_name="Unknown",
                staff_email="unknown@example.com",
                query_type=QueryType.OTHER,
                urgency_level=Priority.NORMAL,
                query_summary=subject or "Unable to parse query",
                detailed_description=email_body[:500],
                requires_ops_approval=True
            )
            
    def generate_summary(self, parsed_query: ParsedEmailQuery, email_body: str) -> EmailSummary:
        """Generate executive summary and action items"""
        try:
            prompt = f"""
            Based on this HR query, provide an executive summary and analysis:
            
            Query Type: {parsed_query.query_type.value}
            Summary: {parsed_query.query_summary}
            Details: {parsed_query.detailed_description}
            Urgency: {parsed_query.urgency_level.value}
            
            Original Email:
            {email_body}
            
            Provide:
            1. An executive summary (2-3 sentences) suitable for management review
            2. Key points (3-5 bullet points)
            3. Action items (what needs to be done)
            4. Any risks identified (compliance, legal, employee relations)
            5. Recommended tone for response (professional, empathetic, formal, etc.)
            
            Return as JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an HR expert providing management summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            summary_data = json.loads(response.choices[0].message.content)
            return EmailSummary(**summary_data)
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return EmailSummary(
                executive_summary="Summary generation failed. Please review the original query.",
                key_points=["Error in AI summary generation"],
                action_items=["Manual review required"],
                recommended_response_tone="professional"
            )
            
    def generate_response_suggestion(self, query: ParsedEmailQuery, summary: EmailSummary, 
                                   company_context: Optional[str] = None) -> str:
        """Generate a suggested response to the query"""
        try:
            context = company_context or "Standard HR policies apply."
            
            prompt = f"""
            Generate a professional HR response to this employee query:
            
            Query Summary: {query.query_summary}
            Query Type: {query.query_type.value}
            Urgency: {query.urgency_level.value}
            Detailed Description: {query.detailed_description}
            
            Recommended Tone: {summary.recommended_response_tone}
            Key Points to Address: {', '.join(summary.key_points)}
            
            Company Context: {context}
            
            Generate a response that:
            1. Acknowledges the query professionally
            2. Shows empathy where appropriate
            3. Provides clear next steps
            4. Mentions that the query is being reviewed by management (if requires_ops_approval is true)
            5. Sets expectations for response time
            6. Maintains appropriate HR boundaries
            
            The response should be ready to send after ops manager approval.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional HR consultant drafting responses to employee queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response suggestion: {str(e)}")
            return f"""
            Dear {query.staff_name},
            
            Thank you for your query regarding {query.query_summary}.
            
            We have received your message and it has been assigned a ticket number for tracking. 
            Your query is currently being reviewed by our HR team and management.
            
            We will respond to you within 24-48 hours with further information.
            
            Best regards,
            HR Team
            """
            
    def analyze_thread_context(self, messages: List[Dict]) -> Dict:
        """Analyze an entire email thread for context and patterns"""
        try:
            # Prepare thread history
            thread_text = "\n\n".join([
                f"From: {msg['sender']}\nDate: {msg['email_date']}\n{msg['body_text']}"
                for msg in messages
            ])
            
            prompt = f"""
            Analyze this email thread and provide insights:
            
            {thread_text}
            
            Provide:
            1. Thread summary
            2. Current status of the issue
            3. Unresolved items
            4. Escalation indicators
            5. Recommended next actions
            
            Return as JSON.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are analyzing HR email threads for patterns and context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error analyzing thread: {str(e)}")
            return {
                "thread_summary": "Unable to analyze thread",
                "current_status": "Unknown",
                "unresolved_items": [],
                "escalation_indicators": [],
                "recommended_next_actions": ["Manual review required"]
            } 