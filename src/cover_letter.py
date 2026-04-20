"""
Cover Letter Generator Module
Wraps the existing src/generators/cover_letter.py with API integration for Streamlit app.
"""

import os
import requests
from datetime import datetime


class CoverLetterGenerator:
    """Cover letter generator with AI-powered content generation."""

    def __init__(self, api_base_url: str, api_key: str, model: str = "gpt-4"):
        """
        Initialize the cover letter generator.

        Args:
            api_base_url: Base URL for the API endpoint
            api_key: API key for authentication
            model: Model to use for generation
        """
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.output_dir = "output/cover_letters"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(
        self,
        parsed_resume: dict,
        job_description: str,
        company_details: str,
        target_role: str,
        target_location: str,
    ) -> dict:
        """
        Generate a cover letter based on resume, job description, and company details.

        Args:
            parsed_resume: Parsed resume data from parser module
            job_description: Job description text
            company_details: Company information text
            target_role: Target job role
            target_location: Target job location

        Returns:
            dict with 'markdown' and 'file_path' keys
        """
        # Extract user details from parsed resume
        personal_info = parsed_resume.get("personal_info", {})
        name = personal_info.get("name", "Candidate")
        email = personal_info.get("email", "")
        phone = personal_info.get("phone", "")
        location = personal_info.get("location", target_location)

        # Build prompt for cover letter generation
        prompt = self._build_prompt(
            name=name,
            email=email,
            phone=phone,
            location=location,
            job_description=job_description,
            company_details=company_details,
            target_role=target_role,
            target_location=target_location,
            experience=parsed_resume.get("experience", []),
            skills=parsed_resume.get("skills", {}),
        )

        # Generate content via API
        content = self._call_api(prompt)

        # Create the cover letter
        cover_letter = self._create_cover_letter(
            name=name,
            email=email,
            phone=phone,
            location=location,
            target_company=company_details.split("\n")[0]
            if company_details
            else "Target Company",
            target_role=target_role,
            content=content,
        )

        # Save to file
        filename = f"{name.replace(' ', '_')}_Cover_Letter_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
        file_path = os.path.join(self.output_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cover_letter)

        return {"markdown": cover_letter, "file_path": file_path}

    def _build_prompt(
        self,
        name: str,
        email: str,
        phone: str,
        location: str,
        job_description: str,
        company_details: str,
        target_role: str,
        target_location: str,
        experience: list,
        skills: dict,
    ) -> str:
        """Build the prompt for cover letter generation."""

        exp_summary = ""
        if experience:
            for exp in experience[:3]:  # Top 3 experiences
                exp_summary += f"- {exp.get('title', 'Role')} at {exp.get('company', 'Company')}: {exp.get('period', '')}\n"

        skills_text = ""
        if skills:
            all_skills = (
                skills.get("product", [])
                + skills.get("ai_tech", [])
                + skills.get("tools", [])
            )
            skills_text = ", ".join(all_skills[:15])

        prompt = f"""Write a professional cover letter for the following candidate:

CANDIDATE INFORMATION:
- Name: {name}
- Email: {email}
- Phone: {phone}
- Location: {location}
- Target Role: {target_role}
- Target Location: {target_location}

KEY EXPERIENCE:
{exp_summary}

SKILLS: {skills_text}

JOB DESCRIPTION:
{job_description}

COMPANY DETAILS:
{company_details}

Instructions:
1. Write a compelling cover letter that highlights relevant experience
2. Reference specific aspects of the job description and company
3. Keep it concise (3-4 paragraphs)
4. Use professional tone
5. Include specific achievements where relevant
6. End with a strong call to action

Write only the cover letter content (no placeholders):"""

        return prompt

    def _call_api(self, prompt: str) -> str:
        """Call the API to generate cover letter content."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert cover letter writer. Write compelling, personalized cover letters that highlight candidate achievements and match job requirements.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }

        try:
            response = requests.post(
                f"{self.api_base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except requests.exceptions.RequestException as e:
            # Fallback to a generic cover letter if API fails
            return self._fallback_cover_letter()

    def _fallback_cover_letter(self) -> str:
        """Generate a fallback cover letter if API fails."""
        return """I am writing to express my strong interest in the position. With my proven track record in product management and technical expertise, I am confident in my ability to contribute effectively to your team.

Throughout my career, I have demonstrated the ability to drive product strategy, lead cross-functional teams, and deliver results that impact business outcomes. I am excited about the opportunity to bring my skills and experience to your organization.

I would welcome the opportunity to discuss how my background aligns with your needs. Thank you for considering my application."""

    def _create_cover_letter(
        self,
        name: str,
        email: str,
        phone: str,
        location: str,
        target_company: str,
        target_role: str,
        content: str,
    ) -> str:
        """Create the formatted cover letter."""

        letter = f"""{name}
{location} | {phone}
{email}

Hiring Manager
{target_company}
{target_location}

RE: {target_role} Application

Dear Hiring Manager,

{content}

Sincerely,

{name}"""

        return letter.strip()

    def generate_pdf(self, cover_letter: str, output_path: str = None) -> str:
        """
        Generate PDF from cover letter text.

        Args:
            cover_letter: Cover letter text
            output_path: Optional output path for PDF

        Returns:
            Path to generated PDF
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(
                    self.output_dir, f"cover_letter_{timestamp}.pdf"
                )

            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
            )

            styles = getSampleStyleSheet()
            story = []

            # Add each paragraph
            for para in cover_letter.split("\n\n"):
                if para.strip():
                    story.append(Paragraph(para.strip(), styles["Normal"]))
                    story.append(Spacer(1, 12))

            doc.build(story)
            return output_path

        except ImportError:
            # reportlab not installed
            return None
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None


if __name__ == "__main__":
    # Test the generator
    generator = CoverLetterGenerator(
        api_base_url="https://api.openai.com", api_key="test-key", model="gpt-4"
    )

    sample_resume = {
        "personal_info": {
            "name": "Ali Husain Sorathiya",
            "email": "test@example.com",
            "phone": "+971-524678604",
            "location": "Dubai, UAE",
        },
        "experience": [
            {
                "title": "Senior Product Manager",
                "company": "CAFU",
                "period": "2023-Present",
            }
        ],
        "skills": {
            "product": ["Product Strategy", "Roadmapping"],
            "ai_tech": ["Python", "SQL"],
            "tools": ["Jira", "Confluence"],
        },
    }

    result = generator.generate(
        parsed_resume=sample_resume,
        job_description="Looking for a Product Manager with API experience",
        company_details="Tech Company in Dubai",
        target_role="Senior Product Manager",
        target_location="Dubai, UAE",
    )

    print(f"Cover letter generated: {result['file_path']}")
    print(f"\nContent:\n{result['markdown'][:500]}...")
