"""
Requirements Agent - Generates use cases and business requirements
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class RequirementsAgent(BaseAgent):
    """
    Agent responsible for generating use cases and detailed business requirements
    from structured notes
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="RequirementsAgent",
            description="Generates use cases and business requirements",
            model="gpt-4o",
            temperature=0.5,
            max_tokens=4000
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate use cases and requirements from structured notes
        
        Input:
            - structured_notes: Structured meeting notes
            - project_name: Name of the project
            
        Output:
            - use_cases: List of detailed use cases
            - business_requirements: Detailed business requirements
        """
        try:
            self.log_execution("start", "Generating requirements and use cases")
            self.validate_input(input_data, ["structured_notes", "project_name"])
            
            notes = input_data["structured_notes"]
            project_name = input_data["project_name"]
            
            # Serialize notes for prompt
            notes_text = json.dumps(notes, indent=2) if isinstance(notes, dict) else str(notes)
            
            system_message = """You are an expert Business Analyst and Requirements Engineer.
Your task is to analyze structured meeting notes and create comprehensive use cases and business requirements following enterprise standards."""
            
            user_message = f"""Based on the following structured meeting notes, create detailed use cases and business requirements.

Project Name: {project_name}

Structured Notes:
{notes_text}

Please generate the following in JSON format:

1. **use_cases**: An array of use case objects, each containing:
   - id: Unique identifier (UC-001, UC-002, etc.)
   - title: Use case title
   - description: Detailed description
   - actors: Who interacts with this feature
   - preconditions: What must be true before this use case
   - main_flow: Step-by-step main scenario (array of steps)
   - alternate_flows: Alternative scenarios (if applicable)
   - postconditions: Expected state after completion
   - priority: high, medium, or low
   - business_value: Why this use case matters

2. **business_requirements**: An object containing:
   - overview: High-level project overview
   - business_goals: List of business objectives
   - success_criteria: Measurable success metrics
   - constraints: Business or technical constraints
   - assumptions: Key assumptions being made
   - risks: Potential risks and mitigation strategies

Generate at least 4-6 comprehensive use cases based on the discussion points and requirements.

Return ONLY valid JSON without any markdown formatting."""

            self.log_execution("llm_call", "Generating use cases and requirements")
            response = await self._call_llm(system_message, user_message)
            
            # Parse JSON response
            try:
                response = response.strip()
                if response.startswith("```json"):
                    response = response.split("```json")[1].split("```")[0].strip()
                elif response.startswith("```"):
                    response = response.split("```")[1].split("```")[0].strip()
                
                requirements_data = json.loads(response)
                
                use_cases = requirements_data.get("use_cases", [])
                business_requirements = requirements_data.get("business_requirements", {})
                
                self.log_execution("success", f"Generated {len(use_cases)} use cases")
                
                return AgentResult(
                    success=True,
                    data={
                        "use_cases": use_cases,
                        "business_requirements": business_requirements,
                        "project_name": project_name
                    },
                    metadata={
                        "agent": self.config.name,
                        "use_case_count": len(use_cases)
                    }
                )
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {str(e)}")
                return AgentResult(
                    success=False,
                    data=None,
                    error=f"JSON parsing failed: {str(e)}",
                    metadata={"agent": self.config.name}
                )
                
        except Exception as e:
            self.logger.error(f"Error in RequirementsAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
