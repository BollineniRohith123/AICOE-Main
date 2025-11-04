# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

AICOE (AI Center of Excellence) is a multi-agent AI automation platform that transforms meeting transcripts into comprehensive product deliverables. The system uses 12+ specialized AI agents orchestrated through a Google ADK-inspired architecture to generate PRDs, mockups, proposals, architecture diagrams, and more in under 30 minutes.

**Key Technologies:**
- Backend: Python 3.8+, FastAPI, OpenRouter API
- Frontend: React 19, Tailwind CSS, Radix UI
- Architecture: Multi-agent orchestration with shared workflow context
- Communication: REST API + WebSocket for real-time updates

## Common Commands

### Starting/Stopping the Platform

```bash
# Start both backend and frontend
./start.sh

# Check server status
./status.sh

# Stop all servers
./stop.sh

# Full restart
./stop.sh && sleep 2 && ./start.sh
```

### Backend Development

```bash
# Manual backend start (for development with live logs)
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Run backend tests
cd backend
source venv/bin/activate
pytest tests/

# Install/update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Check backend health
curl http://localhost:8000/health
```

### Frontend Development

```bash
# Manual frontend start (for development with live logs)
cd frontend
npm start

# Run frontend tests
cd frontend
npm test

# Build for production
cd frontend
npm run build

# Install/update frontend dependencies
cd frontend
npm install
```

### Debugging

```bash
# View live backend logs
tail -f logs/backend.log

# View live frontend logs
tail -f logs/frontend.log

# Search for errors
grep -i error logs/backend.log
grep -i error logs/frontend.log

# Check ports
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill stuck processes
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :3000 | xargs kill -9  # Frontend
```

### Testing Individual Components

```bash
# Test specific agent (after starting backend)
curl -X POST http://localhost:8000/api/transcript/process \
  -H "Content-Type: application/json" \
  -d '{"transcript": "test transcript content"}'

# Test WebSocket connection (in browser console)
# const ws = new WebSocket('ws://localhost:8000/api/ws/test-workflow');

# Test API endpoints
curl http://localhost:8000/api/projects
curl http://localhost:8000/api/agents/status
```

## Architecture

### Multi-Agent Orchestration System

The platform uses a **Google ADK-inspired orchestration pattern** where specialized agents collaborate through a shared `WorkflowContext`:

```
User Upload → Intake Agent → Orchestrator → [12 Specialized Agents] → Results
                                  ↓
                          WorkflowContext (Shared State)
                                  ↓
                    Agent Communication Hub → Real-time WebSocket Updates
```

**Key Architecture Components:**

1. **OrchestratorAgent** (`backend/agents/orchestrator.py`): Coordinates agent execution, manages dependencies, handles errors, and tracks workflow progress. The orchestrator can run agents sequentially or in parallel based on dependencies.

2. **WorkflowContext** (`backend/agents/workflow_context.py`): Shared context object that enables cross-agent collaboration. Each agent can access outputs from previous agents, maintaining consistency across the entire workflow. This is critical for design system consistency in HTML-generating agents.

3. **BaseAgent** (`backend/agents/base_agent.py`): Abstract base class for all agents with common functionality including LLM calls with retry logic, input validation, and workflow context integration.

4. **Agent Communication Hub** (`backend/agents/agent_communication.py`): Message-passing system for inter-agent communication and status broadcasting.

5. **Storage Agent** (`backend/agents/storage_agent.py`): Manages all file I/O operations and project data persistence in the `storage/` directory.

### The 12 Specialized Agents

Each agent is a self-contained module in `backend/agents/`:

- **IntakeAgent**: Processes raw transcripts into structured notes (XML)
- **ResearcherAgent**: Gathers industry insights and competitive analysis (JSON)
- **BlueprintAgent**: Generates use cases and requirements (JSON)
- **KnowledgeBaseAgent**: Provides domain expertise and best practices
- **PRDAgent**: Creates Product Requirements Documents (HTML + XML)
- **MockupAgent**: Builds interactive HTML prototypes with Apple-inspired design
- **DataAgent**: Generates synthetic demo data for testing
- **ProposalAgent**: Creates commercial proposals with pricing (HTML + XML)
- **BOMAgent**: Generates Bill of Materials with cost estimates (HTML + XML)
- **ArchitectureAgent**: Designs system architecture diagrams (HTML + XML)
- **ReviewerAgent**: Performs quality assurance on all outputs (JSON)
- **CaseStudyGalleryAgent**: Curates case study gallery (HTML)

### Design System Consistency

**CRITICAL**: All HTML-generating agents (PRD, Mockup, Proposal, BOM, Architecture, Gallery) MUST use the **unified AICOE design system** defined in `backend/agents/design_system.py`. The WorkflowContext automatically injects design guidelines into each agent's prompt to ensure visual consistency.

**Design System Elements:**
- **Colors**: `#1a1a2e` (Navy), `#ff69b4` (Pink), `#00ffcc` (Cyan), `#00e5b3` (Turquoise)
- **Typography**: SF Pro Display with fluid sizing using `clamp()`
- **Spacing**: 8px grid system
- **Components**: Apple-inspired cards, buttons, smooth animations
- **Icons**: Lucide React icons for consistency

### WebSocket Real-Time Updates

The system uses WebSocket connections (`/api/ws/{workflow_id}`) to stream real-time progress updates to the frontend as agents execute. Each agent broadcasts status messages through the orchestrator to connected clients.

