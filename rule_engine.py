"""
Deterministic Rule Engine for ATS Resume Analysis.

This module handles ALL scoring, counting, and classification.
The LLM is NOT allowed to calculate scores — only explain, critique, and rewrite.

Architecture:
    PDF -> Text Extraction -> Rule Engine (this) -> LLM Critique -> Score Validator -> Output
"""

import re
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# --- Constants ---

STRONG_ACTION_VERBS: frozenset[str] = frozenset({
    "led", "managed", "developed", "created", "implemented", "increased",
    "reduced", "achieved", "delivered", "optimized", "orchestrated",
    "spearheaded", "generated", "negotiated", "cultivated", "analyzed",
    "formulated", "executed", "accelerated", "pioneered", "transformed",
    "built", "scaled", "launched", "drove", "architected", "designed",
    "established", "streamlined", "directed", "mentored", "automated",
    "revamped", "consolidated", "migrated", "integrated", "championed",
})

WEAK_VERB_PATTERNS: tuple[str, ...] = (
    "responsible for",
    "worked on",
    "helped with",
    "assisted in",
    "involved in",
    "participated in",
    "tasked with",
    "in charge of",
)

METRIC_PATTERNS: list[str] = [
    r'\d+%',                      # Percentage
    r'\$[\d,.]+[KMB]?',           # Dollar amount ($50K, $1.2M)
    r'\d+\+',                     # Numbers with plus
    r'\d+x',                      # Multipliers
    r'\d[\d,]*\s+users',          # User counts
    r'\d[\d,]*\s+customers',      # Customer counts
    r'\d[\d,]*\s+million',        # Millions
    r'\d[\d,]*\s+billion',        # Billions
    r'reduced\s+(?:by\s+)?\d+',   # Reductions
    r'increased\s+(?:by\s+)?\d+', # Increases
    r'grew\s+(?:by\s+)?\d+',      # Growth
    r'\d[\d,]*\s+(?:team|people|engineers|members)',  # Team size
    r'\d[\d,]*\s+(?:projects|products|features)',     # Project scale
]

ATS_SECTION_HEADERS: list[str] = [
    "experience", "education", "skills", "summary", "objective",
    "projects", "certifications", "awards", "publications",
]


# --- Data Classes ---

@dataclass(frozen=True)
class BulletAnalysis:
    text: str
    has_metric: bool
    has_strong_verb: bool
    has_weak_verb: bool
    classification: str  # "strong", "medium", "weak"
    word_count: int


@dataclass(frozen=True)
class RuleEngineResult:
    bullets: list[str]
    bullet_analyses: list[BulletAnalysis]
    bullet_classification: Dict[str, int]
    total_bullets: int
    bullets_with_metrics: int
    metric_ratio: float
    weak_verb_count: int
    ats_issues: list[Dict[str, str]]
    section_headers_found: list[str]
    section_headers_missing: list[str]
    scores: Dict[str, int]
    raw_text: str


# --- Core Functions ---

def extract_bullets(text: str) -> list[str]:
    """Extract bullet points from resume text."""
    lines = text.split('\n')
    bullets: list[str] = []

    for line in lines:
        cleaned = line.strip()
        # Match lines starting with bullet chars or that look like bullet content
        if re.match(r'^[-\u2022\u25cf\u25cb\u2023*]\s+', cleaned):
            content = re.sub(r'^[-\u2022\u25cf\u25cb\u2023*]\s+', '', cleaned)
            if len(content) > 20:
                bullets.append(content)
        elif re.match(r'^\d+[.)]\s+', cleaned):
            content = re.sub(r'^\d+[.)]\s+', '', cleaned)
            if len(content) > 20:
                bullets.append(content)

    # Fallback: if no bullets found with markers, try splitting by newlines
    # and look for sentences that read like accomplishments
    if not bullets:
        for line in lines:
            cleaned = line.strip()
            if len(cleaned) > 30 and any(
                cleaned.lower().startswith(v) for v in STRONG_ACTION_VERBS
            ):
                bullets.append(cleaned)

    return bullets


def has_metric(text: str) -> bool:
    """Detect quantifiable metrics in text."""
    return any(
        bool(re.search(pattern, text, re.IGNORECASE))
        for pattern in METRIC_PATTERNS
    )


