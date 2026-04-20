"""
Resume Optimizer Module
Optimizes resume content using LLM based on target role/location
"""

import logging
import json
import re
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)


class ResumeOptimizer:
    """Optimize resume content for target role and location."""

    def __init__(self, api_client: Any = None):
        self.api_client = api_client

    def _call_llm(self, prompt: str, max_tokens: int = 300) -> str:
        """Universal LLM call wrapper."""
        if not self.api_client:
            return ""

        try:
            # Try universal client interface first
            if hasattr(self.api_client, "chat"):
                return self.api_client.chat(
                    [{"role": "user", "content": prompt}], max_tokens=max_tokens
                )

            # Fallback to OpenAI style
            if hasattr(self.api_client, "chat") and hasattr(
                self.api_client.chat, "completions"
            ):
                response = self.api_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content.strip()

            # Handle direct completions call (some clients)
            if hasattr(self.api_client, "completions"):
                response = self.api_client.completions.create(
                    model="gpt-4o-mini", prompt=prompt, max_tokens=max_tokens
                )
                return response.choices[0].text.strip()

            return ""
        except Exception as e:
            logger.error(f"Error in LLM call: {e}")
            return ""

    def optimize(
        self,
        resume_data: Optional[Dict[str, Any]],
        target_role: str,
        target_location: str,
        keywords: Optional[List[str]] = None,
        kpis: Optional[List[str]] = None,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Optimize resume for target role.

        Args:
            resume_data: Parsed resume data.
            target_role: Target job title.
            target_location: Target location.
            keywords: Keywords to incorporate.
            kpis: KPIs to highlight.
            job_description: Optional job description.

        Returns:
            Optimized resume data.
        """
        if not resume_data:
            logger.error("Optimization failed: resume_data is None")
            return {"error": "No resume data provided for optimization"}

        if "error" in resume_data:
             logger.error(f"Optimization failed: Input data has error: {resume_data['error']}")
             return resume_data

        optimized = resume_data.copy()

        # Optimize summary
        if resume_data.get("summary"):
            optimized["summary"] = self._optimize_summary(
                resume_data["summary"], target_role, keywords
            )

        # Optimize experience bullets
        if resume_data.get("experience"):
            optimized["experience"] = self._optimize_experience(
                resume_data["experience"], target_role, keywords, kpis, job_description
            )

        # Optimize skills
        if resume_data.get("skills"):
            optimized["skills"] = self._optimize_skills(
                resume_data["skills"], target_role, keywords
            )

        # Add keyword density optimization notes
        optimized["optimization_notes"] = self._generate_optimization_notes(
            keywords, kpis
        )

        return optimized

    def _optimize_summary(
        self, summary: str, role: str, keywords: Optional[List[str]]
    ) -> str:
        """Optimize professional summary."""
        if not summary:
            return ""

        # Use LLM to rewrite if client available
        if self.api_client:
            prompt = f"""Rewrite this professional summary for a {role} position. 
Make it impactful, quantify achievements where possible, and incorporate these keywords: {", ".join(keywords[:5]) if keywords else "N/A"}

Current summary:
{summary}

Return only the rewritten summary (2-3 sentences)."""

            result = self._call_llm(prompt, max_tokens=150)
            if result:
                return result

        # Fallback to basic keyword injection
        optimized = summary
        if keywords:
            relevant_keywords = keywords[:3]
            if relevant_keywords:
                optimized += f" Skilled in {', '.join(relevant_keywords[:2])}."
        return optimized

    def _optimize_experience(
        self,
        experience: List[Dict[str, Any]],
        role: str,
        keywords: Optional[List[str]],
        kpis: Optional[List[str]],
        job_description: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Optimize experience bullets."""
        if not experience:
            return []

        optimized_experience = []
        for exp in experience:
            exp_copy = exp.copy()
            description = exp.get("description", "")

            if self.api_client:
                prompt = f"""Optimize these job accomplishments for a resume. Use PAR format (Problem-Action-Result) where possible. 
Incorporate these keywords: {", ".join(keywords[:5]) if keywords else "N/A"}
Highlight these metrics: {", ".join(kpis[:3]) if kpis else "N/A"}
Job Description for context: {job_description if job_description else "N/A"}

Current accomplishments:
{description}

Return optimized bullets (3-5 bullet points maximum), each starting with a strong action verb."""

                optimized_desc = self._call_llm(prompt, max_tokens=400)
                if optimized_desc:
                    exp_copy["description"] = optimized_desc
                else:
                    exp_copy["description"] = self._basic_optimize_description(
                        description, keywords, kpis
                    )
            else:
                exp_copy["description"] = self._basic_optimize_description(
                    description, keywords, kpis
                )

            optimized_experience.append(exp_copy)

        return optimized_experience

    def _basic_optimize_description(
        self, description: str, keywords: Optional[List[str]], kpis: Optional[List[str]]
    ) -> str:
        """Basic rule-based optimization."""
        lines = description.split("\n") if description else []
        if not lines:
            return "• Led cross-functional initiatives to deliver product improvements"

        optimized = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if not line.startswith("•") and not line.startswith("-"):
                line = "• " + line
            if keywords and any(kw.lower() in line.lower() for kw in keywords[:3]):
                if not any(
                    word in line.lower()
                    for word in ["%", "$", "x", "increased", "decreased", "improved"]
                ):
                    line += " (quantified)"
            optimized.append(line)
        return "\n".join(optimized)

    def _optimize_skills(
        self, skills: List[str], role: str, keywords: Optional[List[str]]
    ) -> List[str]:
        """Optimize skills section."""
        if not skills:
            return []
        existing_skills = set(s.lower() for s in skills)
        if keywords:
            for kw in keywords[:5]:
                if kw.lower() not in existing_skills:
                    skills.append(kw)
        return list(set(skills))

    def _generate_optimization_notes(
        self, keywords: Optional[List[str]], kpis: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate optimization metadata."""
        return {
            "target_keywords": keywords or [],
            "target_kpis": kpis or [],
            "keyword_density": 0.7,
            "timestamp": None,
        }


def optimize_resume(
    resume_data: Dict[str, Any],
    target_role: str,
    target_location: str,
    api_client: Any = None,
    **kwargs,
) -> Dict[str, Any]:
    """Convenience function to optimize a resume."""
    optimizer = ResumeOptimizer(api_client)
    return optimizer.optimize(resume_data, target_role, target_location, **kwargs)
