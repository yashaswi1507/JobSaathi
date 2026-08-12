from fastapi import APIRouter

router = APIRouter()

# ── Built-in salary dataset (India market, 2024-25) ──────────
SALARY_DATA = [
    # AI / ML
    {"role": "Machine Learning Engineer",  "min_lpa": 8,  "max_lpa": 30, "avg_lpa": 16, "entry_level": "6-10 LPA",  "mid_level": "12-22 LPA", "senior_level": "22-40 LPA", "demand": "Very High", "growth": "35%", "top_skills": ["Python", "TensorFlow", "PyTorch", "MLflow", "AWS"]},
    {"role": "Data Scientist",             "min_lpa": 7,  "max_lpa": 28, "avg_lpa": 14, "entry_level": "5-9 LPA",   "mid_level": "10-20 LPA", "senior_level": "20-35 LPA", "demand": "Very High", "growth": "32%", "top_skills": ["Python", "Statistics", "SQL", "Tableau", "ML"]},
    {"role": "AI Engineer",                "min_lpa": 10, "max_lpa": 40, "avg_lpa": 20, "entry_level": "8-12 LPA",  "mid_level": "15-28 LPA", "senior_level": "28-50 LPA", "demand": "Very High", "growth": "45%", "top_skills": ["Python", "LangChain", "LLM", "FastAPI", "AWS"]},
    {"role": "Generative AI Engineer",     "min_lpa": 12, "max_lpa": 45, "avg_lpa": 22, "entry_level": "8-14 LPA",  "mid_level": "16-30 LPA", "senior_level": "30-55 LPA", "demand": "Very High", "growth": "60%", "top_skills": ["Python", "LangChain", "OpenAI", "RAG", "Vector DB"]},
    {"role": "NLP Engineer",               "min_lpa": 10, "max_lpa": 35, "avg_lpa": 18, "entry_level": "7-12 LPA",  "mid_level": "14-25 LPA", "senior_level": "24-40 LPA", "demand": "High",      "growth": "38%", "top_skills": ["Python", "BERT", "HuggingFace", "SpaCy", "Transformers"]},
    {"role": "Deep Learning Engineer",     "min_lpa": 12, "max_lpa": 40, "avg_lpa": 20, "entry_level": "8-14 LPA",  "mid_level": "16-28 LPA", "senior_level": "28-50 LPA", "demand": "High",      "growth": "40%", "top_skills": ["PyTorch", "TensorFlow", "CUDA", "CNN", "Transformers"]},
    {"role": "MLOps Engineer",             "min_lpa": 10, "max_lpa": 35, "avg_lpa": 18, "entry_level": "7-12 LPA",  "mid_level": "14-25 LPA", "senior_level": "24-40 LPA", "demand": "Very High", "growth": "42%", "top_skills": ["MLflow", "Kubeflow", "Docker", "Kubernetes", "AWS"]},

    # Software Engineering
    {"role": "Software Engineer",          "min_lpa": 5,  "max_lpa": 25, "avg_lpa": 12, "entry_level": "3-6 LPA",   "mid_level": "8-18 LPA",  "senior_level": "18-35 LPA", "demand": "Very High", "growth": "22%", "top_skills": ["Python", "Java", "System Design", "AWS", "Docker"]},
    {"role": "Full Stack Developer",       "min_lpa": 5,  "max_lpa": 25, "avg_lpa": 12, "entry_level": "3-7 LPA",   "mid_level": "8-18 LPA",  "senior_level": "18-32 LPA", "demand": "Very High", "growth": "25%", "top_skills": ["React", "Node.js", "MongoDB", "AWS", "Docker"]},
    {"role": "Backend Developer",          "min_lpa": 5,  "max_lpa": 25, "avg_lpa": 12, "entry_level": "3-7 LPA",   "mid_level": "8-18 LPA",  "senior_level": "18-30 LPA", "demand": "High",      "growth": "22%", "top_skills": ["Python", "Node.js", "PostgreSQL", "Redis", "Docker"]},
    {"role": "Frontend Developer",         "min_lpa": 4,  "max_lpa": 22, "avg_lpa": 10, "entry_level": "3-6 LPA",   "mid_level": "7-15 LPA",  "senior_level": "15-28 LPA", "demand": "High",      "growth": "20%", "top_skills": ["React", "TypeScript", "CSS", "Webpack", "Figma"]},

    # Data
    {"role": "Data Analyst",               "min_lpa": 4,  "max_lpa": 18, "avg_lpa": 9,  "entry_level": "3-5 LPA",   "mid_level": "6-12 LPA",  "senior_level": "12-22 LPA", "demand": "High",      "growth": "28%", "top_skills": ["SQL", "Python", "Tableau", "Excel", "Power BI"]},
    {"role": "Data Engineer",              "min_lpa": 8,  "max_lpa": 30, "avg_lpa": 16, "entry_level": "6-10 LPA",  "mid_level": "12-22 LPA", "senior_level": "22-38 LPA", "demand": "Very High", "growth": "35%", "top_skills": ["Spark", "Kafka", "Airflow", "Python", "AWS"]},

    # DevOps / Cloud
    {"role": "DevOps Engineer",            "min_lpa": 7,  "max_lpa": 30, "avg_lpa": 15, "entry_level": "5-9 LPA",   "mid_level": "10-20 LPA", "senior_level": "20-35 LPA", "demand": "Very High", "growth": "30%", "top_skills": ["Docker", "Kubernetes", "AWS", "Terraform", "CI/CD"]},
    {"role": "Cloud Architect",            "min_lpa": 15, "max_lpa": 50, "avg_lpa": 28, "entry_level": "10-16 LPA", "mid_level": "20-35 LPA", "senior_level": "35-60 LPA", "demand": "High",      "growth": "32%", "top_skills": ["AWS", "Azure", "GCP", "Kubernetes", "Terraform"]},
    {"role": "Cybersecurity Engineer",     "min_lpa": 6,  "max_lpa": 28, "avg_lpa": 14, "entry_level": "4-8 LPA",   "mid_level": "10-20 LPA", "senior_level": "20-35 LPA", "demand": "High",      "growth": "28%", "top_skills": ["SIEM", "Penetration Testing", "Python", "Networking"]},

    # Product / Design
    {"role": "Product Manager",            "min_lpa": 10, "max_lpa": 40, "avg_lpa": 20, "entry_level": "7-12 LPA",  "mid_level": "15-28 LPA", "senior_level": "28-50 LPA", "demand": "High",      "growth": "25%", "top_skills": ["Product Roadmap", "Agile", "Analytics", "SQL", "Jira"]},
    {"role": "UX Designer",                "min_lpa": 5,  "max_lpa": 22, "avg_lpa": 11, "entry_level": "3-6 LPA",   "mid_level": "7-15 LPA",  "senior_level": "15-28 LPA", "demand": "High",      "growth": "22%", "top_skills": ["Figma", "User Research", "Prototyping", "Adobe XD"]},

    # Business
    {"role": "Business Analyst",           "min_lpa": 5,  "max_lpa": 20, "avg_lpa": 10, "entry_level": "3-6 LPA",   "mid_level": "7-14 LPA",  "senior_level": "14-25 LPA", "demand": "High",      "growth": "18%", "top_skills": ["SQL", "Excel", "Requirements", "Agile", "Tableau"]},
    {"role": "Financial Analyst",          "min_lpa": 5,  "max_lpa": 22, "avg_lpa": 11, "entry_level": "3-6 LPA",   "mid_level": "7-15 LPA",  "senior_level": "15-28 LPA", "demand": "Medium",    "growth": "15%", "top_skills": ["Excel", "Financial Modeling", "SQL", "Bloomberg"]},
    {"role": "HR Manager",                 "min_lpa": 4,  "max_lpa": 18, "avg_lpa": 9,  "entry_level": "3-5 LPA",   "mid_level": "6-12 LPA",  "senior_level": "12-22 LPA", "demand": "Medium",    "growth": "12%", "top_skills": ["Recruitment", "HR Policies", "Payroll", "Communication"]},
    {"role": "Marketing Analyst",          "min_lpa": 4,  "max_lpa": 16, "avg_lpa": 8,  "entry_level": "3-5 LPA",   "mid_level": "5-11 LPA",  "senior_level": "11-20 LPA", "demand": "Medium",    "growth": "18%", "top_skills": ["Google Analytics", "SEO", "SQL", "Excel", "Content"]},
]


