from fastapi import (
    FastAPI,
    HTTPException,
    BackgroundTasks,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from both backend/.env and repo root .env (if present)
BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

# Backend .env
load_dotenv(os.path.join(BASE_DIR, ".env"))
# Root .env
load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Global storage for workflow connections and state
active_workflows = {}  # workflow_id -> {"ws": websocket, "data": workflow_data}
workflow_states = {}  # workflow_id -> {"status": "running/completed/failed", "results": {}, "progress": []}

# Import agents
from agents.orchestrator import OrchestratorAgent
from agents.agent_communication import AgentCommunicationHub
from agents.storage_agent import StorageAgent
from agents.researcher_agent import ResearcherAgent
from agents.prd_agent import PRDAgent
from agents.architecture_agent import ArchitectureAgent
from agents.mockup_agent import MockupAgent
from agents.proposal_agent import ProposalAgent
from agents.reviewer_agent import ReviewerAgent
from agents.knowledge_base_agent import KnowledgeBaseAgent
from agents.bom_agent import BOMAgent
from agents.data_agent import DataAgent
from agents.blueprint_agent import BlueprintAgent
from agents.gallery_agent import CaseStudyGalleryAgent
from agents.intake_agent import IntakeAgent
from agents.llm_client import LLMClient

app = FastAPI(
    title="AICOE Automation Platform",
    description="AI Center of Excellence - Intelligent Project Automation",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize LLM client (fallback to mock if API key missing)
if not os.getenv("OPENROUTER_API_KEY"):
    print("WARNING: OPENROUTER_API_KEY not set. Using mock LLM client.")
    from agents.llm_client_mock import LLMClient as MockLLMClient

    llm_client = MockLLMClient()
else:
    llm_client = LLMClient()

# Initialize agents
orchestrator = OrchestratorAgent(llm_client)

# Initialize individual agents (for direct access if needed)
agent_comm = AgentCommunicationHub()
storage_agent = StorageAgent(llm_client, base_storage_path="storage")
researcher_agent = ResearcherAgent(llm_client)
prd_agent = PRDAgent(llm_client)
architecture_agent = ArchitectureAgent(llm_client)
mockup_agent = MockupAgent(llm_client)
proposal_agent = ProposalAgent(llm_client)
reviewer_agent = ReviewerAgent(llm_client)
knowledge_base_agent = KnowledgeBaseAgent(llm_client)
bom_agent = BOMAgent(llm_client)
data_agent = DataAgent(llm_client)
blueprint_agent = BlueprintAgent(llm_client)
gallery_agent = CaseStudyGalleryAgent(llm_client)
intake_agent = IntakeAgent(llm_client)


# Pydantic models
class ProjectRequest(BaseModel):
    project_name: str
    description: str
    requirements: Optional[str] = None
    industry: Optional[str] = None
    budget: Optional[float] = None
    timeline: Optional[str] = None


class TranscriptRequest(BaseModel):
    transcript: str
    project_id: Optional[str] = None


class AgentStatus(BaseModel):
    agent_name: str
    status: str
    progress: float
    message: Optional[str] = None


class ProjectStatus(BaseModel):
    project_id: str
    status: str
    progress: float
    current_agent: Optional[str] = None
    agents_status: List[AgentStatus]
    created_at: datetime
    updated_at: datetime


# Routes
@app.get("/")
async def root():
    return {
        "message": "AICOE Automation Platform API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}


@app.post("/api/projects/create")
async def create_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    try:
        # Create project using orchestrator
        project_id = await orchestrator.create_project(
            name=request.project_name,
            description=request.description,
            requirements=request.requirements,
            industry=request.industry,
            budget=request.budget,
            timeline=request.timeline,
        )

        # Start background processing
        background_tasks.add_task(process_project, project_id)

        return {
            "project_id": project_id,
            "status": "created",
            "message": "Project created successfully. Processing started.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/status")
async def get_project_status(project_id: str):
    try:
        status = await orchestrator.get_project_status(project_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Project not found: {str(e)}")


@app.get("/api/projects")
async def list_projects():
    try:
        projects = await storage_agent.list_projects()
        return {"projects": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/transcript/process")
async def process_transcript(
    request: TranscriptRequest, background_tasks: BackgroundTasks
):
    try:
        # Process transcript using intake agent
        result = await intake_agent.process_transcript(
            transcript=request.transcript, project_id=request.project_id
        )

        if request.project_id:
            # Start background processing for existing project
            background_tasks.add_task(process_project, request.project_id)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/status")
async def get_agents_status():
    try:
        # Get status of all agents
        agents_status = agent_comm.get_all_agents_status()
        return {"agents": agents_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background task function
async def process_project(project_id: str):
    try:
        await orchestrator.process_project(project_id)
    except Exception as e:
        print(f"Error processing project {project_id}: {str(e)}")


# WebSocket endpoint for real-time workflow updates
@app.websocket("/api/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    await websocket.accept()
    print(f"WebSocket connection accepted for workflow: {workflow_id}")

    # Store the connection
    active_workflows[workflow_id] = {"ws": websocket, "data": None}

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            action = data.get("action")

            print(f"Received WebSocket message: {data}")

            if action == "start":
                # Start a new workflow
                project_name = data.get("project_name")
                transcript = data.get("transcript")

                if not project_name or not transcript:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Missing project_name or transcript",
                        }
                    )
                    continue

                # Store workflow data
                active_workflows[workflow_id]["data"] = {
                    "project_name": project_name,
                    "transcript": transcript,
                }

                # Initialize workflow state
                workflow_states[workflow_id] = {
                    "status": "running",
                    "results": {},
                    "progress": [],
                    "current_agent": None,
                    "agent_statuses": {},
                }

                # Start workflow in background
                asyncio.create_task(
                    execute_workflow(workflow_id, project_name, transcript)
                )

            elif action == "reconnect":
                # Handle reconnection - send current state
                print(f"Reconnection request for workflow: {workflow_id}")

                if workflow_id in workflow_states:
                    state = workflow_states[workflow_id]
                    await websocket.send_json(
                        {
                            "type": "reconnect_ack",
                            "message": f"Reconnected to workflow {workflow_id}",
                            "status": state["status"],
                            "current_agent": state.get("current_agent"),
                            "agent_statuses": state.get("agent_statuses", {}),
                            "results": state.get("results")
                            if state["status"] == "completed"
                            else None,
                        }
                    )

                    # Resend progress messages
                    for progress_msg in state.get("progress", []):
                        await websocket.send_json(progress_msg)
                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Workflow {workflow_id} not found",
                        }
                    )

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for workflow: {workflow_id}")
        # Keep workflow state but remove connection
        if workflow_id in active_workflows:
            del active_workflows[workflow_id]
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.send_json(
            {"type": "error", "message": f"WebSocket error: {str(e)}"}
        )


# Function to execute workflow with progress updates
async def execute_workflow(workflow_id: str, project_name: str, transcript: str):
    """Execute the workflow and send real-time updates via WebSocket"""

    async def progress_callback(progress_data):
        """Callback to send progress updates to WebSocket"""
        if workflow_id in active_workflows:
            try:
                # Update workflow state
                if workflow_id in workflow_states:
                    workflow_states[workflow_id]["current_agent"] = progress_data.get(
                        "stage"
                    )
                    workflow_states[workflow_id]["agent_statuses"][
                        progress_data.get("stage")
                    ] = {
                        "status": progress_data.get("status"),
                        "message": progress_data.get("message"),
                        "timestamp": progress_data.get("timestamp"),
                    }
                    workflow_states[workflow_id]["progress"].append(
                        {"type": "progress", **progress_data}
                    )

                # Send to WebSocket
                ws = active_workflows[workflow_id]["ws"]
                await ws.send_json({"type": "progress", **progress_data})
                print(
                    f"Sent progress update: {progress_data.get('stage')} - {progress_data.get('status')}"
                )
            except Exception as e:
                print(f"Failed to send progress update: {str(e)}")

    try:
        # Execute the workflow with progress callback
        print(f"Starting workflow execution for: {project_name}")
        result = await orchestrator.execute_workflow(
            project_name=project_name,
            transcript=transcript,
            workflow_type="full",
            progress_callback=progress_callback,
        )

        # Update workflow state
        workflow_states[workflow_id]["status"] = "completed"
        workflow_states[workflow_id]["results"] = result

        # Send completion message
        if workflow_id in active_workflows:
            ws = active_workflows[workflow_id]["ws"]
            await ws.send_json(
                {
                    "type": "complete",
                    "message": "Workflow completed successfully",
                    "project_name": project_name,
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "results": result.get("results", {}),
                }
            )
            print(f"Workflow completed: {workflow_id}")

    except Exception as e:
        print(f"Workflow execution failed: {str(e)}")
        import traceback

        traceback.print_exc()

        # Update workflow state
        workflow_states[workflow_id]["status"] = "failed"

        # Send error message
        if workflow_id in active_workflows:
            try:
                ws = active_workflows[workflow_id]["ws"]
                await ws.send_json(
                    {"type": "error", "message": f"Workflow failed: {str(e)}"}
                )
            except:
                pass


# Get workflow status endpoint
@app.get("/api/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """Get the current status of a workflow"""
    if workflow_id not in workflow_states:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    state = workflow_states[workflow_id]
    return {
        "workflow_id": workflow_id,
        "status": state["status"],
        "current_agent": state.get("current_agent"),
        "agent_statuses": state.get("agent_statuses", {}),
        "results": state.get("results") if state["status"] == "completed" else None,
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": True,
        "message": exc.detail,
        "status_code": exc.status_code
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return {
        "error": True,
        "message": "Internal server error",
        "details": str(exc)
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True, log_level="info")
