"""
Knowledge Base Agent - Enriches documents with domain knowledge and best practices
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class KnowledgeBaseAgent(BaseAgent):
    """
    Agent responsible for enriching document generation with domain knowledge,
    AI design patterns, compliance rules, and best practices
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="KnowledgeBaseAgent",
            description="Enriches documents with domain knowledge and best practices",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.4,
            max_tokens=12000
        )
        super().__init__(config, llm_client)
        
        # Built-in knowledge base (in production, this would be ChromaDB/vector store)
        self.knowledge_base = {
            "ai_design_patterns": [
                "Multi-agent orchestration with Google ADK",
                "Prompt engineering best practices",
                "LLM chain-of-thought reasoning",
                "RAG (Retrieval Augmented Generation)",
                "Agent communication protocols"
            ],
            "compliance_rules": [
                "Data privacy and GDPR compliance",
                "Secure API key management",
                "Audit trail requirements",
                "Role-based access control (RBAC)",
                "Data encryption at rest and in transit"
            ],
            "best_practices": [
                "Apple-style UI/UX design principles",
                "Responsive design patterns",
                "Accessibility (WCAG) guidelines",
                "Performance optimization",
                "Error handling and recovery"
            ],
            "integration_patterns": [
                "Google Drive API integration",
                "OAuth 2.0 authentication",
                "RESTful API design",
                "WebSocket for real-time updates",
                "Microservices architecture"
            ]
        }
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Enrich documents with relevant knowledge and suggestions
        
        Input:
            - document_type: Type of document (prd, mockup, requirements, etc.)
            - content: Current document content
            - project_name: Name of the project
            
        Output:
            - enrichment_suggestions: List of suggestions and enhancements
            - relevant_patterns: Relevant design patterns and best practices
        """
        try:
            self.log_execution("start", "Enriching document with knowledge base")
            self.validate_input(input_data, ["document_type", "content", "project_name"])
            
            document_type = input_data["document_type"]
            content = input_data["content"]
            project_name = input_data["project_name"]
            research_insights = input_data.get("research_insights", {})

            # Communicate with other agents
            self.log_execution("communication", "Analyzing content from previous agents")

            # Create prompt for knowledge enrichment
            system_message = """You are an expert knowledge base system with deep understanding of:
- AI/ML design patterns and best practices
- Software architecture and integration patterns
- Compliance and security requirements
- UI/UX design principles
- Enterprise software development
- Industry trends and competitive landscapes

Your task is to analyze documents and provide relevant suggestions, patterns, and best practices.
You MUST validate technical standards against research findings and incorporate regulatory requirements."""

            research_text = json.dumps(research_insights, indent=2) if research_insights else "No research insights available"

            user_message = f"""Analyze the following {document_type} document and provide enrichment suggestions:

Project Name: {project_name}

Document Content:
{json.dumps(content, indent=2)[:2000]}  # Limit content size

Research Insights (IMPORTANT - Use this to validate and enrich):
{research_text[:1500]}  # Limit research size

Available Knowledge Base Categories:
- AI Design Patterns
- Compliance Rules
- Best Practices
- Integration Patterns

INSTRUCTIONS:
1. Validate technical standards against research findings
2. Incorporate regulatory requirements from research
3. Reference industry best practices from research insights
4. Ensure compliance with technical standards mentioned in research
5. Identify gaps between current requirements and industry standards

Please provide:
1. Relevant patterns and best practices that apply to this project
2. Suggestions for improvement or enhancement (based on research insights)
3. Potential risks or compliance considerations (including regulatory requirements from research)
4. Integration recommendations (aligned with technical standards from research)

Return in JSON format:
{{
    "relevant_patterns": [
        {{
            "category": "category name",
            "pattern": "pattern name",
            "description": "how it applies",
            "priority": "high/medium/low"
        }}
    ],
    "suggestions": [
        {{
            "area": "area of improvement",
            "suggestion": "specific suggestion",
            "rationale": "why this is important"
        }}
    ],
    "compliance_notes": ["note1", "note2"],
    "integration_recommendations": ["rec1", "rec2"]
}}

Return ONLY valid JSON without markdown formatting."""

            self.log_execution("llm_call", "Generating knowledge enrichment")
            response = await self._call_llm(system_message, user_message)
            
            # Parse JSON response
            try:
                response = response.strip()
                if response.startswith("```json"):
                    response = response.split("```json")[1].split("```")[0].strip()
                elif response.startswith("```"):
                    response = response.split("```")[1].split("```")[0].strip()
                
                enrichment = json.loads(response)
                
                num_patterns = len(enrichment.get("relevant_patterns", []))
                num_suggestions = len(enrichment.get("suggestions", []))
                
                self.log_execution(
                    "success",
                    f"Generated {num_patterns} patterns and {num_suggestions} suggestions"
                )
                
                # Share enrichment with other agents
                self.log_execution("communication", "Sharing enrichment data with all agents")
                
                return AgentResult(
                    success=True,
                    data={
                        "enrichment": enrichment,
                        "project_name": project_name,
                        "document_type": document_type,
                        "knowledge_base_categories": list(self.knowledge_base.keys())
                    },
                    metadata={
                        "agent": self.config.name,
                        "patterns_found": num_patterns,
                        "suggestions_made": num_suggestions
                    }
                )
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {str(e)}")
                
                return AgentResult(
                    success=True,
                    data={
                        "enrichment": {"raw_response": response},
                        "project_name": project_name,
                        "warning": "Could not parse as JSON"
                    },
                    metadata={"agent": self.config.name}
                )
                
        except Exception as e:
            self.logger.error(f"Error in KnowledgeBaseAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
    
    def search_knowledge_base(self, query: str, category: str = None) -> List[str]:
        """
        Search the knowledge base for relevant information
        
        Args:
            query: Search query
            category: Optional category to search in
            
        Returns:
            List of relevant knowledge items
        """
        results = []
        
        if category and category in self.knowledge_base:
            results = [
                item for item in self.knowledge_base[category]
                if query.lower() in item.lower()
            ]
        else:
            for cat_items in self.knowledge_base.values():
                results.extend([
                    item for item in cat_items
                    if query.lower() in item.lower()
                ])
        
        return results

