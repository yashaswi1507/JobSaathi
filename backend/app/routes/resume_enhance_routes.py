"""
routes/resume_enhance_routes.py
---------------------------------
Two new endpoints for the smart resume enhancement flow:

  POST /resume/analyze-and-suggest
    → Upload resume → get domain/level detection + template suggestion

  POST /resume/enhance-and-build
    → Accept suggestion → Groq improves content → PDF generated

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\routes\\resume_enhance_routes.py

REGISTER IN main.py:
  from app.routes import resume_enhance_routes
  app.include_router(resume_enhance_routes.router,
                     prefix="/resume", tags=["Resume Enhancement"])
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import spacy
import os

import re as _re

def _extract_email_simple(text):
    m = _re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return m.group() if m else ""

def _extract_phone_simple(text):
    m = _re.search(r'(\+91[\s-]?)?[6-9]\d{9}|\+\d{1,3}[\s-]\d{10}', text)
    return m.group().strip() if m else ""

def _extract_linkedin_simple(text):
    m = _re.search(r'linkedin\.com/in/[\w-]+', text, _re.IGNORECASE)
    return m.group() if m else ""

def _extract_github_simple(text):
    m = _re.search(r'github\.com/[\w-]+', text, _re.IGNORECASE)
    return m.group() if m else ""

def _extract_name_simple(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        if (len(line.split()) <= 4 and
            not _re.search(r'@|linkedin|github|\d{10}|http', line.lower()) and
            not any(kw in line.lower() for kw in ['resume','cv','skills','objective'])):
            return line
    return ""


router = APIRouter()


# ============================================================
# STEP 1: Analyze & Suggest
# ============================================================
@router.post("/analyze-and-suggest")
async def analyze_and_suggest(file: UploadFile = File(...)):
    """
    STEP 1 of the smart enhancement flow.

    Upload a resume (PDF or image) → system automatically:
      1. Extracts text using OCR if needed
      2. Detects domain (software/aiml/marketing etc.)
      3. Detects career level (fresher/junior/mid/senior/lead)
      4. Calculates current ATS score
      5. Suggests best matching CareerShield template
      6. Extracts structured data ready for rebuilding

    Response includes:
      - detected_domain, detected_level (with confidence)
      - current_ats_score → estimated_ats_after (after rebuild)
      - suggested_template: {design, level, domain, template_id}
      - improvements_needed: list of specific suggestions
      - extracted_data: structured resume data for rebuild step

    Frontend: show this to user as a summary card with a
    "Proceed / Build Enhanced Resume" button.
    """
    ext = os.path.splitext(file.filename.lower())[1]
    allowed = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type '{ext}'")

    file_bytes = await file.read()

    # Extract text
    try:
        from app.ocr_extractor import extract_and_clean
        text = extract_and_clean(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(500, f"Text extraction failed: {str(e)}")

    if not text.strip():
        raise HTTPException(400, "Could not extract text from this file.")

    # Extract skills using existing parser (most reliable part)
    try:
        from app.resume_parser import extract_skills_with_confidence
        skills_raw = extract_skills_with_confidence(text)
        skills = [s["skill"] for s in skills_raw if s["confidence"] > 0.4]
    except Exception:
        skills = []

    # Analyze and suggest
    from app.resume_analyzer import analyze_resume_and_suggest
    result = analyze_resume_and_suggest(text, skills)

    # Store raw text for Step 2 (LLM will do proper extraction)
    # We do NOT use regex-based extract_structured_data() anymore
    # because it fails on WeasyPrint PDFs and complex layouts.
    # Instead Step 2 uses LLM (parse_raw_resume_to_json) which is
    # much more reliable for any PDF format.
    result["resume_text"] = text
    result["extracted_data"] = {
        "name":           _extract_name_simple(text),
        "email":          _extract_email_simple(text),
        "phone":          _extract_phone_simple(text),
        "location":       "",
        "linkedin":       _extract_linkedin_simple(text),
        "github":         _extract_github_simple(text),
        "summary":        "",
        "experience":     [],
        "education":      [],
        "skills":         skills,
        "projects":       [],
        "certifications": [],
        "achievements":   [],
        "publications":   [],
    }
    result["note"] = (
        "In Step 2, set use_llm_parse=true for best results — "
        "Groq will properly extract all sections from your resume text."
    )

    return result


# ============================================================
# STEP 2: Enhance & Build
# ============================================================
class EnhanceRequest(BaseModel):
    # Extracted data from step 1 (can be modified by user)
    extracted_data: dict
    resume_text: Optional[str] = ""

    # Template choices (from suggestion, user can override)
    design: Optional[str] = "modern"
    level: Optional[str] = "fresher"
    domain: Optional[str] = "software"

    # Options
    use_ai: Optional[bool] = True
    use_llm_parse: Optional[bool] = True  # Always True by default now


@router.post("/enhance-and-build")
async def enhance_and_build(request: EnhanceRequest):
    """
    STEP 2 of the smart enhancement flow.

    Takes the extracted data from /analyze-and-suggest
    (possibly modified by the user) and:
      1. Optionally re-parses with LLM for better structure
      2. Groq improves summary, bullets, project descriptions
      3. Generates professional PDF with chosen template

    Returns: downloadable PDF

    Send:
    {
      "extracted_data": { ...from step 1 response... },
      "resume_text": "...",   // from step 1 (needed for LLM re-parse)
      "design": "modern",
      "level": "fresher",
      "domain": "aiml",
      "use_ai": true,
      "use_llm_parse": false  // true = use Groq to re-extract structure
    }
    """
    from app.resume_builder import build_resume_pdf
    from app.llm_service import improve_resume_content, parse_raw_resume_to_json
    import copy

    data = copy.deepcopy(request.extracted_data)

    # If extraction was minimal (only contact info), force LLM parse
    has_minimal_data = (
        not data.get("experience") and
        not data.get("skills") and
        not data.get("education")
    )

    # Use LLM to parse full structure from resume text
    if (request.use_llm_parse or has_minimal_data) and request.resume_text:
        try:
            parsed = parse_raw_resume_to_json(
                request.resume_text,
                domain=request.domain,
                level=request.level
            )
            if "error" not in parsed:
                # LLM parsed data is more complete — use it
                # But keep contact info from regex (more reliable)
                contact_fields = ["name", "email", "phone", "location",
                                  "linkedin", "github"]
                for key in contact_fields:
                    if data.get(key):  # keep regex-extracted contact
                        parsed[key] = data[key]
                data = parsed
        except Exception:
            pass

    # Groq content improvement
    if request.use_ai:
        try:
            data = improve_resume_content(
                data,
                domain=request.domain,
                level=request.level
            )
        except Exception:
            pass  # fail gracefully, use original data

    # Build PDF
    try:
        pdf_bytes = build_resume_pdf(
            data,
            design=request.design,
            level=request.level,
            domain=request.domain,
        )
        name = data.get("name", "resume").replace(" ", "_")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={name}_enhanced.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {str(e)}")