import streamlit as st
import os
import sys
import yaml

# --- Robust Path Configuration ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.dirname(CURRENT_DIR)
AI_AGENT_SRC = os.path.join(REPOS_DIR, "AIAGENT", "src")

if os.path.exists(AI_AGENT_SRC):
    if AI_AGENT_SRC not in sys.path:
        sys.path.insert(0, AI_AGENT_SRC)
else:
    FALLBACK_AI_AGENT_SRC = "/Users/alihusainsorathiya/Documents/resume/AIAGENT/src"
    if os.path.exists(FALLBACK_AI_AGENT_SRC):
        if FALLBACK_AI_AGENT_SRC not in sys.path:
            sys.path.insert(0, FALLBACK_AI_AGENT_SRC)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from rezi_agent import ReziResumeAgent
    from rezi_bridge import ReziBridge
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.stop()

# --- Page Config ---
st.set_page_config(page_title="Advanced ATS Resume Analysis Engine", page_icon="🚀", layout="wide")

# --- Session State ---
if "agent" not in st.session_state:
    st.session_state.agent = None
if "analysis" not in st.session_state:
    st.session_state.analysis = None
if "optimized_data" not in st.session_state:
    st.session_state.optimized_data = None
if "selected_model" not in st.session_state:
    st.session_state.selected_model = None

# --- Cached Helpers ---
@st.cache_data(ttl=300)
def fetch_available_models(api_url):
    return ReziResumeAgent.get_available_models(api_url)

def get_api_base_url():
    config_path = os.path.join(REPOS_DIR, 'AIAGENT', 'config.yaml')
    if not os.path.exists(config_path):
         config_path = "/Users/alihusainsorathiya/Documents/resume/AIAGENT/config.yaml"
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get("api", {}).get("base_url", "http://127.0.0.1:9090/v1")
        except:
            pass
    return "http://127.0.0.1:9090/v1"

