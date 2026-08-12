"""
routes/resume_features_routes.py
----------------------------------
FastAPI endpoints for the 3 non-LLM resume features:
  POST /resume/grammar-check         — grammar issues + corrected text
  POST /resume/keyword-optimization  — missing keywords vs JD
  POST /resume/keyword-stuffing      — recruiter-side stuffing detection

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\routes\\resume_features_routes.py

REGISTER IN main.py:
  from app.routes import resume_features_routes
  app.include_router(resume_features_routes.router,
                     prefix="/resume", tags=["Resume Features"])
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.resume_features import (
    check_grammar,
    get_keyword_optimization,
    detect_keyword_stuffing,
)
from app.ocr_extractor import extract_and_clean

router = APIRouter()

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}


def _check_extension(filename: str):
    import os
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Accepted: PDF, PNG, JPG"
        )
    return ext


# ============================================================
# 1. Grammar Fix
# ============================================================
@router.post("/grammar-check")
async def grammar_check(
    file: UploadFile = File(None),
    text: str = Form(default=""),
):
    """
    Checks grammar of resume text.
    Accepts either:
      - file upload (PDF/image resume) → text is extracted first
      - raw text directly via form field
    Returns grammar issues with suggestions and a corrected version.
    """
    if file and file.filename:
        _check_extension(file.filename)
        file_bytes = await file.read()
        text = extract_and_clean(file_bytes, file.filename)

    if not text.strip():
        raise HTTPException(status_code=400,
                            detail="No text provided — upload a file or send text.")

    result = check_grammar(text)
    return result


# ============================================================
# 2. Keyword Optimization
# ============================================================
@router.post("/keyword-optimization")
async def keyword_optimization(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
    job_description: str = Form(...),
):
    """
    Compares resume against a job description and returns:
      - missing_keywords: important JD words not in resume
      - present_keywords: JD words already covered
      - optimization_score: % coverage
      - suggestions: specific keywords/phrases to add

    Accepts either file upload OR raw resume_text.
    job_description is always required.
    """
    if file and file.filename:
        _check_extension(file.filename)
        file_bytes = await file.read()
        resume_text = extract_and_clean(file_bytes, file.filename)

    if not resume_text.strip():
        raise HTTPException(status_code=400,
                            detail="No resume text — upload a file or send resume_text.")
    if not job_description.strip():
        raise HTTPException(status_code=400,
                            detail="job_description is required.")

    result = get_keyword_optimization(resume_text, job_description)
    return result


# ============================================================
# 3. Keyword Stuffing Detection (Recruiter-side)
# ============================================================
@router.post("/keyword-stuffing")
async def keyword_stuffing_check(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
):
    """
    RECRUITER-SIDE: detects keyword stuffing in a candidate's resume.
    Returns:
      - is_stuffed: True/False
      - confidence: 0.0 (normal) to 1.0 (heavily stuffed)
      - stuffed_keywords: the over-repeated keywords
      - reasons: human-readable explanations

    Accepts either file upload OR raw resume_text.
    """
    if file and file.filename:
        _check_extension(file.filename)
        file_bytes = await file.read()
        resume_text = extract_and_clean(file_bytes, file.filename)

    if not resume_text.strip():
        raise HTTPException(status_code=400,
                            detail="No resume text — upload a file or send resume_text.")

    result = detect_keyword_stuffing(resume_text)
    return result