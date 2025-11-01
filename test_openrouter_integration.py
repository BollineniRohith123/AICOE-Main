#!/usr/bin/env python3
"""
Test script for OpenRouter API integration
Tests the real LLM client with various scenarios
"""
import asyncio
import sys
import os
import logging

# Add backend to path
sys.path.append('/app/backend')

from agents.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_basic_functionality():
    """Test basic OpenRouter API functionality"""
    print("🧪 Testing OpenRouter API Integration")
    print("=" * 50)
    
    try:
        # Initialize client
        print("1. Initializing LLM Client...")
        client = LLMClient()
        print("✅ Client initialized successfully")
        
        # Test simple message
        print("\n2. Testing simple message...")
        response = await client.send_message_async(
            user_message="Hello! Please respond with 'API connection successful' if you can read this.",
            system_message="You are a helpful assistant. Respond concisely.",
            temperature=0.3,
            max_tokens=100
        )
        print(f"✅ Response received: {response[:100]}...")
        
        # Test with different parameters
        print("\n3. Testing with different parameters...")
        response2 = await client.send_message_async(
            user_message="Write a very short haiku about technology.",
            system_message="You are a creative poet.",
            temperature=0.8,
            max_tokens=50
        )
        print(f"✅ Creative response: {response2}")
        
        # Test JSON generation
        print("\n4. Testing JSON generation...")
        response3 = await client.send_message_async(
            user_message="Generate a simple JSON object with name and age fields. Return only valid JSON.",
            system_message="You are a JSON generator. Return only valid JSON without markdown.",
            temperature=0.1,
            max_tokens=100
        )
        print(f"✅ JSON response: {response3}")
        
        print("\n🎉 All tests passed! OpenRouter integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_synchronous_wrapper():
    """Test the synchronous wrapper"""
    print("\n5. Testing synchronous wrapper...")
    try:
        client = LLMClient()
        response = client.send_message(
            user_message="Test sync call. Respond with 'Sync working'.",
            temperature=0.1,
            max_tokens=50
        )
        print(f"✅ Sync response: {response}")
        return True
    except Exception as e:
        print(f"❌ Sync test failed: {str(e)}")
        return False

async def test_error_handling():
    """Test error handling scenarios"""
    print("\n6. Testing error handling...")
    
    # Test with invalid API key
    try:
        print("   Testing invalid API key...")
        invalid_client = LLMClient(api_key="invalid-key")
        await invalid_client.send_message_async("test")
        print("❌ Should have failed with invalid key")
        return False
    except Exception as e:
        print(f"✅ Correctly handled invalid key: {type(e).__name__}")
    
    # Test with very long message (should work but test timeout handling)
    try:
        print("   Testing reasonable message length...")
        client = LLMClient()
        long_message = "Please summarize this: " + "test " * 100
        response = await client.send_message_async(
            user_message=long_message,
            max_tokens=50
        )
        print(f"✅ Handled long message: {len(response)} chars")
        return True
    except Exception as e:
        print(f"❌ Long message test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting OpenRouter API Integration Tests")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return False
    
    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Run tests
    tests = [
        test_basic_functionality(),
        test_error_handling()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    # Test sync wrapper
    sync_result = test_synchronous_wrapper()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    
    success_count = sum(1 for r in results if r is True) + (1 if sync_result else 0)
    total_tests = len(results) + 1
    
    print(f"✅ Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests passed! OpenRouter integration is fully functional.")
        return True
    else:
        print("❌ Some tests failed. Check the logs above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)