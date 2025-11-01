"""
Mockup Agent - Generates Apple-style HTML mockups
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class MockupAgent(BaseAgent):
    """
    Agent responsible for generating Apple-style HTML mockups
    Creates interactive, beautiful HTML pages following AICOE design guidelines
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="MockupAgent",
            description="Generates Apple-style HTML mockups with UC001 AICOE branding",
            model="x-ai/grok-code-fast-1",  # OpenAI GPT-OSS-120B via OpenRouter
            temperature=0.6,
            max_tokens=12000  # Increased from 6000 to handle complex mockups
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate Apple-style HTML mockup with multi-page support

        Input:
            - use_cases: Use cases to visualize
            - project_name: Name of the project
            - structured_notes: Optional context
            - prd_content: Optional PRD content for richer context
            - technical_stack: Optional technical stack information

        Output:
            - mockup_pages: Dictionary of HTML pages (index.html and additional pages)
            - mockup_html: Main index.html content (for backward compatibility)
        """
        try:
            self.log_execution("start", "Generating HTML mockup prototypes")
            self.validate_input(input_data, ["project_name"])

            project_name = input_data["project_name"]
            use_cases = input_data.get("use_cases", [])
            structured_notes = input_data.get("structured_notes", {})
            prd_content = input_data.get("prd_content", "")
            technical_stack = input_data.get("technical_stack", {})

            # Extract additional context for richer mockups
            case_study_context = self._extract_case_study_context(
                structured_notes,
                prd_content,
                technical_stack
            )

            # Determine if we need multiple pages
            # CHANGED: Always generate separate pages for each use case (if any exist)
            num_use_cases = len(use_cases) if isinstance(use_cases, list) else 0
            needs_multiple_pages = num_use_cases >= 1  # Generate separate pages for ALL use cases

            # Generate main index.html
            self.log_execution("llm_call", "Generating index.html with enhanced context")
            index_html = await self._generate_index_page(
                project_name,
                use_cases,
                structured_notes,
                needs_multiple_pages,
                case_study_context
            )

            # Store all pages
            mockup_pages = {
                "index.html": index_html
            }

            # Generate MULTIPLE SCREEN MOCKUPS for EACH use case
            if needs_multiple_pages and isinstance(use_cases, list):
                total_screens = 0

                # DEBUG: Log use_cases structure
                self.logger.info(f"[MockupAgent] DEBUG: use_cases type: {type(use_cases)}")
                self.logger.info(f"[MockupAgent] DEBUG: use_cases length: {len(use_cases)}")
                if len(use_cases) > 0:
                    self.logger.info(f"[MockupAgent] DEBUG: First use_case type: {type(use_cases[0])}")
                    self.logger.info(f"[MockupAgent] DEBUG: First use_case: {use_cases[0]}")

                for idx, use_case in enumerate(use_cases, 1):
                    # CRITICAL FIX: Check if use_case is a dict
                    if not isinstance(use_case, dict):
                        self.logger.error(f"[MockupAgent] ERROR: use_case {idx} is not a dict, it's a {type(use_case)}: {use_case}")
                        continue

                    # Extract main flow steps to determine number of screens
                    main_flow = use_case.get("main_flow", [])
                    num_screens = len(main_flow) if main_flow else 4  # Default to 4 screens if no main_flow

                    # Ensure at least 3 screens per use case
                    if num_screens < 3:
                        num_screens = 4  # Default to 4 screens for better mockup coverage

                    total_screens += num_screens

                self.log_execution("llm_call", f"Generating {total_screens} screen mockups across {num_use_cases} use cases")

                # Generate screens for each use case
                for uc_idx, use_case in enumerate(use_cases, 1):
                    # CRITICAL FIX: Skip if use_case is not a dict
                    if not isinstance(use_case, dict):
                        self.logger.error(f"[MockupAgent] Skipping use_case {uc_idx} - not a dict: {type(use_case)}")
                        continue

                    main_flow = use_case.get("main_flow", [])
                    num_screens = len(main_flow) if main_flow else 4
                    if num_screens < 3:
                        num_screens = 4

                    # Generate each screen for this use case
                    for screen_idx in range(1, num_screens + 1):
                        page_name = f"use-case-{uc_idx}-screen-{screen_idx}.html"

                        # Determine which flow step this screen represents
                        flow_step = main_flow[screen_idx - 1] if screen_idx <= len(main_flow) else None

                        page_html = await self._generate_use_case_screen(
                            project_name,
                            use_case,
                            uc_idx,
                            num_use_cases,
                            screen_idx,
                            num_screens,
                            flow_step,
                            case_study_context
                        )
                        mockup_pages[page_name] = page_html
                        self.log_execution("progress", f"Generated screen {screen_idx}/{num_screens} for use case {uc_idx}: {page_name}")

            total_chars = sum(len(html) for html in mockup_pages.values())
            self.log_execution("success", f"Generated {len(mockup_pages)} HTML pages ({total_chars} total characters)")

            return AgentResult(
                success=True,
                data={
                    "mockup_pages": mockup_pages,
                    "mockup_html": index_html,  # Backward compatibility
                    "project_name": project_name,
                    "page_count": len(mockup_pages),
                    "total_size": total_chars,
                    "use_case_count": num_use_cases
                },
                metadata={
                    "agent": self.config.name,
                    "format": "html",
                    "multi_page": needs_multiple_pages,
                    "pages_generated": list(mockup_pages.keys())
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

    def _extract_case_study_context(self, structured_notes: dict, prd_content: str, technical_stack: dict) -> dict:
        """Extract rich context from case study for better mockup generation"""
        context = {
            "overview": structured_notes.get("company_overview", ""),
            "objective": structured_notes.get("meeting_objective", ""),
            "target_audience": "",
            "key_features": [],
            "technical_stack": [],
            "pain_points": structured_notes.get("pain_points", []),
            "requirements": structured_notes.get("requirements", []),
            "decisions": structured_notes.get("decisions_made", [])
        }

        # Extract target audience from decisions
        for decision in context["decisions"]:
            if "target audience" in decision.lower() or "user" in decision.lower():
                context["target_audience"] = decision
                break

        # Extract technical stack
        tech_constraints = structured_notes.get("technical_constraints", [])
        for constraint in tech_constraints:
            if any(tech in constraint for tech in ["React", "Node", "Python", "AWS", "PostgreSQL", "MongoDB"]):
                context["technical_stack"].append(constraint)

        # Extract key features from requirements
        context["key_features"] = structured_notes.get("requirements", [])[:5]  # Top 5 features

        return context

    async def _generate_index_page(self, project_name: str, use_cases: list, structured_notes: dict, has_subpages: bool, case_study_context: dict = None) -> str:
        """Generate the main index.html page with enhanced context"""
        use_cases_text = json.dumps(use_cases, indent=2) if use_cases else "No specific use cases provided"
        notes_text = json.dumps(structured_notes, indent=2) if structured_notes else "No additional context"

        # Prepare enhanced context summary
        context_summary = ""
        if case_study_context:
            context_summary = f"""
