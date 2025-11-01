#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for AICOE Automation Platform

This script tests all backend API endpoints including:
- Health check
- Status management
- Transcript processing workflow
- Project management
- Artifact downloads
- Database operations
"""

import asyncio
import aiohttp
import json
import time
from pathlib import Path
from datetime import datetime
import sys
import os

# Add backend directory to path for imports
sys.path.append('/app/backend')

# Configuration
BACKEND_URL = "http://localhost:8001"
API_BASE = f"{BACKEND_URL}/api"
TEST_TRANSCRIPT_FILE = "/app/test_transcript_ui_test.txt"

class APITester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.project_id = None
        self.workflow_id = None
        
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
    
    async def test_health_check(self):
        """Test GET /api/ endpoint"""
        try:
            async with self.session.get(f"{API_BASE}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "running":
                        self.log_result("Health Check", True, "API is running and responsive", data)
                        return True
                    else:
                        self.log_result("Health Check", False, f"Unexpected status: {data.get('status')}", data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("Health Check", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Health Check", False, f"Connection error: {str(e)}")
            return False
    
    async def test_status_endpoints(self):
        """Test POST /api/status and GET /api/status endpoints"""
        try:
            # Test POST /api/status
            test_data = {"client_name": "backend_test_client"}
            async with self.session.post(f"{API_BASE}/status", json=test_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("client_name") == "backend_test_client" and "id" in data:
                        self.log_result("Status Creation", True, "Status check created successfully", data)
                        status_create_success = True
                    else:
                        self.log_result("Status Creation", False, "Invalid response format", data)
                        status_create_success = False
                else:
                    text = await response.text()
                    self.log_result("Status Creation", False, f"HTTP {response.status}", text)
                    status_create_success = False
            
            # Test GET /api/status
            async with self.session.get(f"{API_BASE}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        self.log_result("Status Retrieval", True, f"Retrieved {len(data)} status checks", {"count": len(data)})
                        status_get_success = True
                    else:
                        self.log_result("Status Retrieval", False, "Response is not a list", data)
                        status_get_success = False
                else:
                    text = await response.text()
                    self.log_result("Status Retrieval", False, f"HTTP {response.status}", text)
                    status_get_success = False
            
            return status_create_success and status_get_success
            
        except Exception as e:
            self.log_result("Status Endpoints", False, f"Error: {str(e)}")
            return False
    
    async def load_test_transcript(self):
        """Load test transcript from file"""
        try:
            with open(TEST_TRANSCRIPT_FILE, 'r') as f:
                return f.read().strip()
        except Exception as e:
            self.log_result("Load Transcript", False, f"Failed to load transcript: {str(e)}")
            return None
    
    async def test_process_transcript(self):
        """Test POST /api/process-transcript endpoint"""
        try:
            transcript = await self.load_test_transcript()
            if not transcript:
                return False
            
            test_data = {
                "project_name": "Test Task Management App",
                "transcript": transcript
            }
            
            async with self.session.post(f"{API_BASE}/process-transcript", json=test_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if "project_id" in data and "workflow_id" in data:
                        self.project_id = data["project_id"]
                        self.workflow_id = data["workflow_id"]
                        self.log_result("Process Transcript", True, "Workflow started successfully", {
                            "project_id": self.project_id,
                            "workflow_id": self.workflow_id,
                            "status": data.get("status")
                        })
                        return True
                    else:
                        self.log_result("Process Transcript", False, "Missing project_id or workflow_id", data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("Process Transcript", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Process Transcript", False, f"Error: {str(e)}")
            return False
    
    async def test_workflow_status(self):
        """Test GET /api/workflow/{workflow_id}/status endpoint"""
        if not self.workflow_id:
            self.log_result("Workflow Status", False, "No workflow_id available from previous test")
            return False
        
        try:
            async with self.session.get(f"{API_BASE}/workflow/{self.workflow_id}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    if "workflow_id" in data and "status" in data:
                        self.log_result("Workflow Status", True, f"Status: {data.get('status')}", {
                            "workflow_id": data.get("workflow_id"),
                            "status": data.get("status"),
                            "project_name": data.get("project_name")
                        })
                        return True
                    else:
                        self.log_result("Workflow Status", False, "Invalid response format", data)
                        return False
                else:
                    text = await response.text()
                    self.log_result("Workflow Status", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Workflow Status", False, f"Error: {str(e)}")
            return False
    
    async def test_projects_endpoints(self):
        """Test GET /api/projects and GET /api/projects/{project_id} endpoints"""
        try:
            # Test GET /api/projects
            async with self.session.get(f"{API_BASE}/projects") as response:
                if response.status == 200:
                    data = await response.json()
                    if "projects" in data and "count" in data:
                        self.log_result("List Projects", True, f"Found {data['count']} projects", {"count": data["count"]})
                        list_success = True
                    else:
                        self.log_result("List Projects", False, "Invalid response format", data)
                        list_success = False
                else:
                    text = await response.text()
                    self.log_result("List Projects", False, f"HTTP {response.status}", text)
                    list_success = False
            
            # Test GET /api/projects/{project_id} if we have a project_id
            if self.project_id:
                async with self.session.get(f"{API_BASE}/projects/{self.project_id}") as response:
                    if response.status == 200:
                        data = await response.json()
                        if "id" in data and "project_name" in data:
                            self.log_result("Get Project", True, f"Retrieved project: {data.get('project_name')}", {
                                "project_id": data.get("id"),
                                "project_name": data.get("project_name"),
                                "status": data.get("status")
                            })
                            get_success = True
                        else:
                            self.log_result("Get Project", False, "Invalid response format", data)
                            get_success = False
                    elif response.status == 404:
                        self.log_result("Get Project", True, "Project not found (expected for new workflow)", {"status": 404})
                        get_success = True  # This is expected for a new workflow that hasn't completed
                    else:
                        text = await response.text()
                        self.log_result("Get Project", False, f"HTTP {response.status}", text)
                        get_success = False
            else:
                self.log_result("Get Project", False, "No project_id available from previous test")
                get_success = False
            
            return list_success and get_success
            
        except Exception as e:
            self.log_result("Projects Endpoints", False, f"Error: {str(e)}")
            return False
    
    async def test_download_artifacts(self):
        """Test GET /api/download/{project_id}/{artifact_type} endpoint"""
        if not self.project_id:
            self.log_result("Download Artifacts", False, "No project_id available from previous test")
            return False
        
        try:
            # Test with a common artifact type
            artifact_type = "prd"
            async with self.session.get(f"{API_BASE}/download/{self.project_id}/{artifact_type}") as response:
                if response.status == 200:
                    # Check if it's a file response
                    content_type = response.headers.get('content-type', '')
                    if 'html' in content_type or 'xml' in content_type:
                        self.log_result("Download Artifacts", True, f"Artifact download successful: {artifact_type}", {
                            "content_type": content_type,
                            "artifact_type": artifact_type
                        })
                        return True
                    else:
                        self.log_result("Download Artifacts", False, f"Unexpected content type: {content_type}")
                        return False
                elif response.status == 404:
                    self.log_result("Download Artifacts", True, "Artifact not found (expected for new workflow)", {"status": 404})
                    return True  # This is expected for a new workflow that hasn't completed
                else:
                    text = await response.text()
                    self.log_result("Download Artifacts", False, f"HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Download Artifacts", False, f"Error: {str(e)}")
            return False
    
    async def test_database_connection(self):
        """Test database connectivity by checking if status operations work"""
        try:
            # Create a test status entry
            test_data = {"client_name": "db_test_client"}
            async with self.session.post(f"{API_BASE}/status", json=test_data) as response:
                if response.status == 200:
                    data = await response.json()
                    test_id = data.get("id")
                    
                    # Retrieve all status entries to verify database read
                    async with self.session.get(f"{API_BASE}/status") as get_response:
                        if get_response.status == 200:
                            status_list = await get_response.json()
                            # Check if our test entry is in the list
                            found = any(item.get("id") == test_id for item in status_list)
                            if found:
                                self.log_result("Database Connection", True, "Database read/write operations successful", {
                                    "test_id": test_id,
                                    "total_entries": len(status_list)
                                })
                                return True
                            else:
                                self.log_result("Database Connection", False, "Test entry not found in database")
                                return False
                        else:
                            text = await get_response.text()
                            self.log_result("Database Connection", False, f"Database read failed: HTTP {get_response.status}", text)
                            return False
                else:
                    text = await response.text()
                    self.log_result("Database Connection", False, f"Database write failed: HTTP {response.status}", text)
                    return False
        except Exception as e:
            self.log_result("Database Connection", False, f"Error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting AICOE Automation Platform Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("Database Connection", self.test_database_connection),
            ("Status Endpoints", self.test_status_endpoints),
            ("Process Transcript", self.test_process_transcript),
            ("Workflow Status", self.test_workflow_status),
            ("Projects Endpoints", self.test_projects_endpoints),
            ("Download Artifacts", self.test_download_artifacts),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name}...")
            try:
                success = await test_func()
                results[test_name] = success
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for success in results.values() if success)
        total = len(results)
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! Backend API is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the details above.")
        
        return results
    
    def get_detailed_results(self):
        """Get detailed test results for reporting"""
        return self.test_results

async def main():
    """Main test execution"""
    async with APITester() as tester:
        results = await tester.run_all_tests()
        
        # Save detailed results
        detailed_results = tester.get_detailed_results()
        results_file = "/app/backend_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
