import streamlit as st
import requests

# --- Backend API URL ---
API_URL = "http://127.0.0.1:8000"                    # FastAPI backend address

# --- Page title ---
st.set_page_config(page_title="CareerShield AI", layout="wide")
st.title("CareerShield AI — Testing Dashboard")

# --- Sidebar navigation ---
page = st.sidebar.selectbox("Select Module", [
    "Fraud Detection",
    "Resume Analysis",
    "Career Recommendation",
    "Interview Prep",
    "Generate Report"
])

# ============================================================
# PAGE 1 — FRAUD DETECTION
# ============================================================
if page == "Fraud Detection":
    st.header("Job Fraud Detection")

    job_title       = st.text_input("Job Title", "Data Entry Specialist")
    company_profile = st.text_area("Company Profile (leave empty to test fraud)", "")
    salary_range    = st.text_input("Salary Range", "Not Specified")
    job_description = st.text_area("Job Description", 
        "URGENT HIRING! Work from home, no experience needed. Earn $5000 weekly guaranteed!")

    if st.button("Check for Fraud"):
        # send request to fraud endpoint
        response = requests.post(f"{API_URL}/fraud/check", json={
            "job_description": job_description,
            "job_title":       job_title,
            "company_profile": company_profile,
            "salary_range":    salary_range
        })

        if response.status_code == 200:
            result = response.json()
            # show fraud probability
            prob = result['fraud_probability']
            st.metric("Fraud Probability", f"{prob * 100:.0f}%")

            # show fraud status
            if result['is_fraud']:
                st.error("This job posting appears to be FRAUDULENT")
            else:
                st.success("This job posting appears to be LEGITIMATE")

            # show reasons
            if result['reasons']:
                st.subheader("Fraud Indicators:")
                for reason in result['reasons']:
                    st.write(f"• {reason}")
        else:
            st.error(f"Error: {response.text}")

# ============================================================
# PAGE 2 — RESUME ANALYSIS
# ============================================================
elif page == "Resume Analysis":
    st.header("Resume Analysis")

    resume_text = st.text_area("Paste Resume Text Here", height=300,
        placeholder="Paste your resume text here...")
    job_desc = st.text_area("Paste Job Description (for ATS score)", height=150,
        placeholder="Paste job description here...")

    if st.button("Analyze Resume"):
        if not resume_text.strip():
            st.warning("Please paste your resume text first.")
        else:
            import sys
            sys.path.append(r'C:\CareerShieldAI\backend\app')
            from resume_parser import (extract_skills, extract_education,
                                       extract_experience, calculate_quality_score,
                                       calculate_ats_score)

            # run analysis directly (no API call needed for text input)
            skills     = extract_skills(resume_text)
            education  = extract_education(resume_text)
            experience = extract_experience(resume_text)
            quality    = calculate_quality_score(resume_text)
            ats        = calculate_ats_score(resume_text, job_desc) if job_desc else 0

            # show results
            col1, col2, col3 = st.columns(3)
            col1.metric("Quality Score", f"{quality}/100")
            col2.metric("ATS Match",     f"{ats}%")
            col3.metric("Experience",    f"{experience} years")

            st.subheader("Skills Found:")
            st.write(skills if skills else "No skills detected")

            st.subheader("Education Found:")
            st.write(education if education else "No education detected")

# ============================================================
# PAGE 3 — CAREER RECOMMENDATION
# ============================================================
elif page == "Career Recommendation":
    st.header("Career Recommendation")

    skills_input = st.text_input("Enter your skills (comma separated)",
        "python, machine learning, sql, aws, docker")

    if st.button("Get Recommendations"):
        import sys
        sys.path.append(r'C:\CareerShieldAI\backend\app')
        from career_recommender import recommend_careers, find_skill_gap

        skills = [s.strip() for s in skills_input.split(',')]  # split by comma

        with st.spinner("Finding best career matches..."):
            recommendations = recommend_careers(skills, top_n=5)  # call directly

        st.subheader("Top Career Matches:")
        for i, rec in enumerate(recommendations, 1):
            with st.expander(f"{i}. {rec['job_title']} — {rec['match_score']}% match"):
                st.write(f"Required Skills: {rec['required_skills'][:200]}")

        # --- Also show skill gap for top role ---
        top_role = recommendations[0]
        gap = find_skill_gap(skills, top_role['required_skills'])

        st.subheader("Skill Gap for Top Role:")
        st.write(f"Already Have: {gap['matching_skills']}")
        st.write(f"Need to Learn: {gap['missing_skills']}")

