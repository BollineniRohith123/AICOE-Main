"""
PRD Agent - Assembles comprehensive Product Requirements Document
Generates HTML directly from XML using LLM transformation
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
import json


class PRDAgent(BaseAgent):
    """
    Agent responsible for creating comprehensive PRD documents
    Takes XML input and generates beautiful HTML output using LLM
    """

    def __init__(self, llm_client):
        config = AgentConfig(
            name="PRDAgent",
            description="Creates comprehensive Product Requirements Documents",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.4,
            max_tokens=12000  # Increased to handle complex HTML generation
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate comprehensive PRD document as HTML

        This is a TWO-STAGE process:
        Stage 1: Generate structured XML (for data storage and IP)
        Stage 2: Transform XML to beautiful HTML using LLM

        Input:
            - structured_notes: From TranscriptAgent
            - use_cases: From RequirementsAgent
            - business_requirements: From RequirementsAgent
            - project_name: Name of the project

        Output:
            - prd_xml: Structured XML document
            - prd_html: Beautiful HTML document
        """
        try:
            self.log_execution("start", "Generating PRD document")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            structured_notes = input_data.get("structured_notes", {})
            use_cases = input_data.get("use_cases", [])
            business_reqs = input_data.get("business_requirements", {})
            research_insights = input_data.get("research_insights", {})

            # Prepare context for PRD generation
            research_text = json.dumps(research_insights, indent=2) if research_insights else "No research insights available"

            context_text = f"""
Project Name: {project_name}

Structured Meeting Notes:
{json.dumps(structured_notes, indent=2)}

Use Cases:
{json.dumps(use_cases, indent=2)}

Business Requirements:
{json.dumps(business_reqs, indent=2)}

Research Insights (CRITICAL - Use this extensively):
{research_text}
"""

            # STAGE 1: Generate XML for data storage
            xml_system_message = """## ROLE AND GOAL
You are an expert Technical Writer who creates comprehensive Product Requirements Documents (PRDs). Your goal is to assemble the vision, requirements, and use cases into a single, formal XML document.

## CONTEXT
You will receive structured data from previous agents.

## STEP-BY-STEP PROCESS
1. Extract the project vision, business requirements, and stakeholders from the input.
2. Extract the full use case model from the input.
3. Synthesize this information to define what is in scope and out of scope for the project.
4. Formulate key business goals based on the requirements.
5. Define at least two critical non-functional requirements (e.g., Security, Performance).
6. Assemble all sections into the strict XML format defined below.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, valid XML document. Your entire response MUST be only this XML.

<productRequirementsDocument>
    <title>PRD for [Project Name]</title>
    <executiveSummary>A one-paragraph summary of the project's purpose and scope.</executiveSummary>
    <scope>
        <inScope>A bulleted list of features that are in scope for the MVP.</inScope>
        <outOfScope>A bulleted list of features that are explicitly out of scope.</outOfScope>
    </scope>
    <businessGoals>
        <goal>Increase marketing efficiency by 50%.</goal>
        <goal>Reduce compliance violations by 90%.</goal>
    </businessGoals>
    <useCases>
        <useCaseModel>
            <useCase>
                <title>Use Case Title</title>
                <primaryActor>Primary Actor</primaryActor>
                <secondaryActors>
                    <actor>Secondary Actor 1</actor>
                </secondaryActors>
                <description>Use case description</description>
                <mainFlow>
                    <step>Step 1</step>
                    <step>Step 2</step>
                </mainFlow>
                <alternativeFlows>
                    <flow id="A1" trigger="Alternative condition">
                        <step>Alternative step 1</step>
                    </flow>
                </alternativeFlows>
                <exceptionFlows>
                    <flow id="E1" trigger="Exception condition">
                        <step>Exception step 1</step>
                    </flow>
                </exceptionFlows>
            </useCase>
        </useCaseModel>
    </useCases>
    <nonFunctionalRequirements>
        <requirement type="Security">All sensitive data must be encrypted at rest and in transit using industry-standard protocols.</requirement>
        <requirement type="Performance">The system must respond to 95% of user queries in under 2 seconds.</requirement>
    </nonFunctionalRequirements>
</productRequirementsDocument>

## GUIDELINES & CONSTRAINTS
- The PRD must be professional, well-structured, and comprehensive.
- NEVER output anything other than the specified XML structure."""

            self.log_execution("llm_call", "Generating PRD XML")

            xml_response = await self._call_llm(
                xml_system_message,
                f"""Generate a PRD XML document for project: {project_name}

Input Data:
{context_text}""",
                max_tokens=8000
            )

            # Clean XML response
            prd_xml = xml_response.strip()
            if prd_xml.startswith("```xml"):
                prd_xml = prd_xml.split("```xml")[1].split("```")[0].strip()
            elif prd_xml.startswith("```"):
                prd_xml = prd_xml.split("```")[1].split("```")[0].strip()

            self.log_execution("success", f"Generated PRD XML ({len(prd_xml)} characters)")

            # STAGE 2: Transform XML to HTML using LLM
            design_system = get_design_system_prompt()

            html_system_message = f"""## ROLE AND GOAL
You are an expert Technical Writer and Information Designer. Your goal is to transform a raw PRD in XML format into a professional, client-ready, and interactive HTML document.

{design_system}

## CONTEXT
You will be given a single input: an XML string containing a `<productRequirementsDocument>`.

## STEP-BY-STEP PROCESS
1. Parse the input XML to identify all sections (Executive Summary, Scope, Use Cases, etc.).
2. Generate a clean HTML structure that represents this document.
3. Create an interactive, smooth-scrolling Table of Contents at the top of the document that links to each major section.
4. Style the entire document with absolute precision according to the AICOE design system above.
5. Return the final, single HTML file as a string.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, complete HTML string as your response. DO NOT include any other text, explanation, or formatting like markdown code fences. Your response should start with `<!DOCTYPE html>` and end with `</html>`.

## ADDITIONAL REQUIREMENTS
- Use CSS variables from the design system
- Include Lucide icons for visual enhancement
- Add smooth transitions and micro-interactions
- Ensure responsive design for all devices
- Include AICOE logo in footer with gradient effect
- Make the document visually stunning and professional
- **Interactivity:** The Table of Contents links MUST be functional and scroll smoothly to the corresponding sections.
- **Responsive:** The design must work perfectly on desktop, tablet, and mobile.
- **Print-friendly:** Include print styles for professional PDF generation."""

            self.log_execution("llm_call", "Transforming XML to HTML")

            html_response = await self._call_llm(
                html_system_message,
                f"""Transform this PRD XML into a beautiful, professional HTML document:

{prd_xml}""",
                max_tokens=12000
            )

            # Clean HTML response
            prd_html = html_response.strip()
            if prd_html.startswith("```html"):
                prd_html = prd_html.split("```html")[1].split("```")[0].strip()
            elif prd_html.startswith("```"):
                prd_html = prd_html.split("```")[1].split("```")[0].strip()

            # Validate HTML starts correctly
            if not prd_html.startswith("<!DOCTYPE"):
                self.logger.warning("Generated HTML doesn't start with DOCTYPE, prepending it")
                prd_html = "<!DOCTYPE html>\n" + prd_html

            self.log_execution("success", f"Generated PRD HTML ({len(prd_html)} characters)")

            return AgentResult(
                success=True,
                data={
                    "prd_xml": prd_xml,
                    "prd_html": prd_html,
                    "project_name": project_name
                },
                metadata={
                    "agent": self.config.name,
                    "format": "xml+html"
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
