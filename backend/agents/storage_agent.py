"""
Storage/Collaboration Agent - Manages project folders, versioning, and file storage
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentConfig, AgentResult
from datetime import datetime
from pathlib import Path
import json
import os


class ProjectStructure:
    """Represents the project folder structure as per PRD"""
    def __init__(self, project_name: str, base_path: str = "./projects"):
        self.project_name = project_name
        self.base_path = Path(base_path)
        self.project_root = self.base_path / self._sanitize_name(project_name)
        
        # Define folder structure from PRD (with new specialized folders)
        self.folders = {
            "root": self.project_root,
            "transcripts": self.project_root / "MeetingTranscripts",
            "notes": self.project_root / "MeetingNotes",
            "research": self.project_root / "ResearchFindings",
            "use_cases": self.project_root / "UseCases",
            "synthetic_data": self.project_root / "SyntheticData",

            # NEW: Case Studies folder structure (replaces old HTML/Version1/Mockups)
            "case_studies": self.project_root / "CaseStudies",

            # Document folders
            "prd": self.project_root / "PRDDocuments",
            "architecture": self.project_root / "SystemArchitecture",
            "commercial_proposals": self.project_root / "CommercialProposals",
            "bom": self.project_root / "BillOfMaterials",

            # Other folders
            "feedback": self.project_root / "ReviewerFeedback",
            "audit": self.project_root / "AuditLogs"
        }
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for filesystem"""
        return "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
    
    def create_structure(self):
        """Create the complete folder structure"""
        for folder_path in self.folders.values():
            folder_path.mkdir(parents=True, exist_ok=True)
        return True
    
    def get_path(self, folder_key: str) -> Path:
        """Get path for a specific folder"""
        return self.folders.get(folder_key, self.project_root)

    def create_use_case_folder(self, use_case_id: str, use_case_name: str) -> Path:
        """
        Create a folder for a specific use case within CaseStudies

        Args:
            use_case_id: Use case ID (e.g., "UC-001")
            use_case_name: Use case name (e.g., "Secure User Registration")

        Returns:
            Path to the created use case folder
        """
        # Sanitize use case name for folder
        sanitized_name = self._sanitize_name(use_case_name)
        folder_name = f"{use_case_id}_{sanitized_name}"

        # Create folder path
        use_case_folder = self.folders["case_studies"] / folder_name
        use_case_folder.mkdir(parents=True, exist_ok=True)

        return use_case_folder

    async def _create_use_case_folder_action(
        self,
        project_name: str,
        use_case_id: str,
        use_case_name: str
    ) -> AgentResult:
        """Action handler for creating use case folder"""
        if project_name not in self.projects:
            await self._create_project(project_name)

        project = self.projects[project_name]
        use_case_folder = project.create_use_case_folder(use_case_id, use_case_name)

        return AgentResult(
            success=True,
            data={
                "project_name": project_name,
                "use_case_id": use_case_id,
                "folder_path": str(use_case_folder)
            },
            metadata={"agent": self.config.name, "action": "create_use_case_folder"}
        )


