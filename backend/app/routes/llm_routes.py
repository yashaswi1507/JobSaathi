"""
routes/llm_routes.py
---------------------
FastAPI endpoints for all LLM-based features (powered by Groq API).

Endpoints:
  POST /ai/resume/rewrite          — AI resume rewrite
  POST /ai/resume/bullets          — bullet point improvement
  POST /ai/resume/cover-letter     — cover letter generator
  POST /ai/resume/email            — professional email generator
  POST /ai/resume/linkedin-message — LinkedIn message generator
  POST /ai/linkedin/improve        — LinkedIn profile improvement
  POST /ai/career/chat             — RAG career assistant chatbot

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\routes\\llm_routes.py

REGISTER IN main.py — add these 2 lines:
  from app.routes import llm_routes
  app.include_router(llm_routes.router, prefix="/ai", tags=["AI Features"])
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.llm_service import (
    ai_rewrite_resume,
    improve_bullets,
    generate_cover_letter,
    generate_email,
    generate_linkedin_message,
    improve_linkedin_profile,
    career_chat,
    parse_raw_resume_to_json,
    improve_resume_content,
)
from app.resume_builder import build_resume_pdf

router = APIRouter()


# ============================================================
# Helpers
# ============================================================
ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

def _check_ext(filename: str):
    import os
    ext = os.path.splitext(filename.lower())[1]
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type '{ext}'")

async def _get_text(file: UploadFile, raw_text: str) -> str:
    if file and file.filename:
        _check_ext(file.filename)
        return extract_and_clean(await file.read(), file.filename)
    return raw_text


# ============================================================
# 1. AI Resume Rewrite
# ============================================================
@router.post("/resume/rewrite")
async def resume_rewrite(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
    target_role: str = Form(default=""),
):
    """
    Rewrites the resume to be more impactful using AI.
    Send either a file upload OR resume_text as form field.
    Optionally specify target_role for tailored rewriting.
    """
    text = await _get_text(file, resume_text)
    if not text.strip():
        raise HTTPException(400, "No resume text provided.")
    return ai_rewrite_resume(text, target_role)


# ============================================================
# 2. Bullet Point Improvement
# ============================================================
class BulletsRequest(BaseModel):
    bullet_points: List[str]
    role: Optional[str] = ""

@router.post("/resume/bullets")
async def resume_bullets(request: BulletsRequest):
    """
    Improves resume bullet points with stronger action verbs
    and quantified outcomes.
    Send: {"bullet_points": ["managed team", "did sales"], "role": "Product Manager"}
    """
    if not request.bullet_points:
        raise HTTPException(400, "bullet_points list is empty.")
    return improve_bullets(request.bullet_points, request.role)


# ============================================================
# 3. Cover Letter Generator
# ============================================================
@router.post("/resume/cover-letter")
async def cover_letter(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
    job_description: str = Form(...),
    company_name: str = Form(default=""),
    applicant_name: str = Form(default=""),
):
    """
    Generates a tailored cover letter from resume + job description.
    """
    text = await _get_text(file, resume_text)
    if not text.strip():
        raise HTTPException(400, "No resume text provided.")
    if not job_description.strip():
        raise HTTPException(400, "job_description is required.")
    return generate_cover_letter(text, job_description, company_name, applicant_name)


# ============================================================
# 4. Professional Email Generator
# ============================================================
@router.post("/resume/email")
async def professional_email(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
    job_description: str = Form(default=""),
    email_type: str = Form(default="application"),
    recipient_name: str = Form(default=""),
    sender_name: str = Form(default=""),
):
    """
    Generates a professional email.
    email_type: application | follow_up | networking | thank_you
    """
    text = await _get_text(file, resume_text)
    return generate_email(text, job_description, email_type,
                          recipient_name, sender_name)


# ============================================================
# 5. LinkedIn Message Generator
# ============================================================
@router.post("/resume/linkedin-message")
async def linkedin_message(
    file: UploadFile = File(None),
    resume_text: str = Form(default=""),
    recipient_role: str = Form(default=""),
    purpose: str = Form(default="networking"),
):
    """
    Generates a LinkedIn connection request or InMail FROM the candidate
    TO a recruiter/professional.
    purpose options:
      networking    — professionally connect and expand network
      job_inquiry   — ask about job opportunities
      mentorship    — seek career advice
      referral      — request a referral for a job
      follow_up     — follow up after interview or conversation
      collaboration — explore project collaboration
    """
    text = await _get_text(file, resume_text)
    return generate_linkedin_message(text, recipient_role, purpose)


# ============================================================
# 6. LinkedIn Profile Improvement
# ============================================================
class LinkedInRequest(BaseModel):
    current_headline: Optional[str] = ""
    current_about: Optional[str] = ""
    skills: Optional[List[str]] = []
    target_role: Optional[str] = ""

@router.post("/linkedin/improve")
async def linkedin_improve(request: LinkedInRequest):
    """
    Suggests improved LinkedIn headline, about section, and skills.
    Send: {
      "current_headline": "...",
      "current_about": "...",
      "skills": ["Python", "ML"],
      "target_role": "Data Scientist"
    }
    """
    return improve_linkedin_profile(
        request.current_headline,
        request.current_about,
        request.skills,
        request.target_role,
    )


# ============================================================
# 7. RAG Career Assistant (chatbot)
# ============================================================
class ChatRequest(BaseModel):
    message: str
    resume_text: Optional[str] = ""
    conversation_history: Optional[List[dict]] = []

@router.post("/career/chat")
async def career_assistant(request: ChatRequest):
    """
    Multi-turn AI career guidance chatbot.
    Send conversation history for context-aware responses.

    Request:
    {
      "message": "What roles suit my background?",
      "resume_text": "...",     // optional, for personalized advice
      "conversation_history": [ // optional, for multi-turn
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."}
      ]
    }
    Response:
    {
      "reply": "Based on your background...",
      "role": "assistant"
    }
    """
    if not request.message.strip():
        raise HTTPException(400, "message is required.")
    return career_chat(
        request.message,
        request.resume_text,
        request.conversation_history,
    )


# ============================================================
# 8. LLM Resume Builder — Raw text → Structured JSON (Option B)
# ============================================================
class RawResumeRequest(BaseModel):
    raw_text: str
    domain: Optional[str] = "software"
    level: Optional[str] = "fresher"

@router.post("/resume/parse-raw")
async def parse_raw_resume(request: RawResumeRequest):
    """
    Converts raw unstructured resume text or basic info into
    structured JSON ready for /resume/build.

    User can paste anything — paragraphs, bullet points, copy-paste
    from old resume — LLM structures it automatically.

    Send:
    {
      "raw_text": "I am Rahul, B.Tech CS from Delhi Uni 2024...",
      "domain": "software",
      "level": "fresher"
    }

    Returns structured JSON matching /resume/build request schema.
    """
    if not request.raw_text.strip():
        raise HTTPException(400, "raw_text is required.")
    return parse_raw_resume_to_json(
        request.raw_text, request.domain, request.level
    )


# ============================================================
# 9. LLM Resume Builder — Improve + Build PDF in one step (A+B)
# ============================================================
class SmartBuildRequest(BaseModel):
    # Option B: raw text input
    raw_text: Optional[str] = ""
    # Option A: already structured data (if user filled a form)
    structured_data: Optional[dict] = None
    # Template settings
    design: Optional[str] = "classic"
    level: Optional[str] = "fresher"
    domain: Optional[str] = "software"
    improve_with_llm: Optional[bool] = True

@router.post("/resume/smart-build")
async def smart_build_resume(request: SmartBuildRequest):
    """
    The most powerful resume builder endpoint — combines both options:

    Option B: If raw_text is provided, LLM first parses it into
              structured JSON automatically.
    Option A: LLM then improves the content (bullets, summary,
              project descriptions) to be more impactful.
    Finally:  PDF is generated with the chosen design/level/domain.

    Returns: downloadable PDF

    Send:
    {
      "raw_text": "I am Rahul, CS grad, interned at TechCorp...",
      "design": "modern",
      "level": "fresher",
      "domain": "software",
      "improve_with_llm": true
    }

    OR with pre-structured data:
    {
      "structured_data": {"name": "Rahul", "skills": [...], ...},
      "design": "modern",
      "level": "experienced",
      "domain": "data_science",
      "improve_with_llm": true
    }
    """
    from fastapi.responses import Response

    # Step 1: Get structured data
    if request.structured_data:
        data = request.structured_data
    elif request.raw_text.strip():
        data = parse_raw_resume_to_json(
            request.raw_text, request.domain, request.level
        )
        if "error" in data:
            raise HTTPException(500, f"Could not parse resume: {data.get('error')}")
    else:
        raise HTTPException(400, "Provide either raw_text or structured_data.")

    # Step 2: Improve content with LLM (if requested)
    if request.improve_with_llm:
        data = improve_resume_content(data, request.domain, request.level)

    # Step 3: Build PDF
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
            headers={"Content-Disposition": f"attachment; filename={name}_resume.pdf"}
        )
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {str(e)}")