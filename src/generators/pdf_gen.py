from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
import json

class ResumeGenerator:
    def __init__(self, output_path):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self.custom_styles()

    def custom_styles(self):
        # Header Style
        self.styles.add(ParagraphStyle(
            name='NameHeader',
            fontSize=18,
            leading=22,
            alignment=1, # Center
            spaceAfter=2,
            fontName='Helvetica-Bold'
        ))
        # Subheader (Contact)
        self.styles.add(ParagraphStyle(
            name='ContactInfo',
            fontSize=9,
            alignment=1,
            spaceAfter=12
        ))
        # Section Heading
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            fontSize=12,
            leading=14,
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=5,
            borderPadding=(0, 0, 1, 0),
            borderColor=colors.black,
        ))
        # Job Title / Company
        self.styles.add(ParagraphStyle(
            name='JobHeader',
            fontSize=10,
            leading=12,
            fontName='Helvetica-Bold',
            spaceBefore=6
        ))
        # Bullet Points
        if 'CustomBullet' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomBullet',
                fontSize=9,
                leading=11,
                leftIndent=15,
                firstLineIndent=0,
                spaceBefore=3
            ))

    def generate(self, data):
        doc = SimpleDocTemplate(self.output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []

        # 1. Header
        story.append(Paragraph(data['personal_info']['name'].upper(), self.styles['NameHeader']))

        contact = f"{data['personal_info']['location']} | {data['personal_info']['email']} | {data['personal_info']['phone']}<br/>"
        contact += f"<b>Visa:</b> {data['personal_info']['visa_status']} | <b>Notice:</b> {data['personal_info']['notice_period']}"
        story.append(Paragraph(contact, self.styles['ContactInfo']))

        # 2. Summary
        story.append(Paragraph("PROFESSIONAL SUMMARY", self.styles['SectionHeading']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
        story.append(Paragraph(data['summary'], self.styles['Normal']))
        story.append(Spacer(1, 10))

        # 3. Experience
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", self.styles['SectionHeading']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))

        for exp in data['experience']:
            header = f"<b>{exp['title']}</b> | {exp['company']} | {exp['location']} | {exp['period']}"
            story.append(Paragraph(header, self.styles['JobHeader']))
            for bullet in exp['bullets']:
                # PAR Framework: Problem -> Action -> Result
                text = f"• <b>[Problem]:</b> {bullet['problem']} <b>[Action]:</b> {bullet['action']} <b>[Result]:</b> {bullet['result']}"
                story.append(Paragraph(text, self.styles['CustomBullet']))
            story.append(Spacer(1, 5))

        # 4. Skills
        story.append(Paragraph("TECHNICAL SKILLS", self.styles['SectionHeading']))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black))

        skills_text = f"<b>Product:</b> {', '.join(data['skills']['product'])}<br/>"
        skills_text += f"<b>AI & Tech:</b> {', '.join(data['skills']['ai_tech'])}<br/>"
        skills_text += f"<b>Tools:</b> {', '.join(data['skills']['tools'])}"
        story.append(Paragraph(skills_text, self.styles['Normal']))

        doc.build(story)
        print(f"PDF generated at {self.output_path}")

if __name__ == "__main__":
    with open('data/master_profile.json', 'r') as f:
        data = json.load(f)
    gen = ResumeGenerator('ai-resume/Ali_Husain_Sorathiya_Sr_PM_Tailored.pdf')
    gen.generate(data)
