import streamlit as st
import os
import sys
import json
import yaml
from pathlib import Path

# --- Path Configuration ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
AI_AGENT_SRC = os.path.join(CURRENT_DIR, "src")

if os.path.exists(AI_AGENT_SRC):
    if AI_AGENT_SRC not in sys.path:
        sys.path.insert(0, AI_AGENT_SRC)

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
    config_path = os.path.join(CURRENT_DIR, 'config.yaml')
    if not os.path.exists(config_path):
         config_path = os.path.join(CURRENT_DIR, "config.yaml.template")

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
    Renders the overhauled Deterministic ATS Resume Analysis report.
    """
    if not analysis:
        return

    scores = analysis.get("scores", {})
    summary = analysis.get("candidate_summary", {})
    content = analysis.get("content_analysis", {})

    # 1. Executive Summary Header
    st.markdown("### 📊 Advanced ATS Analysis Report")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.metric("Overall Score", f"{scores.get('overall_score', 0)}/100")
        grade = "F"
        s = scores.get('overall_score', 0)
        if s >= 90: grade = "A+"
        elif s >= 80: grade = "A"
        elif s >= 70: grade = "B"
        elif s >= 60: grade = "C"
        st.caption(f"Grade: **{grade}**")
    with col2:
        st.metric("Metric Density", f"{int(content.get('metric_ratio', 0) * 100)}%")
        st.caption(f"{content.get('bullets_with_metrics', 0)} of {content.get('total_bullets', 0)} bullets")
    with col3:
        st.info(f"**Target Role:** {summary.get('inferred_role', 'Unknown')}\n\n**Seniority:** {summary.get('seniority_level', 'Unknown')} ({summary.get('years_of_experience', 'N/A')})")

    st.divider()

    # 2. Five-Category Score Breakdown
    st.markdown("### 🔍 Scoring Framework Breakdown")
    cols = st.columns(5)

    categories = [
        ("ATS Compatibility", "ats_compatibility", "⚙️"),
        ("Content Impact", "content_impact", "💥"),
        ("Readability", "readability", "📖"),
        ("Keyword Strength", "keyword_strength", "🔑"),
        ("Role Alignment", "role_alignment", "🎯")
    ]

    for i, (label, key, icon) in enumerate(categories):
        with cols[i]:
            score = scores.get(key, 0)
            st.markdown(f"**{icon} {label}**")
            st.markdown(f"## {score}%")
            st.progress(score / 100)

    st.divider()

    # 3. Mistake Detection (Strict)
    st.markdown("### 🚨 Mistake Detection")
    mistakes = analysis.get("mistakes", {})

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        critical = mistakes.get("critical", [])
        st.error(f"**Critical ({len(critical)})**")
        for m in critical: st.markdown(f"• {m}")
    with m_col2:
        major = mistakes.get("major", [])
        st.warning(f"**Major ({len(major)})**")
        for m in major: st.markdown(f"• {m}")
    with m_col3:
        minor = mistakes.get("minor", [])
        st.info(f"**Minor ({len(minor)})**")
        for m in minor: st.markdown(f"• {m}")

    st.divider()

    # 4. Bullet Point Analysis
    st.markdown("### 📝 Bullet Point Quality")
    b_class = content.get("bullet_classification", {})

    b_cols = st.columns(3)
    b_cols[0].success(f"**Strong:** {b_class.get('strong', 0)}")
    b_cols[1].warning(f"**Medium:** {b_class.get('medium', 0)}")
    b_cols[2].error(f"**Weak:** {b_class.get('weak', 0)}")

    if content.get("weak_bullet_examples"):
        st.markdown("#### ✨ STAR/XYZ Rewrites")
        for item in content["weak_bullet_examples"]:
            with st.expander(f"Original: {item.get('original')[:60]}..."):
                st.markdown(f"**Original:** `{item.get('original')}`")
                st.success(f"**Improved:** {item.get('improved')}")
                st.markdown("---")

    st.divider()

    # 5. ATS Issues & Recommendations
    st.markdown("### 🛡️ ATS Technical Audit")
    ats_issues = analysis.get("ats_issues", [])
    if ats_issues:
        for issue in ats_issues:
            severity = issue.get("severity", "Medium")
            if "High" in severity:
                st.error(f"🚨 **{issue.get('issue')}**\n\n*Impact:* {issue.get('impact')}")
            elif "Medium" in severity:
                st.warning(f"⚠️ **{issue.get('issue')}**\n\n*Impact:* {issue.get('impact')}")
            else:
                st.info(f"ℹ️ **{issue.get('issue')}**")

    st.markdown("### 🎯 Priority Recommendations")
    recs = analysis.get("recommendations", [])
    for r in sorted(recs, key=lambda x: x.get('priority', 99)):
        st.info(f"**{r.get('priority')}. {r.get('issue')}**\n\n**Fix:** {r.get('fix')}\n\n*Expected Impact:* {r.get('expected_impact')}")

    # 6. Keyword Analysis
    with st.expander("🔑 Keyword Coverage Analysis", expanded=False):
        kw_data = analysis.get("keyword_analysis", {})
        st.metric("Coverage", f"{kw_data.get('coverage_percentage', 0)}%")
        st.progress(kw_data.get('coverage_percentage', 0) / 100)

        k_col1, k_col2 = st.columns(2)
        with k_col1:
            st.write("**Missing Keywords**")
            for k in kw_data.get("missing_keywords", []): st.write(f"❌ {k}")
        with k_col2:
            st.write("**Present Keywords**")
            for k in kw_data.get("present_keywords", []): st.write(f"✅ {k}")

    # 7. Raw Text Preview
    with st.expander("📄 Raw Text Preview (Verification)", expanded=False):
        raw_text = analysis.get("raw_text", "No raw text available.")
        if not raw_text and st.session_state.agent and hasattr(st.session_state.agent, 'structured_data'):
            raw_text = st.session_state.agent.structured_data.get("raw_text", "No raw text available.")
        st.text_area("Extracted Text", value=raw_text, height=300, disabled=True)

# --- UI Layout ---
st.title("🚀 Advanced ATS Resume Analysis Engine")
st.markdown(
    """
