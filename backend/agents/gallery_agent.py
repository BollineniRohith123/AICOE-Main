"""
Case Study Gallery Agent - Generates master gallery index for all projects
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentConfig, AgentResult
from .design_system import get_design_system_prompt
from pathlib import Path
import json
import os
from datetime import datetime
import re


class CaseStudyGalleryAgent(BaseAgent):
    """
    Agent responsible for generating a master gallery index showing all case studies
    Scans all completed projects and creates a beautiful Apple-style gallery with AICOE branding
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="CaseStudyGalleryAgent",
            description="Generates master gallery index for all case studies with AICOE branding",
            model="x-ai/grok-code-fast-1",  # OpenAI GPT-OSS-120B via OpenRouter
            temperature=0.6,
            max_tokens=16000
        )
        super().__init__(config, llm_client)
        self.storage_path = Path("./backend/storage")
        self.gallery_path = self.storage_path / "case-study-gallery"
        
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Generate master gallery index for all case studies
        
        Input:
            - current_project_name: Name of the current project (optional)
            - force_regenerate: Force full regeneration (default: False)
            
        Output:
            - gallery_html: Master gallery index.html content
            - gallery_data: Metadata for all case studies
            - case_study_count: Number of case studies in gallery
        """
        try:
            self.log_execution("start", "Generating case study gallery")
            
            # Create gallery folder if it doesn't exist
            self.gallery_path.mkdir(parents=True, exist_ok=True)
            
            # Scan all projects and extract metadata
            self.log_execution("scan", "Scanning all projects for metadata")
            case_studies = await self._scan_all_projects()
            
            self.log_execution("info", f"Found {len(case_studies)} case studies")
            
            # Load existing gallery data
            gallery_data_path = self.gallery_path / "gallery-data.json"
            existing_data = {}
            if gallery_data_path.exists():
                with open(gallery_data_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Merge with existing data (preserve any manual edits)
            for study in case_studies:
                workflow_id = study['workflow_id']
                if workflow_id in existing_data:
                    # Preserve existing data but update key fields
                    existing_data[workflow_id].update(study)
                else:
                    existing_data[workflow_id] = study
            
            # Save updated gallery data
            with open(gallery_data_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
            
            self.log_execution("success", f"Saved metadata for {len(existing_data)} case studies")
            
            # Generate gallery HTML
            self.log_execution("llm_call", "Generating gallery HTML with AICOE branding")
            gallery_html = await self._generate_gallery_html(list(existing_data.values()))
            
            # Save gallery HTML
            gallery_html_path = self.gallery_path / "index.html"
            with open(gallery_html_path, 'w') as f:
                f.write(gallery_html)
            
            self.log_execution("success", f"Generated gallery at {gallery_html_path}")
            
            return AgentResult(
                success=True,
                data={
                    "gallery_html": gallery_html,
                    "gallery_data": existing_data,
                    "case_study_count": len(existing_data),
                    "gallery_path": str(gallery_html_path)
                },
                metadata={
                    "agent": self.config.name,
                    "case_study_count": len(existing_data)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error in CaseStudyGalleryAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
    
    async def _scan_all_projects(self) -> List[Dict[str, Any]]:
        """Scan all project folders and extract metadata"""
        case_studies = []
        
        # Scan all workflow folders in storage
        if not self.storage_path.exists():
            self.logger.warning(f"Storage path does not exist: {self.storage_path}")
            return case_studies
        
        for folder in self.storage_path.iterdir():
            if folder.is_dir() and folder.name != "case-study-gallery":
                workflow_results_path = folder / "workflow_results.json"
                
                if workflow_results_path.exists():
                    try:
                        with open(workflow_results_path, 'r') as f:
                            workflow_data = json.load(f)
                        
                        # Extract metadata
                        metadata = self._extract_metadata(workflow_data, folder.name)
                        if metadata:
                            case_studies.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"Failed to process {folder.name}: {str(e)}")
        
        # Sort by date (newest first)
        case_studies.sort(key=lambda x: x.get('date_created', ''), reverse=True)
        
        return case_studies
    
    def _extract_metadata(self, workflow_data: Dict, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from workflow results"""
        try:
            results = workflow_data.get('results', {})
            context = workflow_data.get('context', {})
            
            # Extract project name
            project_name = workflow_data.get('project_name', 'Unknown Project')
            
            # Extract date
            date_created = context.get('start_time', datetime.utcnow().isoformat())
            
            # Extract description from structured notes
            transcript_data = results.get('transcript', {})
            structured_notes = transcript_data.get('structured_notes', {})
            description = structured_notes.get('meeting_objective', '')
            if not description:
                key_points = structured_notes.get('key_discussion_points', [])
                description = ' '.join(key_points[:2]) if key_points else 'No description available'
            
            # Extract use cases count
            requirements_data = results.get('requirements', {})
            use_cases = requirements_data.get('use_cases', [])
            use_case_count = len(use_cases) if isinstance(use_cases, list) else 0
            
            # Extract technology stack
            tech_stack = self._extract_tech_stack(results, structured_notes)
            
            # Extract industry/domain
            industry = self._extract_industry(structured_notes, description, project_name)
            
            # Check if mockup exists
            mockup_path = f"backend/storage/{workflow_id}/index.html"
            has_mockup = Path(mockup_path).exists()
            
            return {
                'workflow_id': workflow_id,
                'project_name': project_name,
                'description': description[:200],  # Limit description length
                'date_created': date_created,
                'use_case_count': use_case_count,
                'tech_stack': tech_stack,
                'industry': industry,
                'has_mockup': has_mockup,
                'mockup_url': f"../{workflow_id}/index.html" if has_mockup else None
            }
        except Exception as e:
            self.logger.error(f"Error extracting metadata: {str(e)}")
            return None
    
    def _extract_tech_stack(self, results: Dict, structured_notes: Dict) -> List[str]:
        """Extract technology stack from various sources"""
        tech_stack = set()
        
        # From technical constraints
        constraints = structured_notes.get('technical_constraints', [])
        for constraint in constraints:
            if isinstance(constraint, str):
                # Look for common tech keywords
                tech_keywords = ['React', 'Node.js', 'Python', 'AWS', 'PostgreSQL', 'MongoDB', 
                               'Redis', 'Docker', 'Kubernetes', 'TypeScript', 'JavaScript',
                               'React Native', 'Angular', 'Vue', 'Django', 'Flask', 'FastAPI',
                               'MySQL', 'GraphQL', 'REST', 'Azure', 'GCP', 'Firebase']
                for keyword in tech_keywords:
                    if keyword.lower() in constraint.lower():
                        tech_stack.add(keyword)
        
        # From decisions made
        decisions = structured_notes.get('decisions_made', [])
        for decision in decisions:
            if isinstance(decision, str):
                for keyword in ['React', 'Node.js', 'Python', 'AWS', 'PostgreSQL', 'MongoDB', 
                              'React Native', 'TypeScript', 'Docker']:
                    if keyword.lower() in decision.lower():
                        tech_stack.add(keyword)
        
        return sorted(list(tech_stack))[:6]  # Limit to 6 technologies
    
    def _extract_industry(self, structured_notes: Dict, description: str, project_name: str) -> str:
        """Extract industry/domain from project data"""
        # Combine text for analysis
        text = f"{project_name} {description}".lower()
        
        # Industry keywords mapping
        industries = {
            'Healthcare': ['health', 'medical', 'patient', 'hospital', 'clinic', 'doctor', 'nurse'],
            'Finance': ['finance', 'banking', 'payment', 'transaction', 'investment', 'trading'],
            'E-commerce': ['ecommerce', 'e-commerce', 'shop', 'store', 'retail', 'product', 'cart'],
            'Education': ['education', 'learning', 'student', 'course', 'school', 'university'],
            'Fitness': ['fitness', 'workout', 'exercise', 'gym', 'health', 'nutrition', 'training'],
            'Food & Beverage': ['restaurant', 'food', 'meal', 'dining', 'recipe', 'cooking'],
            'Real Estate': ['real estate', 'property', 'housing', 'rental', 'apartment'],
            'Transportation': ['transport', 'logistics', 'delivery', 'shipping', 'fleet'],
            'Manufacturing': ['manufacturing', 'production', 'factory', 'supply chain'],
            'Analytics': ['analytics', 'dashboard', 'reporting', 'metrics', 'data visualization'],
            'Social': ['social', 'community', 'networking', 'messaging', 'chat'],
            'Productivity': ['productivity', 'task', 'todo', 'project management', 'collaboration']
        }
        
        for industry, keywords in industries.items():
            for keyword in keywords:
                if keyword in text:
                    return industry
        
        return 'General'
    
    async def _generate_gallery_html(self, case_studies: List[Dict]) -> str:
        """Generate the gallery HTML - using template instead of LLM for reliability"""

        # Instead of using LLM (which can be unreliable), use a template
        # This ensures consistent, functional output every time
        return self._generate_gallery_html_template(case_studies)

    def _generate_gallery_html_template(self, case_studies: List[Dict]) -> str:
        """Generate gallery HTML using a template"""

        # Prepare case studies data for the prompt
        case_studies_json = json.dumps(case_studies, indent=2)

        # Generate complete HTML with embedded data and JavaScript
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AICOE Case Study Gallery</title>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {{
            --aicoe-primary: #0066cc;
            --aicoe-accent: #00d9ff;
            --aicoe-dark: #1d1d1f;
            --aicoe-gray: #6e6e73;
            --aicoe-light-gray: #f5f5f7;
            --aicoe-white: #ffffff;
            --aicoe-success: #34c759;
            --aicoe-warning: #ff9500;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--aicoe-light-gray);
            color: var(--aicoe-dark);
            line-height: 1.6;
        }}

        /* Navigation */
        nav {{
            background: var(--aicoe-white);
            padding: 1rem 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .nav-container {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .nav-brand {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--aicoe-primary);
        }}

        /* Hero Section */
        .hero {{
            background: linear-gradient(135deg, var(--aicoe-primary), var(--aicoe-accent));
            color: var(--aicoe-white);
            padding: 4rem 2rem;
            text-align: center;
        }}

        .hero h1 {{
            font-size: 3rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }}

        .hero p {{
            font-size: 1.25rem;
            opacity: 0.9;
        }}

        /* Filters */
        .filters {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            align-items: flex-end;
        }}

        .filter-group {{
            flex: 1;
            min-width: 200px;
        }}

        .filter-group label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: var(--aicoe-gray);
            font-size: 0.875rem;
        }}

        .filter-group select,
        .filter-group input {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
            background: var(--aicoe-white);
        }}

        .filter-group select:focus,
        .filter-group input:focus {{
            outline: none;
            border-color: var(--aicoe-primary);
        }}

        .clear-filters {{
            padding: 0.75rem 1.5rem;
            background: var(--aicoe-gray);
            color: var(--aicoe-white);
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s ease;
        }}

        .clear-filters:hover {{
            background: #5a5a5f;
        }}

        /* Results Count */
        .results-count {{
            max-width: 1400px;
            margin: 0 auto 1rem;
            padding: 0 2rem;
            color: var(--aicoe-gray);
            font-size: 0.875rem;
        }}

        /* Gallery Grid */
        .gallery {{
            max-width: 1400px;
            margin: 2rem auto;
            padding: 0 2rem 4rem;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}

        /* Case Study Card */
        .case-study-card {{
            background: var(--aicoe-white);
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
        }}

        .case-study-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }}

        .case-study-card.hidden {{
            display: none;
        }}

        .industry-badge {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background: var(--aicoe-primary);
            color: var(--aicoe-white);
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1rem;
            align-self: flex-start;
        }}

        .card-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            color: var(--aicoe-dark);
        }}

        .card-description {{
            color: var(--aicoe-gray);
            margin-bottom: 1rem;
            line-height: 1.6;
            flex-grow: 1;
        }}

        .tech-stack {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }}

        .tech-tag {{
            padding: 0.25rem 0.75rem;
            background: var(--aicoe-light-gray);
            color: var(--aicoe-gray);
            border-radius: 12px;
            font-size: 0.875rem;
        }}

        .card-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #eee;
        }}

        .meta-info {{
            display: flex;
            gap: 1rem;
            font-size: 0.875rem;
            color: var(--aicoe-gray);
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        .view-button {{
            padding: 0.75rem 1.5rem;
            background: var(--aicoe-primary);
            color: var(--aicoe-white);
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s ease;
        }}

        .view-button:hover {{
            background: #0052a3;
        }}

        .view-button:disabled {{
            background: var(--aicoe-gray);
            cursor: not-allowed;
        }}

        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: var(--aicoe-gray);
        }}

        .empty-state i {{
            font-size: 4rem;
            margin-bottom: 1rem;
            opacity: 0.5;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 2rem;
            }}

            .filters {{
                flex-direction: column;
            }}

            .filter-group {{
                width: 100%;
            }}

            .gallery {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <nav>
        <div class="nav-container">
            <div class="nav-brand">🎨 AICOE Case Study Gallery</div>
        </div>
    </nav>

    <div class="hero">
        <h1>Case Study Gallery</h1>
        <p>Explore our collection of AI-powered project mockups and prototypes</p>
    </div>

    <div class="filters">
        <div class="filter-group">
            <label>Industry</label>
            <select id="industryFilter">
                <option value="">All Industries</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Technology</label>
            <select id="techFilter">
                <option value="">All Technologies</option>
            </select>
        </div>
        <div class="filter-group">
            <label>Search</label>
            <input type="text" id="searchInput" placeholder="Search projects...">
        </div>
        <div class="filter-group">
            <label>Sort By</label>
            <select id="sortFilter">
                <option value="date-desc">Newest First</option>
                <option value="date-asc">Oldest First</option>
                <option value="name-asc">Name (A-Z)</option>
                <option value="name-desc">Name (Z-A)</option>
                <option value="usecases-desc">Most Use Cases</option>
                <option value="usecases-asc">Least Use Cases</option>
            </select>
        </div>
        <button class="clear-filters" onclick="clearFilters()">Clear Filters</button>
    </div>

    <div class="results-count" id="resultsCount"></div>

    <div class="gallery" id="gallery"></div>

    <div class="empty-state" id="emptyState" style="display: none;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
        <h2>No case studies found</h2>
        <p>Try adjusting your filters or search terms</p>
    </div>

    <script>
        // Embedded case studies data
        const caseStudies = {case_studies_json};

        let filteredStudies = [...caseStudies];

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', () => {{
            populateFilters();
            renderGallery();

            // Add event listeners
            document.getElementById('industryFilter').addEventListener('change', applyFilters);
            document.getElementById('techFilter').addEventListener('change', applyFilters);
            document.getElementById('searchInput').addEventListener('input', applyFilters);
            document.getElementById('sortFilter').addEventListener('change', applyFilters);
        }});

        function populateFilters() {{
            // Get unique industries
            const industries = [...new Set(caseStudies.map(s => s.industry))].sort();
            const industryFilter = document.getElementById('industryFilter');
            industries.forEach(industry => {{
                const option = document.createElement('option');
                option.value = industry;
                option.textContent = industry;
                industryFilter.appendChild(option);
            }});

            // Get unique technologies
            const technologies = [...new Set(caseStudies.flatMap(s => s.tech_stack || []))].sort();
            const techFilter = document.getElementById('techFilter');
            technologies.forEach(tech => {{
                const option = document.createElement('option');
                option.value = tech;
                option.textContent = tech;
                techFilter.appendChild(option);
            }});
        }}

        function applyFilters() {{
            const industryFilter = document.getElementById('industryFilter').value;
            const techFilter = document.getElementById('techFilter').value;
            const searchQuery = document.getElementById('searchInput').value.toLowerCase();
            const sortFilter = document.getElementById('sortFilter').value;

            // Filter
            filteredStudies = caseStudies.filter(study => {{
                // Industry filter
                if (industryFilter && study.industry !== industryFilter) return false;

                // Technology filter
                if (techFilter && (!study.tech_stack || !study.tech_stack.includes(techFilter))) return false;

                // Search filter
                if (searchQuery) {{
                    const searchText = `${{study.project_name}} ${{study.description}} ${{study.industry}}`.toLowerCase();
                    if (!searchText.includes(searchQuery)) return false;
                }}

                return true;
            }});

            // Sort
            filteredStudies.sort((a, b) => {{
                switch(sortFilter) {{
                    case 'date-desc':
                        return new Date(b.date_created) - new Date(a.date_created);
                    case 'date-asc':
                        return new Date(a.date_created) - new Date(b.date_created);
                    case 'name-asc':
                        return a.project_name.localeCompare(b.project_name);
                    case 'name-desc':
                        return b.project_name.localeCompare(a.project_name);
                    case 'usecases-desc':
                        return b.use_case_count - a.use_case_count;
                    case 'usecases-asc':
                        return a.use_case_count - b.use_case_count;
                    default:
                        return 0;
                }}
            }});

            renderGallery();
        }}

        function clearFilters() {{
            document.getElementById('industryFilter').value = '';
            document.getElementById('techFilter').value = '';
            document.getElementById('searchInput').value = '';
            document.getElementById('sortFilter').value = 'date-desc';
            applyFilters();
        }}

        function renderGallery() {{
            const gallery = document.getElementById('gallery');
            const emptyState = document.getElementById('emptyState');
            const resultsCount = document.getElementById('resultsCount');

            // Update results count
            resultsCount.textContent = `Showing ${{filteredStudies.length}} of ${{caseStudies.length}} case studies`;

            if (filteredStudies.length === 0) {{
                gallery.style.display = 'none';
                emptyState.style.display = 'block';
                return;
            }}

            gallery.style.display = 'grid';
            emptyState.style.display = 'none';
            gallery.innerHTML = '';

            filteredStudies.forEach(study => {{
                const card = createCaseStudyCard(study);
                gallery.appendChild(card);
            }});
        }}

        function createCaseStudyCard(study) {{
            const card = document.createElement('div');
            card.className = 'case-study-card';

            // Format date
            const date = new Date(study.date_created);
            const formattedDate = date.toLocaleDateString('en-US', {{ year: 'numeric', month: 'short', day: 'numeric' }});

            // Tech stack HTML
            const techStackHTML = (study.tech_stack || []).map(tech =>
                `<span class="tech-tag">${{tech}}</span>`
            ).join('');

            card.innerHTML = `
                <div class="industry-badge">${{study.industry}}</div>
                <h3 class="card-title">${{study.project_name}}</h3>
                <p class="card-description">${{study.description || 'No description available'}}</p>
                ${{techStackHTML ? `<div class="tech-stack">${{techStackHTML}}</div>` : ''}}
                <div class="card-meta">
                    <div class="meta-info">
                        <div class="meta-item">
                            <span>📅</span>
                            <span>${{formattedDate}}</span>
                        </div>
                        <div class="meta-item">
                            <span>📋</span>
                            <span>${{study.use_case_count}} use cases</span>
                        </div>
                    </div>
                </div>
                <button class="view-button" onclick="viewMockup('${{study.mockup_url}}')" ${{!study.has_mockup ? 'disabled' : ''}}>
                    ${{study.has_mockup ? 'View Mockup →' : 'No Mockup'}}
                </button>
            `;

            return card;
        }}

        function viewMockup(url) {{
            if (url) {{
                window.location.href = url;
            }}
        }}
    </script>