def render_analysis_report(analysis):
    """
    Renders the Hybrid ATS Resume Analysis report.
    Shows which scores are deterministic (Python) vs LLM-derived.
    """
    if not analysis:
        return

    scores = analysis.get("scores", {})
    summary = analysis.get("candidate_summary", {})
    content = analysis.get("content_analysis", {})
    scoring_method = analysis.get("scoring_method", "unknown")

    # 0. Scoring Method Badge
    if scoring_method == "hybrid":
        st.success("Hybrid Analysis: Deterministic Rule Engine + LLM Critique")
    else:
        st.warning("Legacy LLM-only analysis")

    # 1. Executive Summary Header
    st.markdown("### Executive Summary")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        overall = scores.get('overall_score', 0)
        st.metric("Overall Score", f"{overall}/100")
        grade = "F"
        if overall >= 90: grade = "A+"
        elif overall >= 80: grade = "A"
        elif overall >= 70: grade = "B"
        elif overall >= 60: grade = "C"
        st.caption(f"Grade: **{grade}**")
    with col2:
        metric_ratio = content.get('metric_ratio', 0)
        st.metric("Metric Density", f"{int(metric_ratio * 100)}%")
        st.caption(f"{content.get('bullets_with_metrics', 0)} of {content.get('total_bullets', 0)} bullets")
    with col3:
        st.info(f"**Target Role:** {summary.get('inferred_role', 'Unknown')}\n\n**Seniority:** {summary.get('seniority_level', 'Unknown')} ({summary.get('years_of_experience', 'N/A')})")

    st.divider()

    # 2. Five-Category Score Breakdown
    st.markdown("### Scoring Framework Breakdown")
    cols = st.columns(5)

    deterministic_fields = set(analysis.get("deterministic_fields", []))

    categories = [
        ("ATS Compatibility", "ats_compatibility"),
        ("Content Impact", "content_impact"),
        ("Readability", "readability"),
        ("Keyword Strength", "keyword_strength"),
        ("Role Alignment", "role_alignment"),
    ]

    for i, (label, key) in enumerate(categories):
        with cols[i]:
            score = scores.get(key, 0)
            source = "Python" if key in deterministic_fields else "LLM"
            st.markdown(f"**{label}**")
            st.markdown(f"## {score}%")
            st.progress(score / 100)
            st.caption(f"Source: {source}")

    st.divider()

    # 3. Mistake Detection (Strict)
    st.markdown("### Mistake Detection")
    mistakes = analysis.get("mistakes", {})

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        critical = mistakes.get("critical", [])
        st.error(f"**Critical ({len(critical)})**")
        for m in critical: st.markdown(f"- {m}")
    with m_col2:
        major = mistakes.get("major", [])
        st.warning(f"**Major ({len(major)})**")
        for m in major: st.markdown(f"- {m}")
    with m_col3:
        minor = mistakes.get("minor", [])
        st.info(f"**Minor ({len(minor)})**")
        for m in minor: st.markdown(f"- {m}")

    st.divider()

    # 4. Bullet Point Analysis (Deterministic)
    st.markdown("### Bullet Point Quality (Deterministic)")
    b_class = content.get("bullet_classification", {})

    b_cols = st.columns(3)
    b_cols[0].success(f"**Strong:** {b_class.get('strong', 0)}")
    b_cols[1].warning(f"**Medium:** {b_class.get('medium', 0)}")
    b_cols[2].error(f"**Weak:** {b_class.get('weak', 0)}")

    if content.get("weak_bullet_examples"):
        st.markdown("#### STAR/XYZ Rewrites (LLM)")
        for item in content["weak_bullet_examples"]:
            original = item.get('original', '')
            if not original:
                continue
            with st.expander(f"Original: {original[:60]}..."):
                st.markdown(f"**Original:** `{original}`")
                if item.get("issue"):
                    st.warning(f"**Issue:** {item['issue']}")
                st.success(f"**Improved:** {item.get('improved', '')}")

    st.divider()

    # 5. ATS Issues & Recommendations
    st.markdown("### ATS Technical Audit (Deterministic)")
    ats_issues = analysis.get("ats_issues", [])
    if ats_issues:
        for issue in ats_issues:
            severity = issue.get("severity", "Medium")
            if "High" in severity:
                st.error(f"**{issue.get('issue')}**\n\n*Impact:* {issue.get('impact')}")
            elif "Medium" in severity:
                st.warning(f"**{issue.get('issue')}**\n\n*Impact:* {issue.get('impact')}")
            else:
                st.info(f"**{issue.get('issue')}**")
    else:
        st.success("No ATS compatibility issues detected.")

    st.markdown("### Priority Recommendations (LLM)")
    recs = analysis.get("recommendations", [])
    for r in sorted(recs, key=lambda x: x.get('priority', 99)):
        st.info(f"**{r.get('priority')}. {r.get('issue')}**\n\n**Fix:** {r.get('fix')}\n\n*Expected Impact:* {r.get('expected_impact')}")

    # 6. Keyword Analysis
    with st.expander("Keyword Coverage Analysis (LLM)", expanded=False):
        kw_data = analysis.get("keyword_analysis", {})
        coverage = kw_data.get('coverage_percentage', 0)
        st.metric("Coverage", f"{coverage}%")
        st.progress(min(coverage, 100) / 100)

        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.write("**Missing Keywords**")
            for k in kw_data.get("missing_keywords", []): st.write(f"- {k}")
        with k_col2:
            st.write("**Present Keywords**")
            for k in kw_data.get("present_keywords", []): st.write(f"- {k}")

    # 7. Score Validation Log
    with st.expander("Score Validation Details", expanded=False):
        metric_ratio_val = content.get("metric_ratio", 0)
        b_class_val = content.get("bullet_classification", {})
        total_b = sum(b_class_val.values())
        weak_r = b_class_val.get("weak", 0) / total_b if total_b > 0 else 0

        st.markdown("**Validation Rules Applied:**")
        if metric_ratio_val < 0.2:
            st.error(f"Rule 1: metric_ratio={metric_ratio_val} < 0.2 -> score capped at 45")
        if weak_r > 0.6:
            st.error(f"Rule 2: weak_ratio={weak_r:.1%} > 60% -> score capped at 50")
        if metric_ratio_val == 0:
            st.error("Rule 3: zero metrics -> score capped at 30")
        if metric_ratio_val >= 0.2 and weak_r <= 0.6:
            st.success("No score caps applied - metrics and quality pass thresholds")

        det_fields = analysis.get("deterministic_fields", [])
        llm_fields = analysis.get("llm_fields", [])
        st.markdown(f"**Deterministic fields:** {', '.join(det_fields)}")
        st.markdown(f"**LLM fields:** {', '.join(llm_fields)}")

    # 8. Raw Text Preview
    with st.expander("Raw Text Preview (Verification)", expanded=False):
        raw_text = analysis.get("raw_text", "No raw text available.")
        if not raw_text and st.session_state.agent and hasattr(st.session_state.agent, 'structured_data'):
            raw_text = st.session_state.agent.structured_data.get("raw_text", "No raw text available.")
        st.text_area("Extracted Text", value=raw_text, height=300, disabled=True)

