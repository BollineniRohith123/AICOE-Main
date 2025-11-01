"""
Mockup Agent - Generates Apple-style HTML mockups using LLM transformation
Advanced architecture: Makes SEPARATE API calls for each mockup for premium quality
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
import json
import asyncio


class MockupAgent(BaseAgent):
    """
    Agent responsible for generating Apple-style HTML mockups
    Makes separate LLM calls for each mockup to ensure premium quality

    Architecture:
    1. Generate index.html (dashboard) - 1 API call
    2. For each use case, generate mockup - 1 API call per use case
    3. Combine all results
    """

    def __init__(self, llm_client):
        config = AgentConfig(
            name="MockupAgent",
            description="Generates premium Apple-style HTML mockups with AICOE branding",
            model="x-ai/grok-code-fast-1",
            temperature=0.6,
            max_tokens=16000  # Per mockup (not all at once)
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate Apple-style HTML mockups with SEPARATE API calls for premium quality

        Input:
            - use_cases: Use cases to visualize
            - project_name: Name of the project
            - structured_notes: Optional context

        Output:
            - mockup_pages: Dictionary of HTML pages
            - use_case_structure: Metadata about generated structure
        """
        try:
            self.log_execution("start", "Generating premium HTML mockups with separate API calls")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            use_cases = input_data.get("use_cases", [])
            structured_notes = input_data.get("structured_notes", {})

            num_use_cases = len(use_cases) if isinstance(use_cases, list) else 0

            self.log_execution("info", f"Will make {num_use_cases + 1} API calls: 1 for index + {num_use_cases} for use cases")

            # Dictionary to store all generated HTML pages
            all_mockup_pages = {}

            # STEP 1: Generate index.html (dashboard)
            self.log_execution("progress", "Step 1: Generating index.html dashboard")
            index_html = await self._generate_index_page(project_name, use_cases, structured_notes)
            all_mockup_pages["index.html"] = index_html
            self.log_execution("success", "✓ Generated index.html")

            # STEP 2: Generate each use case mockup separately
            self.log_execution("progress", f"Step 2: Generating {num_use_cases} use case mockups")

            for idx, use_case in enumerate(use_cases, 1):
                uc_id = use_case.get("id", f"UC-{idx:03d}")
                uc_name = use_case.get("name", f"Use Case {idx}")

                self.log_execution("progress", f"  [{idx}/{num_use_cases}] Generating mockup for {uc_id}: {uc_name}")

                # Generate mockup for this specific use case
                uc_mockup_pages = await self._generate_use_case_mockup(
                    project_name,
                    use_case,
                    structured_notes
                )

                # Add to all pages
                all_mockup_pages.update(uc_mockup_pages)

                self.log_execution("success", f"  ✓ Generated {len(uc_mockup_pages)} page(s) for {uc_id}")

            self.log_execution("success", f"✓ Generated all {len(all_mockup_pages)} mockup pages")

            # Analyze structure for metadata
            use_case_structure = self._analyze_structure(all_mockup_pages)

            return AgentResult(
                success=True,
                data={
                    "mockup_pages": all_mockup_pages,
                    "use_case_structure": use_case_structure,
                    "project_name": project_name,
                    "num_pages": len(all_mockup_pages)
                },
                metadata={
                    "agent": self.config.name,
                    "num_pages": len(all_mockup_pages),
                    "structure": use_case_structure
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in MockupAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )

    async def _generate_index_page(
        self,
        project_name: str,
        use_cases: List[Dict[str, Any]],
        structured_notes: Dict[str, Any]
    ) -> str:
        """
        Generate the main index.html dashboard page

        This page showcases all use cases with beautiful cards
        """
        design_system = get_design_system_prompt()

        system_message = f"""You are a world-class UI/UX designer specializing in Apple-inspired dashboards with AICOE branding.

{design_system}

## YOUR TASK
Create a stunning **index.html** dashboard page that showcases all use cases for this project.

## DESIGN REQUIREMENTS
1. **Hero Section**: Project name, tagline, beautiful gradient background
2. **Use Case Grid**: Beautiful cards for each use case with:
   - Use case ID and name
   - Brief description
   - Icon (using Lucide icons)
   - "View Mockup" button linking to the mockup
   - Hover effects and micro-interactions
3. **Navigation**: Smooth scroll, responsive design
4. **Footer**: AICOE branding with gradient logo
5. **Premium Quality**: Every pixel matters - use design system meticulously

## NAVIGATION LINKS
For each use case card, the "View Mockup" button should link to:
- `{{USE_CASE_ID}}_mockup.html` (you'll decide later if it's single or multi-screen)

## OUTPUT FORMAT
Return ONLY the complete HTML string. Start with <!DOCTYPE html> and end with </html>.
NO markdown code fences, NO explanations, NO additional text."""

        use_cases_summary = []
        for uc in use_cases:
            use_cases_summary.append({
                "id": uc.get("id", "UC-XXX"),
                "name": uc.get("name", "Unnamed Use Case"),
                "description": uc.get("description", "No description provided")
            })

        user_message = f"""Create the index.html dashboard for:

Project Name: {project_name}

Use Cases ({len(use_cases)} total):
{json.dumps(use_cases_summary, indent=2)}

Make it absolutely stunning - this is the first page users see!"""

        response = await self._call_llm(system_message, user_message, max_tokens=16000)

        # Clean response
        html_content = self._clean_html_response(response)

        return html_content

    async def _generate_use_case_mockup(
        self,
        project_name: str,
        use_case: Dict[str, Any],
        structured_notes: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate mockup(s) for a single use case

        Returns a dictionary of filename -> HTML content
        Can return single page or multiple pages depending on complexity
        """
        design_system = get_design_system_prompt()

        uc_id = use_case.get("id", "UC-XXX")
        uc_name = use_case.get("name", "Unnamed Use Case")
        uc_description = use_case.get("description", "")
        uc_steps = use_case.get("steps", [])
        num_steps = len(uc_steps) if isinstance(uc_steps, list) else 0

        system_message = f"""You are a world-class UI/UX designer specializing in Apple-inspired mockups with AICOE branding.

{design_system}

## YOUR TASK
Create a premium mockup for a SINGLE use case. You need to decide:
- **SINGLE-PAGE MOCKUP**: If the use case is simple (≤3 steps)
- **MULTI-SCREEN MOCKUP**: If the use case is complex (>3 steps)

## DECISION CRITERIA
**Create SINGLE-PAGE mockup when:**
- Use case has ≤3 steps
- Simple CRUD operations
- Basic forms or dashboards
- Straightforward user flows

**Create MULTI-SCREEN mockup when:**
- Use case has >3 steps
- Complex workflows (e.g., registration → verification → setup)
- Multiple user roles or states
- Rich interactions requiring separate screens

## OUTPUT FORMAT FOR SINGLE-PAGE
Return a JSON object with ONE file:
{{
  "{uc_id}_mockup.html": "<!DOCTYPE html>..."
}}

## OUTPUT FORMAT FOR MULTI-SCREEN
Return a JSON object with MULTIPLE files:
{{
  "{uc_id}_index.html": "<!DOCTYPE html>...",  // Overview page
  "{uc_id}_screen-01.html": "<!DOCTYPE html>...",  // First screen
  "{uc_id}_screen-02.html": "<!DOCTYPE html>...",  // Second screen
  ...
}}

## NAVIGATION REQUIREMENTS
- **Single-page**: "Back to Dashboard" button → ../index.html
- **Multi-screen overview**: Links to each screen, "Back to Dashboard" button
- **Multi-screen screens**: Prev/Next buttons, breadcrumbs, "Back to Overview", "Back to Dashboard"

## DESIGN REQUIREMENTS
1. **Premium Quality**: This is the ONLY use case you're working on - make it perfect!
2. **Realistic Data**: Use real-looking sample data, not placeholders
3. **Micro-interactions**: Smooth transitions, hover effects, loading states
4. **Responsive**: Mobile-first, works on all devices
5. **Accessibility**: ARIA labels, semantic HTML, keyboard navigation

## FINAL OUTPUT
Return ONLY the JSON object. No markdown code fences, no explanations."""

        user_message = f"""Create a premium mockup for this use case:

Use Case ID: {uc_id}
Use Case Name: {uc_name}
Description: {uc_description}
Number of Steps: {num_steps}

Steps:
{json.dumps(uc_steps, indent=2)}

Analyze the complexity and create either a single-page or multi-screen mockup.
Make it absolutely beautiful - you have full focus on this ONE use case!"""

        response = await self._call_llm(system_message, user_message, max_tokens=16000)

        # Clean and parse response
        response_clean = response.strip()

        # Remove markdown code fences if present
        if response_clean.startswith("```json"):
            response_clean = response_clean.split("```json")[1].split("```")[0].strip()
        elif response_clean.startswith("```"):
            response_clean = response_clean.split("```")[1].split("```")[0].strip()

        # Parse JSON
        try:
            mockup_pages = json.loads(response_clean)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse use case mockup JSON for {uc_id}: {str(e)}")
            # Fallback: create a simple error page
            mockup_pages = {
                f"{uc_id}_mockup.html": f"<!DOCTYPE html><html><body><h1>Error generating mockup for {uc_name}</h1></body></html>"
            }

        # Unescape HTML content
        unescaped_pages = {}
        for page_name, html_content in mockup_pages.items():
            if isinstance(html_content, str):
                unescaped_html = html_content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                unescaped_pages[page_name] = unescaped_html
            else:
                unescaped_pages[page_name] = html_content

        return unescaped_pages

    def _clean_html_response(self, response: str) -> str:
        """Clean HTML response from LLM"""
        response_clean = response.strip()

        # Remove markdown code fences if present
        if response_clean.startswith("```html"):
            response_clean = response_clean.split("```html")[1].split("```")[0].strip()
        elif response_clean.startswith("```"):
            response_clean = response_clean.split("```")[1].split("```")[0].strip()

        # Unescape if needed
        response_clean = response_clean.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')

        return response_clean

    def _analyze_structure(self, mockup_pages: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze the generated mockup structure
        
        Returns metadata about single-page vs multi-screen use cases
        """
        structure = {
            "total_pages": len(mockup_pages),
            "has_index": "index.html" in mockup_pages,
            "use_cases": {}
        }
        
        # Analyze each page
        for filename in mockup_pages.keys():
            if filename == "index.html":
                continue
            
            # Extract use case ID
            if "_" in filename:
                uc_id = filename.split("_")[0]  # e.g., "UC-001"
                
                if uc_id not in structure["use_cases"]:
                    structure["use_cases"][uc_id] = {
                        "type": "unknown",
                        "pages": []
                    }
                
                structure["use_cases"][uc_id]["pages"].append(filename)
                
                # Determine type
                if "screen-" in filename:
                    structure["use_cases"][uc_id]["type"] = "multi-screen"
                elif filename.endswith("_mockup.html"):
                    structure["use_cases"][uc_id]["type"] = "single-page"
                elif filename.endswith("_index.html"):
                    structure["use_cases"][uc_id]["type"] = "multi-screen"
        
        return structure
