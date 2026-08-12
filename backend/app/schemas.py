from pydantic import BaseModel
from typing import List, Optional

# --- User schemas ---
class UserRegister(BaseModel):
    username: str                  # username for registration
    email: str                     # email address
    password: str                  # plain password (will be hashed)

class UserLogin(BaseModel):
    email: str                     # email for login
    password: str                  # plain password to verify

class TokenResponse(BaseModel):
    access_token: str              # JWT token returned after login
    token_type: str = "bearer"     # token type always bearer

# --- Resume schemas ---
class ResumeAnalysisResponse(BaseModel):
    skills: List[str]              # extracted skills list
    education: List[str]           # extracted education
    experience: int                # years of experience
    quality_score: float           # resume quality score 0-100
    ats_score: float               # ATS match score 0-100

# --- Fraud schemas ---
class FraudCheckRequest(BaseModel):
    job_description: str           # job posting text to check
    job_title: Optional[str] = ""  # optional job title
    company_profile: Optional[str] = ""  # optional company info
    salary_range: Optional[str] = "Not Specified"  # optional salary
    company_name: Optional[str] = ""     # NEW: claimed company name, used
                                          # for logo + domain-consistency checks
    company_domain: Optional[str] = ""   # NEW: domain mentioned in posting
                                          # (e.g. "techcorp.com"), used for
                                          # domain-consistency check
    html_content: Optional[str] = ""     # NEW: raw HTML of the posting, if
                                          # available (e.g. future browser
                                          # extension) — plain-text paste
                                          # will leave this empty, which is
                                          # fine, the check is simply skipped
    logo_path: Optional[str] = ""        # NEW: server-side path to an
                                          # uploaded logo image, if the user
                                          # uploaded one alongside the posting

class FraudCheckResponse(BaseModel):
    fraud_probability: float       # probability of fraud 0-1
    is_fraud: bool                 # true if fraud probability > 0.5
    reasons: List[str]             # list of fraud reasons
    shap_explanation: List[dict] = []   # top contributing features from
                                        # the model itself (SHAP)
    advanced_signals: List[dict] = []  # NEW: results from the HTML / logo /
                                        # domain-consistency proof-of-concept
                                        # checks, when applicable inputs were
                                        # provided. Empty list if none of
                                        # html_content/logo_path/company_domain
                                        # were supplied in the request.

# --- Career schemas ---
class CareerRequest(BaseModel):
    skills: List[str]              # list of skills from resume
    target_role: str = ""          # optional target role for skill gap
    missing_skills: List[str] = [] # optional missing skills

class CareerResponse(BaseModel):
    recommendations: list          # list of recommended roles
    skill_gap: dict                # matching and missing skills
    roadmap: List[str]             # step by step learning path

# --- Interview schemas ---
class InterviewRequest(BaseModel):
    target_role: str               # target job role
    skills: List[str]              # current skills
    missing_skills: List[str]      # missing skills from gap analysis

print("Schemas loaded successfully.")