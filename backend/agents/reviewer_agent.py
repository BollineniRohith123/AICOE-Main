"""
Reviewer Agent - Manages feedback loops and document review cycles
Enhanced with HTML validation and UC001 styling compliance checks
"""
from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent, AgentConfig, AgentResult
from datetime import datetime
import json
import os
import re
from pathlib import Path


class ReviewCycle:
    """Represents a review cycle for a document"""
    def __init__(
        self,
        document_id: str,
        document_type: str,
        version: int,
        reviewer: str
    ):
        self.document_id = document_id
        self.document_type = document_type
        self.version = version
        self.reviewer = reviewer
        self.feedback_items: List[Dict] = []
        self.status = "pending"  # pending, in_review, approved, rejected
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()


class ReviewerAgent(BaseAgent):
    """
    Agent responsible for managing review cycles, feedback, and document approval
    Supports annotation, accept/reject, and regeneration workflows
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="ReviewerAgent",
            description="Manages feedback loops, document review cycles, and HTML validation",
            model="x-ai/grok-code-fast-1",  # OpenAI GPT-OSS-120B via OpenRouter
            temperature=0.5,
            max_tokens=12000
        )
        super().__init__(config, llm_client)
        self.review_cycles: Dict[str, ReviewCycle] = {}
        self.feedback_history: List[Dict] = []
        self.validation_results: Dict[str, Dict] = {}
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Process review feedback and manage review cycles
        
        Input:
            - action: "create_review", "add_feedback", "approve", "reject", "request_regeneration"
            - document_id: ID of the document being reviewed
            - document_type: Type of document (prd, mockup, etc.)
            - feedback: Optional feedback data
            - reviewer: Name of the reviewer
            
        Output:
            - review_status: Current status of the review
            - feedback_summary: Summary of feedback
            - next_actions: Recommended next steps
        """
        try:
            self.log_execution("start", "Processing review action")
            self.validate_input(input_data, ["action", "document_id", "document_type"])
            
            action = input_data["action"]
            document_id = input_data["document_id"]
            document_type = input_data["document_type"]
            reviewer = input_data.get("reviewer", "Anonymous")
            
            # Communicate with other agents
            self.log_execution("communication", f"Processing {action} for {document_type}")
            
            if action == "create_review":
                result = await self._create_review_cycle(
                    document_id, document_type, reviewer, input_data
                )
            elif action == "add_feedback":
                result = await self._add_feedback(
                    document_id, input_data.get("feedback", {}), reviewer
                )
            elif action == "approve":
                result = await self._approve_document(document_id, reviewer)
            elif action == "reject":
                result = await self._reject_document(
                    document_id, input_data.get("reason", ""), reviewer
                )
            elif action == "request_regeneration":
                result = await self._request_regeneration(
                    document_id, input_data.get("feedback", {}), reviewer
                )
            elif action == "analyze_feedback":
                result = await self._analyze_feedback(document_id, input_data)
            elif action == "validate_all_files":
                result = await self._validate_all_files(input_data)
            else:
                raise ValueError(f"Unknown action: {action}")

            return result

        except Exception as e:
            self.logger.error(f"Error in ReviewerAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )

    async def _validate_all_files(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Validate all generated HTML files for UC001 styling compliance and completeness

        Input:
            - project_name: Name of the project
            - project_path: Path to the project directory

        Output:
            - validation_results: Dictionary of validation results for each file
            - all_passed: Boolean indicating if all files passed validation
            - failed_files: List of files that failed validation
            - issues: List of all issues found
        """
        try:
            project_name = input_data.get("project_name", "")
            project_path = input_data.get("project_path", "")

            if not project_path or not os.path.exists(project_path):
                raise ValueError(f"Invalid project path: {project_path}")

            self.log_execution("start", f"Validating all HTML files for project: {project_name}")

            # Define files to validate
            files_to_validate = {
                "PRD": os.path.join(project_path, "PRDDocuments", "PRD_v1.html"),
                "Commercial Proposal": os.path.join(project_path, "CommercialProposals", "proposal_v1.html"),
                "BOM": os.path.join(project_path, "BillOfMaterials", "bom_v1.html"),
                "Architecture Diagram": os.path.join(project_path, "ArchitectureDiagrams", "architecture_v1.html"),
            }

            # Add mockup files
            mockups_dir = os.path.join(project_path, "HTML", "Version1", "Mockups")
            if os.path.exists(mockups_dir):
                for file in os.listdir(mockups_dir):
                    if file.endswith(".html"):
                        files_to_validate[f"Mockup: {file}"] = os.path.join(mockups_dir, file)

            validation_results = {}
            all_issues = []
            failed_files = []

            # Validate each file
            for file_name, file_path in files_to_validate.items():
                self.log_execution("validation", f"Validating {file_name}")

                if not os.path.exists(file_path):
                    validation_results[file_name] = {
                        "passed": False,
                        "issues": [f"File not found: {file_path}"],
                        "file_path": file_path
                    }
                    failed_files.append(file_name)
                    all_issues.append(f"{file_name}: File not found")
                    continue

                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Validate HTML structure and UC001 styling
                issues = self._validate_html_file(content, file_name)

                passed = len(issues) == 0
                validation_results[file_name] = {
                    "passed": passed,
                    "issues": issues,
                    "file_path": file_path,
                    "file_size": len(content)
                }

                if not passed:
                    failed_files.append(file_name)
                    all_issues.extend([f"{file_name}: {issue}" for issue in issues])

            all_passed = len(failed_files) == 0

            self.log_execution(
                "success" if all_passed else "warning",
                f"Validation complete: {len(validation_results) - len(failed_files)}/{len(validation_results)} files passed"
            )

            return AgentResult(
                success=True,
                data={
                    "validation_results": validation_results,
                    "all_passed": all_passed,
                    "failed_files": failed_files,
                    "issues": all_issues,
                    "total_files": len(validation_results),
                    "passed_files": len(validation_results) - len(failed_files)
                },
                metadata={
                    "agent": self.config.name,
                    "action": "validate_all_files",
                    "project_name": project_name
                }
            )

        except Exception as e:
            self.logger.error(f"Error validating files: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )

    def _validate_html_file(self, content: str, file_name: str) -> List[str]:
        """
        Validate a single HTML file for UC001 styling compliance

        Returns:
            List of issues found (empty list if validation passes)
        """
        issues = []

        # Check 1: Valid HTML structure
        if not content.strip().upper().startswith("<!DOCTYPE HTML"):
            issues.append("Missing or invalid DOCTYPE declaration")

        if "<html" not in content.lower():
            issues.append("Missing <html> tag")

        if "<head>" not in content.lower():
            issues.append("Missing <head> tag")

        if "<body>" not in content.lower():
            issues.append("Missing <body> tag")

        # Check 2: UC001 Color Palette
        uc001_colors = [
            "--primary-navy",
            "--accent-pink",
            "--accent-cyan",
            "--text-primary",
            "--bg-white",
            "--bg-gray"
        ]

        missing_colors = []
        for color in uc001_colors:
            if color not in content:
                missing_colors.append(color)

        if missing_colors:
            issues.append(f"Missing UC001 color variables: {', '.join(missing_colors)}")

        # Check 3: Lucide Icons Integration
        if "lucide" not in content.lower():
            issues.append("Missing Lucide Icons CDN or initialization")

        # Check 4: Responsive Design
        if "@media" not in content.lower():
            issues.append("Missing responsive design (@media queries)")

        # Check 5: Print Styles
        if "@media print" not in content.lower():
            issues.append("Missing print-friendly CSS (@media print)")

        # Check 6: Font Smoothing
        if "-webkit-font-smoothing" not in content:
            issues.append("Missing font smoothing (-webkit-font-smoothing)")

        # Check 7: UC001 Shadows
        if "--shadow" not in content:
            issues.append("Missing UC001 shadow variables (--shadow, --shadow-hover)")

        # Check 8: Gradient Text (for headers)
        if "gradient" not in content.lower() and "PRD" in file_name or "Proposal" in file_name:
            issues.append("Missing gradient text effects for headings")

        # Check 9: Border Radius
        if "border-radius" not in content.lower():
            issues.append("Missing border-radius styling")

        # Check 10: Content Completeness (basic check)
        if len(content) < 1000:
            issues.append(f"File appears incomplete (only {len(content)} characters)")

        return issues
    
    async def _create_review_cycle(
        self,
        document_id: str,
        document_type: str,
        reviewer: str,
        input_data: Dict
    ) -> AgentResult:
        """Create a new review cycle"""
        version = input_data.get("version", 1)
        
        review_cycle = ReviewCycle(document_id, document_type, version, reviewer)
        self.review_cycles[document_id] = review_cycle
        
        self.log_execution("success", f"Created review cycle for {document_id}")
        
        return AgentResult(
            success=True,
            data={
                "review_cycle_id": document_id,
                "status": "pending",
                "version": version,
                "reviewer": reviewer,
                "created_at": review_cycle.created_at
            },
            metadata={"agent": self.config.name, "action": "create_review"}
        )
    
    async def _add_feedback(
        self,
        document_id: str,
        feedback: Dict,
        reviewer: str
    ) -> AgentResult:
        """Add feedback to a review cycle"""
        if document_id not in self.review_cycles:
            raise ValueError(f"No review cycle found for document: {document_id}")
        
        review_cycle = self.review_cycles[document_id]
        
        feedback_item = {
            "reviewer": reviewer,
            "timestamp": datetime.utcnow().isoformat(),
            "feedback": feedback
        }
        
        review_cycle.feedback_items.append(feedback_item)
        review_cycle.status = "in_review"
        review_cycle.updated_at = datetime.utcnow().isoformat()
        
        self.feedback_history.append(feedback_item)
        
        self.log_execution("success", f"Added feedback to {document_id}")
        
        return AgentResult(
            success=True,
            data={
                "review_cycle_id": document_id,
                "status": review_cycle.status,
                "feedback_count": len(review_cycle.feedback_items)
            },
            metadata={"agent": self.config.name, "action": "add_feedback"}
        )
    
    async def _approve_document(self, document_id: str, reviewer: str) -> AgentResult:
        """Approve a document"""
        if document_id not in self.review_cycles:
            raise ValueError(f"No review cycle found for document: {document_id}")
        
        review_cycle = self.review_cycles[document_id]
        review_cycle.status = "approved"
        review_cycle.updated_at = datetime.utcnow().isoformat()
        
        self.log_execution("success", f"Approved document {document_id}")
        
        # Notify other agents
        self.log_execution("communication", "Notifying agents of approval")
        
        return AgentResult(
            success=True,
            data={
                "review_cycle_id": document_id,
                "status": "approved",
                "reviewer": reviewer,
                "approved_at": review_cycle.updated_at
            },
            metadata={"agent": self.config.name, "action": "approve"}
        )
    
    async def _reject_document(
        self,
        document_id: str,
        reason: str,
        reviewer: str
    ) -> AgentResult:
        """Reject a document"""
        if document_id not in self.review_cycles:
            raise ValueError(f"No review cycle found for document: {document_id}")
        
        review_cycle = self.review_cycles[document_id]
        review_cycle.status = "rejected"
        review_cycle.updated_at = datetime.utcnow().isoformat()
        
        self.log_execution("success", f"Rejected document {document_id}")
        
        return AgentResult(
            success=True,
            data={
                "review_cycle_id": document_id,
                "status": "rejected",
                "reason": reason,
                "reviewer": reviewer,
                "rejected_at": review_cycle.updated_at
            },
            metadata={"agent": self.config.name, "action": "reject"}
        )
    
    async def _request_regeneration(
        self,
        document_id: str,
        feedback: Dict,
        reviewer: str
    ) -> AgentResult:
        """Request document regeneration with feedback"""
        if document_id not in self.review_cycles:
            raise ValueError(f"No review cycle found for document: {document_id}")
        
        review_cycle = self.review_cycles[document_id]
        
        # Add feedback
        await self._add_feedback(document_id, feedback, reviewer)
        
        self.log_execution("communication", "Requesting regeneration from relevant agents")
        
        return AgentResult(
            success=True,
            data={
                "review_cycle_id": document_id,
                "status": "regeneration_requested",
                "feedback": feedback,
                "next_version": review_cycle.version + 1
            },
            metadata={"agent": self.config.name, "action": "request_regeneration"}
        )
    
    async def _analyze_feedback(
        self,
        document_id: str,
        input_data: Dict
    ) -> AgentResult:
        """Analyze feedback using LLM to generate actionable insights"""
        if document_id not in self.review_cycles:
            raise ValueError(f"No review cycle found for document: {document_id}")
        
        review_cycle = self.review_cycles[document_id]
        
        system_message = """You are an expert at analyzing review feedback and generating actionable insights.
Your task is to synthesize feedback from multiple reviewers and provide clear, prioritized recommendations."""
        
        user_message = f"""Analyze the following review feedback:

Document Type: {review_cycle.document_type}
Version: {review_cycle.version}

Feedback Items:
{json.dumps(review_cycle.feedback_items, indent=2)}

Please provide:
1. Summary of key themes in the feedback
2. Prioritized list of changes needed
3. Suggestions for improvement
4. Estimated impact of each change

Return in JSON format with keys: summary, priority_changes, suggestions, impact_analysis"""

        self.log_execution("llm_call", "Analyzing feedback")
        response = await self._call_llm(system_message, user_message)
        
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response.split("```json")[1].split("```")[0].strip()
            elif response.startswith("```"):
                response = response.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(response)
            
            return AgentResult(
                success=True,
                data={
                    "review_cycle_id": document_id,
                    "analysis": analysis,
                    "feedback_count": len(review_cycle.feedback_items)
                },
                metadata={"agent": self.config.name, "action": "analyze_feedback"}
            )
            
        except json.JSONDecodeError:
            return AgentResult(
                success=True,
                data={
                    "review_cycle_id": document_id,
                    "analysis": {"raw_response": response}
                },
                metadata={"agent": self.config.name}
            )

