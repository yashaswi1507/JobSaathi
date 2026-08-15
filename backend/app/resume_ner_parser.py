"""
resume_ner_parser.py
--------------------
NER-based Resume Parser using spaCy
Extracts: Skills, Companies, Job Titles, Dates, Education, Location
Primary  → spaCy NER (en_core_web_sm)
Fallback → Rule-based regex extraction
"""

import re
import os
from typing import Dict, List

# ── spaCy NER Setup ───────────────────────────────────────────
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            print("[NER] spaCy model loaded ✅")
        except Exception as e:
            print(f"[NER] spaCy not available: {e} — using rule-based fallback")
            _nlp = False
    return _nlp if _nlp else None

# ── Domain-specific skill patterns ────────────────────────────
TECH_SKILLS = {
    "languages":   ["python","java","javascript","typescript","c++","c#","golang","ruby","kotlin","swift","scala","rust","php","r"],
    "web":         ["react","angular","vue","nodejs","html","css","django","fastapi","flask","spring","express","nextjs","graphql","rest api"],
    "data":        ["machine learning","deep learning","tensorflow","pytorch","sklearn","scikit-learn","pandas","numpy","matplotlib","seaborn","spark","hadoop","kafka"],
    "database":    ["sql","mysql","postgresql","mongodb","redis","elasticsearch","sqlite","oracle","cassandra"],
    "devops":      ["docker","kubernetes","aws","azure","gcp","jenkins","git","github","ci/cd","terraform","ansible","linux","bash"],
    "ai_ml":       ["nlp","computer vision","bert","gpt","llm","generative ai","rag","langchain","transformers","huggingface","opencv"],
    "tools":       ["jira","confluence","slack","figma","postman","tableau","power bi","excel","jupyter"],
}

ALL_SKILLS = [s for skills in TECH_SKILLS.values() for s in skills]

DEGREE_PATTERNS = [
    r'b\.?tech', r'b\.?e\.?', r'm\.?tech', r'mba', r'b\.?sc', r'm\.?sc',
    r'ph\.?d', r'bachelor', r'master', r'doctorate', r'b\.?com', r'm\.?com',
    r'b\.?ca', r'm\.?ca', r'diploma'
]

JOB_TITLES = [
    "software engineer", "senior engineer", "junior engineer", "lead engineer",
    "data scientist", "ml engineer", "ai engineer", "devops engineer",
    "full stack developer", "backend developer", "frontend developer",
    "product manager", "project manager", "tech lead", "team lead",
    "data analyst", "business analyst", "cloud architect", "solution architect",
    "intern", "trainee", "associate", "consultant", "director", "vp", "cto", "ceo",
]

# ── NER Extraction ─────────────────────────────────────────────
def _extract_with_spacy(text: str) -> Dict:
    nlp = _get_nlp()
    if not nlp:
        return {}

    doc = nlp(text[:5000])  # Limit for performance

    entities = {
        "companies":  [],
        "locations":  [],
        "dates":      [],
        "persons":    [],
    }

    for ent in doc.ents:
        if ent.label_ == "ORG":
            company = ent.text.strip()
            if len(company) > 2 and company not in entities["companies"]:
                entities["companies"].append(company)
        elif ent.label_ in ["GPE", "LOC"]:
            loc = ent.text.strip()
            if loc not in entities["locations"]:
                entities["locations"].append(loc)
        elif ent.label_ == "DATE":
            date = ent.text.strip()
            if date not in entities["dates"]:
                entities["dates"].append(date)
        elif ent.label_ == "PERSON":
            person = ent.text.strip()
            if person not in entities["persons"]:
                entities["persons"].append(person)

    return entities


# ── Rule-based Extraction ──────────────────────────────────────
def _extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found.append(skill.title())
    # Deduplicate
    return list(dict.fromkeys(found))


def _extract_skills_by_category(text: str) -> Dict:
    text_lower = text.lower()
    result = {}
    for category, skills in TECH_SKILLS.items():
        matched = [s.title() for s in skills
                   if re.search(r'\b' + re.escape(s) + r'\b', text_lower)]
        if matched:
            result[category] = matched
    return result