def has_strong_verb(text: str) -> bool:
    """Detect strong action verbs in the first few words."""
    words = text.lower().split()[:3]
    return any(word in STRONG_ACTION_VERBS for word in words)


def has_weak_verb(text: str) -> bool:
    """Detect weak/passive phrasing."""
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in WEAK_VERB_PATTERNS)


def classify_bullet(bullet: str) -> str:
    """Classify a bullet as strong, medium, or weak."""
    metric = has_metric(bullet)
    strong = has_strong_verb(bullet)
    weak = has_weak_verb(bullet)

    if weak:
        return "weak"
    if metric and strong:
        return "strong"
    if metric or strong:
        return "medium"
    return "weak"


def analyze_bullet(bullet: str) -> BulletAnalysis:
    """Full analysis of a single bullet point."""
    return BulletAnalysis(
        text=bullet,
        has_metric=has_metric(bullet),
        has_strong_verb=has_strong_verb(bullet),
        has_weak_verb=has_weak_verb(bullet),
        classification=classify_bullet(bullet),
        word_count=len(bullet.split()),
    )


# --- Scoring Functions ---

def score_content_impact(metric_ratio: float, weak_verb_count: int, total_bullets: int) -> int:
    """Deterministic content impact score based on metric density."""
    if metric_ratio >= 0.6:
        base = 95
    elif metric_ratio >= 0.4:
        base = 80
    elif metric_ratio >= 0.2:
        base = 60
    else:
        base = 30

    # Penalize weak verbs
    if total_bullets > 0:
        weak_ratio = weak_verb_count / total_bullets
        if weak_ratio > 0.3:
            base -= 15
        elif weak_ratio > 0.1:
            base -= 10

    return max(0, min(100, base))


def score_ats_compatibility(text: str) -> Tuple[int, list[Dict[str, str]]]:
    """Score ATS compatibility with deductions for common issues."""
    score = 100
    issues: list[Dict[str, str]] = []

    # Check for table indicators
    if re.search(r'\t{2,}', text) or re.search(r'\|.*\|.*\|', text):
        score -= 20
        issues.append({
            "issue": "Table or multi-column layout detected",
            "severity": "High",
            "impact": "ATS parsers may scramble content in multi-column layouts"
        })

    # Check for missing standard sections
    text_lower = text.lower()
    required_sections = ["experience", "education", "skills"]
    for section in required_sections:
        if section not in text_lower:
            score -= 15
            issues.append({
                "issue": f"Missing '{section.title()}' section",
                "severity": "High",
                "impact": f"ATS requires standard '{section}' section header"
            })

    # Check for special characters / unicode icons
    icon_count = len(re.findall(r'[\U0001F300-\U0001F9FF]', text))
    if icon_count > 0:
        score -= 10
        issues.append({
            "issue": f"Contains {icon_count} emoji/icon characters",
            "severity": "Medium",
            "impact": "Many ATS systems cannot parse emoji or special unicode"
        })

    # Check for potential header/footer interference
    lines = text.strip().split('\n')
    if lines and len(lines[0].strip()) < 5:
        score -= 5
        issues.append({
            "issue": "Possible header/footer artifacts in extracted text",
            "severity": "Low",
            "impact": "May confuse ATS section parsing"
        })

    # Check for inconsistent bullet formatting
    bullet_styles = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('-'):
            bullet_styles.add('dash')
        elif stripped.startswith('\u2022'):
            bullet_styles.add('bullet')
        elif stripped.startswith('*'):
            bullet_styles.add('asterisk')
    if len(bullet_styles) > 1:
        score -= 10
        issues.append({
            "issue": "Inconsistent bullet point formatting",
            "severity": "Medium",
            "impact": "Mixed bullet styles may confuse ATS parsing"
        })

    return max(0, score), issues


def score_readability(text: str, bullets: list[str]) -> int:
    """Score readability and structure."""
    score = 100

    # Check for long sentences (> 25 words)
    long_bullets = sum(1 for b in bullets if len(b.split()) > 25)
    if long_bullets > 0:
        score -= min(15, long_bullets * 5)

    # Check for dense text (very few line breaks)
    lines = text.strip().split('\n')
    non_empty_lines = [l for l in lines if l.strip()]
    if len(non_empty_lines) > 0:
        avg_line_length = sum(len(l) for l in non_empty_lines) / len(non_empty_lines)
        if avg_line_length > 120:
            score -= 10

    # Check section hierarchy
    text_lower = text.lower()
    found_sections = sum(
        1 for s in ATS_SECTION_HEADERS if s in text_lower
    )
    if found_sections < 3:
        score -= 15

    return max(0, min(100, score))


