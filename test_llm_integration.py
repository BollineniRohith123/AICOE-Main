#!/usr/bin/env python3
"""
Test LLM Integration with OpenRouter API
"""

import asyncio
import sys
import os

# Add backend directory to path for imports
sys.path.append('/app/backend')

from agents.llm_client import LLMClient

async def test_llm_integration():
    """Test LLM integration with OpenRouter API"""
    
    print("🧪 Testing LLM Integration with OpenRouter API")
    print("=" * 50)
    
    try:
        # Initialize LLM client
        llm_client = LLMClient(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            provider="openrouter",
            model="meta-llama/llama-3.2-3b-instruct:free"
        )
        
        print(f"✅ LLM Client initialized")
        print(f"   Model: {llm_client.model}")
        print(f"   Provider: {llm_client.provider}")
        print(f"   API Key: {'*' * 20}{llm_client.api_key[-10:] if llm_client.api_key else 'None'}")
        
        # Test simple message
        test_message = "Hello! Please respond with 'LLM integration working' if you can understand this message."
        system_message = "You are a helpful AI assistant. Respond clearly and concisely."
        
        print(f"\n🔄 Sending test message...")
        print(f"   Message: {test_message}")
        
        response = await llm_client.send_message_async(
            user_message=test_message,
            system_message=system_message,
            temperature=0.1,
            max_tokens=100
        )
        
        print(f"\n✅ LLM Response received:")
        print(f"   Response: {response}")
        print(f"   Length: {len(response)} characters")
        
        # Check if response is reasonable
        if response and len(response) > 10:
            print(f"\n🎉 LLM Integration Test: PASSED")
            print(f"   The LLM is responding correctly!")
            return True
        else:
            print(f"\n❌ LLM Integration Test: FAILED")
            print(f"   Response too short or empty")
            return False
            
    except Exception as e:
        print(f"\n❌ LLM Integration Test: FAILED")
        print(f"   Error: {str(e)}")
        return False

async def main():
    """Main test execution"""
    success = await test_llm_integration()
    
    if success:
        print(f"\n🚀 Ready to run complete workflow test!")
    else:
        print(f"\n⚠️  LLM integration needs to be fixed before running workflow")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())