Professional resume scoring and optimization powered by deep AI analysis and strict ATS compliance standards.
"""
)

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Model Selection
    st.subheader("🤖 Model Selection")
    api_url = get_api_base_url()
    models = fetch_available_models(api_url)
    
    if models:
        st.session_state.selected_model = st.selectbox(
            "Select LLM Model", 
            options=models,
            index=0 if st.session_state.selected_model not in models else models.index(st.session_state.selected_model)
        )
    else:
        st.warning("⚠️ Could not fetch models. Using default from config.")
        st.session_state.selected_model = None

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
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("1. Analysis & ATS Scoring")
        if st.button("Run Advanced ATS Analysis"):
            with st.spinner("Executing detailed audit..."):
                try:
                    st.session_state.analysis = st.session_state.agent.analyze_resume()
                    if st.session_state.analysis and "error" in st.session_state.analysis:
                        st.error(f"Analysis Error: {st.session_state.analysis['error']}")
                    else:
                        st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

        if st.session_state.analysis and "error" not in st.session_state.analysis:
            render_analysis_report(st.session_state.analysis)
        elif st.session_state.analysis and "error" in st.session_state.analysis:
            st.warning("Please resolve the error above before continuing.")

    with col2:
        st.subheader("2. Target & Optimization")
        target_role = st.text_input("Target Role", value="Product Manager")
        target_location = st.text_input("Target Location", value="Dubai, UAE")

        # Logic to determine if we can optimize
        can_optimize = False
        if st.session_state.agent and st.session_state.agent.structured_data:
            if "error" not in st.session_state.agent.structured_data:
                can_optimize = True

        if st.button("Optimize for Rezi", disabled=not can_optimize):
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
            st.info("💡 Please run a successful ATS Analysis first to enable optimization.")

    if st.session_state.optimized_data:
        st.divider()
        st.header("✨ Optimized Content")
        st.write("This content is ready to be pushed to Rezi.")

        # Display preview of optimized experience
        st.subheader("Experience")
        for exp in st.session_state.optimized_data.get("experience", []):
            title = exp.get("title", exp.get("role", "Unknown Role"))
            company = exp.get("company", "Unknown Company")
            with st.expander(f"Role: {title} at {company}"):
                desc = exp.get("description", "")
                if isinstance(desc, list):
                    for bullet in desc:
                        st.write(f"• {bullet}")
                else:
                    # Split string description by bullets or newlines
                    bullets = [b.strip() for b in desc.split("\n") if b.strip()]
                    for bullet in bullets:
                        if not bullet.startswith("•") and not bullet.startswith("-"):
                            st.write(f"• {bullet}")
                        else:
                            st.write(bullet)

        st.subheader("📤 Sync to Rezi Platform")
        st.code(
            f"Tool: {st.session_state.rezi_call}\nArgs: {json.dumps(st.session_state.rezi_args, indent=2)}"
        )

        if st.button("Push to Rezi (MCP)"):
            st.info("Initiating Rezi MCP tool call...")
            st.warning(
                "Manual Step: Please ask me to 'Run the Rezi tool with these args' in the chat to finalize."
            )

else:
    st.info("Please upload a resume in the sidebar to get started.")