def _find_role(role: str):
    """Find best matching role in dataset."""
    role_lower = role.lower().strip()
    # Exact match first
    for r in SALARY_DATA:
        if r["role"].lower() == role_lower:
            return r
    # Partial match
    for r in SALARY_DATA:
        if role_lower in r["role"].lower() or r["role"].lower() in role_lower:
            return r
    # Word overlap match
    query_words = set(role_lower.split())
    best, best_score = None, 0
    for r in SALARY_DATA:
        title_words = set(r["role"].lower().split())
        score = len(query_words & title_words)
        if score > best_score:
            best_score, best = score, r
    return best if best_score > 0 else None


# ── Routes ───────────────────────────────────────────────────
@router.get("/salary")
def get_salary(role: str = ""):
    if not role.strip():
        return {"error": "Please provide a role name"}

    match = _find_role(role)
    if not match:
        return {
            "role":    role,
            "message": "Role not found. Try: Data Scientist, ML Engineer, Software Engineer",
            "entry_level":  "3-6 LPA",
            "mid_level":    "8-15 LPA",
            "senior_level": "15-30 LPA",
            "top_skills":   [],
        }

    return {
        "role":         match["role"],
        "min_lpa":      match["min_lpa"],
        "max_lpa":      match["max_lpa"],
        "avg_lpa":      match["avg_lpa"],
        "entry_level":  match["entry_level"],
        "mid_level":    match["mid_level"],
        "senior_level": match["senior_level"],
        "demand":       match["demand"],
        "growth":       match["growth"],
        "top_skills":   match.get("top_skills", []),
    }


@router.get("/salary/all")
def get_all_salaries():
    return SALARY_DATA


@router.get("/salary/high-demand")
def get_high_demand():
    high = [r for r in SALARY_DATA if r["demand"] in ["Very High", "High"]]
    high.sort(key=lambda x: x["avg_lpa"], reverse=True)
    return {"roles": high}