CASE STUDY CONTEXT:
- Overview: {case_study_context.get('overview', 'N/A')}
- Objective: {case_study_context.get('objective', 'N/A')}
- Target Audience: {case_study_context.get('target_audience', 'N/A')}
- Key Features: {', '.join(case_study_context.get('key_features', [])[:3])}
- Technical Stack: {', '.join(case_study_context.get('technical_stack', []))}
"""

        system_message = """## ROLE AND GOAL
You are a world-class UI/UX Engineer who specializes in creating pixel-perfect, interactive, multi-page web prototypes. Your design philosophy is inspired by Apple's clean, minimalist, and high-contrast aesthetic. Your goal is to take a set of use cases and produce a fully functional, navigable set of HTML files.

## CONTEXT
You will receive the `<useCaseModel>` XML from the Blueprint Agent and the JSON data from the Data Agent.

## STEP-BY-STEP PROCESS
1. Analyze the use cases to identify the number of distinct screens required.
2. Create a main `index.html` page that serves as a dashboard or entry point, linking to each use case mockup.
3. For each `<useCase>` in the XML, create a corresponding `use-case-X.html` file that visually represents the main flow.
4. Use the synthetic JSON data to populate the mockups with realistic content.
5. Implement navigation between all pages (e.g., "Back to Home," "Next Use Case").
6. Apply the AICOE branding and design guidelines with absolute precision.
7. Return all generated files as a single JSON object.

