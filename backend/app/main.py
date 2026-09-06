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
from app.routes import auth, resume, fraud, career, salary, history, rag_routes

# Optional routes - load safely
try:
    from app.routes import reports
except: reports = None
try:
    from app.routes import resume_features_routes
except: resume_features_routes = None
try:
    from app.routes import llm_routes
except: llm_routes = None
try:
    from app.routes import resume_builder_routes
except: resume_builder_routes = None
try:
    from app.routes import recruiter_routes
except: recruiter_routes = None
try:
    from app.routes import resume_enhance_routes
except: resume_enhance_routes = None
try:
    from app.routes import voice_interview_route
except: voice_interview_route = None

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

# Core routes - safe include
def safe_include(router_module, prefix, tags):
    try:
        if router_module:
            app.include_router(router_module.router, prefix=prefix, tags=tags)
    except Exception as e:
        print(f"[routes] Skipping {prefix}: {e}")

safe_include(auth,                   "/auth",      ["Authentication"])
safe_include(resume,                 "/resume",    ["Resume"])
safe_include(fraud,                  "/fraud",     ["Fraud"])
safe_include(career,                 "/career",    ["Career"])
safe_include(salary,                 "/salary",    ["Salary"])
safe_include(history,                "/history",   ["History"])
safe_include(rag_routes,             "/rag",       ["RAG"])
safe_include(reports,                "/reports",   ["Reports"])
safe_include(resume_features_routes, "/resume",    ["Resume Features"])
safe_include(llm_routes,             "/llm",       ["LLM"])
safe_include(resume_builder_routes,  "/resume",    ["Builder"])
safe_include(recruiter_routes,       "/recruiter", ["Recruiter"])
safe_include(resume_enhance_routes,  "/resume",    ["Enhance"])
safe_include(voice_interview_route,  "/voice",     ["Voice"])

@app.get("/")
def root():
    return {"message": "CareerShield AI API is running", "version": "2.0.0"}