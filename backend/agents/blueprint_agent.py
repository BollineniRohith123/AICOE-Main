"""
Requirements Agent - Generates use cases and business requirements
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class BlueprintAgent(BaseAgent):
    """
    Agent responsible for generating use cases and detailed business requirements
    from structured notes
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="BlueprintAgent",
            description="Generates use cases and business requirements",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.5,
            max_tokens=12000
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
            research_insights = input_data.get("research_insights", {})

            # Serialize notes for prompt
            notes_text = json.dumps(notes, indent=2) if isinstance(notes, dict) else str(notes)
            research_text = json.dumps(research_insights, indent=2) if research_insights else "No research insights available"

            system_message = """You are an expert Business Analyst and Requirements Engineer with deep knowledge of industry trends and competitive landscapes.
Your task is to analyze structured meeting notes and research insights to create comprehensive use cases and business requirements following enterprise standards.
You MUST incorporate industry trends, competitor insights, and best practices from the research data into your requirements."""

            user_message = f"""Based on the following structured meeting notes and research insights, create detailed use cases and business requirements.

Project Name: {project_name}

Structured Notes:
{notes_text}

Research Insights (IMPORTANT - Use this to enrich your requirements):
{research_text}

INSTRUCTIONS:
1. Analyze the industry trends and incorporate relevant trends into your use cases
2. Reference competitor insights to identify must-have features and differentiators
3. Apply best practices from the research to ensure high-quality requirements
4. Align technical requirements with industry technical standards
5. Consider user expectations from the research when defining use case flows
6. Include regulatory requirements where applicable

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
            # Use higher max_tokens for complex JSON generation
            response = await self._call_llm(system_message, user_message, max_tokens=12000)

            # Parse JSON response with retry logic
            requirements_data = None
            max_retries = 2

            for attempt in range(max_retries):
                try:
                    response = response.strip()
                    if response.startswith("```json"):
                        response = response.split("```json")[1].split("```")[0].strip()
                    elif response.startswith("```"):
                        response = response.split("```")[1].split("```")[0].strip()

                    requirements_data = json.loads(response)
                    break  # Success!

                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response (attempt {attempt + 1}/{max_retries}): {str(e)}")

                    if attempt < max_retries - 1:
                        # Try to fix the JSON by asking the LLM
                        self.log_execution("llm_call", "Retrying with JSON repair request")
                        repair_prompt = f"""The previous response had a JSON parsing error: {str(e)}

Please fix the following JSON and return ONLY valid, complete JSON without any markdown formatting:

{response}

Make sure all strings are properly terminated and all brackets are closed."""

                        response = await self._call_llm(
                            "You are a JSON repair expert. Fix malformed JSON and return only valid JSON.",
                            repair_prompt,
                            max_tokens=12000
                        )
                    else:
                        # Final attempt failed
                        return AgentResult(
                            success=False,
                            data=None,
                            error=f"JSON parsing failed after {max_retries} attempts: {str(e)}",
                            metadata={"agent": self.config.name}
                        )

            if requirements_data:
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
                
        except Exception as e:
            self.logger.error(f"Error in RequirementsAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
