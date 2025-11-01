#!/usr/bin/env python3
"""
Test OpenRouter API key with different models
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
backend_dir = Path("/app/backend")
load_dotenv(backend_dir / '.env')

api_key = os.getenv("OPENROUTER_API_KEY")

async def test_openrouter_models():
    """Test different models on OpenRouter"""
    from openai import AsyncOpenAI
    
    models_to_test = [
        "openai/gpt-4o-mini",  # OpenAI model through OpenRouter
        "anthropic/claude-3.5-sonnet",  # Claude model
        "google/gemini-pro-1.5",  # Gemini model
        "x-ai/grok-2-1212",  # Grok model (more stable than fast)
    ]
    
    for model in models_to_test:
        print(f"\n🔵 Testing model: {model}")
        print("=" * 60)
        
        try:
            client = AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Say 'Hello from OpenRouter!' and nothing else"}
                ],
                max_tokens=50,
                extra_headers={
                    "HTTP-Referer": "https://aicoe-platform.local",
                    "X-Title": "AICOE Automation Platform"
                }
            )
            
            result = response.choices[0].message.content
            print(f"✅ SUCCESS with {model}")
            print(f"Response: {result[:100]}")
            return model  # Return first working model
            
        except Exception as e:
            print(f"❌ FAILED with {model}: {str(e)}")
    
    return None

async def main():
    print("🤖 Testing OpenRouter API Key with Multiple Models")
    print("=" * 60)
    print(f"API Key: {api_key[:15]}...")
    print()
    
    working_model = await test_openrouter_models()
    
    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
        print(f"✅ Update server.py to use this model!")
    else:
        print("\n❌ No working models found. API key may be invalid or account has issues.")
        print("Please check:")
        print("1. Account is active at https://openrouter.ai/")
        print("2. API key is not revoked")
        print("3. Account has credits/payment method")

if __name__ == "__main__":
    asyncio.run(main())
