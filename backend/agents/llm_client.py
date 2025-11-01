"""
Mock LLM Client for Testing
This allows testing the full workflow without a valid API key
"""
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Mock LLM Client that returns realistic responses for testing
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: str = "x-ai/grok-code-fast-1"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "mock-key")
        self.provider = provider
        self.model = model
        self.logger = logging.getLogger("llm_client_mock")
        self.logger.info(f"⚠️ MOCK MODE: Using mock LLM client for testing")
    
    async def send_message_async(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Mock send message - returns context-appropriate responses
        """
        self.logger.info(f"🔵 MOCK API CALL | msg_length={len(user_message)}")
        
        import json
        
        # Detect if JSON output is expected
        needs_json = "json" in user_message.lower() or "JSON" in user_message
        
        # Generate mock responses based on message content
        if "use_cases" in user_message and "business_requirements" in user_message:
            response = self._generate_requirements_json()
        elif "PRD" in user_message or "product requirements" in user_message.lower():
            response = self._generate_prd_json() if needs_json else self._generate_mock_prd()
        elif "mockup" in user_message.lower() or "HTML" in user_message:
            response = self._generate_mock_mockup()
        elif "commercial proposal" in user_message.lower() or "proposal" in user_message.lower():
            response = self._generate_proposal_json() if needs_json else self._generate_mock_proposal()
        elif "BOM" in user_message or "bill of materials" in user_message.lower():
            response = self._generate_bom_json() if needs_json else self._generate_mock_bom()
        elif "architecture" in user_message.lower() or "system diagram" in user_message.lower():
            response = self._generate_architecture_json() if needs_json else self._generate_mock_architecture()
        else:
            response = self._generate_generic_response(user_message)
        
        self.logger.info(f"🟢 MOCK API CALL SUCCESS | Response: {len(response)} chars")
        return response
    
    def _generate_mock_prd(self) -> str:
        """Generate mock PRD content"""
        # Check if JSON response is expected
        return self._generate_json_or_text("prd")
    
    def _generate_requirements_json(self) -> str:
        """Generate mock requirements in JSON format"""
        import json
        data = {
            "use_cases": [
                {
                    "id": "UC-001",
                    "title": "User Registration",
                    "description": "Allow new users to register with email and password",
                    "actors": ["New User", "System"],
                    "preconditions": ["User has valid email address"],
                    "main_flow": [
                        "User navigates to registration page",
                        "User enters email and password",
                        "System validates input",
                        "System creates user account",
                        "System sends confirmation email"
                    ],
                    "alternate_flows": ["Email already exists: System shows error"],
                    "postconditions": ["User account is created", "User can login"],
                    "priority": "high",
                    "business_value": "Essential for user management"
                },
                {
                    "id": "UC-002",
                    "title": "Create Task",
                    "description": "Users can create new tasks with details",
                    "actors": ["Registered User", "System"],
                    "preconditions": ["User is logged in"],
                    "main_flow": [
                        "User clicks 'New Task' button",
                        "User enters task details",
                        "User sets priority and due date",
                        "System saves task",
                        "System displays success message"
                    ],
                    "alternate_flows": ["Invalid data: System shows validation errors"],
                    "postconditions": ["Task is created in database"],
                    "priority": "high",
                    "business_value": "Core feature for task management"
                },
                {
                    "id": "UC-003",
                    "title": "View Dashboard",
                    "description": "Users can view task statistics and overview",
                    "actors": ["Registered User", "System"],
                    "preconditions": ["User is logged in"],
                    "main_flow": [
                        "User navigates to dashboard",
                        "System loads user's tasks",
                        "System calculates statistics",
                        "System displays dashboard"
                    ],
                    "alternate_flows": [],
                    "postconditions": ["Dashboard is displayed"],
                    "priority": "high",
                    "business_value": "Provides quick overview of tasks"
                },
                {
                    "id": "UC-004",
                    "title": "Filter Tasks",
                    "description": "Users can filter tasks by status and priority",
                    "actors": ["Registered User", "System"],
                    "preconditions": ["User is logged in", "Tasks exist"],
                    "main_flow": [
                        "User selects filter criteria",
                        "System applies filters",
                        "System displays filtered results"
                    ],
                    "alternate_flows": ["No results: System shows empty state"],
                    "postconditions": ["Filtered tasks are displayed"],
                    "priority": "medium",
                    "business_value": "Improves task discovery and organization"
                }
            ],
            "business_requirements": {
                "overview": "A modern task management application designed for individual productivity",
                "business_goals": [
                    "Increase user productivity",
                    "Provide simple task organization",
                    "Enable task tracking and completion"
                ],
                "success_criteria": [
                    "90% user satisfaction rate",
                    "50% increase in task completion",
                    "10,000 active users in first year"
                ],
                "constraints": [
                    "Must work on mobile and desktop",
                    "Budget: $50,000",
                    "Timeline: 12 weeks"
                ],
                "assumptions": [
                    "Users have internet access",
                    "Users prefer simple over complex features"
                ],
                "risks": [
                    {
                        "risk": "Low user adoption",
                        "mitigation": "Launch beta program and gather feedback"
                    },
                    {
                        "risk": "Technical complexity",
                        "mitigation": "Use proven technology stack"
                    }
                ]
            }
        }
        return json.dumps(data, indent=2)
    
    def _generate_mock_prd(self) -> str:
        """Generate mock PRD as text"""
        return """# Product Requirements Document

## Project Overview
Task Management Application - A modern productivity tool

## Core Features
1. User Authentication (email/password)
2. Task CRUD operations
3. Dashboard with statistics
4. Filtering and sorting

## Technical Stack
- Frontend: React.js
- Backend: Node.js
- Database: MongoDB
"""
    
    def _generate_prd_json(self) -> str:
        """Generate PRD in JSON/structured format"""
        import json
        return json.dumps({
            "title": "Product Requirements Document - Task Manager",
            "sections": {
                "overview": "Modern task management application",
                "features": ["Authentication", "Task Management", "Dashboard"],
                "tech_stack": {"frontend": "React", "backend": "Node.js", "database": "MongoDB"}
            }
        }, indent=2)
    
    def _generate_proposal_json(self) -> str:
        """Generate commercial proposal in JSON"""
        import json
        return json.dumps({
            "proposal": {
                "project_name": "Task Management App",
                "total_cost": 45000,
                "timeline_weeks": 12,
                "breakdown": {
                    "development": 30000,
                    "design": 8000,
                    "testing": 5000,
                    "deployment": 2000
                }
            }
        }, indent=2)
    
    def _generate_bom_json(self) -> str:
        """Generate BOM in JSON"""
        import json
        return json.dumps({
            "bill_of_materials": {
                "frontend": ["React 18.x", "Tailwind CSS"],
                "backend": ["Node.js 20.x", "Express.js"],
                "database": ["MongoDB Atlas"],
                "hosting": ["Vercel", "AWS EC2"]
            }
        }, indent=2)
    
    def _generate_architecture_json(self) -> str:
        """Generate architecture in JSON"""
        import json
        return json.dumps({
            "architecture": {
                "type": "Three-tier architecture",
                "layers": {
                    "frontend": "React SPA",
                    "backend": "REST API with Node.js",
                    "database": "MongoDB"
                },
                "security": ["HTTPS", "JWT", "Input validation"]
            }
        }, indent=2)
    
    def _generate_mock_mockup(self) -> str:
        """Generate mock mockup HTML"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Manager - Interactive Mockup</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .dashboard { 
            max-width: 1200px;
            width: 100%;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 32px; font-weight: 700; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 16px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-number { font-size: 36px; font-weight: 700; color: #667eea; }
        .stat-label { color: #666; margin-top: 8px; font-size: 14px; }
        .content { padding: 30px; }
        .section-title { font-size: 24px; font-weight: 600; margin-bottom: 20px; color: #333; }
        .task-list { display: grid; gap: 15px; }
        .task-card { 
            border: 2px solid #e9ecef;
            padding: 20px;
            border-radius: 12px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .task-card:hover { 
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }
        .task-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px; }
        .task-title { font-size: 18px; font-weight: 600; color: #333; }
        .priority-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .priority-high { background: #fee; color: #c00; }
        .priority-medium { background: #ffeaa7; color: #d63031; }
        .priority-low { background: #e3f2fd; color: #1565c0; }
        .task-description { color: #666; margin-bottom: 12px; line-height: 1.6; }
        .task-footer { display: flex; justify-content: space-between; align-items: center; font-size: 14px; }
        .task-status { 
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 500;
        }
        .status-todo { background: #e3f2fd; color: #1565c0; }
        .status-progress { background: #fff3e0; color: #e65100; }
        .status-done { background: #e8f5e9; color: #2e7d32; }
        .add-task-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 32px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }
        .add-task-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>📋 Task Management Dashboard</h1>
            <p>Organize, track, and complete your tasks efficiently</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">12</div>
                <div class="stat-label">Total Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">5</div>
                <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">7</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">3</div>
                <div class="stat-label">High Priority</div>
            </div>
        </div>
        
        <div class="content">
            <h2 class="section-title">Your Tasks</h2>
            <div class="task-list">
                <div class="task-card">
                    <div class="task-header">
                        <div class="task-title">Complete Project Documentation</div>
                        <span class="priority-badge priority-high">High Priority</span>
                    </div>
                    <div class="task-description">
                        Finalize all project documentation including technical specs, user guides, and API documentation.
                    </div>
                    <div class="task-footer">
                        <span>Due: Today</span>
                        <span class="task-status status-progress">In Progress</span>
                    </div>
                </div>
                
                <div class="task-card">
                    <div class="task-header">
                        <div class="task-title">Review Pull Requests</div>
                        <span class="priority-badge priority-medium">Medium</span>
                    </div>
                    <div class="task-description">
                        Review and approve pending pull requests from team members.
                    </div>
                    <div class="task-footer">
                        <span>Due: Tomorrow</span>
                        <span class="task-status status-todo">To Do</span>
                    </div>
                </div>
                
                <div class="task-card">
                    <div class="task-header">
                        <div class="task-title">Deploy to Production</div>
                        <span class="priority-badge priority-high">High Priority</span>
                    </div>
                    <div class="task-description">
                        Deploy the latest version to production environment after testing.
                    </div>
                    <div class="task-footer">
                        <span>Due: Next Week</span>
                        <span class="task-status status-todo">To Do</span>
                    </div>
                </div>
                
                <div class="task-card">
                    <div class="task-header">
                        <div class="task-title">Update Dependencies</div>
                        <span class="priority-badge priority-low">Low</span>
                    </div>
                    <div class="task-description">
                        Update all project dependencies to latest stable versions.
                    </div>
                    <div class="task-footer">
                        <span>Due: 2 weeks</span>
                        <span class="task-status status-done">Done</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <button class="add-task-btn" onclick="alert('Add Task functionality would open a modal here')">+</button>
    
    <script>
        // Add click handlers for interactivity
        document.querySelectorAll('.task-card').forEach(card => {
            card.addEventListener('click', function() {
                this.style.background = this.style.background === 'rgb(248, 249, 250)' ? 'white' : '#f8f9fa';
            });
        });
    </script>
</body>
</html>"""
    
    def _generate_mock_proposal(self) -> str:
        """Generate mock commercial proposal"""
        return """# Commercial Proposal

## Project: Task Management Application

### Investment Summary
**Total Project Cost:** $45,000
**Timeline:** 12 weeks
**Team Size:** 4 developers

### Cost Breakdown
1. Development: $30,000
2. Design: $8,000
3. Testing: $5,000
4. Deployment: $2,000

### Deliverables
- Fully functional web application
- User documentation
- Admin panel
- 3 months post-launch support

### ROI Projection
- Expected users: 5,000 in Year 1
- Revenue potential: $120,000/year
- Break-even: 6 months
"""
    
    def _generate_mock_bom(self) -> str:
        """Generate mock BOM"""
        return """# Bill of Materials

## Technical Stack

### Frontend
- React.js 18.x
- Tailwind CSS
- Axios for API calls

### Backend
- Node.js 20.x
- Express.js
- JWT authentication

### Database
- MongoDB Atlas
- Mongoose ODM

### Hosting
- Frontend: Vercel
- Backend: AWS EC2
- Database: MongoDB Atlas

### Third-party Services
- SendGrid (Email)
- Stripe (Payments)
"""
    
    def _generate_mock_architecture(self) -> str:
        """Generate mock architecture"""
        return """# System Architecture

## Architecture Overview
Three-tier architecture with React frontend, Node.js backend, and MongoDB database.

## Components

### Frontend Layer
- React SPA
- State management with Context API
- Responsive design

### Backend Layer
- RESTful API
- JWT authentication
- Business logic

### Data Layer
- MongoDB for persistence
- Redis for caching

## Security
- HTTPS encryption
- JWT tokens
- Input validation
"""
    
    def _generate_generic_response(self, message: str) -> str:
        """Generate generic mock response"""
        return f"""Based on the meeting transcript analysis:

Key points identified:
1. User requirements clearly defined
2. Technical approach outlined
3. Timeline and deliverables established

Recommendations:
- Proceed with proposed architecture
- Implement in phases
- Regular testing and feedback

This is a mock response for testing purposes."""
    
    def send_message(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Synchronous wrapper for send_message_async
        """
        import asyncio
        return asyncio.run(
            self.send_message_async(
                user_message=user_message,
                system_message=system_message,
                session_id=session_id,
                temperature=temperature,
                max_tokens=max_tokens
            )
        )
