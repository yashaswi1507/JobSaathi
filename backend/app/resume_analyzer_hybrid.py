"""
resume_analyzer_hybrid.py
--------------------------
Hybrid Resume Analysis:
Primary   → Groq LLM (intelligent, context-aware scoring)
Fallback  → Rule-based NLP (always works, no API needed)
"""

import os, re, json
from groq import Groq

# ── Groq client ───────────────────────────────────────────────
def _get_groq():
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        return None
    try:
        return Groq(api_key=key)
    except Exception:
        return None

# ── LLM Analysis ─────────────────────────────────────────────
def _llm_analyze(resume_text: str, job_description: str = "") -> dict:
    """Use Groq to intelligently score the resume."""
    client = _get_groq()
    if not client:
        raise Exception("Groq not available")

    jd_context = f"\nJob Description:\n{job_description[:500]}" if job_description else ""

    prompt = f"""Analyze this resume and give scores from 0-100.
Return ONLY valid JSON, no explanation.

Resume:
{resume_text[:2000]}
{jd_context}

Return this exact JSON:
{{
  "overall_score": 85,
  "content_score": 80,
  "skills_score": 90,
  "experience_score": 75,
  "education_score": 85,
  "formatting_score": 80,
  "ats_score": 82,
  "strengths": ["Strong technical skills", "Good work experience"],
  "improvements": ["Add quantifiable achievements", "Include more keywords"],
  "skills_detected": ["Python", "Machine Learning", "SQL"],
  "summary": "Well-structured resume with strong technical background."
}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a professional resume analyst. Return ONLY valid JSON."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=600,
        temperature=0.3,
    )

    raw   = response.choices[0].message.content
    clean = re.sub(r"```[a-z]*|```", "", raw).strip()
    s, e  = clean.find("{"), clean.rfind("}") + 1
    if s >= 0 and e > s:
        result = json.loads(clean[s:e])
        result["analysis_method"] = "llm"
        return result
    raise Exception("Could not parse LLM response")


# ── Rule-based Fallback ────────────────────────────────────────
SKILL_KEYWORDS = {
    "programming": ["python","java","javascript","c++","c#","golang","ruby","kotlin","swift","typescript","php","scala","rust"],
    "web":         ["react","angular","vue","nodejs","html","css","django","fastapi","flask","spring","express"],
    "data":        ["machine learning","deep learning","tensorflow","pytorch","sklearn","pandas","numpy","sql","mongodb","postgresql","mysql","spark","hadoop"],
    "devops":      ["docker","kubernetes","aws","azure","gcp","jenkins","git","ci/cd","terraform","ansible","linux"],
    "soft":        ["leadership","communication","teamwork","problem solving","analytical","management","agile","scrum"],
}

ACTION_VERBS = ["developed","built","designed","implemented","led","managed","created","improved",
                "optimized","architected","deployed","analyzed","collaborated","delivered","achieved",
                "increased","reduced","launched","automated","streamlined"]

def _rule_based_analyze(resume_text: str, job_description: str = "") -> dict:
    """Fallback rule-based analysis — always works."""
    text_lower = resume_text.lower()
    words      = text_lower.split()
    word_count = len(words)

    # ── Skills Score ─────────────────────────────────────────
    found_skills = []
    total_skill_keywords = 0
    matched = 0
    for category, skills in SKILL_KEYWORDS.items():
        for skill in skills:
            total_skill_keywords += 1
            if skill in text_lower:
                matched += 1
                found_skills.append(skill.title())
    skills_score = min(100, int((matched / max(total_skill_keywords, 1)) * 400))

    # ── Content Score ────────────────────────────────────────
    action_count = sum(1 for v in ACTION_VERBS if v in text_lower)
    has_summary  = any(w in text_lower for w in ["summary","objective","profile","about"])
    has_projects = any(w in text_lower for w in ["project","github","portfolio"])
    has_numbers  = len(re.findall(r'\d+%|\d+\+|\$\d+|\d+ years?', resume_text)) > 0
    content_score = min(100, 30 + (action_count * 5) + (has_summary*15) + (has_projects*15) + (has_numbers*20))

    # ── Experience Score ─────────────────────────────────────
    has_exp      = any(w in text_lower for w in ["experience","work history","employment","internship"])
    years_match  = re.findall(r'(\d+)\+?\s*years?', text_lower)
    years_exp    = max([int(y) for y in years_match], default=0) if years_match else 0
    exp_score    = min(100, 40 + (has_exp*20) + min(years_exp*8, 40))

    # ── Education Score ──────────────────────────────────────
    has_degree   = any(w in text_lower for w in ["b.tech","btech","b.e","mtech","m.tech","mba","bsc","msc","bachelor","master","phd","degree"])
    has_college  = any(w in text_lower for w in ["university","college","institute","iit","nit","bits"])
    has_cgpa     = bool(re.search(r'cgpa|gpa|percentage|%', text_lower))
    edu_score    = min(100, 40 + (has_degree*25) + (has_college*20) + (has_cgpa*15))

    # ── Formatting Score ─────────────────────────────────────
    has_sections = sum(1 for s in ["education","experience","skills","projects","certifications","achievements"] if s in text_lower)
    good_length  = 200 <= word_count <= 800
    has_email    = bool(re.search(r'[\w.]+@[\w.]+', resume_text))
    has_phone    = bool(re.search(r'[\+]?[\d\s\-\(\)]{10,}', resume_text))
    format_score = min(100, (has_sections * 12) + (good_length * 15) + (has_email * 10) + (has_phone * 10) + 10)

    # ── Weighted overall ─────────────────────────────────────
    overall = int(
        content_score    * 0.30 +
        skills_score     * 0.25 +
        exp_score        * 0.20 +
        edu_score        * 0.15 +
        format_score     * 0.10
    )

    # ── ATS score ────────────────────────────────────────────
    if job_description:
        jd_words  = set(job_description.lower().split())
        res_words = set(text_lower.split())
        common    = jd_words & res_words
        ats_score = min(100, int(len(common) / max(len(jd_words), 1) * 200))
    else:
        ats_score = overall

    # ── Strengths & Improvements ─────────────────────────────
    strengths, improvements = [], []
    if skills_score >= 60:  strengths.append("Strong skills section")
    if action_count >= 3:   strengths.append("Good use of action verbs")
    if has_projects:        strengths.append("Projects included")
    if has_numbers:         strengths.append("Quantified achievements")
    if has_degree:          strengths.append("Education credentials")
    if not has_numbers:     improvements.append("Add quantifiable achievements (%, numbers, $)")
    if action_count < 3:    improvements.append("Use more action verbs (Led, Built, Improved)")
    if not has_projects:    improvements.append("Add projects section with GitHub links")
    if skills_score < 40:   improvements.append("Add more relevant technical skills")
    if not has_summary:     improvements.append("Add a professional summary")

    return {
        "overall_score":    overall,
        "quality_score":    overall,
        "content_score":    content_score,
        "skills_score":     skills_score,
        "experience_score": exp_score,
        "education_score":  edu_score,
        "formatting_score": format_score,
        "ats_score":        ats_score,
        "strengths":        strengths[:4],
        "improvements":     improvements[:4],
        "skills":           found_skills[:15],
        "skills_detected":  found_skills[:15],
        "word_count":       word_count,
        "analysis_method":  "rule_based",
        "summary":          f"Resume analyzed using rule-based NLP. {len(found_skills)} skills detected.",
    }


# ── Main hybrid function ──────────────────────────────────────
def analyze_resume_hybrid(resume_text: str, job_description: str = "") -> dict:
    """
    Hybrid analysis:
    1. Try Groq LLM first (smart, context-aware)
    2. Fall back to rule-based NLP if LLM fails
    """
    if not resume_text or len(resume_text.strip()) < 50:
        return {"error": "Resume text too short or empty", "overall_score": 0}

    # Try LLM first
    try:
        print("[resume_analyzer] Trying LLM analysis...")
        result = _llm_analyze(resume_text, job_description)

        # Merge with rule-based skills detection (LLM might miss some)
        rule = _rule_based_analyze(resume_text, job_description)
        if not result.get("skills_detected"):
            result["skills_detected"] = rule["skills_detected"]
        if not result.get("skills"):
            result["skills"] = rule["skills_detected"]

        result["quality_score"] = result.get("overall_score", result.get("quality_score", 0))
        print(f"[resume_analyzer] LLM analysis done. Score: {result.get('overall_score')}")
        return result

    except Exception as e:
        print(f"[resume_analyzer] LLM failed ({e}) — using rule-based fallback")
        return _rule_based_analyze(resume_text, job_description)