</body>
</html>"""

        return html

    async def _generate_gallery_html_old(self, case_studies: List[Dict]) -> str:
        """Generate the gallery HTML using LLM (OLD METHOD - kept for reference)"""

        # Prepare case studies data for the prompt
        case_studies_json = json.dumps(case_studies, indent=2)

        system_message = """You are a world-class UI/UX designer specializing in Apple-style, minimalist web design with UC001 AICOE branding.
You create beautiful, modern, responsive HTML pages with clean aesthetics, Lucide icons, and excellent user experience."""

        user_message = f"""Create a stunning Case Study Gallery page with UC001 AICOE branding.

CASE STUDIES DATA:
{case_studies_json}

MANDATORY UC001 AICOE DESIGN REQUIREMENTS:
1. Color Palette (STRICT):
   - Primary: #0066cc (AICOE Blue)
   - Accent: #00d9ff (Bright Cyan)
   - Dark: #1d1d1f (Almost Black)
   - Gray: #6e6e73 (Medium Gray)
   - Light Gray: #f5f5f7 (Background)
   - White: #ffffff
   - Success: #34c759
   - Warning: #ff9500

2. Typography:
   - Font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
   - Headings: Bold, clean, generous spacing
   - Body: 16px base, 1.6 line-height

3. Layout:
   - Sticky navigation bar with AICOE logo and "Case Study Gallery" title
   - Hero section with title "AICOE Case Study Gallery" and subtitle
   - Filter bar with: Industry dropdown, Technology dropdown, Search box, Sort dropdown
   - Responsive grid of case study cards (3 columns on desktop, 2 on tablet, 1 on mobile)
   - Each card should have: Project name, Description, Industry badge, Tech stack tags, Use case count, Date, "View Mockup" button

