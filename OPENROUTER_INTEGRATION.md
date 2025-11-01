# OpenRouter API Integration

## Overview

This project now includes a production-ready OpenRouter API integration that replaces the previous mock implementation. The integration provides robust error handling, automatic model fallback, and comprehensive logging.

## Features

### ✅ Production-Ready Implementation
- Real OpenRouter API calls using aiohttp
- Comprehensive error handling and recovery
- Automatic model fallback for reliability
- Detailed logging and monitoring
- Both async and sync method support

### ✅ Error Handling
- **Authentication Errors**: Clear messages for invalid API keys
- **Rate Limiting**: Automatic fallback to alternative models
- **Insufficient Credits**: Graceful fallback to free models
- **Network Issues**: Timeout handling and retry logic
- **Invalid Responses**: JSON parsing error recovery

### ✅ Model Management
- **Primary Model**: Configurable main model (default: free model)
- **Fallback Models**: Automatic fallback to free models when needed
- **Free Models Available**:
  - `deepseek/deepseek-chat-v3.1:free`
  - `nvidia/nemotron-nano-9b-v2:free`
  - `minimax/minimax-m2:free`
  - `qwen/qwen3-coder:free`
  - `meta-llama/llama-3.2-3b-instruct:free`

## Setup

### 1. Get OpenRouter API Key
1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Create an account or sign in
3. Go to [API Keys](https://openrouter.ai/keys)
4. Generate a new API key
5. Ensure your account has credits or use free models

### 2. Configure Environment
```bash
# Set in your .env file
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
```

### 3. Verify Installation
```bash
# Test the integration
cd /app
python test_openrouter_integration.py
```

## Usage

### Basic Usage
```python
from agents.llm_client import LLMClient

# Initialize client (uses environment variable)
client = LLMClient()

# Send a message (synchronous)
response = client.send_message(
    user_message="Hello, how are you?",
    system_message="You are a helpful assistant.",
    temperature=0.7,
    max_tokens=1000
)
print(response)
```

### Async Usage
```python
import asyncio
from agents.llm_client import LLMClient

async def main():
    client = LLMClient()
    
    response = await client.send_message_async(
        user_message="Write a Python function to calculate fibonacci numbers.",
        system_message="You are a coding assistant.",
        temperature=0.3,
        max_tokens=500
    )
    print(response)

asyncio.run(main())
```

### Custom Configuration
```python
# Use specific model and API key
client = LLMClient(
    api_key="your-api-key",
    model="openai/gpt-4o-mini",  # Will fallback to free models if needed
    provider="openrouter"
)
```

### Connection Testing
```python
import asyncio
from agents.llm_client import LLMClient

async def test_connection():
    client = LLMClient()
    status = await client.test_connection()
    
    if status['status'] == 'success':
        print(f"✅ Connected! {status['total_models']} models available")
        print(f"Test response: {status['test_response']}")
    else:
        print(f"❌ Connection failed: {status['error']}")

asyncio.run(test_connection())
```

## API Reference

### LLMClient Class

#### Constructor
```python
LLMClient(
    api_key: Optional[str] = None,           # API key (uses env var if None)
    provider: str = "openrouter",            # Provider name
    model: str = "deepseek/deepseek-chat-v3.1:free"  # Primary model
)
```

#### Methods

##### send_message_async()
```python
async def send_message_async(
    user_message: str,                       # User's message
    system_message: str = "You are a helpful AI assistant.",  # System prompt
    session_id: Optional[str] = None,        # Session ID for context
    temperature: float = 0.7,                # Generation temperature (0.0-2.0)
    max_tokens: int = 4000                   # Maximum tokens to generate
) -> str
```

##### send_message()
```python
def send_message(
    user_message: str,
    system_message: str = "You are a helpful AI assistant.",
    session_id: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000
) -> str
```

##### test_connection()
```python
async def test_connection() -> Dict[str, Any]
```
Returns connection status and available models information.

## Error Handling

The client provides detailed error messages for common issues:

### API Key Issues
```
❌ OpenRouter API Key Invalid: User account not found. 
Please check your API key at https://openrouter.ai/keys
```

### Rate Limiting
```
⚠️ Rate Limited | Model: openai/gpt-4o | Error: Too many requests
🔄 Trying next model due to rate limit...
```

### Insufficient Credits
```
💳 Insufficient Credits | Model: openai/gpt-4o | Error: Insufficient balance
🔄 Trying free model due to insufficient credits...
```

## Logging

The client provides comprehensive logging:

```
🚀 OpenRouter LLM Client initialized
   Model: deepseek/deepseek-chat-v3.1:free
   API Key: sk-or-v1-d54876...5dce04a979

🔵 OpenRouter API Call (Attempt 1) | Model: deepseek/deepseek-chat-v3.1:free
   Temp: 0.7 | Max tokens: 1000 | Message: 25 chars

🟢 OpenRouter API Success | Model: deepseek/deepseek-chat-v3.1:free
   Response: 150 chars | Tokens: 15+35=50
```

## Troubleshooting

### Common Issues

1. **"User not found" Error**
   - Check if your API key is valid
   - Verify your OpenRouter account is active
   - Ensure you have credits or are using free models

2. **"No cookie auth credentials" Error**
   - Verify API key format (should start with `sk-or-v1-`)
   - Check for extra spaces or characters in the key

3. **Rate Limiting**
   - The client automatically falls back to free models
   - Consider upgrading your OpenRouter plan

4. **Network Timeouts**
   - Check your internet connection
   - The client has 2-minute timeout by default

### Getting Help

1. **OpenRouter Documentation**: https://openrouter.ai/docs
2. **API Status**: https://status.openrouter.ai
3. **Account Dashboard**: https://openrouter.ai/activity
4. **Available Models**: https://openrouter.ai/models

## Integration Status

✅ **COMPLETE**: Production-ready OpenRouter API integration
- Real API calls with comprehensive error handling
- Automatic model fallback for reliability
- Detailed logging and monitoring
- Both synchronous and asynchronous support
- Connection testing and validation
- Comprehensive test suite

The integration is ready for production use with a valid OpenRouter API key.