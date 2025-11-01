"""
Synthetic Data Agent - Generates realistic demo data for mockups
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class DataAgent(BaseAgent):
    """
    Agent responsible for generating realistic synthetic data for demos and mockups
    Creates CSV/JSON data based on use case specifications
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="DataAgent",
            description="Generates realistic demo data sets for mockups and visualizations",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.7,
            max_tokens=12000  # Increased from 4000 to handle complex data sets
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate synthetic data based on use cases and requirements
        
        Input:
            - use_cases: List of use cases from RequirementsAgent
            - requirements: Business requirements
            - project_name: Name of the project
            
        Output:
            - synthetic_data: Dict with generated data sets
        """
        try:
            self.log_execution("start", "Generating synthetic data")
            self.validate_input(input_data, ["use_cases", "project_name"])
            
            use_cases = input_data["use_cases"]
            project_name = input_data["project_name"]
            requirements = input_data.get("requirements", {})
            
            # Communicate with other agents
            self.log_execution("communication", "Requesting additional context from RequirementsAgent")
            
            # Create prompt for generating synthetic data
            system_message = """You are an expert at generating realistic synthetic data for software demos and mockups.
Your task is to create sample data that is:
1. Realistic and representative of real-world scenarios
2. Diverse and comprehensive
3. Properly formatted (JSON/CSV)
4. Aligned with the use cases and requirements"""
            
            user_message = f"""Generate realistic synthetic data for the following project:

Project Name: {project_name}

Use Cases:
{json.dumps(use_cases, indent=2)}

Requirements:
{json.dumps(requirements, indent=2)}

Please generate synthetic data sets that would be useful for demonstrating these use cases.
For each use case, create appropriate sample data.

Return the data in JSON format with the following structure:
{{
    "data_sets": [
        {{
            "name": "Dataset name",
            "description": "What this data represents",
            "use_case_id": "UC-XXX",
            "format": "json" or "csv",
            "schema": {{...}},
            "sample_data": [...]
        }}
    ],
    "summary": "Brief summary of generated data"
}}

Return ONLY valid JSON without markdown formatting."""

            self.log_execution("llm_call", "Generating synthetic data sets")
            response = await self._call_llm(system_message, user_message)
            
            # Parse JSON response
            try:
                response = response.strip()
                if response.startswith("```json"):
                    response = response.split("```json")[1].split("```")[0].strip()
                elif response.startswith("```"):
                    response = response.split("```")[1].split("```")[0].strip()
                
                synthetic_data = json.loads(response)
                
                num_datasets = len(synthetic_data.get("data_sets", []))
                self.log_execution("success", f"Generated {num_datasets} data sets")
                
                # Share data with other agents
                self.log_execution("communication", "Sharing synthetic data with MockupAgent")
                
                return AgentResult(
                    success=True,
                    data={
                        "synthetic_data": synthetic_data,
                        "project_name": project_name,
                        "num_datasets": num_datasets
                    },
                    metadata={
                        "agent": self.config.name,
                        "datasets_generated": num_datasets
                    }
                )
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {str(e)}")
                
                return AgentResult(
                    success=True,
                    data={
                        "synthetic_data": {"raw_response": response},
                        "project_name": project_name,
                        "warning": "Could not parse as JSON"
                    },
                    metadata={"agent": self.config.name}
                )
                
        except Exception as e:
            self.logger.error(f"Error in SyntheticDataAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )

