#!/usr/bin/env python3
"""
Comprehensive Backend Testing with Messy Transcript for AICOE Platform

This script performs comprehensive testing including:
- API endpoint testing
- WebSocket real-time monitoring
- Complete workflow execution with complex transcript
- Performance monitoring
- Artifact generation verification
- Error handling and logging
"""

import asyncio
import aiohttp
import websockets
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import sys
import os
import subprocess

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configuration
BACKEND_URL = "https://test-bug-fixer.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"
WS_BASE = f"{BACKEND_URL.replace('https://', 'wss://')}/api"
TEST_TRANSCRIPT_FILE = "/app/test_messy_transcript.txt"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/comprehensive_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComprehensiveBackendTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.project_id = None
        self.workflow_id = None
        self.workflow_start_time = None
        self.agent_execution_times = {}
        self.websocket_messages = []
        self.performance_metrics = {}
        
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
        logger.info(f"{status} {test_name}: {details}")
        if response_data and not success:
            logger.error(f"   Response: {response_data}")
    
    async def load_messy_transcript(self):
        """Load the complex messy transcript"""
        try:
            with open(TEST_TRANSCRIPT_FILE, 'r') as f:
                content = f.read().strip()
                logger.info(f"Loaded messy transcript: {len(content)} characters")
                return content
        except Exception as e:
            self.log_result("Load Messy Transcript", False, f"Failed to load: {str(e)}")
            return None
    
    async def test_basic_api_health(self):
        """Test basic API health before comprehensive testing"""
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
    
    async def initiate_workflow(self):
        """Initiate workflow with messy transcript"""
        try:
            transcript = await self.load_messy_transcript()
            if not transcript:
                return False
            
            test_data = {
                "project_name": "E-Commerce Platform - ShopEasy",
                "transcript": transcript
            }
            
            logger.info("Initiating workflow with complex e-commerce transcript...")
            async with self.session.post(f"{API_BASE}/process-transcript", json=test_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if "project_id" in data and "workflow_id" in data:
                        self.project_id = data["project_id"]
                        self.workflow_id = data["workflow_id"]
                        self.log_result("Workflow Initiation", True, "Complex workflow started successfully", {
                            "project_id": self.project_id,
                            "workflow_id": self.workflow_id,
                            "transcript_length": len(transcript)
                        })
                        return True
                    else:
                        self.log_result("Workflow Initiation", False, "Missing project_id or workflow_id", data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("Workflow Initiation", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Workflow Initiation", False, f"Error: {str(e)}")
            return False
    
    async def monitor_websocket_workflow(self):
        """Monitor complete workflow execution via WebSocket"""
        if not self.workflow_id:
            self.log_result("WebSocket Workflow Monitoring", False, "No workflow_id available")
            return False
        
        try:
            ws_url = f"{WS_BASE}/ws/{self.workflow_id}"
            logger.info(f"Connecting to WebSocket: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                logger.info("WebSocket connected successfully")
                
                # Send start message with transcript data
                transcript = await self.load_messy_transcript()
                start_message = {
                    "action": "start",
                    "project_name": "E-Commerce Platform - ShopEasy",
                    "transcript": transcript
                }
                
                await websocket.send(json.dumps(start_message))
                logger.info("Sent workflow start message")
                
                self.workflow_start_time = time.time()
                completed_agents = []
                agent_start_times = {}
                
                # Monitor workflow progress
                workflow_completed = False
                timeout = 300  # 5 minutes timeout
                start_time = time.time()
                
                while not workflow_completed and (time.time() - start_time) < timeout:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(message)
                        self.websocket_messages.append(data)
                        
                        message_type = data.get("type")
                        stage = data.get("stage")
                        status = data.get("status")
                        
                        logger.info(f"WebSocket message: {message_type} - {stage} - {status}")
                        
                        if message_type == "progress":
                            if stage and stage != "workflow":
                                if status == "running" and stage not in agent_start_times:
                                    agent_start_times[stage] = time.time()
                                    logger.info(f"🚀 Agent {stage} started")
                                
                                elif status == "completed" and stage not in completed_agents:
                                    completed_agents.append(stage)
                                    if stage in agent_start_times:
                                        execution_time = time.time() - agent_start_times[stage]
                                        self.agent_execution_times[stage] = execution_time
                                        logger.info(f"✅ Agent {stage} completed in {execution_time:.2f}s")
                        
                        elif message_type == "complete":
                            workflow_completed = True
                            total_time = time.time() - self.workflow_start_time
                            self.performance_metrics["total_execution_time"] = total_time
                            logger.info(f"🎉 Workflow completed in {total_time:.2f}s")
                            
                            self.log_result("Complete Workflow Execution", True, 
                                          f"All agents completed successfully in {total_time:.2f}s", {
                                "completed_agents": completed_agents,
                                "total_agents": len(completed_agents),
                                "execution_time": total_time,
                                "agent_times": self.agent_execution_times
                            })
                            return True
                        
                        elif message_type == "error":
                            error_msg = data.get("message", "Unknown error")
                            self.log_result("Workflow Execution Error", False, f"Workflow failed: {error_msg}", data)
                            return False
                    
                    except asyncio.TimeoutError:
                        logger.warning("WebSocket message timeout - continuing to wait...")
                        continue
                    except Exception as e:
                        logger.error(f"Error processing WebSocket message: {str(e)}")
                        continue
                
                if not workflow_completed:
                    self.log_result("Workflow Timeout", False, f"Workflow did not complete within {timeout}s", {
                        "completed_agents": completed_agents,
                        "partial_execution_time": time.time() - self.workflow_start_time
                    })
                    return False
                
        except Exception as e:
            self.log_result("WebSocket Workflow Monitoring", False, f"WebSocket error: {str(e)}")
            return False
    
    async def verify_artifact_generation(self):
        """Verify that all expected artifacts were generated"""
        if not self.project_id:
            self.log_result("Artifact Verification", False, "No project_id available")
            return False
        
        try:
            # Get project details
            async with self.session.get(f"{API_BASE}/projects/{self.project_id}") as response:
                if response.status == 200:
                    project_data = await response.json()
                    artifacts = project_data.get("artifacts", {})
                    
                    expected_artifacts = [
                        "prd", "prd_xml", "mockup", "commercial_proposal", 
                        "commercial_proposal_xml", "bom", "bom_xml", 
                        "architecture_diagram", "architecture_xml"
                    ]
                    
                    generated_artifacts = []
                    missing_artifacts = []
                    
                    for artifact in expected_artifacts:
                        if artifact in artifacts:
                            generated_artifacts.append(artifact)
                        else:
                            missing_artifacts.append(artifact)
                    
                    # Test artifact downloads
                    downloadable_artifacts = []
                    for artifact in generated_artifacts:
                        try:
                            async with self.session.get(f"{API_BASE}/download/{self.project_id}/{artifact}") as dl_response:
                                if dl_response.status == 200:
                                    downloadable_artifacts.append(artifact)
                        except Exception as e:
                            logger.warning(f"Failed to download {artifact}: {str(e)}")
                    
                    success = len(generated_artifacts) >= 6  # At least 6 artifacts should be generated
                    
                    self.log_result("Artifact Generation", success, 
                                  f"Generated {len(generated_artifacts)}/{len(expected_artifacts)} artifacts", {
                        "generated": generated_artifacts,
                        "missing": missing_artifacts,
                        "downloadable": downloadable_artifacts,
                        "project_data": project_data
                    })
                    
                    return success
                else:
                    text = await response.text()
                    self.log_result("Artifact Verification", False, f"Failed to get project: HTTP {response.status}", text)
                    return False
        
        except Exception as e:
            self.log_result("Artifact Verification", False, f"Error: {str(e)}")
            return False
    
    async def check_backend_logs(self):
        """Check backend logs for errors"""
        try:
            # Check supervisor backend logs
            log_files = [
                "/var/log/supervisor/backend.err.log",
                "/var/log/supervisor/backend.out.log"
            ]
            
            log_issues = []
            
            for log_file in log_files:
                try:
                    result = subprocess.run(
                        ["tail", "-n", "50", log_file],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode == 0:
                        log_content = result.stdout
                        
                        # Look for error patterns
                        error_patterns = [
                            "ERROR", "CRITICAL", "Exception", "Traceback",
                            "Failed", "timeout", "connection refused"
                        ]
                        
                        for pattern in error_patterns:
                            if pattern.lower() in log_content.lower():
                                log_issues.append(f"{log_file}: Found '{pattern}' in logs")
                    
                except Exception as e:
                    log_issues.append(f"Failed to read {log_file}: {str(e)}")
            
            if log_issues:
                self.log_result("Backend Log Check", False, "Found issues in logs", {"issues": log_issues})
                return False
            else:
                self.log_result("Backend Log Check", True, "No critical issues found in logs")
                return True
        
        except Exception as e:
            self.log_result("Backend Log Check", False, f"Error checking logs: {str(e)}")
            return False
    
    async def performance_analysis(self):
        """Analyze performance metrics"""
        try:
            if not self.agent_execution_times:
                self.log_result("Performance Analysis", False, "No agent execution times available")
                return False
            
            total_time = self.performance_metrics.get("total_execution_time", 0)
            agent_times = self.agent_execution_times
            
            # Calculate statistics
            avg_agent_time = sum(agent_times.values()) / len(agent_times) if agent_times else 0
            slowest_agent = max(agent_times.items(), key=lambda x: x[1]) if agent_times else ("none", 0)
            fastest_agent = min(agent_times.items(), key=lambda x: x[1]) if agent_times else ("none", 0)
            
            performance_report = {
                "total_execution_time": total_time,
                "average_agent_time": avg_agent_time,
                "slowest_agent": {"name": slowest_agent[0], "time": slowest_agent[1]},
                "fastest_agent": {"name": fastest_agent[0], "time": fastest_agent[1]},
                "total_agents": len(agent_times),
                "agent_breakdown": agent_times
            }
            
            # Performance thresholds
            success = (
                total_time < 300 and  # Less than 5 minutes total
                avg_agent_time < 30 and  # Less than 30s average per agent
                len(agent_times) >= 10  # At least 10 agents completed
            )
            
            self.log_result("Performance Analysis", success, 
                          f"Total: {total_time:.2f}s, Avg: {avg_agent_time:.2f}s, Agents: {len(agent_times)}", 
                          performance_report)
            
            return success
        
        except Exception as e:
            self.log_result("Performance Analysis", False, f"Error: {str(e)}")
            return False
    
    async def run_comprehensive_test(self):
        """Run complete comprehensive backend test"""
        logger.info("🚀 Starting Comprehensive Backend Testing with Messy Transcript")
        logger.info(f"Backend URL: {BACKEND_URL}")
        logger.info(f"Test Transcript: {TEST_TRANSCRIPT_FILE}")
        logger.info("=" * 80)
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_basic_api_health),
            ("Workflow Initiation", self.initiate_workflow),
            ("WebSocket Workflow Monitoring", self.monitor_websocket_workflow),
            ("Artifact Generation Verification", self.verify_artifact_generation),
            ("Backend Log Analysis", self.check_backend_logs),
            ("Performance Analysis", self.performance_analysis),
        ]
        
        results = {}
        for test_name, test_func in tests:
            logger.info(f"\n🔍 Running {test_name}...")
            try:
                success = await test_func()
                results[test_name] = success
                if not success and test_name in ["API Health Check", "Workflow Initiation"]:
                    logger.error(f"Critical test failed: {test_name}. Stopping further tests.")
                    break
            except Exception as e:
                logger.error(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                results[test_name] = False
        
        # Generate comprehensive report
        await self.generate_comprehensive_report(results)
        
        return results
    
    async def generate_comprehensive_report(self, results):
        """Generate detailed test report"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 COMPREHENSIVE TEST REPORT")
        logger.info("=" * 80)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        # Test Results Summary
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status} {test_name}")
        
        logger.info(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        # Performance Metrics
        if self.performance_metrics:
            logger.info("\n📈 PERFORMANCE METRICS:")
            total_time = self.performance_metrics.get("total_execution_time", 0)
            logger.info(f"   Total Execution Time: {total_time:.2f}s")
            
            if self.agent_execution_times:
                logger.info(f"   Agents Completed: {len(self.agent_execution_times)}")
                avg_time = sum(self.agent_execution_times.values()) / len(self.agent_execution_times)
                logger.info(f"   Average Agent Time: {avg_time:.2f}s")
                
                slowest = max(self.agent_execution_times.items(), key=lambda x: x[1])
                fastest = min(self.agent_execution_times.items(), key=lambda x: x[1])
                logger.info(f"   Slowest Agent: {slowest[0]} ({slowest[1]:.2f}s)")
                logger.info(f"   Fastest Agent: {fastest[0]} ({fastest[1]:.2f}s)")
        
        # WebSocket Messages Summary
        if self.websocket_messages:
            logger.info(f"\n📡 WebSocket Messages: {len(self.websocket_messages)} received")
            
            message_types = {}
            for msg in self.websocket_messages:
                msg_type = msg.get("type", "unknown")
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            for msg_type, count in message_types.items():
                logger.info(f"   {msg_type}: {count}")
        
        # Save detailed results
        detailed_results = {
            "test_summary": results,
            "performance_metrics": self.performance_metrics,
            "agent_execution_times": self.agent_execution_times,
            "websocket_messages": self.websocket_messages,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        results_file = "/app/comprehensive_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        logger.info(f"\n📄 Detailed results saved to: {results_file}")
        
        # Final assessment
        if passed == total:
            logger.info("🎉 All comprehensive tests passed! AICOE Platform is working correctly with complex input.")
        else:
            logger.info("⚠️  Some tests failed. Check the details above for issues.")
        
        return detailed_results

async def main():
    """Main test execution"""
    async with ComprehensiveBackendTester() as tester:
        results = await tester.run_comprehensive_test()
        return results

if __name__ == "__main__":
    asyncio.run(main())