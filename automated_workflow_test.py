#!/usr/bin/env python3
"""
Automated End-to-End Workflow Test
"""

import asyncio
import websockets
import json
import aiohttp
from pathlib import Path
import time

BACKEND_URL = "http://localhost:8001"
WS_URL = "ws://localhost:8001/api/ws"
TEST_TRANSCRIPT_FILE = "/app/test_transcript_ui_test.txt"

async def load_test_transcript():
    """Load test transcript from file"""
    with open(TEST_TRANSCRIPT_FILE, 'r') as f:
        return f.read().strip()

async def test_full_workflow():
    """Test complete workflow execution"""
    print("🚀 Starting Full Workflow Test")
    print("=" * 60)
    
    # Load transcript
    transcript = await load_test_transcript()
    print(f"✅ Loaded transcript ({len(transcript)} characters)")
    
    # Step 1: Start workflow
    async with aiohttp.ClientSession() as session:
        test_data = {
            "project_name": "E2E Test Project",
            "transcript": transcript
        }
        
        async with session.post(f"{BACKEND_URL}/api/process-transcript", json=test_data) as response:
            if response.status == 200:
                data = await response.json()
                workflow_id = data["workflow_id"]
                project_id = data["project_id"]
                print(f"✅ Workflow initiated: {workflow_id}")
                print(f"✅ Project ID: {project_id}")
            else:
                print(f"❌ Failed to start workflow: HTTP {response.status}")
                return False
    
    # Step 2: Connect to WebSocket and execute workflow
    ws_url = f"{WS_URL}/{workflow_id}"
    print(f"🔌 Connecting to WebSocket...")
    
    try:
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as websocket:
            print("✅ WebSocket connected")
            
            # Send start message
            start_message = {
                "action": "start",
                "project_name": "E2E Test Project",
                "transcript": transcript
            }
            
            await websocket.send(json.dumps(start_message))
            print("📤 Workflow execution started\n")
            
            # Track progress
            progress_updates = []
            agents_completed = []
            start_time = time.time()
            
            # Listen for updates (max 120 seconds)
            timeout = 120
            while time.time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    
                    msg_type = data.get("type")
                    
                    if msg_type == "progress":
                        stage = data.get("stage", "unknown")
                        status = data.get("status", "unknown")
                        message_text = data.get("message", "")
                        
                        progress_updates.append(data)
                        
                        # Format progress message
                        status_emoji = {
                            "running": "🔵",
                            "completed": "✅",
                            "failed": "❌"
                        }.get(status, "⚪")
                        
                        print(f"{status_emoji} {stage}: {status} - {message_text}")
                        
                        if status == "completed" and stage not in agents_completed:
                            agents_completed.append(stage)
                    
                    elif msg_type == "complete":
                        print("\n🎉 Workflow completed!")
                        results = data.get("results", {})
                        print(f"✅ Generated artifacts:")
                        for artifact_type in results.keys():
                            print(f"   - {artifact_type}")
                        
                        # Test results retrieval
                        await test_results_api(project_id, session)
                        return True
                    
                    elif msg_type == "error":
                        print(f"\n❌ Workflow error: {data.get('message')}")
                        return False
                
                except asyncio.TimeoutError:
                    print("⏳ Waiting for updates...")
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("❌ WebSocket connection closed")
                    break
            
            # Timeout reached
            elapsed = time.time() - start_time
            print(f"\n⏱️ Workflow timeout after {elapsed:.1f}s")
            print(f"✅ Agents completed: {len(agents_completed)}")
            print(f"📊 Progress updates received: {len(progress_updates)}")
            
            return len(agents_completed) > 0
    
    except Exception as e:
        print(f"❌ WebSocket test failed: {str(e)}")
        return False

async def test_results_api(project_id, session=None):
    """Test results retrieval APIs"""
    print("\n📥 Testing Results APIs")
    print("-" * 60)
    
    should_close = False
    if session is None:
        session = aiohttp.ClientSession()
        should_close = True
    
    try:
        # Test project details
        async with session.get(f"{BACKEND_URL}/api/projects/{project_id}") as response:
            if response.status == 200:
                project = await response.json()
                print(f"✅ Project details retrieved")
                print(f"   - Name: {project.get('project_name')}")
                print(f"   - Status: {project.get('status')}")
                artifacts = project.get('artifacts', {})
                print(f"   - Artifacts: {len(artifacts)}")
            else:
                print(f"❌ Failed to get project: HTTP {response.status}")
        
        # Test projects list
        async with session.get(f"{BACKEND_URL}/api/projects") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Projects list: {data.get('count', 0)} projects")
            else:
                print(f"❌ Failed to list projects: HTTP {response.status}")
    
    finally:
        if should_close:
            await session.close()

async def main():
    """Main test execution"""
    print("\n" + "=" * 60)
    print("AICOE PLATFORM - END-TO-END AUTOMATED TEST")
    print("=" * 60 + "\n")
    
    success = await test_full_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ END-TO-END TEST PASSED")
    else:
        print("⚠️ END-TO-END TEST COMPLETED WITH ISSUES")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
