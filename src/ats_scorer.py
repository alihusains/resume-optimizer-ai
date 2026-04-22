"""
ATS Scoring Module - Hybrid Architecture (Rules + LLM)

Architecture:
    PDF -> Text Extraction -> Rule Engine (Python) -> LLM Critique -> Score Validator -> Output

The Rule Engine handles ALL scoring, counting, and classification.
The LLM is restricted to: explain, critique, rewrite, keyword analysis, role alignment.
"""

import json
import logging
import os
import sys
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

# Import rule engine
_rule_engine_paths = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "Resume Optimizations"),
    "/Users/alihusainsorathiya/Documents/resume/Resume Optimizations",
]
for _path in _rule_engine_paths:
    if os.path.exists(_path) and _path not in sys.path:
        sys.path.insert(0, _path)
        break

import rule_engine


class ATSScorer:
    def __init__(self, llm_client: Any = None):
        self.llm_client = llm_client
        self.model = llm_client.get_model_name() if llm_client else "unknown"

    def score_all(
        self,
        optimized_resume: str,
        job_description: Optional[str] = None,
        target_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Hybrid ATS Resume Analysis: Rule Engine + LLM Critique.

        Step 1: Rule engine computes deterministic scores
        Step 2: LLM provides critique, rewrites, keyword/role analysis
        Step 3: Merge results and validate final scores
        """
        logger.info("--- START HYBRID ANALYSIS ---")

        # STEP 1: Deterministic Rule Engine
        logger.info("Step 1: Running deterministic rule engine...")
        engine_result = rule_engine.analyze(optimized_resume)

        logger.info(
            f"Rule engine: {engine_result.total_bullets} bullets, "
            f"metric_ratio={engine_result.metric_ratio}, "
            f"classification={engine_result.bullet_classification}"
        )

        # STEP 2: LLM Critique (scores are pre-computed, LLM only explains/rewrites)
        logger.info("Step 2: Running LLM critique...")
        llm_result = self._get_llm_critique(engine_result, job_description, target_keywords or [])

        # STEP 3: Merge deterministic scores with LLM insights
        logger.info("Step 3: Merging results and validating...")
        merged = self._merge_results(engine_result, llm_result)

        merged["raw_text"] = optimized_resume
        return merged

    def _get_llm_critique(
        self,
        engine_result: rule_engine.RuleEngineResult,
        job_description: Optional[str],
        target_keywords: List[str],
    ) -> Dict[str, Any]:
        """
        LLM role: Resume Critic + Rewriter, NOT Score Calculator.

        The LLM receives pre-computed structured data and provides:
        - Keyword analysis (requires domain knowledge)
        - Role alignment assessment
        - Mistake explanations
        - Bullet rewrites
        - Recommendations
        """
        if not self.llm_client:
            return {"error": "No LLM client available"}

        # Build weak bullets list for rewrite requests
        weak_bullets = [
            ba.text for ba in engine_result.bullet_analyses
            if ba.classification == "weak"
        ][:8]  # Cap at 8 to avoid prompt bloat

        # Build the structured input for LLM
        structured_input = json.dumps({
            "bullets": engine_result.bullets[:20],  # Cap for token efficiency
            "bullet_classification": engine_result.bullet_classification,
            "metric_ratio": engine_result.metric_ratio,
            "total_bullets": engine_result.total_bullets,
            "bullets_with_metrics": engine_result.bullets_with_metrics,
            "weak_verb_count": engine_result.weak_verb_count,
            "ats_issues": engine_result.ats_issues,
            "sections_found": engine_result.section_headers_found,
            "sections_missing": engine_result.section_headers_missing,
            "deterministic_scores": engine_result.scores,
            "weak_bullets_to_rewrite": weak_bullets,
        }, indent=2)

        prompt = f"""You are a strict resume evaluator.

IMPORTANT:
- You DO NOT calculate scores
- Scores are already computed externally by a deterministic rule engine
- Your job is to EXPLAIN, CRITIQUE, and IMPROVE

You will receive structured data from a resume analysis system.

---

INPUT STRUCTURE:

{structured_input}

---

TARGET ROLE/JD:
{job_description if job_description else "Infer from the bullet content"}

TARGET KEYWORDS:
{', '.join(target_keywords) if target_keywords else "None specified — infer from content"}

---

YOUR TASK:

1. Infer the candidate's role, seniority, and years of experience
2. Perform keyword analysis: identify 15+ expected keywords, which are present vs missing
3. Assess role alignment (experience vs seniority, leadership signals, career progression)
4. Critically evaluate the resume quality based on the pre-computed data
5. Identify EXACT mistakes (not generic platitudes)
6. Rewrite each weak bullet into a strong one using STAR/XYZ format
7. Provide prioritized recommendations

---

STRICT RULES:

- Be harsh and realistic
- If metric_ratio < 0.3, clearly state the resume is weak
- Do NOT praise unnecessarily
- Do NOT repeat input data
- Do NOT hallucinate experience the candidate doesn't have
- Do NOT invent metrics — rewrites should use placeholder brackets like [X%]

---

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "candidate_summary": {{
    "inferred_role": "",
    "seniority_level": "",
    "years_of_experience": ""
  }},
  "keyword_analysis": {{
    "expected_keywords": [],
    "present_keywords": [],
    "missing_keywords": [],
    "coverage_percentage": 0
  }},
  "role_alignment_score": 0,
  "role_alignment_explanation": "",
  "score_explanations": {{
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
  "bullet_improvements": [
    {{
      "original": "",
      "issue": "",
      "improved": ""
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

        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a senior executive recruiter and ATS expert. "
                        "Scores have already been calculated by a rule engine. "
                        "Your role is critique, explanation, keyword analysis, and rewriting. "
                        "Respond strictly in JSON format."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = self.llm_client.chat(messages, temperature=0.1)

            # Clean markdown fences
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            return self._fallback_llm_result()
        except Exception as e:
            logger.error(f"LLM critique error: {e}")
            return self._fallback_llm_result()

    def _merge_results(
        self,
        engine: rule_engine.RuleEngineResult,
        llm: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge deterministic scores with LLM critique. Scores come from Python only."""

        # Extract LLM-provided keyword and role scores
        keyword_analysis = llm.get("keyword_analysis", {})
        keyword_coverage = keyword_analysis.get("coverage_percentage", 50)

        # Convert keyword coverage to score using deterministic brackets
        if keyword_coverage >= 70:
            keyword_score = min(100, 85 + int((keyword_coverage - 70) * 0.5))
        elif keyword_coverage >= 50:
            keyword_score = 70 + int((keyword_coverage - 50) * 0.7)
        elif keyword_coverage >= 30:
            keyword_score = 40 + int((keyword_coverage - 30) * 1.5)
        else:
            keyword_score = max(0, int(keyword_coverage * 1.3))

        role_alignment_score = min(100, max(0, llm.get("role_alignment_score", 50)))

        # Recompute overall with real keyword and role scores
        overall_raw = int(
            engine.scores["ats_compatibility"] * 0.25
            + engine.scores["content_impact"] * 0.25
            + engine.scores["readability"] * 0.20
            + keyword_score * 0.15
            + role_alignment_score * 0.15
        )

        # Validate final score
        overall_validated = rule_engine.validate_score(
            overall_raw, engine.metric_ratio, engine.bullet_classification
        )

        scores = {
            "overall_score": overall_validated,
            "ats_compatibility": engine.scores["ats_compatibility"],
            "content_impact": engine.scores["content_impact"],
            "readability": engine.scores["readability"],
            "keyword_strength": keyword_score,
            "role_alignment": role_alignment_score,
        }

        grade = self._get_grade(overall_validated)

        # Build merged output
        result: Dict[str, Any] = {
            "candidate_summary": llm.get("candidate_summary", {
                "inferred_role": "Unknown",
                "seniority_level": "Unknown",
                "years_of_experience": "N/A",
            }),
            "scores": scores,
            "score_breakdown_explanation": llm.get("score_explanations", {}),
            "mistakes": llm.get("mistakes", {"critical": [], "major": [], "minor": []}),
            "content_analysis": {
                "total_bullets": engine.total_bullets,
                "bullets_with_metrics": engine.bullets_with_metrics,
                "metric_ratio": engine.metric_ratio,
                "bullet_classification": engine.bullet_classification,
                "weak_bullet_examples": [
                    {
                        "original": bi.get("original", ""),
                        "improved": bi.get("improved", ""),
                        "issue": bi.get("issue", ""),
                    }
                    for bi in llm.get("bullet_improvements", [])
                ],
            },
            "keyword_analysis": keyword_analysis,
            "ats_issues": engine.ats_issues,
            "recommendations": llm.get("recommendations", []),
            "overall": {
                "score": overall_validated,
                "grade": grade,
                "breakdown": {
                    "ATS Compatibility": scores["ats_compatibility"],
                    "Content Impact": scores["content_impact"],
                    "Readability": scores["readability"],
                    "Keywords": scores["keyword_strength"],
                    "Role Alignment": scores["role_alignment"],
                },
            },
            "scoring_method": "hybrid",
            "deterministic_fields": [
                "ats_compatibility", "content_impact", "readability",
                "total_bullets", "bullets_with_metrics", "metric_ratio",
                "bullet_classification",
            ],
            "llm_fields": [
                "keyword_strength", "role_alignment", "mistakes",
                "bullet_improvements", "recommendations", "candidate_summary",
            ],
            "roadmap": [
                rec.get("issue") for rec in llm.get("recommendations", [])
            ],
        }

        logger.info(
            f"Final score: {overall_validated} ({grade}) | "
            f"metric_ratio={engine.metric_ratio} | "
            f"method=hybrid"
        )
        return result

    def _fallback_llm_result(self) -> Dict[str, Any]:
        """Fallback when LLM fails — analysis still works with deterministic scores only."""
        return {
            "candidate_summary": {
                "inferred_role": "Unknown (LLM unavailable)",
                "seniority_level": "Unknown",
                "years_of_experience": "N/A",
            },
            "keyword_analysis": {
                "expected_keywords": [],
                "present_keywords": [],
                "missing_keywords": [],
                "coverage_percentage": 50,
            },
            "role_alignment_score": 50,
            "role_alignment_explanation": "LLM critique unavailable — using neutral score",
            "score_explanations": {},
            "mistakes": {"critical": [], "major": [], "minor": []},
            "bullet_improvements": [],
            "recommendations": [
                {
                    "priority": 1,
                    "issue": "LLM critique failed",
                    "fix": "Review scores manually — deterministic analysis is complete",
                    "expected_impact": "N/A",
                }
            ],
        }

    def _get_grade(self, score: float) -> str:
        if score >= 95: return "A++"
        if score >= 90: return "A+"
        if score >= 85: return "A"
        if score >= 80: return "A-"
        if score >= 70: return "B"
        if score >= 60: return "C"
        return "F"
