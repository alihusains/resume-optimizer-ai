"""
PDF Generator Module
Wraps the existing src/generators/pdf_gen.py with enhanced templates for Streamlit app.
"""

import os
import json
from datetime import datetime
from typing import Dict, Optional


class PDFGenerator:
    """PDF resume generator with multiple templates."""

    TEMPLATES = {
        "modern": "Modern template with clean typography",
        "classic": "Classic template with traditional formatting",
        "technical": "Technical template with bullet-focused layout",
        "executive": "Executive template with emphasis on leadership",
    }

    def __init__(self, template: str = "modern"):
        """
        Initialize the PDF generator.

        Args:
            template: Template name to use for generation
        """
        self.template = template
        self.output_dir = "output/resumes"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, resume_data: Dict, output_filename: str = None) -> str:
        """
        Generate a PDF from resume data.

        Args:
            resume_data: Resume content dictionary with sections
            output_filename: Optional custom filename

        Returns:
            Path to generated PDF
        """
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"resume_{self.template}_{timestamp}.pdf"

        output_path = os.path.join(self.output_dir, output_filename)

        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                HRFlowable,
            )

            # Build based on template
            if self.template == "modern":
                return self._build_modern_template(resume_data, output_path)
            elif self.template == "classic":
                return self._build_classic_template(resume_data, output_path)
            elif self.template == "technical":
                return self._build_technical_template(resume_data, output_path)
            elif self.template == "executive":
                return self._build_executive_template(resume_data, output_path)
            else:
                return self._build_modern_template(resume_data, output_path)

        except ImportError:
            raise ImportError(
                "reportlab is required. Install with: pip install reportlab"
            )
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")

    def _build_modern_template(self, data: Dict, output_path: str) -> str:
        """Build modern template - clean typography with accent colors."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        self._add_custom_styles(styles)

        story = []

        # Header
        personal = data.get("personal_info", {})
        name = personal.get("name", "Your Name").upper()
        story.append(Paragraph(name, styles["NameHeader"]))

        # Contact info
        contact = f"{personal.get('location', 'Location')} | {personal.get('email', 'email@example.com')} | {personal.get('phone', 'Phone')}"
        if personal.get("linkedin"):
            contact += f" | {personal.get('linkedin')}"
        story.append(Paragraph(contact, styles["ContactInfo"]))
        story.append(Spacer(1, 15))

        # Summary
        if data.get("summary"):
            story.append(Paragraph("PROFESSIONAL SUMMARY", styles["SectionHeading"]))
            story.append(
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E4057"))
            )
            story.append(Paragraph(data["summary"], styles["Normal"]))
            story.append(Spacer(1, 10))

        # Experience
        if data.get("experience"):
            story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles["SectionHeading"]))
            story.append(
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E4057"))
            )

            for exp in data["experience"]:
                header = f"<b>{exp.get('title', 'Role')}</b> | {exp.get('company', 'Company')} | {exp.get('location', '')} | {exp.get('period', '')}"
                story.append(Paragraph(header, styles["JobHeader"]))

                for bullet in exp.get("bullets", []):
                    if isinstance(bullet, dict):
                        text = f"• <b>[Problem]:</b> {bullet.get('problem', '')} <b>[Action]:</b> {bullet.get('action', '')} <b>[Result]:</b> {bullet.get('result', '')}"
                    else:
                        text = f"• {bullet}"
                    story.append(Paragraph(text, styles["CustomBullet"]))
                story.append(Spacer(1, 5))

        # Education
        if data.get("education"):
            story.append(Paragraph("EDUCATION", styles["SectionHeading"]))
            story.append(
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E4057"))
            )
            for edu in data["education"]:
                header = f"<b>{edu.get('degree', 'Degree')}</b> | {edu.get('school', 'School')} | {edu.get('year', '')}"
                story.append(Paragraph(header, styles["JobHeader"]))
            story.append(Spacer(1, 10))

        # Skills
        if data.get("skills"):
            story.append(Paragraph("SKILLS", styles["SectionHeading"]))
            story.append(
                HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2E4057"))
            )

            skills = data["skills"]
            skills_text = ""
            if "product" in skills:
                skills_text += f"<b>Product:</b> {', '.join(skills['product'])}<br/>"
            if "ai_tech" in skills:
                skills_text += f"<b>AI & Tech:</b> {', '.join(skills['ai_tech'])}<br/>"
            if "tools" in skills:
                skills_text += f"<b>Tools:</b> {', '.join(skills['tools'])}"

            if skills_text:
                story.append(Paragraph(skills_text, styles["Normal"]))

        doc.build(story)
        print(f"PDF generated at {output_path}")
        return output_path

    def _build_classic_template(self, data: Dict, output_path: str) -> str:
        """Build classic template - traditional formatting."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=60,
            leftMargin=60,
            topMargin=50,
            bottomMargin=50,
        )

        styles = getSampleStyleSheet()

        # Classic styles
        styles.add(
            ParagraphStyle(
                name="ClassicHeader",
                fontSize=14,
                leading=18,
                alignment=1,
                fontName="Times-Bold",
                spaceAfter=5,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ClassicContact", fontSize=10, alignment=1, spaceAfter=15
            )
        )
        styles.add(
            ParagraphStyle(
                name="ClassicSection",
                fontSize=12,
                leading=14,
                fontName="Times-Bold",
                spaceBefore=12,
                spaceAfter=5,
                textColor=colors.black,
            )
        )

        story = []

        # Header
        personal = data.get("personal_info", {})
        story.append(
            Paragraph(
                personal.get("name", "Your Name").upper(), styles["ClassicHeader"]
            )
        )

        contact = f"{personal.get('location', '')} | {personal.get('email', '')} | {personal.get('phone', '')}"
        story.append(Paragraph(contact, styles["ClassicContact"]))

        # Summary
        if data.get("summary"):
            story.append(Paragraph("SUMMARY", styles["ClassicSection"]))
            story.append(Paragraph(data["summary"], styles["Normal"]))
            story.append(Spacer(1, 10))

        # Experience
        if data.get("experience"):
            story.append(Paragraph("EXPERIENCE", styles["ClassicSection"]))
            for exp in data["experience"]:
                header = f"{exp.get('title', '')} - {exp.get('company', '')} ({exp.get('period', '')})"
                story.append(Paragraph(f"<b>{header}</b>", styles["Normal"]))
                for bullet in exp.get("bullets", []):
                    if isinstance(bullet, dict):
                        text = f"• {bullet.get('result', '')}"
                    else:
                        text = f"• {bullet}"
                    story.append(Paragraph(text, styles["Normal"]))
                story.append(Spacer(1, 8))

        # Skills
        if data.get("skills"):
            story.append(Paragraph("SKILLS", styles["ClassicSection"]))
            all_skills = []
            for cat in data["skills"].values():
                if isinstance(cat, list):
                    all_skills.extend(cat)
            story.append(Paragraph(", ".join(all_skills), styles["Normal"]))

        doc.build(story)
        return output_path

    def _build_technical_template(self, data: Dict, output_path: str) -> str:
        """Build technical template - bullet-focused with monospace styling."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=35,
            leftMargin=35,
            topMargin=35,
            bottomMargin=35,
        )

        styles = getSampleStyleSheet()

        # Technical styles
        styles.add(
            ParagraphStyle(
                name="TechHeader",
                fontSize=16,
                leading=20,
                fontName="Courier-Bold",
                alignment=0,
                spaceAfter=3,
            )
        )
        styles.add(
            ParagraphStyle(
                name="TechContact", fontSize=9, fontName="Courier", spaceAfter=12
            )
        )
        styles.add(
            ParagraphStyle(
                name="TechSection",
                fontSize=11,
                leading=14,
                fontName="Courier-Bold",
                spaceBefore=10,
                spaceAfter=4,
                textColor=colors.HexColor("#333333"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="TechBullet",
                fontSize=9,
                leading=11,
                fontName="Courier",
                leftIndent=10,
                firstLineIndent=-10,
            )
        )

        story = []

        personal = data.get("personal_info", {})
        story.append(
            Paragraph(personal.get("name", "Your Name").upper(), styles["TechHeader"])
        )

        contact = f"{personal.get('location', '')} | {personal.get('email', '')} | {personal.get('phone', '')}"
        story.append(Paragraph(contact, styles["TechContact"]))

        # Skills first for technical template
        if data.get("skills"):
            story.append(Paragraph("TECHNICAL SKILLS", styles["TechSection"]))
            for category, skill_list in data["skills"].items():
                if isinstance(skill_list, list):
                    story.append(
                        Paragraph(
                            f"{category.upper()}: {', '.join(skill_list)}",
                            styles["TechBullet"],
                        )
                    )
            story.append(Spacer(1, 10))

        # Then experience
        if data.get("experience"):
            story.append(Paragraph("WORK EXPERIENCE", styles["TechSection"]))
            for exp in data["experience"]:
                header = f"{exp.get('title', '')} @ {exp.get('company', '')} | {exp.get('period', '')}"
                story.append(Paragraph(f"<b>{header}</b>", styles["TechBullet"]))
                for bullet in exp.get("bullets", []):
                    if isinstance(bullet, dict):
                        text = f"  → {bullet.get('result', '')}"
                    else:
                        text = f"  → {bullet}"
                    story.append(Paragraph(text, styles["TechBullet"]))
                story.append(Spacer(1, 5))

        doc.build(story)
        return output_path

    def _build_executive_template(self, data: Dict, output_path: str) -> str:
        """Build executive template - leadership emphasis with premium styling."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib import colors

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=45,
            bottomMargin=45,
        )

        styles = getSampleStyleSheet()

        # Executive styles - more spacing, premium feel
        styles.add(
            ParagraphStyle(
                name="ExecHeader",
                fontSize=20,
                leading=24,
                alignment=1,
                fontName="Helvetica-Bold",
                spaceAfter=2,
                textColor=colors.HexColor("#1a1a1a"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="ExecContact",
                fontSize=10,
                alignment=1,
                spaceAfter=20,
                textColor=colors.HexColor("#555555"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="ExecSection",
                fontSize=13,
                leading=16,
                fontName="Helvetica-Bold",
                spaceBefore=15,
                spaceAfter=8,
                textColor=colors.HexColor("#1a1a1a"),
            )
        )
        styles.add(
            ParagraphStyle(
                name="ExecJob",
                fontSize=11,
                leading=13,
                fontName="Helvetica-Bold",
                spaceBefore=8,
            )
        )
        styles.add(
            ParagraphStyle(
                name="ExecBullet",
                fontSize=10,
                leading=14,
                leftIndent=20,
                firstLineIndent=-15,
            )
        )

        story = []

        personal = data.get("personal_info", {})
        story.append(
            Paragraph(personal.get("name", "Your Name").upper(), styles["ExecHeader"])
        )

        contact_parts = []
        if personal.get("location"):
            contact_parts.append(personal["location"])
        if personal.get("email"):
            contact_parts.append(personal["email"])
        if personal.get("phone"):
            contact_parts.append(personal["phone"])

        story.append(Paragraph(" | ".join(contact_parts), styles["ExecContact"]))

        # Executive summary
        if data.get("summary"):
            story.append(Paragraph("EXECUTIVE SUMMARY", styles["ExecSection"]))
            story.append(Paragraph(data["summary"], styles["Normal"]))
            story.append(Spacer(1, 15))

        # Leadership experience
        if data.get("experience"):
            story.append(Paragraph("LEADERSHIP EXPERIENCE", styles["ExecSection"]))
            for exp in data["experience"]:
                header = f"{exp.get('title', '')} | {exp.get('company', '')}"
                subheader = f"{exp.get('location', '')} | {exp.get('period', '')}"
                story.append(Paragraph(f"<b>{header}</b>", styles["ExecJob"]))
                story.append(Paragraph(subheader, styles["Normal"]))

                for bullet in exp.get("bullets", []):
                    if isinstance(bullet, dict):
                        # Highlight results for executive template
                        result = bullet.get("result", "")
                        if result:
                            story.append(Paragraph(f"→ {result}", styles["ExecBullet"]))
                story.append(Spacer(1, 10))

        # Core competencies
        if data.get("skills"):
            story.append(Paragraph("CORE COMPETENCIES", styles["ExecSection"]))
            all_skills = []
            for cat in data["skills"].values():
                if isinstance(cat, list):
                    all_skills.extend(cat)
            # Display in columns
            skills_per_col = (len(all_skills) + 2) // 3
            for i in range(0, len(all_skills), skills_per_col):
                col_skills = all_skills[i : i + skills_per_col]
                story.append(Paragraph(" • ".join(col_skills), styles["Normal"]))

        doc.build(story)
        return output_path

    def _add_custom_styles(self, styles):
        """Add custom paragraph styles for modern template."""
        if "NameHeader" not in styles:
            styles.add(
                ParagraphStyle(
                    name="NameHeader",
                    fontSize=18,
                    leading=22,
                    alignment=1,
                    spaceAfter=2,
                    fontName="Helvetica-Bold",
                )
            )

        if "ContactInfo" not in styles:
            styles.add(
                ParagraphStyle(
                    name="ContactInfo", fontSize=9, alignment=1, spaceAfter=12
                )
            )

        if "SectionHeading" not in styles:
            styles.add(
                ParagraphStyle(
                    name="SectionHeading",
                    fontSize=12,
                    leading=14,
                    fontName="Helvetica-Bold",
                    spaceBefore=10,
                    spaceAfter=5,
                    textColor=colors.HexColor("#2E4057"),
                )
            )

        if "JobHeader" not in styles:
            styles.add(
                ParagraphStyle(
                    name="JobHeader",
                    fontSize=10,
                    leading=12,
                    fontName="Helvetica-Bold",
                    spaceBefore=6,
                )
            )

        if "CustomBullet" not in styles:
            styles.add(
                ParagraphStyle(
                    name="CustomBullet",
                    fontSize=9,
                    leading=11,
                    leftIndent=15,
                    firstLineIndent=0,
                    spaceBefore=3,
                )
            )

    def generate_markdown(self, resume_data: Dict) -> str:
        """
        Generate markdown version of resume.

        Args:
            resume_data: Resume content dictionary

        Returns:
            Markdown formatted resume
        """
        md = []

        # Header
        personal = resume_data.get("personal_info", {})
        md.append(f"# {personal.get('name', 'Your Name')}")
        md.append("")

        contact = []
        if personal.get("location"):
            contact.append(personal["location"])
        if personal.get("email"):
            contact.append(personal["email"])
        if personal.get("phone"):
            contact.append(personal["phone"])

        md.append(" | ".join(contact))
        md.append("")

        # Summary
        if resume_data.get("summary"):
            md.append("## Professional Summary")
            md.append("")
            md.append(resume_data["summary"])
            md.append("")

        # Experience
        if resume_data.get("experience"):
            md.append("## Professional Experience")
            md.append("")
            for exp in resume_data["experience"]:
                md.append(
                    f"### {exp.get('title', 'Role')} | {exp.get('company', 'Company')}"
                )
                md.append(f"*{exp.get('location', '')} | {exp.get('period', '')}*")
                md.append("")
                for bullet in exp.get("bullets", []):
                    if isinstance(bullet, dict):
                        text = f"- *Result:* {bullet.get('result', '')}"
                    else:
                        text = f"- {bullet}"
                    md.append(text)
                md.append("")

        # Education
        if resume_data.get("education"):
            md.append("## Education")
            md.append("")
            for edu in resume_data["education"]:
                md.append(f"### {edu.get('degree', 'Degree')}")
                md.append(f"*{edu.get('school', 'School')} | {edu.get('year', '')}*")
                md.append("")

        # Skills
        if resume_data.get("skills"):
            md.append("## Skills")
            md.append("")
            for category, skill_list in resume_data["skills"].items():
                if isinstance(skill_list, list):
                    md.append(f"**{category.title()}:** {', '.join(skill_list)}")
            md.append("")

        return "\n".join(md)


if __name__ == "__main__":
    # Test the generator
    generator = PDFGenerator(template="modern")

    sample_resume = {
        "personal_info": {
            "name": "Ali Husain Sorathiya",
            "email": "sorathiyaalihusain@gmail.com",
            "phone": "+971-524678604",
            "location": "Dubai, UAE",
        },
        "summary": "Senior Product Manager with 6+ years experience in B2B SaaS...",
        "experience": [
            {
                "title": "Senior Product Manager",
                "company": "CAFU",
                "location": "Dubai, UAE",
                "period": "2023-Present",
                "bullets": [
                    {
                        "problem": "Low conversion",
                        "action": "Implemented pricing",
                        "result": "+25% conversion",
                    }
                ],
            }
        ],
        "skills": {
            "product": ["Product Strategy", "Roadmapping"],
            "ai_tech": ["Python", "SQL"],
            "tools": ["Jira", "Confluence"],
        },
    }

    # Generate PDF
    pdf_path = generator.generate(sample_resume)
    print(f"PDF generated: {pdf_path}")

    # Generate markdown
    md = generator.generate_markdown(sample_resume)
    print(f"\nMarkdown preview:\n{md[:500]}...")