def _extract_education(text: str) -> List[Dict]:
    text_lower = text.lower()
    education  = []

    degree_pattern = '|'.join(DEGREE_PATTERNS)
    matches = re.finditer(
        rf'({degree_pattern})[^.\n]{{0,80}}',
        text_lower, re.IGNORECASE
    )

    for m in matches:
        edu_text = text[m.start():m.start()+120].strip()
        year_match = re.search(r'\b(19|20)\d{{2}}\b', edu_text)
        education.append({
            "degree":       edu_text.split('\n')[0][:60],
            "year":         year_match.group() if year_match else None,
        })

    return education[:3]


def _extract_experience(text: str) -> Dict:
    text_lower = text.lower()

    # Total years claimed
    exp_matches = re.findall(r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)', text_lower)
    claimed_years = max([int(x) for x in exp_matches], default=0) if exp_matches else 0

    # Job titles
    found_titles = []
    for title in JOB_TITLES:
        if title in text_lower:
            found_titles.append(title.title())

    # Date ranges for timeline
    date_ranges = re.findall(
        r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*\d{4})\s*[-–—to]+\s*((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)?\.?\s*\d{4}|present|current)',
        text_lower
    )

    return {
        "claimed_years": claimed_years,
        "job_titles":    list(dict.fromkeys(found_titles))[:5],
        "date_ranges":   [f"{s} → {e}" for s, e in date_ranges[:4]],
    }


def _extract_contact(text: str) -> Dict:
    email   = re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
    phone   = re.findall(r'[\+]?[\d\s\-\(\)]{10,15}', text)
    linkedin = re.findall(r'linkedin\.com/in/[\w\-]+', text, re.IGNORECASE)
    github   = re.findall(r'github\.com/[\w\-]+', text, re.IGNORECASE)

    return {
        "email":    email[0]    if email    else None,
        "phone":    phone[0].strip() if phone else None,
        "linkedin": linkedin[0] if linkedin else None,
        "github":   github[0]   if github   else None,
    }


# ── Main Parse Function ────────────────────────────────────────
def parse_resume_ner(resume_text: str) -> Dict:
    """
    Full resume parsing using NER + rule-based extraction.
    Returns structured data with all extracted entities.
    """
    if not resume_text or len(resume_text.strip()) < 20:
        return {"error": "Resume text too short"}

    # spaCy NER entities
    spacy_entities = _extract_with_spacy(resume_text)

    # Rule-based extraction
    skills_all        = _extract_skills(resume_text)
    skills_categorized = _extract_skills_by_category(resume_text)
    education         = _extract_education(resume_text)
    experience        = _extract_experience(resume_text)
    contact           = _extract_contact(resume_text)

    # Candidate name — first PERSON from NER or first line
    name = None
    if spacy_entities.get("persons"):
        name = spacy_entities["persons"][0]
    else:
        first_line = resume_text.strip().split('\n')[0].strip()
        if 2 < len(first_line) < 50 and '@' not in first_line:
            name = first_line

    return {
        "name":                 name,
        "contact":              contact,
        "skills":               skills_all[:20],
        "skills_by_category":   skills_categorized,
        "companies":            spacy_entities.get("companies", [])[:8],
        "locations":            spacy_entities.get("locations", [])[:5],
        "dates":                spacy_entities.get("dates", [])[:8],
        "education":            education,
        "experience":           experience,
        "total_skills_found":   len(skills_all),
        "ner_method":           "spaCy en_core_web_sm" if _get_nlp() else "rule_based",
        "parse_success":        True,
    }


if __name__ == "__main__":
    sample = """
Yashaswi Jain
yashaswijain@gmail.com | +91-9027708159 | LinkedIn: linkedin.com/in/yashaswi | GitHub: github.com/yashaswi

EXPERIENCE
ML Engineer — Google (2022 - 2024)
• Built ML pipelines using Python, TensorFlow, PyTorch
• Reduced inference time by 40% using model optimization

Software Developer — Infosys (2020 - 2022)
• Developed REST APIs using FastAPI and PostgreSQL

EDUCATION
B.Tech Computer Science — IIT Delhi (2020) | CGPA: 8.9

SKILLS
Python | Java | React | Machine Learning | Deep Learning | Docker | AWS | SQL
"""
    result = parse_resume_ner(sample)
    import json
    print(json.dumps(result, indent=2))
