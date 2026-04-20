# Advanced ATS Resume Optimization Engine

An AI-driven resume parsing, scoring, and optimization system designed to help candidates reach the top 1% of applicants. This engine simulates modern Applicant Tracking Systems (ATS) and top-tier recruiter evaluations using a deterministic, rule-based scoring model.

## 🚀 Key Features

- **AI-Powered High-Fidelity Parsing**: Uses LLMs to extract structured data (Experience, Education, Skills) from raw text, preserving semantic meaning better than regex.
- **Brutal ATS Audit Engine**: Implements a strict, rule-based scoring framework that penalizes formatting risks, weak bullet points, and missing metrics.
- **STAR/XYZ Rewrite Engine**: Automatically identifies weak accomplishments and provides high-impact rewrites using the STAR or Google XYZ methods.
- **AI-Driven Role Research**: Dynamically identifies role-specific keywords, technical requirements, and target KPIs for any job title and location.
- **Universal LLM Integration**: Built on a universal client supporting OpenAI, Anthropic, Ollama, and local OpenAI-compatible backends (e.g., LM Studio, vLLM).
- **Streamlit Dashboard**: A professional web interface for resume uploads, in-depth analysis reports, and optimization workflows.

## 🛠️ How it Works

1. **Extraction**: The system reads PDF/DOCX files and uses an LLM to "see" the resume structure, converting it into a clean JSON schema.
2. **Analysis**: The engine applies a deterministic scoring model:
   - **ATS Compatibility (25%)**: Checks for parsing risks like columns, tables, and non-standard characters.
   - **Content Impact (25%)**: Measures metric density and action verb strength.
   - **Readability (20%)**: Evaluates formatting consistency and sentence length.
   - **Keyword Strength (15%)**: Matches against dynamically researched role requirements.
   - **Role Alignment (15%)**: Checks seniority level and career progression.
3. **Optimization**: Using the researched role data, it rewrites the resume content to include missing keywords and quantifiable impacts.
4. **Sync**: Prepared for integration with external resume platforms like Rezi.

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- An API Key for your preferred LLM provider (OpenAI, Anthropic) or a local LLM server.

### 2. Clone and Install
```bash
git clone https://github.com/YOUR_USERNAME/resume-optimizer-ai.git
cd resume-optimizer-ai
pip install -r requirements.txt
```

### 3. Configuration
Copy the template configuration file:
```bash
cp config.yaml.template config.yaml
```
Edit `config.yaml` to include your `api_key` and `base_url`.

## 🖥️ Usage

Start the web dashboard:
```bash
streamlit run rezi_ui.py
```

1. **Upload**: Drop your resume (PDF/DOCX) into the sidebar.
2. **Analyze**: Click "Run Advanced ATS Analysis" to get your "brutal" score and roadmap.
3. **Optimize**: Enter your target role (e.g., "Product Manager") and location, then click "Optimize" to generate high-impact content.

## 📂 Project Structure

- `rezi_ui.py`: Main Streamlit application.
- `rezi_agent.py`: Orchestration agent for the optimization pipeline.
- `src/parser.py`: AI-driven document parsing logic.
- `src/ats_scorer.py`: The deterministic evaluation engine.
- `src/optimizer.py`: LLM-based content optimization.
- `src/role_researcher.py`: AI research for role requirements.
- `src/llm/`: Universal LLM client implementations.

---
*Disclaimer: This tool is designed for educational and optimization purposes. Use the feedback to improve your actual career documents.*