# --- UI Layout ---
st.title("Advanced ATS Resume Analysis Engine")
st.markdown(
    """
Professional resume scoring and optimization powered by hybrid analysis (deterministic rules + LLM critique).
"""
)

with st.sidebar:
    st.header("Configuration")

    # Model Selection
    st.subheader("Model Selection")
    api_url = get_api_base_url()
    models = fetch_available_models(api_url)

    if models:
        st.session_state.selected_model = st.selectbox(
            "Select LLM Model",
            options=models,
            index=0 if st.session_state.selected_model not in models else models.index(st.session_state.selected_model)
        )
    else:
        st.warning("Could not fetch models. Using default from config.")
        st.session_state.selected_model = None

    # Rezi API Key
    st.subheader("Rezi MCP Connection")
    rezi_key = st.text_input("Rezi API Key", type="password", value=os.environ.get("REZI_API_KEY", ""))
    if rezi_key:
        os.environ["REZI_API_KEY"] = rezi_key

    cv_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx", "txt"])

    if cv_file:
        # Save temp file
        temp_path = os.path.join("/tmp", cv_file.name)
        with open(temp_path, "wb") as f:
            f.write(cv_file.getbuffer())

        if st.button("Initialize Agent"):
            try:
                st.session_state.agent = ReziResumeAgent(temp_path, model_name=st.session_state.selected_model)
                # Reset previous state when new agent is initialized
                st.session_state.analysis = None
                st.session_state.optimized_data = None
                st.success(f"Agent Initialized with {st.session_state.agent.model}!")
            except Exception as e:
                st.error(f"Failed to initialize agent: {e}")

