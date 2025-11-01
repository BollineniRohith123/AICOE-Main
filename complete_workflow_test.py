#!/usr/bin/env python3
"""
Complete Workflow Testing for AICOE Automation Platform

This script tests the complete end-to-end workflow including:
- WebSocket connection and real-time updates
- Full 12-agent workflow execution with real OpenRouter LLM
- Artifact generation and verification
- Database persistence
- File system verification
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path
from datetime import datetime
import sys
import os
import websockets
from websockets.exceptions import ConnectionClosed

# Configuration
BACKEND_URL = "https://test-bug-fixer.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
WS_BASE = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
TEST_TRANSCRIPT_FILE = "/app/test_transcript_ui_test.txt"

class CompleteWorkflowTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.project_id = None
        self.workflow_id = None
        self.workflow_results = None
        self.agent_progress = {}
        self.completed_agents = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name, success, details, response_data=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
    
    async def load_test_transcript(self):
        """Load test transcript from file"""
        try:
            with open(TEST_TRANSCRIPT_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            self.log_result("Load Transcript", False, f"Failed to load transcript: {str(e)}")
            return None
    
    async def test_api_health(self):
        """Test API health before starting workflow"""
        try:
            async with self.session.get(f"{API_BASE}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "running":
                        self.log_result("API Health Check", True, "Backend API is running", data)
                        return True
                    else:
                        self.log_result("API Health Check", False, f"Unexpected status: {data.get('status')}", data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("API Health Check", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Connection error: {str(e)}")
            return False
    
    async def start_workflow(self):
        """Start the workflow via POST /api/process-transcript"""
        try:
            transcript = await self.load_test_transcript()
            if not transcript:
                return False
            
            test_data = {
                "project_name": "Complete Test - Task Management App",
                "transcript": transcript
            }
            
            async with self.session.post(f"{API_BASE}/process-transcript", json=test_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if "project_id" in data and "workflow_id" in data:
                        self.project_id = data["project_id"]
                        self.workflow_id = data["workflow_id"]
                        self.log_result("Start Workflow", True, "Workflow initiated successfully", {
                            "project_id": self.project_id,
                            "workflow_id": self.workflow_id,
                            "status": data.get("status")
                        })
                        return True
                    else:
                        self.log_result("Start Workflow", False, "Missing project_id or workflow_id", data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("Start Workflow", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Start Workflow", False, f"Error: {str(e)}")
            return False
    
    async def test_websocket_workflow(self):
        """Test complete workflow execution via WebSocket"""
        if not self.workflow_id:
            self.log_result("WebSocket Workflow", False, "No workflow_id available")
            return False
        
        try:
            ws_url = f"{WS_BASE}/api/ws/{self.workflow_id}"
            print(f"🔌 Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                self.log_result("WebSocket Connection", True, "Connected to WebSocket successfully")
                
                # Load transcript for workflow execution
                transcript = await self.load_test_transcript()
                if not transcript:
                    return False
                
                # Send start message
                start_message = {
                    "action": "start",
                    "project_name": "Complete Test - Task Management App",
                    "transcript": transcript
                }
                
                await websocket.send(json.dumps(start_message))
                print(f"📤 Sent start message for workflow: {self.workflow_id}")
                
                # Track workflow progress
                workflow_complete = False
                workflow_success = False
                start_time = time.time()
                timeout = 300  # 5 minutes timeout
                
                expected_agents = [
                    "storage", "transcript", "researcher", "requirements", 
                    "knowledge_base", "prd", "mockup", "synthetic_data",
                    "commercial_proposal", "bom", "architecture", "gallery"
                ]
                
                print(f"🎯 Expected agents: {', '.join(expected_agents)}")
                print(f"⏱️  Starting workflow execution (timeout: {timeout}s)")
                print("=" * 60)
                
                while not workflow_complete and (time.time() - start_time) < timeout:
                    try:
                        # Wait for message with timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        data = json.loads(message)
                        
                        message_type = data.get("type")
                        
                        if message_type == "progress":
                            stage = data.get("stage")
                            status = data.get("status")
                            
                            if stage and stage != "workflow":
                                # Update agent progress
                                self.agent_progress[stage] = status
                                
                                if status == "running":
                                    print(f"🔄 {stage.upper()} Agent: Starting...")
                                elif status == "completed":
                                    if stage not in self.completed_agents:
                                        self.completed_agents.append(stage)
                                    print(f"✅ {stage.upper()} Agent: Completed ({len(self.completed_agents)}/{len(expected_agents)})")
                                elif status == "failed":
                                    print(f"❌ {stage.upper()} Agent: Failed - {data.get('message', 'Unknown error')}")
                            
                            # Check if workflow stage update
                            if stage == "workflow" and status in ["completed", "failed"]:
                                workflow_complete = True
                                workflow_success = (status == "completed")
                                print(f"🏁 Workflow {status.upper()}")
                        
                        elif message_type == "complete":
                            workflow_complete = True
                            workflow_success = True
                            self.workflow_results = data.get("results", {})
                            print(f"🎉 Workflow completed successfully!")
                            print(f"📊 Results: {len(self.workflow_results)} result categories")
                        
                        elif message_type == "error":
                            workflow_complete = True
                            workflow_success = False
                            error_msg = data.get("message", "Unknown error")
                            print(f"💥 Workflow failed: {error_msg}")
                            self.log_result("Workflow Execution", False, f"Workflow failed: {error_msg}")
                    
                    except asyncio.TimeoutError:
                        print("⏰ WebSocket message timeout (30s) - continuing to wait...")
                        continue
                    except ConnectionClosed:
                        print("🔌 WebSocket connection closed")
                        break
                    except Exception as e:
                        print(f"❌ WebSocket error: {str(e)}")
                        break
                
                # Check final results
                elapsed_time = time.time() - start_time
                
                if workflow_complete and workflow_success:
                    self.log_result("Complete Workflow Execution", True, 
                                  f"Workflow completed successfully in {elapsed_time:.1f}s", {
                                      "completed_agents": self.completed_agents,
                                      "total_agents": len(self.completed_agents),
                                      "expected_agents": len(expected_agents),
                                      "execution_time": elapsed_time
                                  })
                    return True
                elif workflow_complete and not workflow_success:
                    self.log_result("Complete Workflow Execution", False, 
                                  f"Workflow failed after {elapsed_time:.1f}s", {
                                      "completed_agents": self.completed_agents,
                                      "failed_at": len(self.completed_agents)
                                  })
                    return False
                else:
                    self.log_result("Complete Workflow Execution", False, 
                                  f"Workflow timeout after {elapsed_time:.1f}s", {
                                      "completed_agents": self.completed_agents,
                                      "timeout": timeout
                                  })
                    return False
        
        except Exception as e:
            self.log_result("WebSocket Workflow", False, f"Error: {str(e)}")
            return False
    
    async def verify_artifacts(self):
        """Verify that all expected artifacts were generated"""
        if not self.project_id:
            self.log_result("Artifact Verification", False, "No project_id available")
            return False
        
        try:
            # Get project details from API
            async with self.session.get(f"{API_BASE}/projects/{self.project_id}") as response:
                if response.status == 200:
                    project_data = await response.json()
                    artifacts = project_data.get("artifacts", {})
                    
                    expected_artifacts = [
                        "prd", "prd_xml", "mockup", "commercial_proposal", 
                        "commercial_proposal_xml", "bom", "bom_xml", 
                        "architecture_diagram", "architecture_xml"
                    ]
                    
                    found_artifacts = []
                    missing_artifacts = []
                    
                    for artifact in expected_artifacts:
                        if artifact in artifacts:
                            found_artifacts.append(artifact)
                        else:
                            missing_artifacts.append(artifact)
                    
                    if len(found_artifacts) >= 6:  # At least 6 major artifacts
                        self.log_result("Artifact Generation", True, 
                                      f"Generated {len(found_artifacts)}/{len(expected_artifacts)} artifacts", {
                                          "found": found_artifacts,
                                          "missing": missing_artifacts
                                      })
                        return True
                    else:
                        self.log_result("Artifact Generation", False, 
                                      f"Only {len(found_artifacts)}/{len(expected_artifacts)} artifacts generated", {
                                          "found": found_artifacts,
                                          "missing": missing_artifacts
                                      })
                        return False
                else:
                    text = await response.text()
                    self.log_result("Artifact Verification", False, f"HTTP {response.status}", text)
                    return False
        
        except Exception as e:
            self.log_result("Artifact Verification", False, f"Error: {str(e)}")
            return False
    
    async def verify_database_persistence(self):
        """Verify that workflow data was persisted to database"""
        if not self.project_id:
            self.log_result("Database Persistence", False, "No project_id available")
            return False
        
        try:
            # Check if project exists in database
            async with self.session.get(f"{API_BASE}/projects/{self.project_id}") as response:
                if response.status == 200:
                    project_data = await response.json()
                    
                    required_fields = ["id", "project_name", "workflow_id", "status", "created_at"]
                    missing_fields = [field for field in required_fields if field not in project_data]
                    
                    if not missing_fields:
                        self.log_result("Database Persistence", True, 
                                      f"Project data persisted correctly", {
                                          "project_id": project_data.get("id"),
                                          "status": project_data.get("status"),
                                          "workflow_id": project_data.get("workflow_id")
                                      })
                        return True
                    else:
                        self.log_result("Database Persistence", False, 
                                      f"Missing fields: {missing_fields}", project_data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("Database Persistence", False, f"HTTP {response.status}", text)
                    return False
        
        except Exception as e:
            self.log_result("Database Persistence", False, f"Error: {str(e)}")
            return False
    
    async def verify_file_system(self):
        """Verify that files were created in the storage directory"""
        if not self.project_id:
            self.log_result("File System Verification", False, "No project_id available")
            return False
        
        try:
            # Check storage directory structure
            storage_dir = Path("/app/backend/storage")
            
            # Project directory should be sanitized project name
            project_name = "Complete Test - Task Management App"
            sanitized_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in project_name)
            project_dir = storage_dir / sanitized_name
            
            if not project_dir.exists():
                self.log_result("File System Verification", False, f"Project directory not found: {project_dir}")
                return False
            
            # Check for expected subdirectories
            expected_dirs = [
                "PRDDocuments", "CaseStudies", "CommercialProposals", 
                "BillOfMaterials", "SystemArchitecture"
            ]
            
            found_dirs = []
            missing_dirs = []
            
            for dir_name in expected_dirs:
                dir_path = project_dir / dir_name
                if dir_path.exists():
                    found_dirs.append(dir_name)
                else:
                    missing_dirs.append(dir_name)
            
            # Check for workflow results file
            results_file = project_dir / "workflow_results.json"
            has_results_file = results_file.exists()
            
            if len(found_dirs) >= 3 and has_results_file:  # At least 3 directories + results file
                self.log_result("File System Verification", True, 
                              f"Found {len(found_dirs)}/{len(expected_dirs)} directories + results file", {
                                  "project_dir": str(project_dir),
                                  "found_dirs": found_dirs,
                                  "missing_dirs": missing_dirs,
                                  "has_results_file": has_results_file
                              })
                return True
            else:
                self.log_result("File System Verification", False, 
                              f"Only {len(found_dirs)}/{len(expected_dirs)} directories found", {
                                  "project_dir": str(project_dir),
                                  "found_dirs": found_dirs,
                                  "missing_dirs": missing_dirs,
                                  "has_results_file": has_results_file
                              })
                return False
        
        except Exception as e:
            self.log_result("File System Verification", False, f"Error: {str(e)}")
            return False
    
    async def run_complete_test(self):
        """Run complete end-to-end workflow test"""
        print("🚀 Starting Complete AICOE Workflow Test with Real OpenRouter LLM")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"WebSocket URL: {WS_BASE}")
        print(f"Model: x-ai/grok-code-fast-1")
        print("=" * 80)
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_api_health),
            ("Start Workflow", self.start_workflow),
            ("Complete Workflow Execution", self.test_websocket_workflow),
            ("Artifact Generation", self.verify_artifacts),
            ("Database Persistence", self.verify_database_persistence),
            ("File System Verification", self.verify_file_system),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                success = await test_func()
                results[test_name] = success
                
                # Stop if critical test fails
                if not success and test_name in ["API Health Check", "Start Workflow"]:
                    print(f"💥 Critical test failed: {test_name}. Stopping execution.")
                    break
                    
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPLETE WORKFLOW TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Agent completion summary
        if self.completed_agents:
            print(f"\n🤖 Agent Completion Summary:")
            print(f"   Completed Agents: {len(self.completed_agents)}")
            print(f"   Agents: {', '.join(self.completed_agents)}")
        
        if passed == total:
            print("🎉 All tests passed! Complete workflow is working correctly.")
            print("✅ AICOE Platform is fully operational with real LLM integration.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return results
    
    def get_detailed_results(self):
        """Get detailed test results for reporting"""
        return {
            "test_results": self.test_results,
            "agent_progress": self.agent_progress,
            "completed_agents": self.completed_agents,
            "workflow_results": self.workflow_results
        }

async def main():
    """Main test execution"""
    async with CompleteWorkflowTester() as tester:
        results = await tester.run_complete_test()
        
        # Save detailed results
        detailed_results = tester.get_detailed_results()
        results_file = "/app/complete_workflow_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())