## OUTPUT FORMAT (CRITICAL)
You MUST produce a single, valid XML document containing the mockup prototype structure. DO NOT include any other text or explanation.

<mockupPrototype>
    <title>Project Mockup Prototype</title>
    <description>A multi-page interactive prototype for the project use cases.</description>
    <screens>
        <screen id="index">
            <title>Main Dashboard</title>
            <content>The main dashboard HTML content with navigation to use cases.</content>
        </screen>
        <screen id="use-case-1">
            <title>Use Case 1: [Title]</title>
            <content>The HTML content for use case 1 mockup.</content>
        </screen>
        <!-- Add more screens as needed -->
    </screens>
</mockupPrototype>

## GUIDELINES & CONSTRAINTS (NON-NEGOTIABLE)
- The XML must contain all the necessary information to generate the HTML mockups.
- Each screen should have a unique id and contain the HTML content structure.
- Include navigation elements between screens.
- Apply AICOE branding and design guidelines.
- Your entire response MUST be only the XML document."""

        navigation_instruction = ""
        if has_subpages:
            navigation_instruction = f"""
IMPORTANT: This is a MULTI-PAGE prototype. Create navigation links to use case detail pages:
- Link format: <a href="use-case-1.html">Use Case 1</a>, <a href="use-case-2.html">Use Case 2</a>, etc.
- Add a "View Details" button on each use case card that links to its detail page
- Include a navigation menu with links to all use case pages
"""

        user_message = f"""Create a beautiful, Apple-style HTML mockup (index.html) with UC001 AICOE branding for the following project:

Project Name: {project_name}

{context_summary}

Use Cases:
{use_cases_text}

Additional Context:
{notes_text}

{navigation_instruction}

MOCKUP GENERATION INSTRUCTIONS:
- Create a comprehensive dashboard that showcases ALL use cases
- Each use case should be displayed as an interactive card with:
  * Use case title and ID
  * Brief description
  * Key actors involved
  * "View Details" button linking to the detailed mockup page
- Include a hero section with project overview and key metrics
- Add a features section highlighting the main capabilities
- Use realistic data and content (not placeholder text)
- Make it look like a real, production-ready application

MANDATORY UC001 AICOE DESIGN REQUIREMENTS:

1. **UC001 AICOE Color Palette** (MUST USE THESE EXACT COLORS):
   CSS Variables to define:
   /* AICOE Primary Colors */
   --primary-navy: #1a1a2e;
   --midnight-blue: #2a2a3e;
   --deep-purple: #3a2a4e;

   /* AICOE Accent Colors */
   --accent-pink: #ff69b4;
   --accent-cyan: #00ffcc;
   --accent-turquoise: #00e5b3;
   --accent-mint: #00cc99;

   /* Supporting Colors */
   --text-primary: #1a1a1a;
   --text-secondary: #666666;
   --bg-white: #ffffff;
   --bg-gray: #f5f5f7;
   --border-gray: #d2d2d7;

   /* Status Colors */
   --success-green: #00cc99;
   --warning-orange: #ff69b4;
   --danger-red: #ff1493;

   /* Shadows */
   --shadow: 0 2px 16px rgba(26, 26, 46, 0.08);
   --shadow-hover: 0 4px 24px rgba(26, 26, 46, 0.12);

2. **Lucide Icons Integration** (MANDATORY):
   - Include Lucide Icons CDN: <script src="https://unpkg.com/lucide@latest"></script>
   - Initialize icons with: lucide.createIcons();
   - Use icons for: navigation (Menu, Home, FileText, Layers, Database, Layout, CheckCircle, Settings)
   - Use icons for features (Zap, Target, Users, TrendingUp, Shield, Clock, etc.)
   - Example: <i data-lucide="home"></i>

3. **UC001 Apple-Style Design**:
   - Clean, minimalist layout with generous white space
   - System fonts: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', sans-serif
   - Smooth transitions (0.3s ease)
   - UC001 shadows: box-shadow: var(--shadow) and var(--shadow-hover)
   - Rounded corners: border-radius: 24px for cards, 12px for buttons
   - Font smoothing: -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;

4. **Layout Structure**:
   - Header with gradient text (h1): background: linear-gradient(135deg, var(--primary-navy) 0%, var(--deep-purple) 50%, var(--accent-pink) 100%);
   - Metadata grid with icons and info
   - Content sections with white background cards
   - Interactive elements with hover effects (transform: translateY(-2px))
   - Footer with AICOE branding and gradient logo

