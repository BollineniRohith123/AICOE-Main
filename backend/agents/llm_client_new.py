"""
OpenRouter LLM Client
Production-ready implementation for OpenRouter API with comprehensive error handling
"""
import os
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    OpenRouter LLM Client - Production implementation with comprehensive error handling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: str = "deepseek/deepseek-chat-v3.1:free"  # Using free model as default
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("❌ OpenRouter API key required. Set OPENROUTER_API_KEY environment variable or pass api_key parameter.")
        
        self.provider = provider
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.logger = logging.getLogger("llm_client")
        
        # Available free models as fallbacks
        self.free_models = [
            "deepseek/deepseek-chat-v3.1:free",
            "nvidia/nemotron-nano-9b-v2:free", 
            "minimax/minimax-m2:free",
            "qwen/qwen3-coder:free",
            "meta-llama/llama-3.2-3b-instruct:free"
        ]
        
        self.logger.info(f"🚀 OpenRouter LLM Client initialized")
        self.logger.info(f"   Model: {self.model}")
        self.logger.info(f"   API Key: {self.api_key[:15]}...{self.api_key[-10:]}")
    
    async def send_message_async(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Send message to OpenRouter API with automatic model fallback
        
        Args:
            user_message: The user's message
            system_message: System prompt
            session_id: Session ID for chat context (optional)
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response text
        """
        # Try primary model first, then fallback to free models
        models_to_try = [self.model] + [m for m in self.free_models if m != self.model]
        
        for attempt, model in enumerate(models_to_try):
            try:
                self.logger.info(f"🔵 OpenRouter API Call (Attempt {attempt + 1}) | Model: {model}")
                self.logger.info(f"   Temp: {temperature} | Max tokens: {max_tokens} | Message: {len(user_message)} chars")
                
                # Prepare request payload according to OpenRouter API spec
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                }
                
                # Add session context if provided
                if session_id:
                    payload["metadata"] = {"session_id": session_id}
                
                # Prepare headers according to OpenRouter documentation
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://aicoe-platform.local",
                    "X-Title": "AICOE Automation Platform",
                    "User-Agent": "AICOE-Platform/1.0"
                }
                
                # Make API request
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        
                        # Handle different response statuses
                        if response.status == 200:
                            response_data = await response.json()
                            
                            # Extract message content
                            if "choices" not in response_data or not response_data["choices"]:
                                raise Exception("No choices in OpenRouter response")
                            
                            message_content = response_data["choices"][0]["message"]["content"]
                            
                            # Log success with usage statistics
                            usage = response_data.get("usage", {})
                            prompt_tokens = usage.get("prompt_tokens", 0)
                            completion_tokens = usage.get("completion_tokens", 0)
                            total_tokens = usage.get("total_tokens", 0)
                            
                            self.logger.info(f"🟢 OpenRouter API Success | Model: {model}")
                            self.logger.info(f"   Response: {len(message_content)} chars | Tokens: {prompt_tokens}+{completion_tokens}={total_tokens}")
                            
                            return message_content
                            
                        elif response.status == 401:
                            error_text = await response.text()
                            self.logger.error(f"🔴 Authentication Error | Status: {response.status} | Error: {error_text}")
                            
                            if "User not found" in error_text:
                                raise Exception("❌ OpenRouter API Key Invalid: User account not found. Please check your API key at https://openrouter.ai/keys")
                            elif "No cookie auth credentials" in error_text:
                                raise Exception("❌ OpenRouter API Key Invalid: Authentication failed. Please verify your API key format.")
                            else:
                                raise Exception(f"❌ OpenRouter Authentication Error: {error_text}")
                                
                        elif response.status == 429:
                            error_text = await response.text()
                            self.logger.warning(f"⚠️ Rate Limited | Model: {model} | Error: {error_text}")
                            if attempt < len(models_to_try) - 1:
                                self.logger.info("🔄 Trying next model due to rate limit...")
                                continue
                            else:
                                raise Exception(f"❌ All models rate limited: {error_text}")
                                
                        elif response.status == 402:
                            error_text = await response.text()
                            self.logger.warning(f"💳 Insufficient Credits | Model: {model} | Error: {error_text}")
                            if attempt < len(models_to_try) - 1:
                                self.logger.info("🔄 Trying free model due to insufficient credits...")
                                continue
                            else:
                                raise Exception(f"❌ Insufficient credits for all models: {error_text}")
                                
                        else:
                            error_text = await response.text()
                            self.logger.error(f"🔴 OpenRouter API Error | Status: {response.status} | Model: {model} | Error: {error_text}")
                            if attempt < len(models_to_try) - 1:
                                self.logger.info("🔄 Trying next model due to API error...")
                                continue
                            else:
                                raise Exception(f"❌ OpenRouter API error {response.status}: {error_text}")
                                
            except asyncio.TimeoutError:
                self.logger.error(f"⏰ Timeout | Model: {model}")
                if attempt < len(models_to_try) - 1:
                    self.logger.info("🔄 Trying next model due to timeout...")
                    continue
                else:
                    raise Exception("❌ All models timed out")
                    
            except aiohttp.ClientError as e:
                self.logger.error(f"🔴 Client Error | Model: {model} | Error: {str(e)}")
                if attempt < len(models_to_try) - 1:
                    self.logger.info("🔄 Trying next model due to client error...")
                    continue
                else:
                    raise Exception(f"❌ Network error for all models: {str(e)}")
                    
            except json.JSONDecodeError as e:
                self.logger.error(f"🔴 JSON Error | Model: {model} | Error: {str(e)}")
                if attempt < len(models_to_try) - 1:
                    self.logger.info("🔄 Trying next model due to JSON error...")
                    continue
                else:
                    raise Exception(f"❌ Invalid response format from all models: {str(e)}")
        
        # If we get here, all models failed
        raise Exception("❌ All OpenRouter models failed. Please check your API key and account status.")
    
    def send_message(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Synchronous wrapper for send_message_async
        """
        return asyncio.run(
            self.send_message_async(
                user_message=user_message,
                system_message=system_message,
                session_id=session_id,
                temperature=temperature,
                max_tokens=max_tokens
            )
        )

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the OpenRouter API connection and return status information
        
        Returns:
            Dictionary with connection status and available models
        """
        try:
            self.logger.info("🔍 Testing OpenRouter API connection...")
            
            # Test 1: Check if we can access models endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        models_data = await response.json()
                        total_models = len(models_data.get('data', []))
                        
                        # Test 2: Try a simple chat completion with a free model
                        test_response = await self.send_message_async(
                            user_message="Say 'Connection test successful' if you can read this.",
                            system_message="You are a test assistant.",
                            temperature=0.1,
                            max_tokens=50
                        )
                        
                        return {
                            "status": "success",
                            "api_key_valid": True,
                            "models_accessible": True,
                            "total_models": total_models,
                            "chat_working": True,
                            "test_response": test_response,
                            "primary_model": self.model,
                            "fallback_models": self.free_models
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "error",
                            "api_key_valid": False,
                            "error": f"Models endpoint failed: {response.status} - {error_text}"
                        }
                        
        except Exception as e:
            return {
                "status": "error",
                "api_key_valid": False,
                "error": str(e)
            }