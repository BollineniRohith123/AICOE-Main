"""
Mockup Agent - Generates Apple-style HTML mockups using LLM transformation
Advanced architecture: Intelligently creates single or multi-screen mockups based on use case complexity
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
import json


class MockupAgent(BaseAgent):
    """
    Agent responsible for generating Apple-style HTML mockups
    Uses LLM to intelligently create single or multi-screen mockups
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="MockupAgent",
            description="Generates premium Apple-style HTML mockups with AICOE branding",
            model="x-ai/grok-code-fast-1",
            temperature=0.6,
            max_tokens=40000  # Increased to handle multiple screens
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate Apple-style HTML mockups with intelligent screen generation
        
        Input:
            - use_cases: Use cases to visualize
            - project_name: Name of the project
            - structured_notes: Optional context
            
        Output:
            - mockup_pages: Dictionary of HTML pages
            - use_case_structure: Metadata about generated structure
        """
        try:
            self.log_execution("start", "Generating premium HTML mockup prototypes")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            use_cases = input_data.get("use_cases", [])
            structured_notes = input_data.get("structured_notes", {})
            
            # Prepare context
            use_cases_text = json.dumps(use_cases, indent=2) if use_cases else "No specific use cases provided"
            notes_text = json.dumps(structured_notes, indent=2) if structured_notes else "No additional context"
            
            num_use_cases = len(use_cases) if isinstance(use_cases, list) else 0
            
            self.log_execution("llm_call", f"Generating intelligent mockups for {num_use_cases} use cases")
            
            # Get the advanced design system prompt
            design_system = get_design_system_prompt()
            
            # System message with advanced design guidelines
            system_message = f"""You are a world-class UI/UX designer and front-end architect specializing in Apple-inspired, premium web experiences with AICOE branding.

{design_system}

## YOUR TASK
Generate a complete set of interactive HTML mockup pages for a project. You will intelligently decide whether each use case needs:
- **SINGLE-PAGE MOCKUP**: For simple use cases (e.g., basic forms, simple dashboards)
- **MULTI-SCREEN MOCKUP**: For complex use cases (e.g., multi-step workflows, complex interactions)

You will create:
1. **index.html**: Main dashboard showcasing all use cases with beautiful cards
2. **Use Case Mockups**: For each use case, create either:
   - A single comprehensive page ({{USE_CASE_ID}}_mockup.html), OR
   - Multiple screen pages ({{USE_CASE_ID}}_screen-01.html, {{USE_CASE_ID}}_screen-02.html, etc.) with an overview page ({{USE_CASE_ID}}_index.html)

## DECISION CRITERIA (THINK CAREFULLY)
**Create SINGLE-PAGE mockup when:**
- Use case has ≤3 steps or screens
- Simple CRUD operations
- Basic forms or dashboards
- Straightforward user flows

**Create MULTI-SCREEN mockup when:**
- Use case has >3 steps or screens
- Complex workflows (e.g., registration → verification → setup → completion)
- Multiple user roles or states
- Rich interactions requiring separate screens

## OUTPUT FORMAT (CRITICAL)
Return a JSON object where:
- Keys are filenames (e.g., "index.html", "UC-001_mockup.html", "UC-002_screen-01.html")
- Values are complete HTML strings (each starting with <!DOCTYPE html> and ending with </html>)

Example for MIXED approach:
{{
  "index.html": "<!DOCTYPE html>...",
  "UC-001_mockup.html": "<!DOCTYPE html>...",  // Simple use case - single page
  "UC-002_index.html": "<!DOCTYPE html>...",   // Complex use case - overview
  "UC-002_screen-01.html": "<!DOCTYPE html>...",  // Screen 1: Login
  "UC-002_screen-02.html": "<!DOCTYPE html>...",  // Screen 2: OAuth
  "UC-002_screen-03.html": "<!DOCTYPE html>...",  // Screen 3: Consent
  "UC-003_mockup.html": "<!DOCTYPE html>..."   // Simple use case - single page
}}

