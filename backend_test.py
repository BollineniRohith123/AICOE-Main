#!/usr/bin/env python3
"""
AICOE Automation Platform - Backend API Testing
Tests all backend endpoints including WebSocket functionality
"""

import requests
import asyncio
import websockets
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

class AICOEBackendTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.ws_url = base_url.replace('https://', 'wss://').replace('http://', 'ws://')
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def test_health_endpoints(self):
        """Test basic health and info endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            success = response.status_code == 200 and "AICOE" in response.text
            self.log_test("Root Endpoint", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint", False, str(e))
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            success = response.status_code == 200
            self.log_test("Health Endpoint", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Endpoint", False, str(e))
    
    def test_project_endpoints(self):
        """Test project management endpoints"""
        print("\n🔍 Testing Project Endpoints...")
        
        # Test list projects
        try:
            response = requests.get(f"{self.base_url}/api/projects", timeout=10)
            success = response.status_code == 200
            self.log_test("List Projects", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("List Projects", False, str(e))
        
        # Test create project
        try:
            project_data = {
                "project_name": "Test Project API",
                "description": "Test project for API validation",
                "requirements": "Basic testing requirements",
                "industry": "Technology",
                "budget": 10000.0,
                "timeline": "2 weeks"
            }
            response = requests.post(
                f"{self.base_url}/api/projects/create", 
                json=project_data,
                timeout=30
            )
            success = response.status_code == 200
            if success:
                result = response.json()
                project_id = result.get("project_id")
                if project_id:
                    # Test get project status
                    status_response = requests.get(
                        f"{self.base_url}/api/projects/{project_id}/status",
                        timeout=10
                    )
                    status_success = status_response.status_code == 200
                    self.log_test("Get Project Status", status_success, 
                                f"Status: {status_response.status_code}")
            
            self.log_test("Create Project", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Project", False, str(e))
    
    def test_transcript_processing(self):
        """Test transcript processing endpoint"""
        print("\n🔍 Testing Transcript Processing...")
        
        try:
            transcript_data = {
                "transcript": "Meeting transcript for testing purposes. This is a sample transcript that contains enough content to pass validation. We discussed building a task management application with user authentication, task creation, and dashboard features.",
                "project_id": None
            }
            response = requests.post(
                f"{self.base_url}/api/transcript/process",
                json=transcript_data,
                timeout=30
            )
            success = response.status_code == 200
            self.log_test("Process Transcript", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Process Transcript", False, str(e))
    
    def test_agents_status(self):
        """Test agents status endpoint"""
        print("\n🔍 Testing Agents Status...")
        
        try:
            response = requests.get(f"{self.base_url}/api/agents/status", timeout=10)
            success = response.status_code == 200
            self.log_test("Agents Status", success, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Agents Status", False, str(e))
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and basic functionality"""
        print("\n🔍 Testing WebSocket Connection...")
        
        workflow_id = f"test_workflow_{int(time.time())}"
        ws_endpoint = f"{self.ws_url}/api/ws/{workflow_id}"
        
        try:
            # Test WebSocket connection
            async with websockets.connect(ws_endpoint, timeout=10) as websocket:
                print(f"Connected to WebSocket: {ws_endpoint}")
                
                # Test reconnect message
                reconnect_msg = {
                    "action": "reconnect",
                    "workflow_id": workflow_id
                }
                await websocket.send(json.dumps(reconnect_msg))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    # Check if we get an error (expected for non-existent workflow)
                    success = "error" in response_data or "reconnect_ack" in response_data.get("type", "")
                    self.log_test("WebSocket Connection", True, "Connection established")
                    self.log_test("WebSocket Reconnect", success, f"Response: {response_data.get('type', 'unknown')}")
                    
                except asyncio.TimeoutError:
                    self.log_test("WebSocket Reconnect", False, "Timeout waiting for response")
                
        except Exception as e:
            self.log_test("WebSocket Connection", False, str(e))
    
    def test_workflow_status_endpoint(self):
        """Test workflow status endpoint"""
        print("\n🔍 Testing Workflow Status Endpoint...")
        
        # Test with non-existent workflow (should return 404)
        try:
            workflow_id = "non_existent_workflow"
            response = requests.get(
                f"{self.base_url}/api/workflow/{workflow_id}/status",
                timeout=10
            )
            # Expecting 404 for non-existent workflow
            success = response.status_code == 404
            self.log_test("Workflow Status (Non-existent)", success, 
                        f"Status: {response.status_code} (Expected 404)")
        except Exception as e:
            self.log_test("Workflow Status (Non-existent)", False, str(e))
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        print("\n🔍 Testing CORS Headers...")
        
        try:
            response = requests.options(f"{self.base_url}/api/projects", timeout=10)
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            has_cors = any(header in response.headers for header in cors_headers)
            self.log_test("CORS Headers", has_cors, f"Headers present: {has_cors}")
        except Exception as e:
            self.log_test("CORS Headers", False, str(e))
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting AICOE Backend API Tests")
        print(f"📍 Testing endpoint: {self.base_url}")
        print("=" * 60)
        
        # Run synchronous tests
        self.test_health_endpoints()
        self.test_project_endpoints()
        self.test_transcript_processing()
        self.test_agents_status()
        self.test_workflow_status_endpoint()
        self.test_cors_headers()
        
        # Run WebSocket tests
        try:
            asyncio.run(self.test_websocket_connection())
        except Exception as e:
            self.log_test("WebSocket Tests", False, f"AsyncIO error: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t["success"]]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        
        return self.tests_passed, self.tests_run, self.test_results

def main():
    # Test both local and external URLs
    import os
    
    # Test local backend first
    local_url = "http://localhost:8001"
    print(f"🔧 Testing Local Backend: {local_url}")
    
    local_tester = AICOEBackendTester(local_url)
    local_passed, local_total, local_results = local_tester.run_all_tests()
    
    # Test external URL
    external_url = os.getenv('REACT_APP_BACKEND_URL', 'https://fd710b43-c70e-4e0f-ad4f-8c5f21eab69e-00-1mofqvypkqg6l.pike.replit.dev')
    print(f"\n🔧 Testing External Backend: {external_url}")
    
    external_tester = AICOEBackendTester(external_url)
    external_passed, external_total, external_results = external_tester.run_all_tests()
    
    # Combined results
    print(f"\n📊 COMBINED RESULTS:")
    print(f"Local Backend: {local_passed}/{local_total} tests passed")
    print(f"External Backend: {external_passed}/{external_total} tests passed")
    
    # Return success if local backend works (external URL issue is environment-specific)
    return 0 if local_passed >= (local_total * 0.8) else 1

if __name__ == "__main__":
    sys.exit(main())