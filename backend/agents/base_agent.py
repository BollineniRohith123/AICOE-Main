"""
Base Agent Class for AICOE Multi-Agent System
Inspired by Google ADK architecture
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)


class AgentConfig:
    """Configuration for an agent"""
    def __init__(
        self,
        name: str,
        description: str,
        model: str = "x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
        temperature: float = 0.7,
        max_tokens: int = 4000,
        timeout: int = 120
    ):
        self.name = name
        self.description = description
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout


class AgentResult:
    """Result from an agent execution"""
    def __init__(
        self,
        success: bool,
        data: Any,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()


class BaseAgent(ABC):
    """
    Base class for all agents in the AICOE platform
    Follows Google ADK principles for agent design
    """
    
    def __init__(self, config: AgentConfig, llm_client):
        self.config = config
        self.llm_client = llm_client
        self.logger = logging.getLogger(f"agent.{config.name}")
        
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main logic
        
        Args:
            input_data: Input data for the agent
            context: Shared context across agents (project info, previous results, etc.)
            
        Returns:
            AgentResult with success status and output data
        """
        pass
    
    async def _call_llm(
        self,
        system_message: str,
        user_message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ) -> str:
        """
        Call the LLM with given messages with automatic retry logic

        Args:
            system_message: System prompt
            user_message: User message/prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            LLM response text
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens

        last_error = None
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 2^attempt seconds
                    wait_time = 2 ** attempt
                    self.logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay")
                    await asyncio.sleep(wait_time)

                response = await self.llm_client.send_message_async(
                    user_message=user_message,
                    system_message=system_message,
                    temperature=temp,
                    max_tokens=tokens
                )
                return response

            except Exception as e:
                last_error = e
                self.logger.warning(f"LLM call attempt {attempt + 1}/{max_retries} failed: {str(e)}")

                # Don't retry on certain errors
                error_str = str(e).lower()
                if any(term in error_str for term in ['authentication', 'api key', 'unauthorized', 'forbidden']):
                    self.logger.error(f"Non-retryable error: {str(e)}")
                    raise

        # All retries exhausted
        self.logger.error(f"LLM call failed after {max_retries} attempts: {str(last_error)}")
        raise Exception(f"LLM call failed after {max_retries} retries: {str(last_error)}")
    
    def validate_input(self, input_data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that input data contains all required keys
        
        Args:
            input_data: Input data to validate
            required_keys: List of required keys
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        missing = [key for key in required_keys if key not in input_data]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")
        return True
    
    def log_execution(self, step: str, details: str):
        """Log execution steps"""
        self.logger.info(f"[{self.config.name}] {step}: {details}")

    def parse_json_response(self, response: str, fallback_key: str = "raw_response") -> Dict[str, Any]:
        """
        Parse JSON response from LLM with robust error handling

        Args:
            response: LLM response text
            fallback_key: Key to use if JSON parsing fails

        Returns:
            Parsed JSON dict or fallback dict with raw response
        """
        import json
        import re

        try:
            # Clean response
            response = response.strip()

            # Remove markdown code blocks
            if response.startswith("```json"):
                response = response.split("```json")[1].split("```")[0].strip()
            elif response.startswith("```"):
                response = response.split("```")[1].split("```")[0].strip()

            # Try to parse directly
            return json.loads(response)

        except json.JSONDecodeError as e:
            self.logger.warning(f"Initial JSON parse failed: {str(e)}")

            # Try to extract JSON from text
            try:
                # Look for JSON object pattern
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)

                # Look for JSON array pattern
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    return json.loads(json_str)

            except json.JSONDecodeError:
                pass

            # Return fallback
            self.logger.error(f"Could not parse JSON from response (length: {len(response)})")
            self.logger.error(f"Response preview: {response[:500]}")
            return {fallback_key: response, "parse_error": str(e)}
