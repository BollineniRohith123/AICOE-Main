"""
Transcript Agent - Processes raw meeting transcripts into structured notes
"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentConfig, AgentResult
import json


class IntakeAgent(BaseAgent):
    """
    Agent responsible for processing raw transcripts into structured notes
    Extracts: Company profile, attendees, objectives, discussion points, action items
    """
    
    def __init__(self, llm_client):
        config = AgentConfig(
            name="IntakeAgent",
            description="Processes raw meeting transcripts into structured notes",
            model="x-ai/grok-code-fast-1",  # GLM-4.6 via OpenRouter
            temperature=0.3,  # Lower temperature for factual extraction
            max_tokens=12000
        )
        super().__init__(config, llm_client)
    
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> AgentResult:
        """
        Process transcript and extract structured information
        
        Input:
            - transcript: Raw meeting transcript text
            - project_name: Name of the project
            
        Output:
            - structured_notes: Dict with structured meeting information
        """
        try:
            self.log_execution("start", "Processing transcript")
            self.validate_input(input_data, ["transcript", "project_name"])
            
            transcript = input_data["transcript"]
            project_name = input_data["project_name"]
            
            # Create prompt for extracting structured notes
            system_message = """You are an expert at analyzing meeting transcripts and extracting structured information.
Your task is to carefully read meeting transcripts and extract key information in a well-organized format."""
            
            user_message = f"""Analyze the following meeting transcript and extract structured information.

Project Name: {project_name}

Transcript:
{transcript}

Please extract and structure the following information in XML format:

<structured_notes>
    <project_name>{project_name}</project_name>
    <company_overview>Brief description of the company/organization (if mentioned, or "Not specified")</company_overview>
    <attendees>
        <attendee>Name and role</attendee>
        <!-- Add more attendee elements as needed -->
    </attendees>
    <meeting_date>Date of meeting (if mentioned, or "Not specified")</meeting_date>
    <meeting_objective>Main purpose/goal of the meeting</meeting_objective>
    <key_discussion_points>
        <point>Discussion point 1</point>
        <!-- Add at least 5-7 key discussion points -->
    </key_discussion_points>
    <pain_points>
        <pain_point>Challenge or problem 1</pain_point>
        <!-- Add more pain points as identified -->
    </pain_points>
    <requirements>
        <requirement>Requirement 1</requirement>
        <!-- Add more requirements as mentioned -->
    </requirements>
    <decisions_made>
        <decision>Decision 1</decision>
        <!-- Add more decisions as reached -->
    </decisions_made>
    <action_items>
        <action_item>Follow-up action 1</action_item>
        <!-- Add more action items if any -->
    </action_items>
    <technical_constraints>
        <constraint>Technical limitation 1</constraint>
        <!-- Add more constraints as mentioned -->
    </technical_constraints>
    <stakeholders>
        <stakeholder>Stakeholder name and role</stakeholder>
        <!-- Add more stakeholders as mentioned -->
    </stakeholders>
</structured_notes>

Return ONLY valid XML without any markdown formatting or explanations. The XML should be well-formed and parseable."""

            self.log_execution("llm_call", "Extracting structured information")
            response = await self._call_llm(system_message, user_message, max_retries=3)

            # Parse XML response
            structured_notes_xml = response.strip()
            if structured_notes_xml.startswith("```xml"):
                structured_notes_xml = structured_notes_xml.split("```xml")[1].split("```")[0].strip()
            elif structured_notes_xml.startswith("```"):
                structured_notes_xml = structured_notes_xml.split("```")[1].split("```")[0].strip()

            self.log_execution(
                "success",
                f"Extracted structured notes XML ({len(structured_notes_xml)} characters)"
            )

            return AgentResult(
                success=True,
                data={
                    "structured_notes_xml": structured_notes_xml,
                    "project_name": project_name,
                    "transcript_length": len(transcript)
                },
                metadata={
                    "agent": self.config.name,
                    "output_format": "xml"
                }
            )
                
        except Exception as e:
            self.logger.error(f"Error in TranscriptAgent: {str(e)}")
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"agent": self.config.name}
            )
