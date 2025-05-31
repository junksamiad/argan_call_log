"""
Direct test of OpenAI Responses API with structured outputs
"""

import os
from openai import OpenAI
from pydantic import BaseModel

print("🧪 Testing OpenAI Responses API...")

client = OpenAI()

# Simple test schema
class SimpleResponse(BaseModel):
    message: str
    confidence: float

print("📝 Testing responses.parse with simple schema...")

try:
    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[
            {
                "role": "user",
                "content": "Respond with a message 'Hello World' and confidence 0.95"
            }
        ],
        text_format=SimpleResponse
    )
    
    print("✅ Responses API successful!")
    print(f"Response type: {type(response)}")
    print(f"Parsed data: {response.output_parsed}")
    print(f"Message: {response.output_parsed.message}")
    print(f"Confidence: {response.output_parsed.confidence}")
    
except Exception as e:
    print(f"❌ Responses API failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Responses API test complete!") 