5. **Printer-Friendly CSS** (MANDATORY @media print rules):
   ```css
   @media print {{
     /* Hide navigation, buttons, interactive elements */
     nav, .no-print, button {{ display: none !important; }}
     /* Ensure readable fonts */
     body {{ font-size: 12pt; color: #000; background: #fff; }}
     /* Remove shadows and effects */
     * {{ box-shadow: none !important; text-shadow: none !important; }}
     /* Page breaks */
     .page-break {{ page-break-before: always; }}
     h1, h2, h3 {{ page-break-after: avoid; }}
     /* Show URLs for links */
     a[href]:after {{ content: " (" attr(href) ")"; }}
   }}
   ```

6. **Responsive Design**:
   - Mobile-first approach
   - Breakpoints: 768px (tablet), 1024px (desktop)
   - Flexible grid with CSS Grid or Flexbox
   - Container max-width: 1200px

7. **Interactive Elements**:
   - Smooth hover effects on cards (transform: translateY(-2px))
   - Button hover states with color transitions
   - Box shadow transitions on hover
   - Gradient text effects for headings

8. **UC001 AICOE Branding Elements**:
   - Header with gradient text using UC001 colors
   - Metadata section with icons (Calendar, User, Tag, Clock)
   - Footer: "Powered by AICOE Multi-Agent Platform"
   - Logo with gradient effect
   - Color scheme strictly follows UC001 palette
   - Professional, enterprise-grade appearance

9. **Self-Contained**:
   - All CSS inline in <style> tag
   - All JavaScript inline in <script> tag
   - Only external dependency: Lucide Icons CDN

IMPORTANT: Return ONLY the complete HTML code, starting with <!DOCTYPE html>.
The HTML must be production-ready, fully functional, and visually stunning.
NO explanations, NO markdown code blocks, JUST the raw HTML."""

        response = await self._call_llm(
            system_message,
            user_message,
            max_tokens=8000
        )

        # Clean response
        html_content = response.strip()
        if html_content.startswith("```html"):
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        elif html_content.startswith("```"):
            html_content = html_content.split("```")[1].split("```")[0].strip()

        # Ensure it starts with <!DOCTYPE html>
        if not html_content.upper().startswith("<!DOCTYPE HTML"):
            self.logger.warning("Response doesn't start with DOCTYPE, may not be valid HTML")

        return html_content

    async def _generate_use_case_screen(
        self,
        project_name: str,
        use_case: dict,
        uc_num: int,
        total_use_cases: int,
        screen_num: int,
        total_screens: int,
        flow_step: dict = None,
        case_study_context: dict = None
    ) -> str:
        """Generate a single screen mockup for a specific step in the use case flow"""

        # Extract use case details
        use_case_id = use_case.get("id", f"UC-{uc_num:03d}")
        use_case_title = use_case.get("title", "Use Case")
        use_case_description = use_case.get("description", "")
        actors = use_case.get("actors", [])
        main_flow = use_case.get("main_flow", [])

        # Determine screen title and description from flow step
        if flow_step:
            screen_title = flow_step.get("step", f"Step {screen_num}")
            screen_description = flow_step.get("description", "")
        else:
            # Generate default screen titles if no flow step provided
            screen_titles = ["Initial Screen", "Main Interface", "Processing", "Confirmation", "Success"]
            screen_title = screen_titles[screen_num - 1] if screen_num <= len(screen_titles) else f"Screen {screen_num}"
            screen_description = f"Screen {screen_num} of the {use_case_title} workflow"

        # Build navigation info
        prev_screen = f"use-case-{uc_num}-screen-{screen_num-1}.html" if screen_num > 1 else None
        next_screen = f"use-case-{uc_num}-screen-{screen_num+1}.html" if screen_num < total_screens else None

        # Build context summary
        context_summary = ""
        if case_study_context:
            context_summary = f"""
CASE STUDY CONTEXT:
- Company: {case_study_context.get('overview', 'N/A')}
- Objective: {case_study_context.get('objective', 'N/A')}
- Target Audience: {case_study_context.get('target_audience', 'N/A')}
- Key Features: {', '.join(case_study_context.get('key_features', [])[:5])}
- Tech Stack: {', '.join(case_study_context.get('technical_stack', [])[:5])}
"""

        system_message = """You are a world-class UI/UX designer and frontend developer specializing in creating pixel-perfect,
