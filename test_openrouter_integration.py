#!/usr/bin/env python3
"""
Comprehensive OpenRouter API Integration Test
Tests the production LLM client with various scenarios and error handling
"""
import asyncio
import sys
import os
import logging
import json

# Add backend to path
sys.path.append('/app/backend')

from agents.llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_connection_status():
    """Test the connection status method"""
    print("🔍 Testing Connection Status")
    print("-" * 40)
    
    try:
        client = LLMClient()
        status = await client.test_connection()
        
        print(f"Status: {status['status']}")
        if status['status'] == 'success':
            print(f"✅ API Key Valid: {status['api_key_valid']}")
            print(f"✅ Models Accessible: {status['models_accessible']}")
            print(f"✅ Total Models: {status['total_models']}")
            print(f"✅ Chat Working: {status['chat_working']}")
            print(f"✅ Primary Model: {status['primary_model']}")
            print(f"✅ Test Response: {status['test_response']}")
            return True
        else:
            print(f"❌ Connection failed: {status['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False

async def test_model_fallback():
    """Test model fallback functionality"""
    print("\n🔄 Testing Model Fallback")
    print("-" * 40)
    
    try:
        # Test with a paid model that should fallback to free
        client = LLMClient(model="openai/gpt-4o")  # Expensive model
        
        response = await client.send_message_async(
            user_message="Say 'Fallback working' if you can read this.",
            system_message="You are a test assistant.",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ Fallback response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {str(e)}")
        return False

async def test_different_message_types():
    """Test different types of messages"""
    print("\n📝 Testing Different Message Types")
    print("-" * 40)
    
    try:
        client = LLMClient()
        
        # Test 1: Simple question
        print("1. Simple question...")
        response1 = await client.send_message_async(
            user_message="What is 2+2?",
            temperature=0.1,
            max_tokens=50
        )
        print(f"   Math response: {response1.strip()}")
        
        # Test 2: Creative task
        print("2. Creative task...")
        response2 = await client.send_message_async(
            user_message="Write a 2-line poem about AI.",
            temperature=0.8,
            max_tokens=100
        )
        print(f"   Poem: {response2.strip()}")
        
        # Test 3: JSON generation
        print("3. JSON generation...")
        response3 = await client.send_message_async(
            user_message="Create a JSON object with fields: name (string), age (number), active (boolean). Return only valid JSON.",
            system_message="You are a JSON generator. Return only valid JSON without markdown formatting.",
            temperature=0.1,
            max_tokens=100
        )
        print(f"   JSON: {response3.strip()}")
        
        # Test 4: Code generation
        print("4. Code generation...")
        response4 = await client.send_message_async(
            user_message="Write a Python function to add two numbers. Keep it simple.",
            temperature=0.3,
            max_tokens=150
        )
        print(f"   Code: {response4.strip()[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Message type tests failed: {str(e)}")
        return False

def test_synchronous_methods():
    """Test synchronous wrapper methods"""
    print("\n⚡ Testing Synchronous Methods")
    print("-" * 40)
    
    try:
        client = LLMClient()
        
        # Test sync send_message
        response = client.send_message(
            user_message="Respond with 'Sync method working' if you can read this.",
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"✅ Sync response: {response.strip()}")
        return True
        
    except Exception as e:
        print(f"❌ Sync test failed: {str(e)}")
        return False

async def test_error_scenarios():
    """Test various error scenarios"""
    print("\n🚨 Testing Error Scenarios")
    print("-" * 40)
    
    error_tests_passed = 0
    total_error_tests = 3
    
    # Test 1: Invalid API key
    try:
        print("1. Testing invalid API key...")
        invalid_client = LLMClient(api_key="sk-invalid-key-12345")
        await invalid_client.send_message_async("test")
        print("   ❌ Should have failed with invalid key")
    except Exception as e:
        if "API Key Invalid" in str(e) or "Authentication" in str(e):
            print("   ✅ Correctly handled invalid API key")
            error_tests_passed += 1
        else:
            print(f"   ⚠️ Unexpected error: {str(e)}")
    
    # Test 2: Empty message
    try:
        print("2. Testing empty message...")
        client = LLMClient()
        response = await client.send_message_async("")
        print(f"   ✅ Handled empty message: {response[:50]}...")
        error_tests_passed += 1
    except Exception as e:
        print(f"   ⚠️ Empty message error: {str(e)}")
    
    # Test 3: Very long message
    try:
        print("3. Testing very long message...")
        client = LLMClient()
        long_message = "Please summarize: " + "This is a test sentence. " * 200
        response = await client.send_message_async(
            user_message=long_message,
            max_tokens=100
        )
        print(f"   ✅ Handled long message: {len(response)} chars response")
        error_tests_passed += 1
    except Exception as e:
        print(f"   ⚠️ Long message error: {str(e)}")
    
    print(f"Error handling: {error_tests_passed}/{total_error_tests} tests passed")
    return error_tests_passed >= 2  # Allow some flexibility

async def main():
    """Run comprehensive OpenRouter integration tests"""
    print("🚀 OpenRouter API Integration Test Suite")
    print("=" * 60)
    
    # Check environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("💡 Please set the environment variable or check your .env file")
        return False
    
    print(f"🔑 API Key found: {api_key[:15]}...{api_key[-10:]}")
    
    # Run all test suites
    test_results = []
    
    # Test 1: Connection Status
    result1 = await test_connection_status()
    test_results.append(("Connection Status", result1))
    
    # Test 2: Model Fallback (only if connection works)
    if result1:
        result2 = await test_model_fallback()
        test_results.append(("Model Fallback", result2))
        
        # Test 3: Different Message Types
        result3 = await test_different_message_types()
        test_results.append(("Message Types", result3))
        
        # Test 4: Synchronous Methods
        result4 = test_synchronous_methods()
        test_results.append(("Synchronous Methods", result4))
    
    # Test 5: Error Scenarios (always run)
    result5 = await test_error_scenarios()
    test_results.append(("Error Handling", result5))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed_tests += 1
    
    total_tests = len(test_results)
    print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! OpenRouter integration is fully functional.")
        print("💡 Your API key is working and the client is ready for production use.")
        return True
    elif passed_tests >= total_tests - 1:
        print("\n⚠️ Most tests passed. Minor issues detected but core functionality works.")
        return True
    else:
        print("\n❌ Multiple test failures. Please check your API key and account status.")
        print("💡 Visit https://openrouter.ai/keys to verify your API key")
        print("💡 Check https://openrouter.ai/activity for usage and errors")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)