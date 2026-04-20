"""
ATS Scoring Module - Advanced Professional Edition
Implements a strict scoring framework and critical AI-powered evaluation.
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "resume_audit.log")
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

class ATSScorer:
    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self.model = llm_client.get_model_name() if llm_client else "unknown"

        self.strong_action_verbs = {
            "led", "managed", "developed", "created", "implemented", "increased",
            "reduced", "achieved", "delivered", "optimized", "orchestrated",
            "spearheaded", "generated", "negotiated", "cultivated", "analyzed",
            "formulated", "executed", "accelerated", "pioneered", "transformed"
        }

    def score_all(
        self,
        optimized_resume: str,
        job_description: Optional[str] = None,
        target_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Run Deterministic ATS Resume Analysis with strict scoring framework.
        """
        # The AI now handles the entire deterministic scoring logic as per the new instructions
        results = self._score_ai_powered(
            optimized_resume, job_description, target_keywords or []
        )

        # Add overall summary for compatibility with existing UI expectations
        if "scores" in results and not results.get("error"):
            overall_score = results["scores"].get("overall_score", 0)
            results["overall"] = {
                "score": overall_score,
                "grade": self._get_grade(overall_score),
                "breakdown": {
                    "ATS Compatibility": results["scores"].get("ats_compatibility", 0),
                    "Content Impact": results["scores"].get("content_impact", 0),
                    "Readability": results["scores"].get("readability", 0),
                    "Keywords": results["scores"].get("keyword_strength", 0),
                    "Role Alignment": results["scores"].get("role_alignment", 0)
                }
            }
            # Roadmap mapping
            results["roadmap"] = [rec.get("issue") for rec in results.get("recommendations", [])]

        results["raw_text"] = optimized_resume
        return results

    def _score_ai_powered(
        self,
        optimized_resume: str,
        job_description: Optional[str] = None,
        target_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Deterministic ATS Resume Evaluation Engine."""
        logger.info(f"--- START DETERMINISTIC AI AUDIT ---")

        try:
            prompt = f"""You are a deterministic ATS Resume Evaluation Engine.

Your task is to evaluate resumes extracted from PDF files with strict, rule-based scoring that simulates real ATS systems and experienced recruiters.

You MUST:
- Be strict and critical (do not inflate scores)
- Penalize heavily for missing metrics, weak bullets, and poor structure
- Quantify everything wherever possible
- Ensure scores match the analysis logically

---

# INPUT

RESUME TEXT:
{optimized_resume}

TARGET ROLE/JD (IF PROVIDED):
{job_description if job_description else "Infer from content"}

TARGET KEYWORDS (IF PROVIDED):
{', '.join(target_keywords) if target_keywords else "None specified"}

---

# SCORING MODEL (MANDATORY)

You MUST calculate scores using the formulas below.

---

## 1. ATS COMPATIBILITY (0–100) — Weight: 25%

Start at 100. Deduct:
- Tables / multi-column indicators: -20
- Missing standard sections: -15 per missing section
- Unclear section headings: -10
- Special characters / icons: -10
- Parsing ambiguity (merged text, broken bullets): -15
- Header/footer interference: -10

Minimum = 0

---

## 2. CONTENT IMPACT (0–100) — Weight: 25%

Let:
- total_bullets = number of bullets in experience
- bullets_with_metrics = bullets containing %, $, numbers, scale

Metric Score:
metric_ratio = bullets_with_metrics / total_bullets

Scoring:
- metric_ratio >= 0.6 → 90–100
- 0.4–0.59 → 70–89
- 0.2–0.39 → 40–69
- < 0.2 → 0–39

Then apply penalties:
- Weak verbs (Responsible for, Worked on): -10
- Repetition across bullets: -10
- No measurable outcomes: -20

---

## 3. READABILITY & STRUCTURE (0–100) — Weight: 20%

Start at 100. Deduct:
- More than 5 bullets per role: -10
- Inconsistent bullet formatting: -10
- Long sentences (>25 words): -10
- Poor spacing / dense text: -10
- Verb tense inconsistency: -10
- No clear section hierarchy: -15

---

## 4. KEYWORD STRENGTH (0–100) — Weight: 15%

Step 1: Infer role
Step 2: Generate expected keyword set (minimum 15 keywords)
Step 3:
keyword_coverage = matched_keywords / expected_keywords

Scoring:
- >= 70% → 85–100
- 50–69% → 70–84
- 30–49% → 40–69
- < 30% → 0–39

Penalty:
- Keyword stuffing detected: -15

---

## 5. ROLE ALIGNMENT (0–100) — Weight: 15%

Evaluate:
- Years of experience vs seniority
- Leadership signals
- Career progression consistency

Scoring:
- Strong alignment: 80–100
- Moderate: 60–79
- Weak: 30–59
- Poor/mismatch: <30

---

## FINAL SCORE

Compute:
overall_score = (ATS * 0.25) + (Impact * 0.25) + (Readability * 0.20) + (Keywords * 0.15) + (Role Alignment * 0.15)
Round to nearest integer.

---

# BULLET CLASSIFICATION (MANDATORY)

For EACH bullet:
- STRONG: Action verb + metric + outcome
- MEDIUM: Action verb, no metric
- WEAK: Generic responsibility / vague / no outcome

---

# OUTPUT FORMAT (STRICT JSON ONLY)

{{
  "candidate_summary": {{
    "inferred_role": "",
    "seniority_level": "",
    "years_of_experience": ""
  }},
  "scores": {{
    "overall_score": 0,
    "ats_compatibility": 0,
    "content_impact": 0,
    "readability": 0,
    "keyword_strength": 0,
    "role_alignment": 0
  }},
  "score_breakdown_explanation": {{
    "ats_compatibility": "",
    "content_impact": "",
    "readability": "",
    "keyword_strength": "",
    "role_alignment": ""
  }},
  "mistakes": {{
    "critical": [],
    "major": [],
    "minor": []
  }},
  "content_analysis": {{
    "total_bullets": 0,
    "bullets_with_metrics": 0,
    "metric_ratio": 0,
    "bullet_classification": {{
      "strong": 0,
      "medium": 0,
      "weak": 0
    }},
    "weak_bullet_examples": [
      {{
        "original": "",
        "improved": ""
      }}
    ]
  }},
  "keyword_analysis": {{
    "expected_keywords": [],
    "present_keywords": [],
    "missing_keywords": [],
    "coverage_percentage": 0
  }},
  "ats_issues": [
    {{
      "issue": "",
      "severity": "High | Medium | Low",
      "impact": ""
    }}
  ],
  "recommendations": [
    {{
      "priority": 1,
      "issue": "",
      "fix": "",
      "expected_impact": ""
    }}
  ]
}}"""

            # Use chat interface of UniversalLLMClient
            messages = [
                {"role": "system", "content": "You are a senior executive recruiter and ATS expert. You provide objective, critical, and actionable feedback strictly in JSON format."},
                {"role": "user", "content": prompt}
            ]
            response = self.llm_client.chat(messages, temperature=0.1)

            try:
                # Clean response if LLM added markdown backticks
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0].strip()

                result = json.loads(response)
                return result
            except Exception as e:
                logger.error(f"Failed to parse AI JSON: {e}. Raw response: {response[:500]}")
                return {
                    "error": "AI response parsing failed",
                    "scores": {"overall_score": 0, "ats_compatibility": 0, "content_impact": 0, "readability": 0, "keyword_strength": 0, "role_alignment": 0}
                }
        except Exception as e:
            logger.error(f"AI Audit Error: {e}")
            return {
                "error": str(e),
                "scores": {"overall_score": 0, "ats_compatibility": 0, "content_impact": 0, "readability": 0, "keyword_strength": 0, "role_alignment": 0}
            }

    def _get_grade(self, score: float) -> str:
        if score >= 95: return "A++"
        if score >= 90: return "A+"
        if score >= 85: return "A"
        if score >= 80: return "A-"
        if score >= 70: return "B"
        if score >= 60: return "C"
        return "F"
