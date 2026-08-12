"""
routes/recruiter_routes.py
---------------------------
Recruiter-side endpoints for resume fraud detection.

Endpoints:
  POST /recruiter/fake-experience  — date overlap + duration check
  POST /recruiter/ai-generated     — AI-generated resume detection
  POST /recruiter/fake-companies   — company domain/email consistency

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\routes\\recruiter_routes.py

REGISTER IN main.py:
  from app.routes import recruiter_routes
  app.include_router(recruiter_routes.router,
                     prefix="/recruiter", tags=["Recruiter Tools"])
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.recruiter_checks import (
    detect_fake_experience,
    detect_ai_generated,
    detect_fake_companies,
)
from app.ocr_extractor import extract_and_clean

router = APIRouter()


# ============================================================
# Schemas
# ============================================================
class ExperienceEntry(BaseModel):
    title: Optional[str] = ""
    company: Optional[str] = ""
    start: str                    # e.g. "Jan 2020"
    end: Optional[str] = "present"
    company_domain: Optional[str] = ""
    company_email: Optional[str] = ""

class FakeExperienceRequest(BaseModel):
    experience: List[ExperienceEntry]

class FakeCompanyRequest(BaseModel):
    experience: List[ExperienceEntry]


# ============================================================
# 1. Fake Experience Detection
# ============================================================
@router.post("/fake-experience")
async def fake_experience_check(request: FakeExperienceRequest):
    """
    Analyzes work experience dates for suspicious patterns:
    overlapping roles, future dates, unrealistic durations.

    Send:
    {
      "experience": [
        {"title": "SDE", "company": "TechCorp",
         "start": "Jan 2020", "end": "Dec 2022"},
        {"title": "Manager", "company": "InfoSys",
         "start": "Mar 2020", "end": "Jun 2021"}
      ]
    }
    """
    exp_list = [e.dict() for e in request.experience]
    return detect_fake_experience(exp_list)


# ============================================================
# 2. AI-Generated Resume Detection
# ============================================================
@router.post("/ai-generated")
async def ai_generated_check(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
):
    """
    Detects if a resume was likely AI-generated using statistical
    heuristics (phrase overuse, sentence uniformity, lexical diversity).

    Accepts file upload (PDF/image) OR raw resume_text.
    Returns: likely_ai_generated (bool), confidence (0-1), signals[]
    """
    if file and file.filename:
        import os
        ext = os.path.splitext(file.filename.lower())[1]
        if ext not in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
            raise HTTPException(400, f"Unsupported file type '{ext}'")
        file_bytes = await file.read()
        resume_text = extract_and_clean(file_bytes, file.filename)

    if not resume_text.strip():
        raise HTTPException(400, "No resume text provided.")

    return detect_ai_generated(resume_text)


# ============================================================
# 3. Fake Company Detection
# ============================================================
@router.post("/fake-companies")
async def fake_company_check(request: FakeCompanyRequest):
    """
    Checks company name vs domain/email consistency in experience.
    Flags mismatches like claiming 'Infosys' but listing 'xyz.com'.

    Send experience list with optional company_domain/company_email:
    {
      "experience": [
        {"company": "Infosys", "company_domain": "infosys.com",
         "start": "Jan 2020", "end": "Dec 2022"},
        {"company": "TCS", "company_email": "hr@tcs.com",
         "start": "Jan 2023", "end": "present"}
      ]
    }
    """
    exp_list = [e.dict() for e in request.experience]
    return detect_fake_companies(exp_list)