# ============================================================
# PAGE 4 — INTERVIEW PREP
# ============================================================
elif page == "Interview Prep":
    st.header("Interview Preparation Kit")

    target_role   = st.text_input("Target Role", "Python Engineer")
    skills_input  = st.text_input("Your Skills (comma separated)",
        "python, sql, aws, docker")
    missing_input = st.text_input("Missing Skills (comma separated)",
        "django, flask, rest")

    if st.button("Generate Interview Kit"):
        import sys
        sys.path.append(r'C:\CareerShieldAI\backend\app')
        from interview_prep import generate_interview_kit

        skills  = [s.strip() for s in skills_input.split(',')]
        missing = [s.strip() for s in missing_input.split(',')]

        kit = generate_interview_kit(                  # call directly
            target_role=target_role,
            resume_skills=skills,
            missing_skills=missing
        )

        st.subheader("Career Roadmap:")
        for step in kit['roadmap']:
            st.write(f"• {step}")

        st.subheader("Technical Questions:")
        for q in kit['technical_questions']:
            st.write(f"• {q}")

        st.subheader("HR Questions:")
        for q in kit['hr_questions']:
            st.write(f"• {q}")

        st.subheader("Project Questions:")
        for q in kit['project_questions']:
            st.write(f"• {q}")

# ============================================================
# PAGE 5 — GENERATE REPORT
# ============================================================
elif page == "Generate Report":
    st.header("Generate PDF Report")
    st.info("Fill in the details below to generate a complete PDF report.")

    quality_score     = st.number_input("Quality Score", 0, 100, 82)
    ats_score         = st.number_input("ATS Score", 0, 100, 75)
    experience        = st.number_input("Experience (years)", 0, 50, 5)
    skills_input      = st.text_input("Skills", "python, sql, aws, docker")
    target_role       = st.text_input("Target Role", "Python Engineer")
    match_score       = st.number_input("Match Score", 0, 100, 85)
    missing_input     = st.text_input("Missing Skills", "django, flask, rest")
    fraud_probability = st.number_input("Fraud Probability", 0.0, 1.0, 0.91)
    is_fraud          = st.checkbox("Is Fraud", value=True)
    fraud_reasons     = st.text_input("Fraud Reasons",
        "Missing company profile, Scam keywords detected")
    roadmap_input     = st.text_input("Roadmap Steps",
        "Step 1: Learn Django, Step 2: Learn REST, Final: Build projects")

    if st.button("Generate PDF Report"):
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        import os

        # create reports folder
        os.makedirs(r'C:\CareerShieldAI\reports', exist_ok=True)
        pdf_path = r'C:\CareerShieldAI\reports\careershield_report.pdf'

        doc    = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story  = []

        # title
        story.append(Paragraph("CareerShield AI Report", styles['Title']))
        story.append(Spacer(1, 20))

        # resume section
        story.append(Paragraph("Resume Analysis", styles['Heading1']))
        story.append(Paragraph(f"Quality Score: {quality_score}/100", styles['Normal']))
        story.append(Paragraph(f"ATS Score: {ats_score}%", styles['Normal']))
        story.append(Paragraph(f"Experience: {experience} years", styles['Normal']))
        story.append(Paragraph(f"Skills: {skills_input}", styles['Normal']))
        story.append(Spacer(1, 15))

        # career section
        story.append(Paragraph("Career Recommendation", styles['Heading1']))
        story.append(Paragraph(f"Target Role: {target_role}", styles['Normal']))
        story.append(Paragraph(f"Match Score: {match_score}%", styles['Normal']))
        story.append(Spacer(1, 15))

        # skill gap section
        story.append(Paragraph("Skill Gap Analysis", styles['Heading1']))
        story.append(Paragraph(f"Skills to Learn: {missing_input}", styles['Normal']))
        story.append(Spacer(1, 15))

        # fraud section
        story.append(Paragraph("Job Fraud Analysis", styles['Heading1']))
        story.append(Paragraph(f"Fraud Probability: {fraud_probability}", styles['Normal']))
        story.append(Paragraph(f"Is Fraud: {is_fraud}", styles['Normal']))
        story.append(Paragraph(f"Reasons: {fraud_reasons}", styles['Normal']))
        story.append(Spacer(1, 15))

        # roadmap section
        story.append(Paragraph("Career Roadmap", styles['Heading1']))
        for step in roadmap_input.split(','):
            story.append(Paragraph(f"• {step.strip()}", styles['Normal']))

        # build PDF
        doc.build(story)

        # offer download
        with open(pdf_path, 'rb') as f:
            st.download_button(
                label="Download PDF Report",
                data=f.read(),
                file_name="careershield_report.pdf",
                mime="application/pdf"
            )
        st.success("Report generated successfully.")