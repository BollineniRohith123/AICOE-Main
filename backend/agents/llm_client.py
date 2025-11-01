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
        
        # Generate mock responses based on message content
        if "PRD" in user_message or "product requirements" in user_message.lower():
            response = self._generate_mock_prd()
        elif "mockup" in user_message.lower() or "design" in user_message.lower():
            response = self._generate_mock_mockup()
        elif "commercial proposal" in user_message.lower() or "proposal" in user_message.lower():
            response = self._generate_mock_proposal()
        elif "BOM" in user_message or "bill of materials" in user_message.lower():
            response = self._generate_mock_bom()
        elif "architecture" in user_message.lower() or "technical" in user_message.lower():
            response = self._generate_mock_architecture()
        else:
            response = self._generate_generic_response(user_message)
        
        self.logger.info(f"🟢 MOCK API CALL SUCCESS | Response: {len(response)} chars")
        return response
    
    def _generate_mock_prd(self) -> str:
        """Generate mock PRD content"""
        return """# Product Requirements Document (PRD)

## Project Overview
**Project Name:** Task Management Application
**Version:** 1.0
**Date:** November 2025

## Executive Summary
A modern, intuitive task management application designed to help users organize and track their daily tasks efficiently.

## Product Vision
Create a clean, Apple-inspired task management solution that focuses on simplicity and user experience.

## Core Features

### 1. User Authentication
- Email and password-based registration
- Secure login system
- User profile management

### 2. Task Management
- Create tasks with title, description, due date
- Priority levels: Low, Medium, High
- Status tracking: To Do, In Progress, Done
- Edit and delete tasks

### 3. Dashboard
- Overview of all tasks
- Statistics by status
- Upcoming tasks view
- Quick task creation

### 4. Filtering & Sorting
- Filter by status and priority
- Sort by due date or creation date

## Technical Requirements
- Frontend: React.js
- Backend: Node.js/Express
- Database: MongoDB
- Modern, responsive design

## Success Metrics
- User engagement rate
- Task completion rate
- User satisfaction score
"""
    
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
