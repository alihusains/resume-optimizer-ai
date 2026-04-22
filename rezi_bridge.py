import os
import logging
import requests
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class ReziBridge:
    """
    Bridge class to interface with the Rezi MCP server.
    Supports both local MCP tool calls and direct Streamable HTTP MCP at https://api.rezi.ai/mcp.

    Available MCP tools:
        - list_resumes: Returns authenticated user's resumes (ID, name, job title, last updated)
        - read_resume: Returns full JSON document for a single resume by resume_id
        - write_resume: Creates (no resume_id) or updates (with resume_id) a resume
    """

    MCP_ENDPOINT = "https://api.rezi.ai/mcp"

    def __init__(self, api_key: Optional[str] = None):
        self.mcp_prefix = "mcp__rezi"
        self.api_key = api_key or os.environ.get("REZI_API_KEY", "")

    # --- Streamable HTTP MCP Client ---

    def _mcp_call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC 2.0 request to the Rezi MCP endpoint.
        Streamable HTTP transport per MCP spec.
        """
        if not self.api_key:
            return {"error": "No REZI_API_KEY set. Export it or pass to ReziBridge(api_key=...)"}

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            response = requests.post(
                self.MCP_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            if "error" in result:
                logger.error(f"MCP error: {result['error']}")
                return {"error": result["error"]}
            return result.get("result", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"MCP request failed: {e}")
            return {"error": str(e)}

    def list_resumes(self) -> Dict[str, Any]:
        """
        List all resumes for the authenticated user.
        Returns lightweight summaries: ID, name, job title, last updated.
        """
        return self._mcp_call("tools/call", {
            "name": "list_resumes",
            "arguments": {},
        })

    def read_resume(self, resume_id: str) -> Dict[str, Any]:
        """
        Read the full JSON document for a single resume.
        """
        return self._mcp_call("tools/call", {
            "name": "read_resume",
            "arguments": {"resume_id": resume_id},
        })

    def write_resume(self, data: Dict[str, Any], resume_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new resume (no resume_id) or update existing (with resume_id).
        """
        args: Dict[str, Any] = {"data": data}
        if resume_id:
            args["resume_id"] = resume_id

        return self._mcp_call("tools/call", {
            "name": "write_resume",
            "arguments": args,
        })

    # --- Data Mapping ---

    def format_for_rezi(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maps internal structured resume data to Rezi's expected schema.
        """
        rezi_data: Dict[str, Any] = {
            "contact": structured_data.get("contact_info", {}),
            "experience": [],
            "education": [],
            "skills": structured_data.get("skills", []),
            "projects": [],
        }

        for exp in structured_data.get("experience", []):
            rezi_data["experience"].append({
                "company": exp.get("company", ""),
                "role": exp.get("role", ""),
                "location": exp.get("location", ""),
                "date_range": exp.get("dates", ""),
                "bullets": exp.get("bullets", []),
            })

        return rezi_data

    # --- Legacy MCP Tool Call Builders ---

    def get_create_resume_call(self, title: str, structured_data: Dict[str, Any]):
        """
        Returns the tool name and arguments for creating a resume via local MCP.
        """
        rezi_payload = self.format_for_rezi(structured_data)
        return f"{self.mcp_prefix}__create_resume", {
            "title": title,
            "data": rezi_payload,
        }

    def get_optimize_section_call(self, resume_id: str, section_type: str, content: Any, keywords: Optional[List[str]] = None):
        """
        Returns the tool call for optimizing a specific section via local MCP.
        """
        return f"{self.mcp_prefix}__optimize_section", {
            "resume_id": resume_id,
            "section_type": section_type,
            "content": content,
            "keywords": keywords or [],
        }

    # --- High-Level Operations ---

    def push_optimized_resume(self, title: str, structured_data: Dict[str, Any], resume_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Push optimized resume data to Rezi via MCP HTTP.
        Creates new if no resume_id, updates existing otherwise.
        """
        rezi_payload = self.format_for_rezi(structured_data)
        rezi_payload["title"] = title

        result = self.write_resume(rezi_payload, resume_id=resume_id)
        if "error" not in result:
            logger.info(f"Successfully pushed resume to Rezi: {title}")
        return result
