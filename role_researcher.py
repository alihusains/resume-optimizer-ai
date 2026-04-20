import os
import sys
import json
import re
from typing import Dict, List, Any

# Add necessary paths
REPOS_DIR = "/Users/alihusainsorathiya/Documents/resume"
AI_AGENT_SRC = os.path.join(REPOS_DIR, 'AIAGENT', 'src')
if AI_AGENT_SRC not in sys.path:
    sys.path.insert(0, AI_AGENT_SRC)

# Note: We rely on the environment having the necessary LLM clients
# but for this script we assume it's used within a session where we can call Agent/Tools.

class RoleResearcher:
    """
    Handles research for target roles and locations to identify keywords and requirements.
    """
    def __init__(self, llm_client=None):
        self.llm = llm_client

    def research_role(self, role: str, location: str) -> Dict[str, Any]:
        """
        Researches the target role and location using AI.
        """
        prompt = f"""
        Research and identify the key requirements for the role of '{role}' in '{location}'.
        Your goal is to provide the exact data needed for ATS optimization.

        Return a STRICT JSON object with these keys:
        1. "keywords": List of the top 15 ATS-critical keywords/skills for this specific role.
        2. "technical_skills": List of must-have technologies or tools.
        3. "kpis": List of 5-7 quantifiable metrics/KPIs typically expected for this level of role (e.g., "Revenue growth %", "Uptime", "Team size").
        4. "soft_skills": List of 5 key interpersonal skills.
        5. "market_insights": A brief 1-sentence note on the current market demand for this role in the specified location.
        """

        if not self.llm:
            return {"role": role, "location": location, "status": "no_llm_client", "keywords": [], "kpis": []}

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])

            # Clean response if LLM added markdown backticks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            research_data = json.loads(response)
            research_data["role"] = role
            research_data["location"] = location
            research_data["status"] = "success"
            return research_data
        except Exception as e:
            return {
                "role": role,
                "location": location,
                "status": f"error: {str(e)}",
                "keywords": ["Leadership", "Management", "Strategy"],
                "kpis": ["Revenue", "Efficiency"]
            }
