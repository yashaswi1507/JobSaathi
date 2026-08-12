"""
career_recommender.py
----------------------
Career recommendation using Sentence Transformers (semantic matching).
Falls back to keyword matching if sentence-transformers not available.
"""

import re

# ── Built-in career dataset ──────────────────────────────────
CAREER_DATA = [
    # Software Engineering
    {"job_title": "Software Engineer",         "skills": "python java javascript react nodejs sql git docker aws system design"},
    {"job_title": "Senior Software Engineer",  "skills": "python java system design microservices kubernetes aws leadership code review"},
    {"job_title": "Full Stack Developer",      "skills": "react nodejs javascript html css mongodb postgresql rest api git"},
    {"job_title": "Backend Developer",         "skills": "python java go nodejs rest api postgresql mongodb redis kafka docker"},
    {"job_title": "Frontend Developer",        "skills": "react angular vuejs javascript typescript html css webpack figma"},
    {"job_title": "Mobile Developer",          "skills": "react native flutter android ios swift kotlin java firebase"},

    # AI / ML
    {"job_title": "Machine Learning Engineer", "skills": "python tensorflow pytorch scikit-learn numpy pandas feature engineering mlflow aws sagemaker"},
    {"job_title": "Data Scientist",            "skills": "python r statistics machine learning pandas numpy matplotlib seaborn sql jupyter"},
    {"job_title": "AI Engineer",               "skills": "python pytorch tensorflow langchain huggingface llm prompt engineering rag fastapi"},
    {"job_title": "Deep Learning Engineer",    "skills": "pytorch tensorflow keras cnn rnn transformer gpu cuda python computer vision nlp"},
    {"job_title": "NLP Engineer",              "skills": "python nlp bert gpt huggingface spacy nltk text classification sentiment analysis"},
    {"job_title": "Computer Vision Engineer",  "skills": "python opencv pytorch tensorflow yolo image processing cnn object detection"},
    {"job_title": "Generative AI Engineer",    "skills": "python langchain llamaindex openai anthropic huggingface prompt engineering rag vector database fastapi"},
    {"job_title": "MLOps Engineer",            "skills": "python mlflow kubeflow docker kubernetes airflow aws sagemaker terraform ci/cd"},

    # Data
    {"job_title": "Data Engineer",             "skills": "python spark kafka airflow hadoop sql postgresql mongodb aws glue databricks"},
    {"job_title": "Data Analyst",              "skills": "sql python excel tableau power bi statistics data visualization pandas numpy"},
    {"job_title": "Business Intelligence",     "skills": "sql tableau power bi excel business analysis reporting data warehouse"},

    # DevOps / Cloud
    {"job_title": "DevOps Engineer",           "skills": "docker kubernetes jenkins ci/cd terraform ansible aws azure linux bash python"},
    {"job_title": "Cloud Architect",           "skills": "aws azure gcp terraform kubernetes microservices security networking cost optimization"},
    {"job_title": "Site Reliability Engineer", "skills": "kubernetes docker prometheus grafana linux python go incident management sre"},
    {"job_title": "Cybersecurity Engineer",    "skills": "network security penetration testing siem python ethical hacking firewall incident response"},

    # Product / Design
    {"job_title": "Product Manager",           "skills": "product roadmap agile scrum analytics sql jira user research go-to-market strategy"},
    {"job_title": "UX Designer",               "skills": "figma adobe xd user research prototyping wireframing usability testing design thinking"},
    {"job_title": "UI Developer",              "skills": "html css javascript react figma responsive design animation accessibility"},

    # Business
    {"job_title": "Business Analyst",          "skills": "sql excel requirements gathering agile jira business process tableau stakeholder management"},
    {"job_title": "Financial Analyst",         "skills": "excel financial modeling sql python bloomberg valuation forecasting accounting"},
    {"job_title": "HR Manager",                "skills": "recruitment hr policies payroll performance management communication leadership"},
    {"job_title": "Marketing Analyst",         "skills": "google analytics seo sem content marketing sql excel crm social media"},
]

# ── Sentence Transformer Setup ────────────────────────────────
_st_model = None
_role_embeddings = None
_USE_ST = False

def _load_sentence_transformer():
    global _st_model, _role_embeddings, _USE_ST
    try:
        from sentence_transformers import SentenceTransformer
        print("[career_recommender] Loading sentence transformer...")
        _st_model = SentenceTransformer('all-MiniLM-L6-v2')
        role_texts = [f"{r['job_title']} {r['skills']}" for r in CAREER_DATA]
        _role_embeddings = _st_model.encode(role_texts, convert_to_tensor=True)
        _USE_ST = True
        print("[career_recommender] Sentence transformer loaded ✅")
    except Exception as e:
        print(f"[career_recommender] Sentence transformer unavailable: {e} — using keyword matching")
        _USE_ST = False

# Load on startup
_load_sentence_transformer()

# ── Semantic matching ─────────────────────────────────────────
def _semantic_recommend(resume_skills: list, top_n: int = 5):
    from sentence_transformers import util
    query = " ".join(resume_skills)
    query_embedding = _st_model.encode(query, convert_to_tensor=True)
    scores = util.cos_sim(query_embedding, _role_embeddings)[0]
    top_indices = scores.argsort(descending=True)[:top_n]

    results = []
    for idx in top_indices:
        role = CAREER_DATA[idx]
        score = float(scores[idx]) * 100
        role_skills = set(role["skills"].split())
        resume_set  = set(s.lower().strip() for s in resume_skills)
        matched     = list(resume_set & role_skills)
        missing     = list(role_skills - resume_set)[:8]
        results.append({
            "job_title":       role["job_title"],
            "match_score":     round(score, 1),
            "required_skills": role["skills"],
            "matched_skills":  matched,
            "missing_skills":  missing,
            "match_method":    "semantic",
        })
    return results

# ── Keyword matching ──────────────────────────────────────────
def _keyword_recommend(resume_skills: list, top_n: int = 5):
    resume_set = set(s.lower().strip() for s in resume_skills)
    scored = []
    for role in CAREER_DATA:
        role_skills = set(role["skills"].split())
        matched     = resume_set & role_skills
        score       = round(len(matched) / max(len(role_skills), 1) * 100, 1)
        missing     = list(role_skills - resume_set)[:8]
        scored.append({
            "job_title":       role["job_title"],
            "match_score":     score,
            "required_skills": role["skills"],
            "matched_skills":  list(matched),
            "missing_skills":  missing,
            "match_method":    "keyword",
        })
    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_n]

# ── Main recommend function ───────────────────────────────────
def recommend_careers(resume_skills: list, top_n: int = 5) -> list:
    if not resume_skills:
        return []
    if _USE_ST:
        return _semantic_recommend(resume_skills, top_n)
    return _keyword_recommend(resume_skills, top_n)

# ── Skill gap ────────────────────────────────────────────────
def find_skill_gap(resume_skills: list, target_role_skills: str, top_n: int = 8):
    resume_set  = set(s.lower().strip() for s in resume_skills)
    role_skills = set(target_role_skills.lower().split())
    matched     = list(resume_set & role_skills)
    missing     = list(role_skills - resume_set)[:top_n]
    return {
        "matching_skills": matched,
        "missing_skills":  missing,
        "match_pct":       round(len(matched) / max(len(role_skills), 1) * 100, 1),
    }
