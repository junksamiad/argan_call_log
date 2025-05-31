"""
Simple OpenAI API test to check connectivity and available methods
"""

import os
from openai import OpenAI

print("🔍 Testing OpenAI SDK...")

# Check if API key is set
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"✅ API key found: {api_key[:10]}...")
else:
    print("❌ No API key found")
    exit(1)

# Initialize client
try:
    client = OpenAI()
    print("✅ OpenAI client initialized")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Check available methods
print(f"📋 Available client methods: {[attr for attr in dir(client) if not attr.startswith('_')]}")

# Check if responses exists
if hasattr(client, 'responses'):
    print("✅ client.responses exists")
    print(f"📋 Responses methods: {[attr for attr in dir(client.responses) if not attr.startswith('_')]}")
else:
    print("❌ client.responses does NOT exist")

# Check if chat exists (fallback)
if hasattr(client, 'chat'):
    print("✅ client.chat exists")
    if hasattr(client.chat, 'completions'):
        print("✅ client.chat.completions exists")
else:
    print("❌ client.chat does NOT exist")

# Try a simple API call
print("\n🧪 Testing simple API call...")
try:
    # Try chat completions (this should always work)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say 'test successful'"}],
        max_tokens=10
    )
    print("✅ Chat completions API working!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Chat completions failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ OpenAI diagnostics complete!") 