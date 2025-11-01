"""
System Architecture Diagram Agent - Generates visual system architecture diagrams
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
import json


class ArchitectureAgent(BaseAgent):
    """
    Agent responsible for creating interactive system architecture diagrams
    Generates HTML with embedded Mermaid diagrams showing component relationships
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="ArchitectureAgent",
            description="Creates interactive system architecture diagrams",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.3,
            max_tokens=12000
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate system architecture diagram as HTML

        This is a TWO-STAGE process:
        Stage 1: Generate structured XML with Mermaid diagram (for data storage and IP)
        Stage 2: Transform XML to beautiful HTML with interactive Mermaid rendering using LLM

        Input:
            - project_name: Name of the project
            - enrichment: Technical architecture from knowledge base
            - use_cases: Use cases for understanding system flows
            - research_insights: Technical patterns and best practices

        Output:
            - architecture_xml: Structured XML with Mermaid diagram
            - architecture_html: Interactive HTML with rendered Mermaid diagrams
        """
        try:
            self.log_execution("start", "Generating architecture diagram")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            enrichment = input_data.get("enrichment", {})
            use_cases = input_data.get("use_cases", [])
            research_insights = input_data.get("research_insights", {})

            # Prepare context
            research_text = json.dumps(research_insights, indent=2) if research_insights else "No research insights available"

            context_text = f"""
Project Name: {project_name}

Technical Architecture:
{json.dumps(enrichment, indent=2)}

Use Cases:
{json.dumps(use_cases[:3], indent=2) if use_cases else "No use cases"}

Research Insights (for architecture patterns):
{research_text[:1500]}
"""

            # STAGE 1: Generate XML with Mermaid diagram for data storage
            xml_system_message = """## ROLE AND GOAL
You are a Senior Cloud Architect and System Designer. Your goal is to create a comprehensive, production-ready system architecture design based on the project requirements and suggested design patterns. Your output must be a structured XML document containing a detailed MermaidJS diagram.

## STEP-BY-STEP PROCESS
1. Review the technical context, use cases, and research findings.
2. Design a comprehensive architecture that includes:
   - Frontend layer (web, mobile, desktop as applicable)
   - API Gateway / Load Balancer
   - Backend services (microservices or monolith)
   - Data layer (databases, caches, message queues)
   - External integrations (third-party APIs, services)
   - Security layer (authentication, authorization)
   - Infrastructure components (CDN, storage, monitoring)
3. Represent this architecture as a detailed MermaidJS flowchart diagram showing:
   - All major components and their relationships
   - Data flow directions
   - Component groupings (using subgraphs if needed)
   - Different node types (databases, services, external systems)
4. Provide a comprehensive breakdown of each major component with technical details.
5. Format the entire design into the strict XML schema below.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, valid XML document. Your entire response MUST be only this XML.

<systemArchitecture>
    <description>A comprehensive overview of the proposed architecture, referencing open-source components, design patterns, and architectural decisions.</description>
    <diagram type="mermaid-flowchart">
        <![CDATA[
            graph TD
                %% Frontend Layer
                A[React Native Mobile App] -->|HTTPS/REST| B[API Gateway - Kong/Nginx]
                A2[React Web App] -->|HTTPS/REST| B

                %% API Gateway & Auth
                B --> C[Auth Service - OAuth 2.0]
                C --> D[Identity Provider]

                %% Backend Services
                B --> E[User Service]
                B --> F[Core Business Logic Service]
                B --> G[Analytics Service]

                %% Data Layer
                E --> H[(PostgreSQL - User Data)]
                F --> I[(MongoDB - Application Data)]
                G --> J[(Redis Cache)]

                %% Message Queue
                F --> K[Message Queue - RabbitMQ/Kafka]
                K --> L[Background Workers]

                %% External Services
                B --> M[Third-Party APIs]
                F --> N[Cloud Storage - S3]
        ]]>
    </diagram>
    <componentBreakdown>
        <component name="React Native Mobile App">Cross-platform mobile application built with React Native, providing native iOS and Android experiences.</component>
        <component name="React Web App">Responsive web application built with React, TypeScript, and modern UI libraries.</component>
        <component name="API Gateway">Kong or Nginx-based API gateway handling routing, rate limiting, authentication, and load balancing.</component>
        <component name="Auth Service">OAuth 2.0 / OpenID Connect authentication service with JWT token management.</component>
        <component name="User Service">Microservice handling user management, profiles, and preferences.</component>
        <component name="Core Business Logic Service">Main application service implementing business rules and workflows.</component>
        <component name="PostgreSQL">Relational database for structured user and transactional data.</component>
        <component name="MongoDB">NoSQL database for flexible, document-based application data.</component>
        <component name="Redis Cache">In-memory cache for session management and performance optimization.</component>
        <component name="Message Queue">Asynchronous message processing using RabbitMQ or Kafka for event-driven architecture.</component>
    </componentBreakdown>
</systemArchitecture>

