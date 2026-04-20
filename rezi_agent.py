import os
import sys
import json
import yaml
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- Path Configuration ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENT_SRC = os.path.join(CURRENT_DIR, "src")

if os.path.exists(AI_AGENT_SRC):
    if AI_AGENT_SRC not in sys.path:
        sys.path.insert(0, AI_AGENT_SRC)

try:
    from parser import ResumeParser
    from ats_scorer import ATSScorer
    from optimizer import ResumeOptimizer
    from rezi_bridge import ReziBridge
    from role_researcher import RoleResearcher
    from llm import create_from_config_file, create_llm_client
except ImportError as e:
    logger.error(f"Import Error: {e}")
    logger.debug(f"Current sys.path: {sys.path}")
    raise

class ReziResumeAgent:
    """
    Main Agent that orchestrates the Rezi Resume Optimization workflow.
    """
    def __init__(self, cv_path: str, model_name: Optional[str] = None):
        self.cv_path = cv_path

        # Load configuration
        config_path = os.path.join(CURRENT_DIR, 'config.yaml')
        if not os.path.exists(config_path):
             config_path = os.path.join(CURRENT_DIR, "config.yaml.template")

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        api_config = config.get("api", {})
        api_base_url = api_config.get("base_url", "http://127.0.0.1:9090/v1")
        api_key = api_config.get("api_key", "dummy")

        # Initialize LLM client
        if model_name:
            # Determine provider based on base_url
            if "anthropic" in api_base_url:
                provider = "anthropic"
            elif "localhost" in api_base_url or "127.0.0.1" in api_base_url:
                provider = "openai"  # Local OpenAI-compatible
            elif "openai" in api_base_url:
                provider = "openai"
            else:
                provider = "openai"  # Default
                
            self.llm_client = create_llm_client(
                provider=provider,
                api_key=api_key,
                base_url=api_base_url,
                model=model_name
            )
        else:
            self.llm_client = create_from_config_file(config_path)
            
        self.model = self.llm_client.get_model_name()
        logger.info(f"Initialized ReziResumeAgent with model: {self.model}")

        # Initialize components with config
        self.parser = ResumeParser(llm_client=self.llm_client)
        self.scorer = ATSScorer(llm_client=self.llm_client)
        self.optimizer = ResumeOptimizer(api_client=self.llm_client)
        self.bridge = ReziBridge()
        self.researcher = RoleResearcher(llm_client=self.llm_client)

        self.structured_data: Optional[Dict[str, Any]] = None
        self.analysis_results: Optional[Dict[str, Any]] = None

    @staticmethod
    def get_available_models(api_base_url: str = "http://127.0.0.1:9090/v1") -> list:
        """
        Fetch available models from the API.
        """
        try:
            # Ensure URL is properly formatted
            if api_base_url.endswith("/v1"):
                url = f"{api_base_url}/models"
            else:
                url = f"{api_base_url.rstrip('/')}/models"
                
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                if isinstance(models_data, dict) and "data" in models_data:
                    return [m["id"] for m in models_data["data"]]
                elif isinstance(models_data, list):
                    return [m.get("id") for m in models_data if "id" in m]
                return []
            return []
        except Exception as e:
            logger.error(f"Error fetching models from {api_base_url}: {e}")
            return []

    def analyze_resume(self) -> Dict[str, Any]:
        """
        Parse and Score the current resume.

        Returns:
            Dict containing ATS scores and feedback.
        """
        logger.info(f"Analyzing resume: {self.cv_path}")
        self.structured_data = self.parser.parse(self.cv_path)

        if not self.structured_data or self.structured_data.get("error"):
            error_msg = self.structured_data.get("error", "Unknown parsing error") if self.structured_data else "Failed to parse resume"
            logger.error(error_msg)
            if self.structured_data is None:
                self.structured_data = {"error": error_msg}
            return {"error": error_msg}

        raw_text = self.structured_data.get("raw_text", "")
        if not raw_text:
            logger.warning("No text extracted from resume. Using structured data string as fallback.")
            raw_text = str(self.structured_data)

        self.analysis_results = self.scorer.score_all(
            optimized_resume=raw_text
        )
        return self.analysis_results

    def optimize_and_sync(self, target_role: str, target_location: str) -> Dict[str, Any]:
        """
        Research, Optimize, and prepare Sync for Rezi.
        
        Args:
            target_role: The job title to optimize for.
            target_location: The geographical location for the role.
            
        Returns:
            Dict containing optimized data and Rezi MCP tool call arguments.
        """
        logger.info(f"Optimizing for {target_role} in {target_location}...")

        if not self.structured_data:
            logger.error("Optimization failed: No structured data available. Run analyze_resume first.")
            return {"error": "No structured data available. Please run analysis first."}
            
        if self.structured_data.get("error"):
            logger.error(f"Optimization failed: Previous parsing error: {self.structured_data.get('error')}")
            return {"error": f"Cannot optimize due to previous parsing error: {self.structured_data.get('error')}"}

        # 1. Research role requirements
        research_data = self.researcher.research_role(target_role, target_location)
        keywords = research_data.get("keywords", [])
        kpis = research_data.get("kpis", [])

        # 2. Optimize content with quantifiable impacts
        optimized_data = self.optimizer.optimize(
            self.structured_data,
            target_role=target_role,
            target_location=target_location,
            keywords=keywords,
            kpis=kpis
        )
        
        if not optimized_data or "error" in optimized_data:
            error_msg = optimized_data.get("error", "Unknown optimization error") if optimized_data else "Failed to optimize content"
            logger.error(error_msg)
            return {"error": error_msg}

        # 3. Prepare Rezi MCP tool call
        tool_name, args = self.bridge.get_create_resume_call(
            title=f"Optimized - {target_role}",
            structured_data=optimized_data
        )

        return {
            "optimized_data": optimized_data,
            "rezi_tool": tool_name,
            "rezi_args": args
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        agent = ReziResumeAgent(sys.argv[1])
        results = agent.analyze_resume()
        print(json.dumps(results, indent=2))
    else:
        logger.warning("No resume path provided.")
        print("Usage: python rezi_agent.py <path_to_resume>")