## DESIGN REQUIREMENTS (PREMIUM QUALITY)
1. **Visual Excellence**: Every pixel matters - use the design system meticulously
2. **Micro-interactions**: Smooth transitions, hover effects, loading states
3. **Real Data**: Use realistic sample data, not placeholders
4. **Responsive**: Mobile-first, works beautifully on all devices
5. **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation
6. **Performance**: Optimized CSS, minimal JavaScript, fast loading
7. **Consistency**: Same design language across all pages
8. **Polish**: Attention to detail - shadows, spacing, typography, colors

## NAVIGATION STRUCTURE
- **index.html**: Links to each use case (either _mockup.html or _index.html)
- **Single-page mockups**: "Back to Dashboard" button → index.html
- **Multi-screen mockups**: 
  - Overview page (_index.html): Shows all screens, links to each screen
  - Each screen: "Previous" / "Next" buttons, "Back to Overview" button, "Back to Dashboard" button
  - Breadcrumb navigation showing current position

## REQUIRED ELEMENTS IN EVERY PAGE
- Semantic HTML5 structure
- Embedded CSS in <style> tag (use CSS variables from design system)
- Lucide icons: <script src="https://unpkg.com/lucide@latest"></script>
- Icon initialization: <script>lucide.createIcons();</script>
- AICOE logo in footer with gradient effect
- Responsive meta viewport tag
- Smooth scroll behavior

## FINAL OUTPUT
Your entire response MUST be ONLY the JSON object. No markdown code fences, no explanations, no additional text."""

            user_message = f"""Create premium, Apple-style HTML mockups with AICOE branding for the following project:

Project Name: {project_name}

Use Cases ({num_use_cases} total):
{use_cases_text}

Additional Context:
{notes_text}

INSTRUCTIONS:
1. Analyze each use case and decide: single-page or multi-screen?
2. Create index.html as a stunning dashboard with all use cases
3. For each use case, generate appropriate mockup(s)
4. Use the design system CSS variables and components
5. Make it look like a real, production-ready application
6. Include realistic UI elements, data, and interactions

CRITICAL: Extract the "id" field from each use case (e.g., "UC-001") and use it in filenames!

Remember: Return ONLY the JSON object with all HTML files. No other text."""

            self.log_execution("progress", "Calling LLM for mockup generation")
            
            response = await self._call_llm(
                system_message,
                user_message,
                max_tokens=40000
            )
            
            # Clean response
            response_clean = response.strip()
            
            # Remove markdown code fences if present
            if response_clean.startswith("```json"):
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1].split("```")[0].strip()
            
            self.log_execution("progress", "Parsing LLM response")
            
            # Parse JSON response
            try:
                mockup_pages = json.loads(response_clean)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
                self.logger.error(f"Response preview: {response_clean[:500]}")
                raise Exception(f"LLM did not return valid JSON: {str(e)}")
            
            # Validate that we got a dictionary
            if not isinstance(mockup_pages, dict):
                raise Exception(f"LLM returned {type(mockup_pages)} instead of dict")
            
            # Unescape HTML content (LLM sometimes double-escapes newlines)
            unescaped_pages = {}
            for page_name, html_content in mockup_pages.items():
                if isinstance(html_content, str):
                    unescaped_html = html_content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                    unescaped_pages[page_name] = unescaped_html
                else:
                    unescaped_pages[page_name] = html_content
            
            mockup_pages = unescaped_pages
            
            # Validate that we have at least index.html
            if "index.html" not in mockup_pages:
                raise Exception("LLM did not generate index.html")
            
            self.log_execution("success", f"Generated {len(mockup_pages)} mockup pages")
            
            # Analyze structure for metadata
            use_case_structure = self._analyze_structure(mockup_pages)
            
            return AgentResult(
                success=True,
                data={
                    "mockup_pages": mockup_pages,
                    "use_case_structure": use_case_structure,
                    "project_name": project_name,
                    "num_pages": len(mockup_pages)
                },
                metadata={
                    "agent": self.config.name,
                    "num_pages": len(mockup_pages),
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