# --- Main App Logic ---
if st.session_state.agent:
    tab_analysis, tab_optimize, tab_rezi = st.tabs(["1. ATS Analysis", "2. Optimize", "3. Rezi Sync"])

    with tab_analysis:
        st.subheader("Hybrid ATS Analysis (Rules + LLM)")
        if st.button("Run Hybrid ATS Analysis"):
            with st.spinner("Step 1: Rule Engine (deterministic)... Step 2: LLM Critique..."):
                try:
                    st.session_state.analysis = st.session_state.agent.analyze_resume()
                    if st.session_state.analysis and "error" in st.session_state.analysis:
                        st.error(f"Analysis Error: {st.session_state.analysis['error']}")
                    else:
                        st.success("Hybrid analysis complete!")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

        if st.session_state.analysis and "error" not in st.session_state.analysis:
            render_analysis_report(st.session_state.analysis)
        elif st.session_state.analysis and "error" in st.session_state.analysis:
            st.warning("Please resolve the error above before continuing.")

    with tab_optimize:
        st.subheader("Target Role & Optimization")
        target_role = st.text_input("Target Role", value="Product Manager")
        target_location = st.text_input("Target Location", value="Dubai, UAE")

        can_optimize = False
        if st.session_state.agent and st.session_state.agent.structured_data:
            if "error" not in st.session_state.agent.structured_data:
                can_optimize = True

        if st.button("Optimize for Target Role", disabled=not can_optimize):
            with st.spinner("Researching & Optimizing..."):
                try:
                    result = st.session_state.agent.optimize_and_sync(
                        target_role, target_location
                    )

                    if result and "error" in result:
                        st.error(f"Optimization Error: {result['error']}")
                    else:
                        st.session_state.optimized_data = result["optimized_data"]
                        st.session_state.rezi_call = result["rezi_tool"]
                        st.session_state.rezi_args = result["rezi_args"]
                        st.success("Optimization Complete!")
                except Exception as e:
                    st.error(f"Optimization failed: {e}")

        if not can_optimize:
            st.info("Run a successful ATS Analysis first to enable optimization.")

        if st.session_state.optimized_data:
            st.divider()
            st.markdown("### Optimized Content Preview")
            for exp in st.session_state.optimized_data.get("experience", []):
                title = exp.get("title", exp.get("role", "Unknown Role"))
                company = exp.get("company", "Unknown Company")
                with st.expander(f"Role: {title} at {company}"):
                    desc = exp.get("description", "")
                    if isinstance(desc, list):
                        for bullet in desc:
                            st.write(f"- {bullet}")
                    else:
                        bullets_list = [b.strip() for b in desc.split("\n") if b.strip()]
                        for bullet in bullets_list:
                            if not bullet.startswith("-"):
                                st.write(f"- {bullet}")
                            else:
                                st.write(bullet)

    with tab_rezi:
        st.subheader("Rezi Platform Sync (MCP)")
        st.markdown(f"**Endpoint:** `{ReziBridge.MCP_ENDPOINT}`")

        bridge = ReziBridge(api_key=rezi_key if rezi_key else None)

        col_rezi1, col_rezi2 = st.columns(2)

        with col_rezi1:
            st.markdown("#### Your Resumes")
            if st.button("List Resumes"):
                with st.spinner("Fetching from Rezi..."):
                    resumes = bridge.list_resumes()
                    if "error" in resumes:
                        st.error(f"Error: {resumes['error']}")
                    else:
                        st.session_state.rezi_resumes = resumes
                        st.success("Resumes loaded")

            if st.session_state.get("rezi_resumes"):
                resume_list = st.session_state.rezi_resumes
                if isinstance(resume_list, dict) and "content" in resume_list:
                    resume_list = resume_list["content"]
                if isinstance(resume_list, list):
                    for r in resume_list:
                        if isinstance(r, dict):
                            st.markdown(f"- **{r.get('name', 'Untitled')}** (ID: `{r.get('id', 'N/A')}`)")

        with col_rezi2:
            st.markdown("#### Read Resume")
            read_id = st.text_input("Resume ID to read")
            if st.button("Read Resume") and read_id:
                with st.spinner("Reading..."):
                    resume_data = bridge.read_resume(read_id)
                    if "error" in resume_data:
                        st.error(f"Error: {resume_data['error']}")
                    else:
                        st.json(resume_data)

        st.divider()

        st.markdown("#### Push Optimized Resume")
        if st.session_state.optimized_data:
            push_title = st.text_input("Resume Title", value="Optimized Resume")
            existing_id = st.text_input("Existing Resume ID (leave blank to create new)", value="")

            if st.button("Push to Rezi"):
                with st.spinner("Pushing to Rezi MCP..."):
                    result = bridge.push_optimized_resume(
                        title=push_title,
                        structured_data=st.session_state.optimized_data,
                        resume_id=existing_id if existing_id else None,
                    )
                    if "error" in result:
                        st.error(f"Push failed: {result['error']}")
                    else:
                        st.success("Resume pushed to Rezi!")
                        st.json(result)
        else:
            st.info("Run optimization first to have content to push.")

else:
    st.info("Please upload a resume in the sidebar to get started.")