### Frontend Architecture

**Component Organization:**
- `src/pages/`: Main page components (Home, TranscriptInput, ProcessingView, Results)
- `src/components/`: Reusable UI components (AgentProgress, AgentCommunication, ProjectFolderTree)
- `src/components/ui/`: Shadcn/Radix UI primitive components
- `src/hooks/`: Custom React hooks

**State Management:**
- Local state for UI interactions
- WebSocket connection for real-time agent updates
- LocalStorage for workflow ID persistence

## Development Workflow

### Adding a New Agent

1. Create new agent file in `backend/agents/` inheriting from `BaseAgent`
2. Implement `execute()` method with agent-specific logic
3. Register agent in `orchestrator.py` agents dictionary
4. Add agent to workflow execution sequence in orchestrator
5. Update frontend `ProcessingView.js` to display new agent status

### Modifying Agent Execution Order

Edit `backend/agents/orchestrator.py` in the `execute_workflow()` method. Agents are executed sequentially by default, but you can modify dependencies to enable parallel execution.

### Working with WorkflowContext

When an agent needs data from previous agents:

```python
# In any agent's execute() method
context = self.workflow_context.get_full_context(current_agent=self.config.name)
previous_outputs = context["all_agent_outputs"]
prd_content = self.workflow_context.get_agent_output("prd")
```

### Environment Configuration

**Backend** (`backend/.env`):
```bash
OPENROUTER_API_KEY=your_api_key_here
```

**Frontend** (`frontend/.env` - optional):
```bash
REACT_APP_BACKEND_URL=http://localhost:8000
```

### LLM Client Architecture

The `LLMClient` (`backend/agents/llm_client.py`) supports:
- Per-agent model selection (different models for different agents)
- Automatic retry logic with exponential backoff
- OpenRouter API integration
- Fallback model configuration

## Common Patterns

### Creating HTML-Generating Agents

When creating or modifying agents that generate HTML (PRD, Mockup, Proposal, etc.):

1. **Always** access design system via WorkflowContext
2. Include design system prompt in LLM call
3. Reference previous agent outputs for consistency
4. Use the standard HTML structure with embedded CSS
5. Include Lucide icons via CDN

### Error Handling

All agents implement retry logic (default 3 attempts). Non-retryable errors (auth, API key issues) fail immediately. Retryable errors use exponential backoff.

### Progress Tracking

Agents broadcast progress updates via the orchestrator:
- Status: "pending", "running", "completed", "failed"
- Progress percentage (0-100)
- Status messages for user feedback

### Storage Patterns

All file operations go through `StorageAgent`:
- Project data: `storage/{project_id}/`
- Results: `storage/{project_id}/results/`
- Logs: `logs/`

## Testing

### Manual Testing Workflow

1. Start platform: `./start.sh`
2. Open frontend: http://localhost:3000
3. Upload test transcript: `test-transcript.txt` or `test_transcript_messy.txt`
4. Monitor agent progress in real-time
5. View results in Results Playground
6. Check logs: `tail -f logs/backend.log logs/frontend.log`

### API Documentation

When backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Important Files

- `backend/server.py`: FastAPI application entry point, API routes, WebSocket handling
- `backend/agents/orchestrator.py`: Multi-agent workflow coordination
- `backend/agents/workflow_context.py`: Shared context system
- `backend/agents/design_system.py`: AICOE design system definition
- `frontend/src/App.js`: React application root with routing
- `frontend/src/pages/ProcessingView.js`: Real-time agent progress visualization
- `start.sh`, `stop.sh`, `status.sh`: Platform management scripts

## Troubleshooting

### Port Already in Use
```bash
lsof -ti :8000 | xargs kill -9  # Backend
lsof -ti :3000 | xargs kill -9  # Frontend
./start.sh
```

### WebSocket Connection Failed
1. Verify backend is running on port 8000
2. Check browser console for CORS errors
3. Verify firewall not blocking WebSocket connections

### Agent Execution Timeout
1. Check OpenRouter API key has sufficient credits
2. Review `logs/backend.log` for specific errors
3. Verify internet connectivity
4. Check agent timeout settings in `base_agent.py`

### Design Inconsistency in Generated HTML
This typically means an agent isn't properly accessing WorkflowContext design guidelines. Check that the agent:
1. Has `self.workflow_context` available
2. Calls `get_full_context()` to retrieve design system
3. Includes design prompt in LLM system message

## Key Dependencies

**Backend:**
- `fastapi==0.110.1`: Web framework
- `uvicorn==0.25.0`: ASGI server
- `websockets==15.0.1`: WebSocket support
- `openai==2.6.1`: LLM API client
- `pydantic==2.12.3`: Data validation
- `python-dotenv==1.2.1`: Environment configuration

**Frontend:**
- `react==19.0.0`: UI library
- `react-router-dom==7.5.1`: Routing
- `axios==1.8.4`: HTTP client
- `@radix-ui/*`: Accessible UI components
- `tailwindcss==3.4.17`: Styling
- `lucide-react==0.507.0`: Icons

## Additional Resources

- **START_HERE.md**: Quick start guide with pre-flight checks
- **COMMANDS.md**: Comprehensive command reference
- **STARTUP_GUIDE.md**: Detailed startup instructions
- **README.md**: Full project documentation
- **AICOE_Platform_PRD.md**: Product requirements document