interactive screen mockups that look like real production applications. You follow Apple's design philosophy and UC001 AICOE branding.

Your mockups are not just documentation - they are realistic, interactive UI screens that demonstrate exactly how the
application will look and feel when built. You use realistic data, proper layouts, and interactive elements.

CRITICAL: Generate ACTUAL UI SCREENS, not documentation pages. Show the real user interface for this specific screen/step."""

        user_message = f"""Create a REALISTIC, INTERACTIVE UI screen mockup for this specific step in the use case flow:

PROJECT: {project_name}
USE CASE: {use_case_id} - {use_case_title}
SCREEN: {screen_num} of {total_screens}
SCREEN TITLE: {screen_title}

{context_summary}

USE CASE DESCRIPTION:
{use_case_description}

ACTORS: {', '.join(actors) if actors else 'End User'}

THIS SCREEN REPRESENTS:
{screen_description}

FULL USE CASE FLOW (for context):
{json.dumps(main_flow, indent=2)}

CRITICAL MOCKUP REQUIREMENTS:

1. **Generate the ACTUAL UI SCREEN for this step**:
   - This is screen {screen_num} out of {total_screens} in the workflow
   - Show the EXACT user interface that would appear at this step
   - Include all form fields, buttons, data displays, navigation elements
   - Use realistic sample data (names, emails, dates, numbers, etc.)
   - Make it look like a screenshot from a real application

2. **Screen-Specific Content**:
   - Focus on THIS specific step: "{screen_title}"
   - Show the UI elements needed for this step (forms, buttons, displays, etc.)
   - Include appropriate input fields, dropdowns, checkboxes, etc.
   - Show realistic data and content (not placeholders like "Lorem ipsum")
   - Add helpful UI hints, tooltips, or validation messages

3. **Navigation & Flow**:
   - Add "← Back to Dashboard" link to index.html
   - Add "← Previous Step" button linking to {prev_screen if prev_screen else 'index.html'}
   - Add "Next Step →" or "Continue" button linking to {next_screen if next_screen else 'index.html'}
   - Show progress indicator: "Step {screen_num} of {total_screens}"
   - Include breadcrumb: Dashboard > {use_case_title} > {screen_title}