## GUIDELINES & CONSTRAINTS
- The architecture MUST be based on open-source technologies unless the client's existing stack dictates otherwise.
- The Mermaid diagram MUST be syntactically correct and comprehensive.
- Include ALL relevant components: frontend, backend, databases, caches, queues, external services, security layers.
- Show clear data flow and relationships between components.
- Use appropriate Mermaid node types: [] for services, [()] for databases, {} for decision points.
- Add comments in the Mermaid diagram to organize sections (e.g., %% Frontend Layer).
- Your entire response MUST be only the XML document."""

            self.log_execution("progress", "Generating architecture XML")

            xml_response = await self._call_llm(xml_system_message, f"""Generate a system architecture XML document for project: {project_name}

Input Data:
{context_text}""")

            architecture_xml = xml_response.strip()

            # Clean XML response
            if architecture_xml.startswith("```xml"):
                architecture_xml = architecture_xml.split("```xml")[1].split("```")[0].strip()
            elif architecture_xml.startswith("```"):
                architecture_xml = architecture_xml.split("```")[1].split("```")[0].strip()

            self.log_execution("success", f"Generated architecture XML ({len(architecture_xml)} chars)")

            # STAGE 2: Transform XML to HTML with interactive Mermaid rendering
            design_system = get_design_system_prompt()
            
            html_system_message = f"""## ROLE AND GOAL
You are an expert Technical Documentation Designer. Your goal is to transform a system architecture XML (containing Mermaid diagrams) into a professional, interactive HTML document with AICOE branding.


{design_system}

## CONTEXT
You will be given an XML string containing a `<systemArchitecture>` with embedded Mermaid diagram code.

## STEP-BY-STEP PROCESS
1. Parse the input XML to extract the architecture description, Mermaid diagram, and component breakdown.
2. Generate a clean HTML structure with:
   - Architecture overview section
   - Interactive Mermaid diagram (using Mermaid.js CDN)
   - Component breakdown with detailed descriptions
   - Professional styling
3. Apply the AICOE branding guidelines with absolute precision.
4. Return the final, single HTML file as a string.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, complete HTML string as your response. DO NOT include any other text, explanation, or formatting like markdown code fences. Your response should start with `<!DOCTYPE html>` and end with `</html>`.

## GUIDELINES & STYLING (NON-NEGOTIABLE)
- **Styling:** All CSS MUST be contained within a `<style>` tag in the `<head>` of the HTML document.
- **Mermaid Setup:**
  * Include Mermaid.js via CDN: `<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>`
  * Initialize Mermaid with custom theme in a `<script>` tag at the end of `<body>`:
    ```javascript
    mermaid.initialize({{
        startOnLoad: true,
        theme: 'base',
        themeVariables: {{
            primaryColor: '#1a1a2e',
            primaryTextColor: '#ffffff',
            primaryBorderColor: '#00ffcc',
            lineColor: '#00ffcc',
            secondaryColor: '#2a2a3e',
            tertiaryColor: '#3a2a4e',
            fontFamily: '-apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif'
        }}
    }});
    ```
  * Place Mermaid diagram code inside a `<div class="mermaid">` element
  * Ensure the diagram container has proper styling (white background, padding, border-radius)
- **Branding:** Use the AICOE color palette (Primary Navy: #1a1a2e, Accent Cyan: #00ffcc, Accent Pink: #ff69b4, etc.)
- **Logo:** Include the AICOE logo in the footer with gradient text effect.
- **Layout:** Clean, minimalist design following Apple's principles with generous whitespace.
- **Typography:** Use -apple-system, BlinkMacSystemFont, 'SF Pro Display' font stack.
- **Interactive:** Mermaid diagram should be interactive, zoomable, and clearly visible.
- **Icons:** Use Lucide icon library via CDN for component cards.
- **Responsive:** Must work on desktop, tablet, and mobile.
- **Print-friendly:** Include print styles.
- **Diagram Visibility:** Ensure the Mermaid diagram is large, clear, and properly styled with AICOE colors."""

            self.log_execution("progress", "Transforming XML to HTML")

            html_response = await self._call_llm(
                html_system_message,
                f"""Transform this system architecture XML into a beautiful, professional HTML document with interactive Mermaid diagram:

{architecture_xml}""",
                max_tokens=12000
            )

            # Clean HTML response
            architecture_html = html_response.strip()
            if architecture_html.startswith("```html"):
                architecture_html = architecture_html.split("```html")[1].split("```")[0].strip()
            elif architecture_html.startswith("```"):
                architecture_html = architecture_html.split("```")[1].split("```")[0].strip()

            # Validate HTML starts correctly
            if not architecture_html.startswith("<!DOCTYPE"):
                self.logger.warning("Generated HTML doesn't start with DOCTYPE, prepending it")
                architecture_html = "<!DOCTYPE html>\n" + architecture_html

            self.log_execution("success", f"Generated architecture HTML ({len(architecture_html)} characters)")

            return AgentResult(
                success=True,
                data={
                    "architecture_xml": architecture_xml,
                    "architecture_html": architecture_html,
                    "project_name": project_name
                },
                metadata={
                    "agent": self.config.name,
                    "format": "xml+html"
                }
            )

        except Exception as e:
            self.logger.error(f"Error in ArchitectureAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