class StorageAgent(BaseAgent):
    """
    Agent responsible for managing project folders, file storage, and versioning
    Implements the folder structure from the PRD
    """
    
    def __init__(self, llm_client, base_storage_path: str = "./projects"):
        config = AgentConfig(
            name="StorageAgent",
            description="Manages project folders, versioning, and file storage",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.3,
            max_tokens=12000
        )
        super().__init__(config, llm_client)
        self.base_storage_path = base_storage_path
        self.projects: Dict[str, ProjectStructure] = {}
        self.version_history: Dict[str, List[Dict]] = {}
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Manage storage operations
        
        Input:
            - action: "create_project", "save_file", "get_file", "list_files", "create_version"
            - project_name: Name of the project
            - Additional parameters based on action
            
        Output:
            - Result of the storage operation
        """
        try:
            self.log_execution("start", "Processing storage operation")
            self.validate_input(input_data, ["action", "project_name"])
            
            action = input_data["action"]
            project_name = input_data["project_name"]
            
            if action == "create_project":
                result = await self._create_project(project_name)
            elif action == "save_file":
                result = await self._save_file(
                    project_name,
                    input_data["folder"],
                    input_data["filename"],
                    input_data["content"],
                    input_data.get("subfolder")  # Optional subfolder parameter
                )
            elif action == "get_file":
                result = await self._get_file(
                    project_name,
                    input_data["folder"],
                    input_data["filename"]
                )
            elif action == "list_files":
                result = await self._list_files(
                    project_name,
                    input_data.get("folder", "root")
                )
            elif action == "create_version":
                result = await self._create_version(
                    project_name,
                    input_data.get("version_info", {})
                )
            elif action == "get_structure":
                result = await self._get_project_structure(project_name)
            elif action == "create_use_case_folder":
                result = await self._create_use_case_folder_action(
                    project_name,
                    input_data["use_case_id"],
                    input_data["use_case_name"]
                )
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in StorageAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
    
    async def _create_project(self, project_name: str) -> AgentResult:
        """Create a new project with folder structure"""
        try:
            project_structure = ProjectStructure(project_name, self.base_storage_path)
            project_structure.create_structure()
            
            self.projects[project_name] = project_structure
            
            # Create initial audit log
            audit_log = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "project_created",
                "project_name": project_name,
                "user": "system"
            }
            
            audit_path = project_structure.get_path("audit") / "audit_log.json"
            with open(audit_path, 'w') as f:
                json.dump([audit_log], f, indent=2)
            
            self.log_execution("success", f"Created project structure for {project_name}")
            
            # Communicate with other agents
            self.log_execution("communication", "Notifying agents of new project structure")
            
            return AgentResult(
                success=True,
                data={
                    "project_name": project_name,
                    "project_root": str(project_structure.project_root),
                    "folders_created": list(project_structure.folders.keys()),
                    "audit_log": audit_log
                },
                metadata={"agent": self.config.name, "action": "create_project"}
            )
            
        except Exception as e:
            raise Exception(f"Failed to create project: {str(e)}")
    
    async def _save_file(
        self,
        project_name: str,
        folder: str,
        filename: str,
        content: Any,
        subfolder: str = None
    ) -> AgentResult:
        """Save a file to the project structure (optionally in a subfolder)"""
        if project_name not in self.projects:
            await self._create_project(project_name)

        project = self.projects[project_name]
        folder_path = project.get_path(folder)

        # If subfolder is specified, create it and use it
        if subfolder:
            folder_path = folder_path / subfolder
            folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / filename
        
        # Determine file type and save accordingly
        if isinstance(content, bytes):
            # Binary content (e.g., PDF files)
            with open(file_path, 'wb') as f:
                f.write(content)
        elif isinstance(content, (dict, list)):
            # JSON content
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
        else:
            # Text content
            with open(file_path, 'w') as f:
                f.write(str(content))
        
        # Log to audit
        await self._log_audit(project_name, "file_saved", {
            "folder": folder,
            "filename": filename,
            "size": os.path.getsize(file_path)
        })
        
        self.log_execution("success", f"Saved {filename} to {folder}")
        
        return AgentResult(
            success=True,
            data={
                "project_name": project_name,
                "folder": folder,
                "filename": filename,
                "file_path": str(file_path),
                "size": os.path.getsize(file_path)
            },
            metadata={"agent": self.config.name, "action": "save_file"}
        )
    
    async def _get_file(
        self,
        project_name: str,
        folder: str,
        filename: str
    ) -> AgentResult:
        """Retrieve a file from the project structure"""
        if project_name not in self.projects:
            raise ValueError(f"Project not found: {project_name}")
        
        project = self.projects[project_name]
        folder_path = project.get_path(folder)
        file_path = folder_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        if filename.endswith('.json'):
            with open(file_path, 'r') as f:
                content = json.load(f)
        else:
            with open(file_path, 'r') as f:
                content = f.read()
        
        return AgentResult(
            success=True,
            data={
                "project_name": project_name,
                "folder": folder,
                "filename": filename,
                "content": content
            },
            metadata={"agent": self.config.name, "action": "get_file"}
        )
    
    async def _list_files(self, project_name: str, folder: str) -> AgentResult:
        """List files in a project folder"""
        if project_name not in self.projects:
            raise ValueError(f"Project not found: {project_name}")
        
        project = self.projects[project_name]
        folder_path = project.get_path(folder)
        
        files = []
        if folder_path.exists():
            files = [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
                }
                for f in folder_path.iterdir()
                if f.is_file()
            ]
        
        return AgentResult(
            success=True,
            data={
                "project_name": project_name,
                "folder": folder,
                "files": files,
                "count": len(files)
            },
            metadata={"agent": self.config.name, "action": "list_files"}
        )
    
    async def _create_version(
        self,
        project_name: str,
        version_info: Dict
    ) -> AgentResult:
        """Create a new version of project artifacts"""
        if project_name not in self.version_history:
            self.version_history[project_name] = []
        
        version_entry = {
            "version": len(self.version_history[project_name]) + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "info": version_info
        }
        
        self.version_history[project_name].append(version_entry)
        
        # Log to audit
        await self._log_audit(project_name, "version_created", version_entry)
        
        return AgentResult(
            success=True,
            data=version_entry,
            metadata={"agent": self.config.name, "action": "create_version"}
        )
    
    async def _get_project_structure(self, project_name: str) -> AgentResult:
        """Get the complete project structure"""
        if project_name not in self.projects:
            await self._create_project(project_name)
        
        project = self.projects[project_name]
        
        structure = {
            "project_name": project_name,
            "project_root": str(project.project_root),
            "folders": {
                key: str(path) for key, path in project.folders.items()
            }
        }
        
        return AgentResult(
            success=True,
            data=structure,
            metadata={"agent": self.config.name, "action": "get_structure"}
        )
    
    async def _log_audit(self, project_name: str, action: str, details: Dict):
        """Log an action to the audit log"""
        if project_name not in self.projects:
            return
        
        project = self.projects[project_name]
        audit_path = project.get_path("audit") / "audit_log.json"
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "user": "system"
        }
        
        # Read existing log
        audit_log = []
        if audit_path.exists():
            with open(audit_path, 'r') as f:
                audit_log = json.load(f)
        
        # Append new entry
        audit_log.append(audit_entry)
        
        # Write back
        with open(audit_path, 'w') as f:
            json.dump(audit_log, f, indent=2)

