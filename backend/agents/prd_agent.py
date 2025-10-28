"""
PRD Agent - Assembles comprehensive Product Requirements Document
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class PRDAgent(BaseAgent):
    """
    Agent responsible for creating comprehensive PRD documents
    Combines all previous agent outputs into a structured PRD
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="PRDAgent",
            description="Creates comprehensive Product Requirements Documents",
            model="gpt-4o",
            temperature=0.4,
            max_tokens=6000
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate comprehensive PRD document
        
        Input:
            - structured_notes: From TranscriptAgent
            - use_cases: From RequirementsAgent
            - business_requirements: From RequirementsAgent
            - project_name: Name of the project
            
        Output:
            - prd_markdown: Complete PRD in Markdown format
            - prd_sections: Structured sections of the PRD
        """
        try:
            self.log_execution("start", "Generating PRD document")
            self.validate_input(input_data, ["project_name"])
            
            project_name = input_data["project_name"]
            structured_notes = input_data.get("structured_notes", {})
            use_cases = input_data.get("use_cases", [])
            business_reqs = input_data.get("business_requirements", {})
            
            # Prepare context for PRD generation
            context_text = f"""
Project Name: {project_name}

Structured Meeting Notes:
{json.dumps(structured_notes, indent=2)}

Use Cases:
{json.dumps(use_cases, indent=2)}

Business Requirements:
{json.dumps(business_reqs, indent=2)}
"""
            
            system_message = """You are an expert Product Manager who creates world-class Product Requirements Documents (PRDs).
Your PRDs are comprehensive, well-structured, and follow industry best practices."""
            
            user_message = f"""Create a comprehensive Product Requirements Document (PRD) based on the following information:

{context_text}

The PRD should include these sections in Markdown format:

# {project_name} - Product Requirements Document

## 1. Executive Summary
Brief overview of the project, its purpose, and expected impact.

## 2. Goals & Objectives
Clear, measurable objectives this product aims to achieve.

## 3. Problem Statement
What problem are we solving? Who has this problem?

## 4. User Personas & Stakeholders
Who will use this product? Key stakeholders involved.

## 5. Features & User Stories
Detailed features and user stories based on the use cases provided.

## 6. Use Cases
Detailed use cases with scenarios, actors, and flows.

## 7. Functional Requirements
Specific, testable functional requirements organized by feature area.

## 8. Non-Functional Requirements
Performance, scalability, security, usability requirements.

## 9. Technical Architecture
High-level technical approach, system components, integrations.

## 10. Acceptance Criteria
How will we know when each feature is complete and working?

## 11. Success Metrics
Key metrics to measure product success.

## 12. Timeline & Milestones
Suggested phases or milestones for development.

## 13. Risks & Mitigation
Potential risks and how to address them.

## 14. Dependencies & Assumptions
What we're depending on and assuming.

## 15. Open Questions
Any unresolved questions or areas needing clarification.

Create a professional, detailed PRD in Markdown format. Make it comprehensive and actionable."""

            self.log_execution("llm_call", "Generating PRD document")
            response = await self._call_llm(
                system_message,
                user_message,
                max_tokens=6000
            )
            
            # Clean markdown if wrapped in code blocks
            prd_content = response.strip()
            if prd_content.startswith("```markdown"):
                prd_content = prd_content.split("```markdown")[1].split("```")[0].strip()
            elif prd_content.startswith("```"):
                prd_content = prd_content.split("```")[1].split("```")[0].strip()
            
            self.log_execution("success", f"Generated PRD ({len(prd_content)} characters)")
            
            return AgentResult(
                success=True,
                data={
                    "prd_markdown": prd_content,
                    "project_name": project_name,
                    "length": len(prd_content),
                    "sections": self._extract_sections(prd_content)
                },
                metadata={
                    "agent": self.config.name,
                    "format": "markdown"
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in PRDAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
    
    def _extract_sections(self, markdown_text: str) -> list:
        """Extract section headings from markdown"""
        sections = []
        for line in markdown_text.split('\n'):
            if line.startswith('## '):
                sections.append(line.replace('## ', '').strip())
        return sections