def detect_sections(text: str) -> Tuple[list[str], list[str]]:
    """Detect which standard ATS sections are present/missing."""
    text_lower = text.lower()
    found = [s for s in ATS_SECTION_HEADERS if s in text_lower]
    missing = [s for s in ATS_SECTION_HEADERS[:5] if s not in text_lower]  # Only check core sections
    return found, missing


# --- Score Validator ---

def validate_score(overall_score: int, metric_ratio: float, classification: Dict[str, int]) -> int:
    """
    Post-validation: ensure scores aren't inflated for weak resumes.
    This is the final safety net before output.
    """
    total = sum(classification.values())
    weak_ratio = classification.get("weak", 0) / total if total > 0 else 1.0

    # Rule 1: Low metric ratio caps the score
    if metric_ratio < 0.2 and overall_score > 50:
        logger.info(f"Score capped: metric_ratio={metric_ratio}, was={overall_score}, now=45")
        return 45

    # Rule 2: Mostly weak bullets caps the score
    if weak_ratio > 0.6 and overall_score > 55:
        logger.info(f"Score capped: weak_ratio={weak_ratio}, was={overall_score}, now=50")
        return 50

    # Rule 3: No metrics at all
    if metric_ratio == 0 and overall_score > 35:
        logger.info(f"Score capped: zero metrics, was={overall_score}, now=30")
        return 30

    return overall_score


# --- Main Entry Point ---

def analyze(text: str) -> RuleEngineResult:
    """
    Run the full deterministic rule engine analysis on resume text.

    This produces all scores and classifications.
    The LLM should receive these results and ONLY provide critique/rewrites.
    """
    # 1. Extract and classify bullets
    bullets = extract_bullets(text)
    bullet_analyses = [analyze_bullet(b) for b in bullets]

    classification = {"strong": 0, "medium": 0, "weak": 0}
    for ba in bullet_analyses:
        classification[ba.classification] += 1

    total = len(bullets)
    metrics_count = sum(1 for ba in bullet_analyses if ba.has_metric)
    metric_ratio = round(metrics_count / total, 2) if total > 0 else 0.0
    weak_verb_count = sum(1 for ba in bullet_analyses if ba.has_weak_verb)

    # 2. Score each category deterministically
    content_impact = score_content_impact(metric_ratio, weak_verb_count, total)
    ats_score, ats_issues = score_ats_compatibility(text)
    readability = score_readability(text, bullets)

    # 3. Detect sections
    found_sections, missing_sections = detect_sections(text)

    # 4. Compute overall (without keyword/role — those need LLM context)
    # Weight: ATS 25%, Content 25%, Readability 20%, Keyword 15%, Role 15%
    # Keyword and Role are set to 50 (neutral) since they require LLM inference
    keyword_placeholder = 50
    role_placeholder = 50
    overall_raw = int(
        ats_score * 0.25
        + content_impact * 0.25
        + readability * 0.20
        + keyword_placeholder * 0.15
        + role_placeholder * 0.15
    )

    # 5. Validate score
    overall_validated = validate_score(overall_raw, metric_ratio, classification)

    scores = {
        "overall_score": overall_validated,
        "ats_compatibility": ats_score,
        "content_impact": content_impact,
        "readability": readability,
        "keyword_strength": keyword_placeholder,  # Will be updated after LLM
        "role_alignment": role_placeholder,        # Will be updated after LLM
    }

    return RuleEngineResult(
        bullets=bullets,
        bullet_analyses=bullet_analyses,
        bullet_classification=classification,
        total_bullets=total,
        bullets_with_metrics=metrics_count,
        metric_ratio=metric_ratio,
        weak_verb_count=weak_verb_count,
        ats_issues=ats_issues,
        section_headers_found=found_sections,
        section_headers_missing=missing_sections,
        scores=scores,
        raw_text=text,
    )
