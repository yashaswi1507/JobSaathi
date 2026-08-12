from fastapi import APIRouter
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
import os

router = APIRouter()

# --- Generate PDF report with all analysis results ---
@router.post("/generate")
def generate_report(data: dict):
    # create reports folder if not exists
    os.makedirs(r'C:\CareerShieldAI\reports', exist_ok=True)

    # define PDF file path
    pdf_path = r'C:\CareerShieldAI\reports\careershield_report.pdf'

    # setup PDF document
    doc    = SimpleDocTemplate(pdf_path, pagesize=letter)  # create doc
    styles = getSampleStyleSheet()                          # get default styles
    story  = []                                             # list of elements

    # --- Title ---
    story.append(Paragraph("CareerShield AI Report", styles['Title']))
    story.append(Spacer(1, 20))                            # add space

    # --- Resume Analysis Section ---
    story.append(Paragraph("Resume Analysis", styles['Heading1']))
    story.append(Paragraph(f"Quality Score: {data.get('quality_score', 'N/A')}/100", styles['Normal']))
    story.append(Paragraph(f"ATS Score: {data.get('ats_score', 'N/A')}%", styles['Normal']))
    story.append(Paragraph(f"Experience: {data.get('experience', 'N/A')} years", styles['Normal']))
    skills = ', '.join(data.get('skills', []))             # join skills list
    story.append(Paragraph(f"Skills: {skills}", styles['Normal']))
    story.append(Spacer(1, 15))

    # --- Career Recommendation Section ---
    story.append(Paragraph("Career Recommendation", styles['Heading1']))
    story.append(Paragraph(f"Target Role: {data.get('target_role', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Match Score: {data.get('match_score', 'N/A')}%", styles['Normal']))
    story.append(Spacer(1, 15))

    # --- Skill Gap Section ---
    story.append(Paragraph("Skill Gap Analysis", styles['Heading1']))
    missing = ', '.join(data.get('missing_skills', []))
    story.append(Paragraph(f"Skills to Learn: {missing}", styles['Normal']))
    story.append(Spacer(1, 15))

    # --- Fraud Analysis Section ---
    story.append(Paragraph("Job Fraud Analysis", styles['Heading1']))
    story.append(Paragraph(f"Fraud Probability: {data.get('fraud_probability', 'N/A')}", styles['Normal']))
    story.append(Paragraph(f"Is Fraud: {data.get('is_fraud', 'N/A')}", styles['Normal']))
    reasons = ', '.join(data.get('fraud_reasons', []))
    story.append(Paragraph(f"Reasons: {reasons}", styles['Normal']))
    story.append(Spacer(1, 15))

    # --- Roadmap Section ---
    story.append(Paragraph("Career Roadmap", styles['Heading1']))
    for step in data.get('roadmap', []):                   # loop through steps
        story.append(Paragraph(f"• {step}", styles['Normal']))

    # --- Build PDF ---
    doc.build(story)                                       # generate PDF file

    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename='careershield_report.pdf'
    )