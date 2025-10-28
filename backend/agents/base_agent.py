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
        model: str = "gpt-4o",
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
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call the LLM with given messages
        
        Args:
            system_message: System prompt
            user_message: User message/prompt
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            LLM response text
        """
        temp = temperature if temperature is not None else self.config.temperature
        tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        try:
            response = await self.llm_client.send_message_async(
                user_message=user_message,
                system_message=system_message,
                temperature=temp,
                max_tokens=tokens
            )
            return response
        except Exception as e:
            self.logger.error(f"LLM call failed: {str(e)}")
            raise
    
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
