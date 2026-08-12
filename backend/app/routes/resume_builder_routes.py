from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from app.resume_builder import build_resume_pdf, get_available_templates
from app.llm_service import improve_resume_content

router = APIRouter()

class ExperienceItem(BaseModel):
    title: str
    company: str
    duration: str
    bullets: Optional[List[str]] = []

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: str
    gpa: Optional[str] = ""

class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = ""
    tech: Optional[str] = ""
    link: Optional[str] = ""
    metrics: Optional[str] = ""

class BuildResumeRequest(BaseModel):
    # Personal info
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    # Sections
    summary: Optional[str] = ""
    experience: Optional[List[ExperienceItem]] = []
    education: Optional[List[EducationItem]] = []
    skills: Optional[List[str]] = []
    projects: Optional[List[ProjectItem]] = []
    certifications: Optional[List[str]] = []
    achievements: Optional[List[str]] = []
    publications: Optional[List[str]] = []
    # Template selection
    design: Optional[str] = "modern"
    level: Optional[str] = "fresher"
    domain: Optional[str] = "software"
    # AI enhancement — True by default
    use_ai: Optional[bool] = True


@router.get("/templates")
def list_templates():
    """Returns all 156 available template combinations."""
    return get_available_templates()


@router.post("/build")
def build_resume(request: BuildResumeRequest):
    """
    Generates a professional PDF resume.

    If use_ai=True (default), Groq automatically:
      - Improves summary to be more impactful
      - Strengthens experience bullets with action verbs + metrics
      - Enhances project descriptions

    If use_ai=False, generates PDF directly from provided data.

    Returns: downloadable PDF

    design options: classic | modern | minimal | executive | creative | academic
    level options:  fresher | experienced
    domain options: software | data_science | marketing | hr | general |
                    aiml | devops | cybersecurity | finance | product |
                    design | business_analyst | sales
    """
    try:
        data = request.dict()

        # Groq AI enhancement
        if request.use_ai:
            try:
                data = improve_resume_content(
                    data,
                    domain=request.domain,
                    level=request.level
                )
            except Exception as e:
                # If Groq fails (no API key, rate limit, etc.)
                # still generate PDF with original data
                data["_ai_note"] = f"AI enhancement skipped: {str(e)}"

        pdf_bytes = build_resume_pdf(
            data,
            design=request.design,
            level=request.level,
            domain=request.domain,
        )
        filename = f"{request.name.replace(' ', '_')}_resume.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")