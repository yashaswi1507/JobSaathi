from fastapi import FastAPI
import subprocess, sys

# Download spaCy model on startup if not present
try:
    import spacy
    spacy.load("en_core_web_sm")
except OSError:
    print("[startup] Downloading spaCy model...")
    subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=False)
except Exception:
    pass
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, resume, fraud, career, reports, salary, history, rag_routes
from app.routes import resume_features_routes, llm_routes
from app.routes import resume_builder_routes, recruiter_routes
from app.routes import resume_enhance_routes
from app.routes import voice_interview_route

app = FastAPI(
    title="CareerShield AI",
    description="Job Fraud Detection & Career Guidance Platform",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Health check endpoints
@app.get("/")
def root():
    return {"status": "JobSaathi AI is running!", "version": "2.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    try:
        from app.database import init_db
        init_db()
    except Exception as e:
        print(f"[startup] DB init warning: {e}")

# Core routes
app.include_router(auth.router,                   prefix="/auth",      tags=["Authentication"])
app.include_router(resume.router,                 prefix="/resume",    tags=["Resume"])
app.include_router(fraud.router,                  prefix="/fraud",     tags=["Fraud Detection"])
app.include_router(career.router,                 prefix="/career",    tags=["Career"])
app.include_router(reports.router,                prefix="/reports",   tags=["Reports"])
app.include_router(salary.router, prefix="/salary", tags=["Salary"])
app.include_router(history.router, prefix="/history", tags=["History"])
app.include_router(rag_routes.router, prefix="/rag", tags=["RAG"])
# New routes
app.include_router(resume_features_routes.router, prefix="/resume",    tags=["Resume Features"])
app.include_router(resume_builder_routes.router,  prefix="/resume",    tags=["Resume Builder"])
app.include_router(llm_routes.router,             prefix="/ai",        tags=["AI Features"])
app.include_router(recruiter_routes.router,       prefix="/recruiter", tags=["Recruiter Tools"])
app.include_router(resume_enhance_routes.router,  prefix="/resume",    tags=["Resume Enhancement"])
app.include_router(voice_interview_route.router,    prefix="/interview", tags=["Voice Interview"])

@app.get("/")
def root():
    return {"message": "CareerShield AI API is running", "version": "2.0.0"}