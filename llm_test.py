#!/usr/bin/env python3
"""
Test LLM Integration for AICOE Platform
"""

import sys
import os
sys.path.append('/app/backend')

from agents.llm_client import LLMClient
import asyncio

async def test_llm_connection():
    """Test LLM client connection and basic functionality"""
    print("🤖 Testing LLM Integration")
    print("=" * 40)
    
    try:
        # Initialize LLM client
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OPENROUTER_API_KEY not found in environment")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        
        llm_client = LLMClient(
            api_key=api_key,
            provider="openrouter",
            model="x-ai/grok-code-fast-1"
        )
        
        print("✅ LLM Client initialized")
        
        # Test simple completion
        test_prompt = "Hello, this is a test. Please respond with 'LLM connection successful'."
        
        print("📤 Sending test prompt...")
        response = await llm_client.send_message_async(test_prompt)
        
        if response and len(response.strip()) > 0:
            print(f"✅ LLM Response received: {response[:100]}...")
            return True
        else:
            print("❌ Empty or invalid LLM response")
            return False
            
    except Exception as e:
        print(f"❌ LLM Test failed: {str(e)}")
        return False

async def main():
    """Main test execution"""
    # Load environment variables
    from dotenv import load_dotenv
    from pathlib import Path
    
    backend_dir = Path("/app/backend")
    load_dotenv(backend_dir / '.env')
    
    success = await test_llm_connection()
    
    if success:
        print("\n🎉 LLM integration is working!")
    else:
        print("\n❌ LLM integration has issues")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())