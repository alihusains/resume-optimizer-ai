import json
import os
import sys
from typing import Dict, List, Any

class ReziBridge:
    """
    Bridge class to interface with the Rezi MCP server.
    Handles mapping internal resume data to Rezi's platform schema.
    """

    def __init__(self):
        # The MCP server name prefix as defined in tool configuration
        self.mcp_prefix = "mcp__rezi"

    def format_for_rezi(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps internal structured resume data to Rezi's expected schema.
        """
        rezi_data = {
            "contact": structured_data.get("contact_info", {}),
            "experience": [],
            "education": [],
            "skills": structured_data.get("skills", []),
            "projects": []
        }

        # Map experience
        for exp in structured_data.get("experience", []):
            rezi_data["experience"].append({
                "company": exp.get("company", ""),
                "role": exp.get("role", ""),
                "location": exp.get("location", ""),
                "date_range": exp.get("dates", ""),
                "bullets": exp.get("bullets", [])
            })

        return rezi_data

    def get_create_resume_call(self, title: str, structured_data: Dict[str, Any]):
        """
        Returns the tool name and arguments for creating a resume.
        """
        rezi_payload = self.format_for_rezi(structured_data)
        return f"{self.mcp_prefix}__create_resume", {
            "title": title,
            "data": rezi_payload
        }

    def get_optimize_section_call(self, resume_id: str, section_type: str, content: Any, keywords: List[str] = None):
        """
        Returns the tool call for optimizing a specific section.
        """
        return f"{self.mcp_prefix}__optimize_section", {
            "resume_id": resume_id,
            "section_type": section_type,
            "content": content,
            "keywords": keywords or []
        }
