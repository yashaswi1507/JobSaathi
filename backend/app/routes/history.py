from fastapi import APIRouter, Header, HTTPException
from app.database import SessionLocal, ResumeHistory, JobAnalysis
from app.auth import decode_token
from datetime import datetime

router = APIRouter()

# --- Helper: get user id from JWT token ---
def get_user_id(authorization: str):
    if not authorization:                              # no token provided
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "")      # remove Bearer prefix
    user_id = decode_token(token)                      # decode JWT token
    if not user_id:                                    # invalid token
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id

# --- Save resume analysis to history ---
@router.post("/save-resume")
def save_resume(data: dict, authorization: str = Header(None)):
    user_id = get_user_id(authorization)               # get user from token
    db = SessionLocal()                                # open database

    record = ResumeHistory(
        user_id    = user_id,
        filename   = data.get("filename", "resume.pdf"),
        skills     = str(data.get("skills", [])),      # save as string
        ats_score  = data.get("ats_score", 0),
        qual_score = data.get("quality_score", 0),
        category   = data.get("category", ""),
        created    = datetime.now()
    )
    db.add(record)                                     # add to database
    db.commit()                                        # save changes
    db.close()                                         # close connection

    return {"message": "Resume analysis saved", "id": record.id}

# --- Save job fraud analysis to history ---
@router.post("/save-job")
def save_job(data: dict, authorization: str = Header(None)):
    user_id = get_user_id(authorization)
    db = SessionLocal()

    record = JobAnalysis(
        user_id       = user_id,
        job_title     = data.get("job_title", ""),
        fraud_score   = data.get("fraud_probability", 0),
        fraud_reasons = str(data.get("reasons", [])),  # save as string
        match_score   = data.get("match_score", 0),
        created       = datetime.now()
    )
    db.add(record)
    db.commit()
    db.close()

    return {"message": "Job analysis saved", "id": record.id}

# --- Get all past resume analyses for user ---
@router.get("/resumes")
def get_resume_history(authorization: str = Header(None)):
    user_id = get_user_id(authorization)
    db = SessionLocal()

    records = db.query(ResumeHistory)\
                .filter(ResumeHistory.user_id == user_id)\
                .order_by(ResumeHistory.created.desc())\
                .all()                                 # get all records newest first
    db.close()

    return [{
        "id":          r.id,
        "filename":    r.filename,
        "skills":      r.skills,
        "ats_score":   r.ats_score,
        "qual_score":  r.qual_score,
        "category":    r.category,
        "created":     str(r.created)
    } for r in records]

# --- Get all past job fraud checks for user ---
@router.get("/jobs")
def get_job_history(authorization: str = Header(None)):
    user_id = get_user_id(authorization)
    db = SessionLocal()

    records = db.query(JobAnalysis)\
                .filter(JobAnalysis.user_id == user_id)\
                .order_by(JobAnalysis.created.desc())\
                .all()
    db.close()

    return [{
        "id":            r.id,
        "job_title":     r.job_title,
        "fraud_score":   r.fraud_score,
        "fraud_reasons": r.fraud_reasons,
        "match_score":   r.match_score,
        "created":       str(r.created)
    } for r in records]

# --- Get everything for dashboard ---
@router.get("/all")
def get_all_history(authorization: str = Header(None)):
    user_id = get_user_id(authorization)
    db = SessionLocal()

    resumes = db.query(ResumeHistory)\
                .filter(ResumeHistory.user_id == user_id)\
                .order_by(ResumeHistory.created.desc())\
                .limit(5).all()                        # last 5 resume checks

    jobs = db.query(JobAnalysis)\
             .filter(JobAnalysis.user_id == user_id)\
             .order_by(JobAnalysis.created.desc())\
             .limit(5).all()                           # last 5 fraud checks
    db.close()

    return {
        "recent_resumes": [{
            "id":        r.id,
            "filename":  r.filename,
            "ats_score": r.ats_score,
            "created":   str(r.created)
        } for r in resumes],
        "recent_jobs": [{
            "id":          j.id,
            "job_title":   j.job_title,
            "fraud_score": j.fraud_score,
            "created":     str(j.created)
        } for j in jobs]
    }