4. Card Design:
   - White background with subtle shadow
   - Hover effect: lift up slightly with stronger shadow
   - Rounded corners (12px)
   - Padding: 24px
   - Industry badge: colored pill at top
   - Tech stack: small gray pills
   - "View Mockup" button: AICOE blue, white text, rounded

5. Filters & Search (MUST IMPLEMENT):
   - Industry filter: dropdown with all unique industries from data
   - Technology filter: dropdown with all unique technologies from data
   - Search: real-time filter by project name, description
   - Sort: by date (newest/oldest), by name (A-Z/Z-A), by use cases (most/least)
   - "Clear Filters" button
   - Show count: "Showing X of Y case studies"

6. JavaScript Functionality (CRITICAL):
   - Implement filter logic for industry, technology, search
   - Implement sort logic
   - Show/hide cards based on filters
   - Update count dynamically
   - Smooth animations for filtering
   - Click on card to navigate to mockup_url

7. Icons:
   - Use Lucide icons (loaded from CDN)
   - Search icon, filter icon, calendar icon, layers icon (for use cases)

8. Responsive Design:
   - Mobile-first approach
   - Breakpoints: 768px (tablet), 1024px (desktop)
   - Touch-friendly buttons (min 44px height)

9. Empty State:
   - If no case studies match filters, show friendly message with icon

IMPORTANT: Return ONLY the complete HTML code, starting with <!DOCTYPE html>.
Include ALL JavaScript for filtering, searching, and sorting inline in <script> tags.
The HTML must be production-ready, fully functional, and visually stunning.
NO explanations, NO markdown code blocks, JUST the raw HTML."""

        response = await self._call_llm(
            system_message,
            user_message,
            max_tokens=16000
        )
        
        # Clean response
        html_content = response.strip()
        if html_content.startswith("```html"):
            html_content = html_content.split("```html")[1].split("```")[0].strip()
        elif html_content.startswith("```"):
            html_content = html_content.split("```")[1].split("```")[0].strip()
        
        return html_content

