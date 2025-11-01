from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import aiofiles
import asyncio

# Import multi-agent system
from agents.llm_client import LLMClient
from agents.orchestrator import OrchestratorAgent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize LLM Client and Orchestrator
# Using OpenRouter API with GLM-4.6 model (NO GPT models)
llm_client = LLMClient(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    provider="openrouter",
    model="x-ai/grok-code-fast-1"
)
orchestrator = OrchestratorAgent(llm_client, db)

# Storage directory for project artifacts
STORAGE_DIR = ROOT_DIR / "storage"
STORAGE_DIR.mkdir(exist_ok=True)

# Workflow state tracking to prevent duplicate executions
active_workflows = {}  # {workflow_id: {"status": "running"|"completed"|"failed", "task": asyncio.Task}}

# Create the main app without a prefix
app = FastAPI(title="AICOE Automation Platform API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.workflow_status: Dict[str, Dict[str, Any]] = {}

    async def connect(self, workflow_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[workflow_id] = websocket
        logging.info(f"WebSocket connected for workflow: {workflow_id}")

    def disconnect(self, workflow_id: str):
        if workflow_id in self.active_connections:
            del self.active_connections[workflow_id]
            logging.info(f"WebSocket disconnected for workflow: {workflow_id}")

    async def send_progress(self, workflow_id: str, data: Dict[str, Any]):
        """Send progress update to connected client"""
        if workflow_id in self.active_connections:
            try:
                await self.active_connections[workflow_id].send_json(data)
                logging.debug(f"Sent progress update for {workflow_id}: {data.get('stage', 'unknown')}")
            except Exception as e:
                logging.error(f"Error sending progress update: {str(e)}")
                self.disconnect(workflow_id)

    def update_status(self, workflow_id: str, status: Dict[str, Any]):
        """Update workflow status"""
        self.workflow_status[workflow_id] = status

    def get_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        return self.workflow_status.get(workflow_id)

manager = ConnectionManager()


# ===== MODELS =====

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class ProcessTranscriptRequest(BaseModel):
    project_name: str = Field(..., min_length=1, description="Name of the project")
    transcript: str = Field(..., min_length=10, description="Meeting transcript text")

class ProcessTranscriptResponse(BaseModel):
    project_id: str
    project_name: str
    status: str
    message: str
    workflow_id: str

class ProjectResponse(BaseModel):
    project_id: str
    project_name: str
    status: str
    created_at: str
    workflow_id: str
    results: Optional[Dict[str, Any]] = None


# ===== ROUTES =====

@api_router.get("/")
async def root():
    return {
        "message": "AICOE Automation Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

@api_router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow
    Returns workflow state, completed agents, and results
    """
    try:
        # Check if workflow exists in active workflows
        if workflow_id in active_workflows:
            workflow_state = active_workflows[workflow_id]

            # Get workflow status from manager
            workflow_status = manager.workflow_status.get(workflow_id, {})

            return {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "project_name": workflow_state.get("project_name"),
                "start_time": workflow_state.get("start_time").isoformat() if workflow_state.get("start_time") else None,
                "end_time": workflow_state.get("end_time").isoformat() if workflow_state.get("end_time") else None,
                "completed_agents": workflow_status.get("completed_agents", []),
                "current_agent": workflow_status.get("current_agent"),
                "agent_statuses": workflow_status.get("agent_statuses", {}),
                "results": workflow_status.get("results"),
                "error": workflow_state.get("error")
            }
        else:
            # Workflow not found in active workflows
            return {
                "workflow_id": workflow_id,
                "status": "not_found",
                "message": "Workflow not found. It may have been cleaned up or never existed."
            }

    except Exception as e:
        logger.error(f"Error retrieving workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve workflow status: {str(e)}")

@api_router.post("/process-transcript")
async def process_transcript(request: ProcessTranscriptRequest):
    """
    Process a meeting transcript through the multi-agent workflow
    Returns workflow_id immediately, client should connect to WebSocket for progress
    """
    try:
        logger.info(f"Processing transcript for project: {request.project_name}")

        # Generate project ID and workflow ID
        project_id = str(uuid.uuid4())
        workflow_id = f"workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{project_id[:8]}"

        # Return immediately with workflow_id
        # Client will connect to WebSocket for progress updates
        return {
            "project_id": project_id,
            "project_name": request.project_name,
            "status": "started",
            "message": "Workflow started. Connect to WebSocket for progress updates.",
            "workflow_id": workflow_id
        }

    except Exception as e:
        logger.error(f"Error starting workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")

@api_router.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """
    WebSocket endpoint for real-time workflow progress updates
    """
    logger.info(f"WebSocket connected for workflow: {workflow_id}")
    await manager.connect(workflow_id, websocket)

    try:
        # Wait for start message from client
        logger.info(f"Waiting for start message from client for workflow: {workflow_id}")
        data = await websocket.receive_json()
        logger.info(f"Received message from client: {data}")

        action = data.get("action")

        # Handle reconnection - don't restart workflow
        if action == "reconnect":
            logger.info(f"Client reconnecting to workflow: {workflow_id}")

            # Check if workflow is still running
            if workflow_id in active_workflows:
                workflow_state = active_workflows[workflow_id]
                await websocket.send_json({
                    "type": "reconnect_ack",
                    "status": workflow_state["status"],
                    "message": f"Reconnected to workflow. Status: {workflow_state['status']}"
                })
            else:
                await websocket.send_json({
                    "type": "reconnect_ack",
                    "status": "unknown",
                    "message": "Workflow not found in active workflows. It may have completed."
                })

            # Continue to keep connection alive section below
            # The workflow will continue sending progress updates through the manager

        elif action == "start":
            # Check if workflow is already running
            if workflow_id in active_workflows:
                workflow_state = active_workflows[workflow_id]
                if workflow_state["status"] == "running":
                    logger.warning(f"Workflow {workflow_id} is already running. Ignoring duplicate start request.")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Workflow is already running. Please wait for it to complete."
                    })
                    return

            project_name = data.get("project_name")
            transcript = data.get("transcript")

            if not project_name or not transcript:
                logger.error(f"Missing project_name or transcript for workflow: {workflow_id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Missing project_name or transcript"
                })
                return

            logger.info(f"Starting workflow for project: {project_name}")

            # Mark workflow as running
            active_workflows[workflow_id] = {
                "status": "running",
                "project_name": project_name,
                "start_time": datetime.utcnow()
            }

            # Initialize workflow status tracking
            manager.workflow_status[workflow_id] = {
                "completed_agents": [],
                "current_agent": None,
                "agent_statuses": {},
                "results": {}
            }

            # Create progress callback
            async def progress_callback(progress_data):
                # CRITICAL: Check if connection is still alive before proceeding
                # This prevents workflows from continuing after client disconnect
                if workflow_id in active_workflow_tasks:
                    task_info = active_workflow_tasks[workflow_id]
                    connection_alive = task_info["connection_alive"]

                    if not connection_alive["alive"]:
                        logger.warning(f"🛑 Connection dead for workflow {workflow_id} - raising CancelledError")
                        raise asyncio.CancelledError("Client disconnected")

                # Update workflow status in manager
                stage = progress_data.get("stage")
                status = progress_data.get("status")

                if stage and stage != "workflow":
                    # Update current agent
                    if status == "running":
                        manager.workflow_status[workflow_id]["current_agent"] = stage

                    # Update agent status
                    manager.workflow_status[workflow_id]["agent_statuses"][stage] = status

                    # Add to completed agents if completed
                    if status == "completed" and stage not in manager.workflow_status[workflow_id]["completed_agents"]:
                        manager.workflow_status[workflow_id]["completed_agents"].append(stage)

                # Send progress update to client
                await manager.send_progress(workflow_id, {
                    "type": "progress",
                    **progress_data
                })

            # Execute workflow with progress callback
            # CRITICAL: Wrap workflow execution in a task so we can cancel it if needed
            try:
                # Create a flag to track if connection is still alive
                connection_alive = {"alive": True}

                # Create workflow task
                workflow_task = asyncio.create_task(
                    orchestrator.execute_workflow(
                        project_name=project_name,
                        transcript=transcript,
                        workflow_type="full",
                        progress_callback=progress_callback
                    )
                )

                # Store task and connection state for potential cancellation
                active_workflow_tasks[workflow_id] = {
                    "task": workflow_task,
                    "connection_alive": connection_alive
                }

                # CRITICAL: Create a background monitor task that checks connection health
                # This ensures workflows are cancelled immediately when connection dies
                async def connection_monitor():
                    """Monitor connection and cancel workflow if it dies"""
                    while not workflow_task.done():
                        await asyncio.sleep(0.5)  # Check every 500ms

                        # CRITICAL: Actively check if WebSocket is still connected
                        # Check the client_state to see if connection is still open
                        try:
                            # Check if websocket is still connected
                            if websocket.client_state.name != "CONNECTED":
                                logger.warning(f"🛑 Connection monitor detected dead connection for {workflow_id} (state: {websocket.client_state.name}) - cancelling workflow")
                                connection_alive["alive"] = False
                                workflow_task.cancel()
                                break
                        except Exception as e:
                            logger.warning(f"🛑 Connection monitor error checking state for {workflow_id}: {str(e)} - cancelling workflow")
                            connection_alive["alive"] = False
                            workflow_task.cancel()
                            break

                        # Also check the flag in case it was set elsewhere
                        if not connection_alive["alive"]:
                            logger.warning(f"🛑 Connection monitor detected dead connection for {workflow_id} (flag set) - cancelling workflow")
                            workflow_task.cancel()
                            break

                # Start the monitor task
                monitor_task = asyncio.create_task(connection_monitor())

                # Wait for workflow to complete
                workflow_result = await workflow_task

                # Cancel monitor task if workflow completes normally
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

                # Update workflow state to completed
                if workflow_id in active_workflows:
                    active_workflows[workflow_id]["status"] = "completed"
                    active_workflows[workflow_id]["end_time"] = datetime.utcnow()

                # Mark connection as no longer alive
                connection_alive["alive"] = False

                # Remove from active tasks
                if workflow_id in active_workflow_tasks:
                    del active_workflow_tasks[workflow_id]

                # Use project name for folder (sanitized)
                # This matches what StorageAgent does
                def sanitize_name(name: str) -> str:
                    return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)

                project_id = sanitize_name(project_name)

                # Project directory is already created by StorageAgent
                project_dir = STORAGE_DIR / project_id

                # Save artifacts
                artifacts = {}

                # PRD files are already saved by orchestrator to PRDDocuments folder
                # Just reference them in artifacts
                if "prd" in workflow_result.get("results", {}):
                    prd_html_file = project_dir / "PRDDocuments" / "PRD_v1.html"
                    prd_xml_file = project_dir / "PRDDocuments" / "PRD_v1.xml"
                    if prd_html_file.exists():
                        artifacts["prd"] = str(prd_html_file)
                    if prd_xml_file.exists():
                        artifacts["prd_xml"] = str(prd_xml_file)

                # Mockup files are already saved by orchestrator to CaseStudies folder
                # Just reference them in artifacts
                if "mockup" in workflow_result.get("results", {}):
                    case_studies_dir = project_dir / "CaseStudies"
                    mockup_index = case_studies_dir / "index.html"
                    if mockup_index.exists():
                        artifacts["mockup"] = str(mockup_index)
                        artifacts["case_studies_index"] = str(mockup_index)

                    # Reference all mockup pages (both single-page and multi-screen)
                    mockup_data = workflow_result["results"]["mockup"]
                    mockup_pages = mockup_data.get("mockup_pages", {})
                    use_case_structure = mockup_data.get("use_case_structure", {})

                    if isinstance(mockup_pages, dict):
                        for page_name in mockup_pages.keys():
                            if page_name == "index.html":
                                continue  # Already referenced above

                            # Check if this is a multi-screen use case
                            if "_" in page_name:
                                uc_id = page_name.split("_")[0]
                                uc_info = use_case_structure.get("use_cases", {}).get(uc_id, {})
                                is_multi_screen = uc_info.get("type") == "multi-screen"

                                if is_multi_screen:
                                    # File is in subfolder: CaseStudies/UC-001/screen-01.html
                                    page_file = case_studies_dir / uc_id / page_name.replace(f"{uc_id}_", "")
                                else:
                                    # File is in root: CaseStudies/UC-001_mockup.html
                                    page_file = case_studies_dir / page_name

                                if page_file.exists():
                                    artifacts[f"mockup_{page_name}"] = str(page_file)

                # Commercial Proposal files are already saved by orchestrator to CommercialProposals folder
                # Just reference them in artifacts
                if "commercial_proposal" in workflow_result.get("results", {}):
                    proposal_html_file = project_dir / "CommercialProposals" / "proposal_v1.html"
                    proposal_xml_file = project_dir / "CommercialProposals" / "proposal_v1.xml"
                    if proposal_html_file.exists():
                        artifacts["commercial_proposal"] = str(proposal_html_file)
                    if proposal_xml_file.exists():
                        artifacts["commercial_proposal_xml"] = str(proposal_xml_file)

                # BOM files are already saved by orchestrator to BillOfMaterials folder
                # Just reference them in artifacts
                if "bom" in workflow_result.get("results", {}):
                    bom_html_file = project_dir / "BillOfMaterials" / "bom_v1.html"
                    bom_xml_file = project_dir / "BillOfMaterials" / "bom_v1.xml"
                    if bom_html_file.exists():
                        artifacts["bom"] = str(bom_html_file)
                    if bom_xml_file.exists():
                        artifacts["bom_xml"] = str(bom_xml_file)

                # Architecture files are already saved by orchestrator to SystemArchitecture folder
                # Just reference them in artifacts
                if "architecture_diagram" in workflow_result.get("results", {}):
                    arch_html_file = project_dir / "SystemArchitecture" / "architecture_v1.html"
                    arch_xml_file = project_dir / "SystemArchitecture" / "architecture_v1.xml"
                    if arch_html_file.exists():
                        artifacts["architecture_diagram"] = str(arch_html_file)
                    if arch_xml_file.exists():
                        artifacts["architecture_xml"] = str(arch_xml_file)

                # Save complete workflow results
                results_file = project_dir / "workflow_results.json"
                async with aiofiles.open(results_file, 'w') as f:
                    await f.write(json.dumps(workflow_result, indent=2, default=str))

                # Store project metadata in database
                project_doc = {
                    "id": project_id,
                    "project_name": project_name,
                    "workflow_id": workflow_id,
                    "status": workflow_result["status"],
                    "created_at": datetime.utcnow().isoformat(),
                    "artifacts": artifacts,
                    "results": workflow_result["results"],
                    "context": workflow_result["context"]
                }

                await db.projects.insert_one(project_doc)

                # Store final results in manager for state persistence
                manager.workflow_status[workflow_id]["results"] = workflow_result["results"]

                # Send completion message
                await websocket.send_json({
                    "type": "complete",
                    "project_id": project_id,
                    "workflow_id": workflow_id,
                    "status": workflow_result["status"],
                    "results": workflow_result["results"]
                })

            except asyncio.CancelledError:
                # Workflow was cancelled (e.g., server shutdown or client disconnect)
                logger.warning(f"Workflow {workflow_id} was cancelled")

                # Update workflow state to failed
                if workflow_id in active_workflows:
                    active_workflows[workflow_id]["status"] = "cancelled"
                    active_workflows[workflow_id]["error"] = "Workflow cancelled"
                    active_workflows[workflow_id]["end_time"] = datetime.utcnow()

                # Remove from active tasks
                if workflow_id in active_workflow_tasks:
                    del active_workflow_tasks[workflow_id]

                await websocket.send_json({
                    "type": "error",
                    "message": "Workflow was cancelled"
                })

            except Exception as e:
                logger.error(f"Workflow execution error: {str(e)}")

                # Update workflow state to failed
                if workflow_id in active_workflows:
                    active_workflows[workflow_id]["status"] = "failed"
                    active_workflows[workflow_id]["error"] = str(e)
                    active_workflows[workflow_id]["end_time"] = datetime.utcnow()

                # Remove from active tasks
                if workflow_id in active_workflow_tasks:
                    del active_workflow_tasks[workflow_id]

                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })

        # Keep connection alive and handle disconnects
        # CRITICAL: The while loop below is NOT reliable for detecting disconnects
        # because WebSocketDisconnect is only raised on abrupt disconnections.
        # The connection monitor task (created above) is the primary mechanism
        # for detecting and cancelling workflows when the connection dies.
        while True:
            try:
                message = await websocket.receive_text()
                if message == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected (abrupt) for workflow: {workflow_id}")

                # CRITICAL: Cancel workflow if client disconnects to prevent orphaned API calls
                if workflow_id in active_workflow_tasks:
                    task_info = active_workflow_tasks[workflow_id]
                    task = task_info["task"]
                    connection_alive = task_info["connection_alive"]

                    # Mark connection as dead
                    connection_alive["alive"] = False

                    if not task.done():
                        logger.warning(f"🛑 Cancelling workflow {workflow_id} due to client disconnect")
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            logger.info(f"✅ Workflow {workflow_id} cancelled successfully")
                        except Exception as e:
                            logger.error(f"❌ Error cancelling workflow {workflow_id}: {str(e)}")
                    del active_workflow_tasks[workflow_id]

                # Update workflow state to cancelled
                if workflow_id in active_workflows:
                    active_workflows[workflow_id]["status"] = "cancelled"
                    active_workflows[workflow_id]["error"] = "Client disconnected"
                    active_workflows[workflow_id]["end_time"] = datetime.utcnow()

                manager.disconnect(workflow_id)
                break
            except Exception as e:
                # Handle any other exceptions (including connection errors)
                logger.warning(f"WebSocket error in keepalive loop for {workflow_id}: {str(e)}")

                # Mark connection as dead
                if workflow_id in active_workflow_tasks:
                    task_info = active_workflow_tasks[workflow_id]
                    connection_alive = task_info["connection_alive"]
                    connection_alive["alive"] = False

                break

    except WebSocketDisconnect:
        # This should not be reached anymore since we handle it in the inner loop
        logger.info(f"WebSocket disconnected (outer handler) for workflow: {workflow_id}")
        manager.disconnect(workflow_id)

    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {str(e)}")

        # Cancel workflow task if it exists
        if workflow_id in active_workflow_tasks:
            task_info = active_workflow_tasks[workflow_id]
            task = task_info["task"]
            connection_alive = task_info["connection_alive"]

            # Mark connection as dead
            connection_alive["alive"] = False

            if not task.done():
                logger.warning(f"Cancelling workflow {workflow_id} due to error")
                task.cancel()
            del active_workflow_tasks[workflow_id]

        # Update workflow state to failed if it was running
        if workflow_id in active_workflows and active_workflows[workflow_id]["status"] == "running":
            active_workflows[workflow_id]["status"] = "failed"
            active_workflows[workflow_id]["error"] = str(e)
            active_workflows[workflow_id]["end_time"] = datetime.utcnow()

        manager.disconnect(workflow_id)

    finally:
        # Ensure workflow task is cleaned up
        if workflow_id in active_workflow_tasks:
            task_info = active_workflow_tasks[workflow_id]
            task = task_info["task"]
            connection_alive = task_info["connection_alive"]

            # Mark connection as dead
            connection_alive["alive"] = False

            if not task.done():
                logger.warning(f"🧹 Cleaning up workflow {workflow_id} in finally block")
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"✅ Workflow {workflow_id} cleaned up successfully")
                except Exception as e:
                    logger.error(f"❌ Error cleaning up workflow {workflow_id}: {str(e)}")
            del active_workflow_tasks[workflow_id]

@api_router.get("/workflow/{workflow_id}/status")
async def get_workflow_status(workflow_id: str):
    """
    Get the current status of a workflow
    """
    try:
        if workflow_id in active_workflows:
            workflow_state = active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": workflow_state["status"],
                "project_name": workflow_state.get("project_name"),
                "start_time": workflow_state.get("start_time").isoformat() if workflow_state.get("start_time") else None,
                "end_time": workflow_state.get("end_time").isoformat() if workflow_state.get("end_time") else None,
                "error": workflow_state.get("error")
            }
        else:
            # Check database for completed workflows
            workflow = await db.workflows.find_one({"_id": workflow_id}, {"_id": 0})
            if workflow:
                return {
                    "workflow_id": workflow_id,
                    "status": workflow.get("status", "unknown"),
                    "project_name": workflow.get("project_name"),
                    "message": "Workflow found in database"
                }
            else:
                raise HTTPException(status_code=404, detail="Workflow not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """
    Get project details and results
    """
    try:
        # Find project in database
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/projects")
async def list_projects():
    """
    List all projects
    """
    try:
        projects = await db.projects.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return {"projects": projects, "count": len(projects)}
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/download/{project_id}/{artifact_type}")
async def download_artifact(project_id: str, artifact_type: str):
    """
    Download a specific artifact (prd or mockup)
    """
    try:
        # Get project from database
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get artifact path
        artifacts = project.get("artifacts", {})
        
        if artifact_type not in artifacts:
            raise HTTPException(status_code=404, detail=f"Artifact '{artifact_type}' not found")
        
        file_path = Path(artifacts[artifact_type])
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        # Determine filename and media type
        if artifact_type == "prd":
            filename = f"{project['project_name']}-PRD.html"
            media_type = "text/html"
        elif artifact_type == "prd_xml":
            filename = f"{project['project_name']}-PRD.xml"
            media_type = "application/xml"
        elif artifact_type == "mockup":
            filename = f"{project['project_name']}-Mockup.html"
            media_type = "text/html"
        elif artifact_type == "commercial_proposal":
            filename = f"{project['project_name']}-Proposal.html"
            media_type = "text/html"
        elif artifact_type == "commercial_proposal_xml":
            filename = f"{project['project_name']}-Proposal.xml"
            media_type = "application/xml"
        elif artifact_type == "bom":
            filename = f"{project['project_name']}-BOM.html"
            media_type = "text/html"
        elif artifact_type == "bom_xml":
            filename = f"{project['project_name']}-BOM.xml"
            media_type = "application/xml"
        elif artifact_type == "architecture_diagram":
            filename = f"{project['project_name']}-Architecture.html"
            media_type = "text/html"
        elif artifact_type == "architecture_xml":
            filename = f"{project['project_name']}-Architecture.xml"
            media_type = "application/xml"
        else:
            filename = file_path.name
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading artifact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Track active workflow tasks for cancellation (must be defined before shutdown handler)
active_workflow_tasks = {}  # {workflow_id: asyncio.Task}

@app.on_event("shutdown")
async def shutdown_event():
    """
    Graceful shutdown: Cancel all running workflows and close database connection
    This prevents API calls from continuing after server shutdown
    """
    logger.info("🛑 Server shutdown initiated - cancelling all active workflows")

    # Cancel all active workflow tasks
    for workflow_id, task_info in list(active_workflow_tasks.items()):
        task = task_info["task"]
        connection_alive = task_info["connection_alive"]

        # Mark connection as dead
        connection_alive["alive"] = False

        if not task.done():
            logger.warning(f"Cancelling workflow {workflow_id} due to server shutdown")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Workflow {workflow_id} cancelled successfully")
            except Exception as e:
                logger.error(f"Error cancelling workflow {workflow_id}: {str(e)}")

    # Clear active workflows
    active_workflows.clear()
    active_workflow_tasks.clear()

    # Close database connection
    client.close()
    logger.info("✅ Server shutdown complete - all workflows cancelled, database closed")