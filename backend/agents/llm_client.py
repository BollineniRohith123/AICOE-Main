"""
LLM Client using OpenAI SDK
Configured for OpenRouter with agent-specific models from environment
"""

import os
from typing import Optional
import asyncio
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around OpenAI SDK for LLM interactions via OpenRouter
    Supports agent-specific model configuration via environment variables
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: str = None,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key not provided and OPENROUTER_API_KEY not found in environment"
            )

        self.provider = provider
        # Default model is sourced from env, but can be overridden by parameter
        self.model = model or os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")
        self.logger = logging.getLogger("llm_client")

        # Initialize OpenAI client with OpenRouter base URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
        )

        # Load agent-specific models from environment variables (OpenRouter model ids)
        self.agent_models = {
            # Core agents
            "intake": os.getenv("INTAKE_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "researcher": os.getenv("RESEARCHER_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "blueprint": os.getenv("BLUEPRINT_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "prd": os.getenv("PRD_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "mockup": os.getenv("MOCKUP_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "data": os.getenv("DATA_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            # Note: Agent name normalization removes "agent" and lowercases without underscores.
            # For KnowledgeBaseAgent, normalized key is "knowledgebase". Support both keys.
            "knowledgebase": os.getenv("KNOWLEDGE_BASE_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "knowledge_base": os.getenv("KNOWLEDGE_BASE_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "reviewer": os.getenv("REVIEWER_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "storage": os.getenv("STORAGE_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "proposal": os.getenv("PROPOSAL_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "bom": os.getenv("BOM_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "architecture": os.getenv("ARCHITECTURE_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "casestudygallery": os.getenv("CASE_STUDY_GALLERY_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),

            # Legacy/misc keys retained for compatibility
            "requirements": os.getenv("REQUIREMENTS_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "synthetic_data": os.getenv("SYNTHETIC_DATA_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "commercial_proposal": os.getenv("COMMERCIAL_PROPOSAL_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "architecture_diagram": os.getenv("ARCHITECTURE_DIAGRAM_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
            "transcript": os.getenv("TRANSCRIPT_AGENT_MODEL", os.getenv("OPENROUTER_MODEL_DEFAULT", "x-ai/grok-4-fast")),
        }

    async def send_message_async(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> str:
        """
        Send a message to the LLM and get response via OpenRouter

        Args:
            user_message: The user's message
            system_message: System prompt
            session_id: Session ID for chat context (not used)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            LLM response text
        """
        try:
            # ENHANCED LOGGING: Track every API call with detailed context
            import traceback
            import inspect

            # Get caller information for debugging
            frame = inspect.currentframe()
            caller_frame = frame.f_back
            caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"

            self.logger.info(
                f"🔵 API CALL START | Model: {self.provider}/{self.model} | Caller: {caller_info}"
            )
            # Apply default token limit if not provided (can be overridden per call)
            effective_max_tokens = max_tokens or int(os.getenv("OPENROUTER_MAX_TOKENS", "16000"))
            self.logger.info(
                f"   Request: temp={temperature}, max_tokens={effective_max_tokens}, msg_length={len(user_message)}"
            )

            # Create messages for OpenRouter API
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]

            # Determine model to use (agent-specific or default)
            agent_name = getattr(self, "_current_agent", None)
            model_to_use = (
                self.agent_models.get(agent_name, self.model)
                if agent_name
                else self.model
            )

            self.logger.info(
                f"🔵 API CALL START | Model: {self.provider}/{model_to_use} | Agent: {agent_name or 'default'}"
            )

            # Call OpenRouter API with optional ranking headers
            response = await self.client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                temperature=temperature,
                max_tokens=effective_max_tokens,
                extra_headers={
                    "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", "http://localhost"),
                    "X-Title": os.getenv("OPENROUTER_X_TITLE", "AICOE Platform"),
                },
            )

            # Extract response text
            response_text = response.choices[0].message.content

            # Calculate token usage if available
            usage = getattr(response, "usage", None)
            if usage:
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(usage, "total_tokens", 0)
                self.logger.info(
                    f"🟢 API CALL SUCCESS | Response: {len(response_text)} chars | Tokens: {prompt_tokens}+{completion_tokens}={total_tokens}"
                )
            else:
                self.logger.info(
                    f"🟢 API CALL SUCCESS | Response: {len(response_text)} chars"
                )

            return response_text

        except Exception as e:
            self.logger.error(f"🔴 API CALL FAILED | Error: {str(e)}")
            raise Exception(f"LLM call failed: {str(e)}")

    def set_current_agent(self, agent_name: str):
        """
        Set the current agent name to use agent-specific model
        """
        self._current_agent = agent_name

    def send_message(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
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
                max_tokens=max_tokens,
            )
        )
