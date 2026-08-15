from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.resume_parser import (extract_skills, extract_skills_with_confidence,
                                extract_education, extract_experience,
                                calculate_quality_score, calculate_ats_score)
from app.ocr_extractor import extract_and_clean
import pypdf
import io

router = APIRouter()                                   # create router for resume endpoints

# --- Helper: extract text from uploaded PDF ---
def extract_pdf_text(file_bytes: bytes) -> str:
    pdf = pypdf.PdfReader(io.BytesIO(file_bytes))     # read PDF from bytes
    text = ""
    for page in pdf.pages:                            # loop through each page
        text += page.extract_text() or ""             # extract text from page
    return text                                        # return full text

# --- Analyze uploaded resume ---
@router.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    # check file is PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    # read file bytes
    file_bytes = await file.read()                    # read uploaded file

    # extract text from PDF
    text = extract_pdf_text(file_bytes)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    # run all parsers
    skills     = extract_skills(text)                 # extract skills
    education  = extract_education(text)              # extract education
    experience = extract_experience(text)             # extract experience years
    # Use hybrid analysis (LLM + rule-based fallback)
    if HYBRID_AVAILABLE:
        result = analyze_resume_hybrid(text, "")
        result["filename"]    = file.filename
        result["resume_text"] = text[:500]
        # Add NER parsing
        if NER_AVAILABLE:
            try:
                ner_data = parse_resume_ner(text)
                result["ner_entities"]       = ner_data
                result["companies_detected"] = ner_data.get("companies", [])
                result["skills_categorized"] = ner_data.get("skills_by_category", {})
                if not result.get("skills"):
                    result["skills"] = ner_data.get("skills", [])
            except Exception as e:
                print(f"[NER] Failed: {e}")
        return result

    quality    = calculate_quality_score(text)        # calculate quality score

    return {
        "skills":        skills,
        "education":     education,
        "experience":    experience,
        "quality_score": quality,
        "resume_text":   text[:500]                   # return first 500 chars as preview
    }

# --- ATS match: resume vs job description ---
@router.post("/ats-match")
async def ats_match(file: UploadFile = File(...), job_description: str = Form(default="")):
    if not job_description.strip():
        raise HTTPException(
            status_code=400,
            detail="job_description is required. Paste the job posting text."
        )

    file_bytes  = await file.read()
    resume_text = extract_and_clean(file_bytes, file.filename)
    ats_score, breakdown = calculate_ats_score(resume_text, job_description)

    resume_scored = extract_skills_with_confidence(resume_text)
    job_scored    = extract_skills_with_confidence(job_description)
    resume_skills = [s["skill"] for s in resume_scored if s["confidence"] > 0]
    job_skills    = [s["skill"] for s in job_scored    if s["confidence"] > 0]
    missing       = [s for s in job_skills if s not in resume_skills]

    return {
        "ats_score":      ats_score,
        "grade":          breakdown.get("total", {}).get("grade", ""),
        "resume_skills":  resume_skills,
        "job_skills":     job_skills,
        "missing_skills": missing,
        "breakdown":      breakdown,
    }

# ============================================================
# ATS SCORE BASED TEMPLATE RECOMMENDATION
# ============================================================
@router.post("/ats-recommend")
async def ats_recommend(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    current_design: str = Form(default="modern"),
    current_level: str = Form(default="fresher"),
    current_domain: str = Form(default="software"),
):
    """
    SMART ATS RECOMMENDATION FLOW:

    1. Upload resume + paste job description
    2. System calculates ATS score with detailed breakdown
    3. Based on score range, recommends best templates:
       - Score < 50  → "Critical" → Top ATS-friendly templates
       - Score 50-70 → "Average"  → Templates to push to 70-80
       - Score 70-80 → "Good"     → Templates to push to 80+
       - Score > 80  → "Excellent" → You're good!
    4. Returns: score, breakdown, ranked template recommendations
    5. Frontend shows: "Apply Template" button → calls /resume/build

    Response includes:
      - current_score, score_range, score_label
      - target_range (e.g. "70-80")
      - recommendations[] — ranked templates with expected boost
      - best_template — #1 recommendation
      - content_improvements — what to fix in content too
      - estimated_score_after — expected score after applying best template
    """
    if not job_description.strip():
        raise HTTPException(400, "job_description is required.")

    file_bytes  = await file.read()
    resume_text = extract_and_clean(file_bytes, file.filename)

    if not resume_text.strip():
        raise HTTPException(400, "Could not extract text from resume.")

    # Calculate ATS score with breakdown
    ats_score, breakdown = calculate_ats_score(resume_text, job_description)

    # Get template recommendations — Groq + rule-based combined
    from app.template_suggester import suggest_templates
    rule_based = suggest_templates(
        ats_score=ats_score,
        level=current_level,
        domain=current_domain,
        breakdown=breakdown,
    )

    # Groq intelligent suggestion
    groq_suggestion = None
    try:
        from app.llm_service import suggest_template_with_groq
        groq_suggestion = suggest_template_with_groq(
            resume_text=resume_text,
            job_description=job_description,
            detected_level=current_level,
            detected_domain=current_domain,
            ats_score=ats_score,
            breakdown=breakdown,
        )
    except Exception:
        pass  # fallback to rule-based only

    # Merge: Groq primary + rule-based alternatives
    final_suggestion = {
        **rule_based,
        "ai_suggestion": groq_suggestion,
        "primary_template": groq_suggestion if groq_suggestion else rule_based.get("primary"),
    }

    # Also extract skills for display
    resume_scored = extract_skills_with_confidence(resume_text)
    job_scored    = extract_skills_with_confidence(job_description)
    resume_skills = [s["skill"] for s in resume_scored if s["confidence"] > 0]
    job_skills    = [s["skill"] for s in job_scored    if s["confidence"] > 0]

    return {
        **final_suggestion,
        "breakdown":      breakdown,
        "resume_skills":  resume_skills,
        "job_skills":     job_skills,
        "missing_skills": [s for s in job_skills if s not in resume_skills],
    }