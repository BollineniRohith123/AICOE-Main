"""
Commercial Proposal Agent - Generates professional commercial proposals
Generates HTML directly from XML using LLM transformation
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
import json


class ProposalAgent(BaseAgent):
    """
    Agent responsible for creating professional commercial proposals
    Takes structured data and generates beautiful HTML output using LLM
    """

    def __init__(self, llm_client):
        config = AgentConfig(
            name="ProposalAgent",
            description="Creates professional commercial proposals with pricing and timelines",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.3,  # Lower temperature for professional business documents
            max_tokens=12000
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate commercial proposal document as HTML

        This is a TWO-STAGE process:
        Stage 1: Generate structured XML (for data storage and IP)
        Stage 2: Transform XML to beautiful HTML using LLM

        Input:
            - project_name: Name of the project
            - prd_markdown: PRD content for context
            - use_cases: Use cases from requirements
            - research_insights: Market research for pricing context

        Output:
            - proposal_xml: Structured XML document
            - proposal_html: Beautiful HTML document
        """
        try:
            self.log_execution("start", "Generating commercial proposal")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            prd_content = input_data.get("prd_markdown", "")
            use_cases = input_data.get("use_cases", [])
            research_insights = input_data.get("research_insights", {})

            # Prepare context
            research_text = json.dumps(research_insights, indent=2) if research_insights else "No research insights available"

            context_text = f"""
Project Name: {project_name}

PRD Summary:
{prd_content[:2000] if prd_content else "No PRD available"}

Use Cases:
{json.dumps(use_cases, indent=2)}

Research Insights (for pricing and market context):
{research_text[:1500]}
"""

            # STAGE 1: Generate XML for data storage
            xml_system_message = """## ROLE AND GOAL
You are a Senior Project Manager responsible for drafting commercial proposals. Your goal is to create a professional proposal document based on the project scope and estimated costs. Your output must be a structured XML document.

## STEP-BY-STEP PROCESS
1. Use the PRD to formulate a clear "Scope of Work" section.
2. Create a high-level project timeline with distinct phases (e.g., Design, Development, Testing).
3. Incorporate the team's daily rate to create a services pricing section.
4. Assemble all sections into the formal XML proposal format below.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, valid XML document. Your entire response MUST be only this XML.

<commercialProposal>
    <introduction>An introduction to the proposal for the client, referencing the project vision.</introduction>
    <scopeOfWork>A summary of the key features and deliverables for the MVP, derived from the PRD's use cases.</scopeOfWork>
    <timeline>
        <phase name="Phase 1: Discovery & Architectural Design" durationWeeks="2"/>
        <phase name="Phase 2: MVP Development & Integration" durationWeeks="6"/>
        <phase name="Phase 3: User Acceptance Testing & Deployment" durationWeeks="2"/>
    </timeline>
    <pricing>
        <services>
            <item name="Blended Team Day Rate (Design & Engineering)" rate="3000.00" currency="GBP" unit="per day"/>
        </services>
        <infrastructure>
            <item name="Estimated Monthly Cloud Costs" rate="365.00" currency="GBP" unit="per month" notes="Based on the Bill of Materials. Billed directly by the cloud provider."/>
        </infrastructure>
    </pricing>
    <nextSteps>The next steps are to review this proposal and schedule a follow-up meeting to discuss the project in more detail.</nextSteps>
</commercialProposal>

## GUIDELINES & CONSTRAINTS
- The proposal must be professional, client-ready, and directly reference the project's goals.
- All pricing must be clear and well-defined.
- Your entire response MUST be only the XML document."""

            self.log_execution("progress", "Generating proposal XML")

            xml_response = await self._call_llm(xml_system_message, f"""Generate a commercial proposal XML document for project: {project_name}

Input Data:
{context_text}""")

            proposal_xml = xml_response.strip()

            # Clean XML response
            if proposal_xml.startswith("```xml"):
                proposal_xml = proposal_xml.split("```xml")[1].split("```")[0].strip()
            elif proposal_xml.startswith("```"):
                proposal_xml = proposal_xml.split("```")[1].split("```")[0].strip()

            self.log_execution("success", f"Generated proposal XML ({len(proposal_xml)} chars)")

            # STAGE 2: Transform XML to HTML using LLM
            design_system = get_design_system_prompt()
            
            html_system_message = f"""## ROLE AND GOAL
You are an expert Business Proposal Designer. Your goal is to transform a commercial proposal XML into a professional, client-ready HTML document with AICOE branding.


{design_system}

## CONTEXT
You will be given an XML string containing a `<commercialProposal>`.

## STEP-BY-STEP PROCESS
1. Parse the input XML to extract all proposal sections.
2. Generate a clean HTML structure with:
   - Executive summary section
   - Scope of work with clear deliverables
   - Visual timeline with phases
   - Pricing breakdown with clear tables
   - Next steps and call-to-action
3. Apply the AICOE branding guidelines with absolute precision.
4. Return the final, single HTML file as a string.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, complete HTML string as your response. DO NOT include any other text, explanation, or formatting like markdown code fences. Your response should start with `<!DOCTYPE html>` and end with `</html>`.

## GUIDELINES & STYLING (NON-NEGOTIABLE)
- **Styling:** All CSS MUST be contained within a `<style>` tag in the `<head>` of the HTML document.
- **Branding:** Use the AICOE color palette (Primary Navy: #1a1a2e, Accent Pink: #ff69b4, etc.)
- **Logo:** Include the AICOE logo in the footer with gradient text effect.
- **Layout:** Clean, minimalist design following Apple's principles.
- **Typography:** Use -apple-system, BlinkMacSystemFont, 'SF Pro Display' font stack.
- **Professional:** Must look like a real, client-ready business proposal.
- **Icons:** Use Lucide icon library via CDN.
- **Responsive:** Must work on desktop, tablet, and mobile.
- **Print-friendly:** Include print styles for PDF generation."""

            self.log_execution("progress", "Transforming XML to HTML")

            html_response = await self._call_llm(
                html_system_message,
                f"""Transform this commercial proposal XML into a beautiful, professional HTML document:

{proposal_xml}""",
                max_tokens=12000
            )

            # Clean HTML response
            proposal_html = html_response.strip()
            if proposal_html.startswith("```html"):
                proposal_html = proposal_html.split("```html")[1].split("```")[0].strip()
            elif proposal_html.startswith("```"):
                proposal_html = proposal_html.split("```")[1].split("```")[0].strip()

            # Validate HTML starts correctly
            if not proposal_html.startswith("<!DOCTYPE"):
                self.logger.warning("Generated HTML doesn't start with DOCTYPE, prepending it")
                proposal_html = "<!DOCTYPE html>\n" + proposal_html

            self.log_execution("success", f"Generated proposal HTML ({len(proposal_html)} characters)")

            return AgentResult(
                success=True,
                data={
                    "proposal_xml": proposal_xml,
                    "proposal_html": proposal_html,
                    "project_name": project_name
                },
                metadata={
                    "agent": self.config.name,
                    "format": "xml+html"
                }
            )

        except Exception as e:
            self.logger.error(f"Error in ProposalAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
