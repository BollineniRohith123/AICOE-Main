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
    
    def _generate_mock_mockup(self) -> str:
        """Generate mock mockup HTML"""
        return """<!DOCTYPE html>
<html>
<head>
    <title>Task Manager Mockup</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .dashboard { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; }
        .task-list { display: grid; gap: 15px; margin-top: 20px; }
        .task-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Task Management Dashboard</h1>
        </div>
        <div class="task-list">
            <div class="task-card">
                <h3>Sample Task 1</h3>
                <p>Complete project documentation</p>
                <span>Priority: High</span>
            </div>
        </div>
    </div>
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
