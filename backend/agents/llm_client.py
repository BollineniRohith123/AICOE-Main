"""
OpenRouter LLM Client
Real implementation using OpenRouter API with OpenAI SDK compatibility
"""
import os
from typing import Optional, Dict, Any
import asyncio
import aiohttp
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    OpenRouter LLM Client using direct HTTP requests for maximum compatibility
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openrouter",
        model: str = "x-ai/grok-code-fast-1"
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("API key not provided and OPENROUTER_API_KEY not found in environment")
        
        self.provider = provider
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.logger = logging.getLogger("llm_client")
        self.logger.info(f"🚀 OpenRouter LLM Client initialized | Model: {self.model}")
    
    async def send_message_async(
        self,
        user_message: str,
        system_message: str = "You are a helpful AI assistant.",
        session_id: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Send message to OpenRouter API
        
        Args:
            user_message: The user's message
            system_message: System prompt
            session_id: Session ID for chat context (optional)
            temperature: Temperature for generation (0.0-2.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLM response text
        """
        try:
            # Log API call start
            self.logger.info(f"🔵 OpenRouter API Call | Model: {self.model} | Temp: {temperature} | Max tokens: {max_tokens}")
            self.logger.info(f"   Message length: {len(user_message)} chars")
            
            # Prepare request payload according to OpenRouter API spec
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Add session context if provided
            if session_id:
                payload["metadata"] = {"session_id": session_id}
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://aicoe-platform.local",
                "X-Title": "AICOE Automation Platform"
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minute timeout
                ) as response:
                    
                    # Check response status
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"🔴 OpenRouter API Error | Status: {response.status} | Error: {error_text}")
                        raise Exception(f"OpenRouter API error {response.status}: {error_text}")
                    
                    # Parse response
                    response_data = await response.json()
                    
                    # Extract message content
                    if "choices" not in response_data or not response_data["choices"]:
                        raise Exception("No choices in OpenRouter response")
                    
                    message_content = response_data["choices"][0]["message"]["content"]
                    
                    # Log usage statistics if available
                    usage = response_data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)
                    
                    self.logger.info(f"🟢 OpenRouter API Success | Response: {len(message_content)} chars")
                    self.logger.info(f"   Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total")
                    
                    return message_content
                    
        except asyncio.TimeoutError:
            self.logger.error("🔴 OpenRouter API Timeout")
            raise Exception("OpenRouter API request timed out")
        except aiohttp.ClientError as e:
            self.logger.error(f"🔴 OpenRouter API Client Error: {str(e)}")
            raise Exception(f"OpenRouter API client error: {str(e)}")
        except json.JSONDecodeError as e:
            self.logger.error(f"🔴 OpenRouter API JSON Decode Error: {str(e)}")
            raise Exception(f"Failed to parse OpenRouter API response: {str(e)}")
        except Exception as e:
            self.logger.error(f"🔴 OpenRouter API Unexpected Error: {str(e)}")
            raise Exception(f"OpenRouter API call failed: {str(e)}")
    
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
