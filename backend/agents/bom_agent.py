"""
Bill of Materials (BOM) Agent - Generates detailed component and resource listings
Generates HTML directly from XML using LLM transformation
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
import json


class BOMAgent(BaseAgent):
    """
    Agent responsible for creating detailed Bill of Materials
    Takes structured data and generates beautiful HTML output using LLM
    """

    def __init__(self, llm_client):
        config = AgentConfig(
            name="BOMAgent",
            description="Creates detailed Bill of Materials with cost estimates",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.2,  # Very low temperature for precise technical specifications
            max_tokens=12000
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate Bill of Materials document as HTML

        This is a TWO-STAGE process:
        Stage 1: Generate structured XML (for data storage and IP)
        Stage 2: Transform XML to beautiful HTML using LLM

        Input:
            - project_name: Name of the project
            - use_cases: Use cases from requirements
            - enrichment: Technical architecture from knowledge base
            - research_insights: Technical standards and best practices

        Output:
            - bom_xml: Structured XML document
            - bom_html: Beautiful HTML document
        """
        try:
            self.log_execution("start", "Generating Bill of Materials")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            use_cases = input_data.get("use_cases", [])
            enrichment = input_data.get("enrichment", {})
            research_insights = input_data.get("research_insights", {})

            # Prepare context
            research_text = json.dumps(research_insights, indent=2) if research_insights else "No research insights available"

            context_text = f"""
Project Name: {project_name}

Use Cases:
{json.dumps(use_cases, indent=2)}

Technical Architecture:
{json.dumps(enrichment, indent=2)}

Research Insights (for technical standards):
{research_text[:1500]}
"""

            # STAGE 1: Generate XML for data storage
            xml_system_message = """## ROLE AND GOAL
You are a Cloud Financial Analyst. Your task is to analyze the system architecture and produce a Bill of Materials (BOM) that estimates the monthly infrastructure costs. Your output must be a structured XML document.

## STEP-BY-STEP PROCESS
1. Analyze the input to identify all necessary infrastructure components (e.g., web servers, API servers, databases).
2. For each component, estimate a reasonable monthly cost based on standard cloud pricing (assume a small-to-medium scale deployment).
3. Categorize each cost item (e.g., "Cloud Infrastructure," "Software Licenses").
4. Calculate the total estimated monthly cost.
5. Format the BOM into the strict XML schema below.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, valid XML document. Your entire response MUST be only this XML.

<billOfMaterials>
    <summary>An estimated monthly cost breakdown for deploying and running the proposed solution.</summary>
    <items>
        <category name="Cloud Infrastructure">
            <item name="Web Server Hosting (2 instances)" provider="Vercel/Netlify" costPerMonth="40.00" />
            <item name="API Server Hosting (2 instances)" provider="AWS/GCP" costPerMonth="100.00" />
            <item name="Managed MongoDB" provider="MongoDB Atlas" costPerMonth="75.00" />
        </category>
        <category name="Third-Party Services">
            <item name="LLM API Usage" provider="OpenAI/Anthropic" costPerMonth="150.00" />
        </category>
    </items>
    <totalCostPerMonth>365.00</totalCostPerMonth>
</billOfMaterials>

## GUIDELINES & CONSTRAINTS
- Costs should be reasonable estimates. Precision is not required, but figures should be realistic.
- Prioritize services that have a free or low-cost tier for an MVP.
- Your entire response MUST be only the XML document."""

            self.log_execution("progress", "Generating BOM XML")

            xml_response = await self._call_llm(xml_system_message, f"""Generate a Bill of Materials XML document for project: {project_name}

Input Data:
{context_text}""")

            bom_xml = xml_response.strip()

            # Clean XML response
            if bom_xml.startswith("```xml"):
                bom_xml = bom_xml.split("```xml")[1].split("```")[0].strip()
            elif bom_xml.startswith("```"):
                bom_xml = bom_xml.split("```")[1].split("```")[0].strip()

            self.log_execution("success", f"Generated BOM XML ({len(bom_xml)} chars)")

            # STAGE 2: Transform XML to HTML using LLM
            design_system = get_design_system_prompt()
            
            html_system_message = f"""## ROLE AND GOAL
You are an expert Financial Report Designer. Your goal is to transform a Bill of Materials XML into a professional, interactive HTML document with AICOE branding.


{design_system}

## CONTEXT
You will be given an XML string containing a `<billOfMaterials>`.

## STEP-BY-STEP PROCESS
1. Parse the input XML to extract all cost categories and items.
2. Generate a clean HTML structure with:
   - A summary section showing total costs
   - Interactive tables for each category
   - Sortable columns
   - Professional styling
3. Apply the AICOE branding guidelines with absolute precision.
4. Return the final, single HTML file as a string.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, complete HTML string as your response. DO NOT include any other text, explanation, or formatting like markdown code fences. Your response should start with `<!DOCTYPE html>` and end with `</html>`.

## GUIDELINES & STYLING (NON-NEGOTIABLE)
- **Styling:** All CSS MUST be contained within a `<style>` tag in the `<head>` of the HTML document.
- **Branding:** Use the AICOE color palette (Primary Navy: #1a1a2e, Accent Cyan: #00ffcc, etc.)
- **Logo:** Include the AICOE logo in the footer with gradient text effect.
- **Layout:** Clean, minimalist design following Apple's principles.
- **Typography:** Use -apple-system, BlinkMacSystemFont, 'SF Pro Display' font stack.
- **Interactivity:** Tables should have sortable columns with hover effects.
- **Icons:** Use Lucide icon library via CDN.
- **Responsive:** Must work on desktop, tablet, and mobile.
- **Print-friendly:** Include print styles."""

            self.log_execution("progress", "Transforming XML to HTML")

            html_response = await self._call_llm(
                html_system_message,
                f"""Transform this BOM XML into a beautiful, professional HTML document:

{bom_xml}""",
                max_tokens=12000
            )

            # Clean HTML response
            bom_html = html_response.strip()
            if bom_html.startswith("```html"):
                bom_html = bom_html.split("```html")[1].split("```")[0].strip()
            elif bom_html.startswith("```"):
                bom_html = bom_html.split("```")[1].split("```")[0].strip()

            # Validate HTML starts correctly
            if not bom_html.startswith("<!DOCTYPE"):
                self.logger.warning("Generated HTML doesn't start with DOCTYPE, prepending it")
                bom_html = "<!DOCTYPE html>\n" + bom_html

            self.log_execution("success", f"Generated BOM HTML ({len(bom_html)} characters)")

            return AgentResult(
                success=True,
                data={
                    "bom_xml": bom_xml,
                    "bom_html": bom_html,
                    "project_name": project_name
                },
                metadata={
                    "agent": self.config.name,
                    "format": "xml+html"
                }
            )

        except Exception as e:
            self.logger.error(f"Error in BOMAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
