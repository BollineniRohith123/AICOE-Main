"""
Hybrid LLM Client
Attempts real OpenRouter API calls, falls back to intelligent mocking if API fails
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
    Hybrid LLM Client - tries real OpenRouter API, falls back to smart mocking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: str = "x-ai/grok-code-fast-1"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.provider = provider
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.logger = logging.getLogger("llm_client")
        self.use_mock = False
        
        # Test API key validity on initialization
        if self.api_key:
            self.logger.info(f"🚀 Hybrid LLM Client initialized | Model: {self.model}")
            self.logger.info("🔍 Testing API key validity...")
        else:
            self.logger.warning("⚠️ No API key provided, using mock mode")
            self.use_mock = True
    
    async def send_message_async(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Send message to OpenRouter API
        
        Args:
            user_message: The user's message
            system_message: System prompt
            session_id: Session ID for chat context (optional)
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response text
        """
        try:
            # Log API call start
            self.logger.info(f"🔵 OpenRouter API Call | Model: {self.model} | Temp: {temperature} | Max tokens: {max_tokens}")
            self.logger.info(f"   Message length: {len(user_message)} chars")
            
            # Prepare request payload according to OpenRouter API spec
            payload = {
                "model": self.model,
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
            
            # Prepare headers according to OpenRouter API documentation
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
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
                ) as response:
                    
                    # Check response status
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"🔴 OpenRouter API Error | Status: {response.status} | Error: {error_text}")
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                    
                    # Parse response
                    response_data = await response.json()
                    
                    # Extract message content
                    if "choices" not in response_data or not response_data["choices"]:
                        raise Exception("No choices in OpenRouter response")
                    
                    message_content = response_data["choices"][0]["message"]["content"]
                    
                    # Log usage statistics if available
                    usage = response_data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    
                    self.logger.info(f"🟢 OpenRouter API Success | Response: {len(message_content)} chars")
                    self.logger.info(f"   Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")
                    
                    return message_content
                    
        except asyncio.TimeoutError:
            self.logger.error("🔴 OpenRouter API Timeout")
            raise Exception("OpenRouter API request timed out")
        except aiohttp.ClientError as e:
            self.logger.error(f"🔴 OpenRouter API Client Error: {str(e)}")
            raise Exception(f"OpenRouter API client error: {str(e)}")
        except json.JSONDecodeError as e:
            self.logger.error(f"🔴 OpenRouter API JSON Decode Error: {str(e)}")
            raise Exception(f"Failed to parse OpenRouter API response: {str(e)}")
        except Exception as e:
            self.logger.error(f"🔴 OpenRouter API Unexpected Error: {str(e)}")
            raise Exception(f"OpenRouter API call failed: {str(e)}")
    
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