4. **UC001 AICOE Design System** (MANDATORY):
   - Color palette: --primary-navy (#1a1a2e), --accent-pink (#ff69b4), --accent-cyan (#00ffcc)
   - Lucide icons CDN: <script src="https://unpkg.com/lucide@latest"></script>
   - SF Pro Display fonts with font smoothing
   - Shadows: --shadow (0 2px 16px rgba(26, 26, 46, 0.08))
   - Border radius: 24px for cards, 12px for buttons
   - Smooth transitions (0.3s ease)
   - Initialize icons: lucide.createIcons();

5. **Interactive Elements**:
   - Realistic form inputs with labels and placeholders
   - Buttons with hover effects (transform: translateY(-2px))
   - Cards with shadow transitions
   - Loading states, success messages, error states (where appropriate)
   - Dropdown menus, toggles, sliders (if needed for this step)

6. **Responsive & Print-Friendly**:
   - Mobile-first responsive design
   - @media print rules to hide navigation
   - Breakpoints at 768px and 1024px

7. **Content Structure**:
   - Header with navigation and breadcrumbs
   - Progress indicator showing current step
   - Main content area with the actual UI for this screen
   - Action buttons (Previous, Next/Continue, Cancel)
   - Footer with AICOE branding

EXAMPLE SCREEN TYPES (adapt based on the step):
- If it's a form step: Show the actual form with all fields
- If it's a display step: Show the data in cards/tables/lists
- If it's a confirmation step: Show summary with confirm/cancel buttons
- If it's a success step: Show success message with next actions

Return ONLY the complete HTML code, starting with <!DOCTYPE html>.
NO explanations, NO markdown code blocks, JUST the raw HTML.
Make it look AMAZING, REALISTIC, and PRODUCTION-READY!"""

        response = await self._call_llm(
            system_message,
            user_message,
            max_tokens=8000
        )

        # Clean response
        html_content = response.strip()
        if html_content.startswith("```html"):
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        elif html_content.startswith("```"):
            html_content = html_content.split("```")[1].split("```")[0].strip()

        return html_content

    async def _generate_use_case_page(self, project_name: str, use_case: dict, page_num: int, total_pages: int, case_study_context: dict = None) -> str:
        """Generate a detailed, realistic use case mockup page"""
        use_case_text = json.dumps(use_case, indent=2)

        # Extract use case details for better mockup generation
        use_case_id = use_case.get("id", f"UC-{page_num:03d}")
        use_case_title = use_case.get("title", "Use Case")
        use_case_description = use_case.get("description", "")
        actors = use_case.get("actors", [])
        main_flow = use_case.get("main_flow", [])
        preconditions = use_case.get("preconditions", [])
        postconditions = use_case.get("postconditions", [])

        system_message = """You are a world-class UI/UX designer and frontend developer specializing in creating pixel-perfect,
interactive mockups that look like real production applications. You follow Apple's design philosophy and UC001 AICOE branding.

Your mockups are not just documentation - they are realistic, interactive prototypes that demonstrate exactly how the
application will look and feel when built. You use realistic data, proper layouts, and interactive elements."""

        user_message = f"""Create a REALISTIC, INTERACTIVE mockup page for this use case (use-case-{page_num}.html):

PROJECT: {project_name}
USE CASE: {use_case_id} - {use_case_title}
PAGE: {page_num} of {total_pages}

USE CASE DETAILS:
{use_case_text}

CRITICAL MOCKUP REQUIREMENTS:

1. **Create ACTUAL UI SCREENS, not documentation**:
   - Design the actual user interface screens that would be used for this use case
   - Show the main flow as a series of interactive screen states or steps
   - Include realistic form fields, buttons, navigation, data displays
   - Use realistic sample data (names, dates, numbers, etc.)
   - Make it look like a real application, not a specification document

2. **Visual Flow Representation**:
   - Show the main flow steps as interactive screen mockups or wireframes
   - Use tabs, accordions, or step indicators to show progression
   - Include "before" and "after" states where applicable
   - Show different screen states (empty state, loading, success, error)

3. **Interactive Elements**:
   - Add realistic buttons, forms, cards, modals
   - Include hover states and transitions
   - Show navigation patterns (breadcrumbs, back buttons, menus)
   - Add interactive components like dropdowns, toggles, sliders

4. **UC001 AICOE Design System**:
   - Color palette: --primary-navy (#1a1a2e), --accent-pink (#ff69b4), --accent-cyan (#00ffcc)
   - Lucide icons for all UI elements
   - SF Pro Display fonts with font smoothing
   - Shadows: --shadow and --shadow-hover
   - Border radius: 24px for cards, 12px for buttons
   - Smooth transitions (0.3s ease)

5. **Navigation**:
   - "← Back to Dashboard" link to index.html
   - "← Previous" link to use-case-{page_num-1}.html (if page_num > 1)
   - "Next →" link to use-case-{page_num+1}.html (if page_num < {total_pages})
   - Breadcrumb navigation showing current position

6. **Responsive & Print-Friendly**:
   - Mobile-first responsive design
   - @media print rules to hide navigation and optimize for printing
   - Breakpoints at 768px and 1024px

7. **Content Structure**:
   - Hero section with use case title and description
   - Actors section showing who uses this feature
   - Main flow visualization (the actual UI screens/steps)
   - Preconditions and postconditions (if relevant)
   - Success metrics or outcomes

EXAMPLE STRUCTURE:
- Header with navigation and breadcrumbs
- Hero section with gradient title
- Actors cards with icons
- Main content: ACTUAL UI MOCKUP SCREENS showing the flow
- Footer with AICOE branding

Return ONLY the complete HTML code, starting with <!DOCTYPE html>.
NO explanations, NO markdown code blocks, JUST the raw HTML.
Make it look AMAZING and REALISTIC!"""

        response = await self._call_llm(
            system_message,
            user_message,
            max_tokens=8000
        )

        # Clean response
        html_content = response.strip()
        if html_content.startswith("```html"):
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        elif html_content.startswith("```"):
            html_content = html_content.split("```")[1].split("```")[0].strip()

        return html_content
