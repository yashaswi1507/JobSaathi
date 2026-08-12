"""
resume_analyzer.py
-------------------
Analyzes an uploaded resume and suggests the best matching
CareerShield template to maximize ATS score.

Flow:
  1. Extract text from uploaded file (PDF/image)
  2. Detect domain (software/aiml/marketing etc.)
  3. Detect level (fresher/junior/mid/senior/lead)
  4. Calculate current ATS score
  5. Suggest best design + level + domain combination
  6. Extract structured data for rebuilding

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\resume_analyzer.py
"""

import re
from collections import Counter


# ============================================================
# DOMAIN DETECTION KEYWORDS
# ============================================================
DOMAIN_KEYWORDS = {
    "aiml": {
        "tensorflow", "pytorch", "keras", "bert", "gpt", "transformer",
        "deep learning", "neural network", "nlp", "computer vision",
        "machine learning", "mlflow", "huggingface", "langchain",
        "llm", "diffusion", "gan", "reinforcement learning", "mlops",
        "feature engineering", "model training", "fine-tuning", "rag",
    },
    "data_science": {
        "data science", "data analyst", "tableau", "power bi", "matplotlib",
        "seaborn", "pandas", "numpy", "scipy", "statistics", "regression",
        "classification", "clustering", "eda", "data visualization",
        "business intelligence", "sql", "excel", "r programming",
        "hypothesis testing", "a/b testing",
    },
    "devops": {
        "devops", "kubernetes", "docker", "jenkins", "ci/cd", "terraform",
        "ansible", "aws", "gcp", "azure", "cloudformation", "helm",
        "prometheus", "grafana", "linux", "bash", "infrastructure",
        "site reliability", "sre", "microservices", "containerization",
    },
    "cybersecurity": {
        "cybersecurity", "penetration testing", "ethical hacking", "soc",
        "siem", "vulnerability", "malware", "firewall", "owasp", "ctf",
        "burp suite", "metasploit", "nmap", "wireshark", "kali",
        "threat intelligence", "incident response", "iso 27001",
    },
    "software": {
        "software engineer", "backend", "frontend", "fullstack", "api",
        "rest api", "graphql", "microservices", "java", "spring boot",
        "node.js", "react", "angular", "vue", "django", "flask",
        "fastapi", "postgresql", "mongodb", "redis", "git", "agile",
    },
    "marketing": {
        "marketing", "seo", "sem", "google ads", "facebook ads",
        "content marketing", "social media", "campaign", "brand",
        "digital marketing", "email marketing", "crm", "hubspot",
        "google analytics", "conversion", "roi", "lead generation",
    },
    "hr": {
        "human resources", "hr", "recruitment", "talent acquisition",
        "onboarding", "payroll", "performance management", "hris",
        "employee relations", "training", "compensation", "benefits",
        "workforce planning", "succession planning", "hrms",
    },
    "finance": {
        "finance", "accounting", "financial modeling", "valuation",
        "dcf", "equity research", "investment banking", "risk management",
        "bloomberg", "chartered accountant", "cfa", "financial analysis",
        "budgeting", "forecasting", "ifrs", "gaap", "audit", "tax",
    },
    "product": {
        "product manager", "product management", "roadmap", "user story",
        "agile", "scrum", "okr", "kpi", "product analytics", "jira",
        "figma", "wireframe", "go-to-market", "stakeholder", "backlog",
        "sprint", "product owner", "ux research", "product strategy",
    },
    "design": {
        "ui design", "ux design", "figma", "sketch", "adobe xd",
        "user research", "wireframe", "prototype", "usability testing",
        "design system", "interaction design", "visual design",
        "typography", "color theory", "design thinking", "invision",
    },
    "business_analyst": {
        "business analyst", "requirements gathering", "gap analysis",
        "process mapping", "bpmn", "use case", "brd", "frd",
        "stakeholder management", "visio", "lucidchart", "feasibility",
        "business process", "workflow", "documentation",
    },
    "sales": {
        "sales", "business development", "account management",
        "lead generation", "cold calling", "negotiation", "crm",
        "salesforce", "pipeline", "quota", "b2b", "b2c", "revenue",
        "client relationship", "deal closing", "territory management",
    },
}

# ============================================================
# LEVEL DETECTION
# ============================================================
LEVEL_INDICATORS = {
    "lead": {
        "keywords": {"vp", "vice president", "director", "head of", "principal",
                     "chief", "staff engineer", "distinguished", "lead engineer",
                     "engineering manager", "head of engineering"},
        "min_years": 8,
    },
    "senior": {
        "keywords": {"senior", "sr.", "sr ", "tech lead", "team lead",
                     "architect", "manager", "lead engineer"},
        "min_years": 5,
    },
    "mid": {
        "keywords": {"mid", "mid-level", "sde ii", "sde 2", "engineer ii",
                     "associate", "specialist"},
        "min_years": 2,
    },
    "junior": {
        "keywords": {"junior", "jr.", "jr ", "sde i", "sde 1", "engineer i",
                     "graduate engineer", "entry level"},
        "min_years": 0,
    },
    "fresher": {
        "keywords": {"fresher", "intern", "trainee", "student", "graduate",
                     "seeking", "looking for", "entry"},
        "min_years": 0,
    },
}

# How many years of experience each level roughly implies
LEVEL_YEAR_MAP = [
    (8, "lead"),
    (5, "senior"),
    (2, "mid"),
    (0.5, "junior"),
    (0, "fresher"),
]

# Best design per domain (aesthetic recommendation)
DOMAIN_DESIGN_MAP = {
    "aiml":            "modern",
    "data_science":    "modern",
    "software":        "minimal",
    "devops":          "minimal",
    "cybersecurity":   "classic",
    "marketing":       "creative",
    "hr":              "classic",
    "finance":         "executive",
    "product":         "modern",
    "design":          "creative",
    "business_analyst":"minimal",
    "sales":           "executive",
    "general":         "classic",
}

# ATS-unfriendly patterns
ATS_PENALTY_PATTERNS = [
    (r'\btable\b',              5,  "Tables reduce ATS readability"),
    (r'[^\x00-\x7F]',          3,  "Special/unicode characters may confuse ATS"),
    (r'\.jpg|\.png|\.jpeg',    10, "Images/graphics not ATS readable"),
    (r'header|footer',         5,  "Headers/footers sometimes skipped by ATS"),
]

# ATS-positive signals
ATS_POSITIVE_SIGNALS = [
    (r'\b(experience|work experience|employment)\b', 10, "Has experience section"),
    (r'\b(education|academic)\b',                    8,  "Has education section"),
    (r'\b(skills|technical skills)\b',               10, "Has skills section"),
    (r'\b(projects?)\b',                             7,  "Has projects section"),
    (r'\b(certifications?|certified)\b',             5,  "Has certifications"),
    (r'\d{4}\s*[-–]\s*(\d{4}|present|current)',      8,  "Has date ranges"),
    (r'\b\d+[%x]\b|\d+\+',                          7,  "Has quantified achievements"),
    (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 5, "Has email"),
    (r'\b\d{10}\b|\+\d{1,3}[\s-]\d{10}',           5,  "Has phone number"),
]


# ============================================================
# DOMAIN DETECTION
# ============================================================
def detect_domain(text: str) -> tuple[str, float, dict]:
    """
    Detects the most likely domain from resume text.
    Returns (domain, confidence, scores_dict).
    """
    text_lower = text.lower()
    scores = {}

    for domain, keywords in DOMAIN_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        scores[domain] = matches

    if not any(scores.values()):
        return "general", 0.0, scores

    sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_domain, best_score = sorted_domains[0]
    second_score = sorted_domains[1][1] if len(sorted_domains) > 1 else 0

    total = sum(scores.values())
    confidence = round(best_score / total, 2) if total > 0 else 0.0

    return best_domain, confidence, scores


# ============================================================
# LEVEL DETECTION
# ============================================================
def detect_level(text: str) -> tuple[str, str]:
    """
    Detects career level from resume text.
    Returns (level, reason).
    """
    text_lower = text.lower()

    # Check explicit level keywords
    for level in ["lead", "senior", "mid", "junior", "fresher"]:
        indicators = LEVEL_INDICATORS[level]
        for kw in indicators["keywords"]:
            if kw in text_lower:
                return level, f"Found keyword: '{kw}'"

    # Estimate from experience years mentioned
    year_mentions = re.findall(r'(\d+)\+?\s*years?\s*(?:of\s*)?experience', text_lower)
    if year_mentions:
        max_years = max(int(y) for y in year_mentions)
        for threshold, level in LEVEL_YEAR_MAP:
            if max_years >= threshold:
                return level, f"{max_years} years of experience mentioned"

    # Check for internship/student signals → fresher
    if any(kw in text_lower for kw in ["intern", "b.tech", "b.e.", "pursuing", "final year"]):
        return "fresher", "Student/intern signals detected"

    return "mid", "No clear level signals — defaulting to mid"


# ============================================================
# ATS SCORE CALCULATION
# ============================================================
def calculate_ats_score(text: str, skills: list) -> dict:
    """
    Calculates current ATS score and identifies improvement areas.
    Returns score (0-100) and breakdown.
    """
    text_lower = text.lower()
    score = 30  # base score
    breakdown = []
    penalties = []

    # Positive signals
    for pattern, points, reason in ATS_POSITIVE_SIGNALS:
        if re.search(pattern, text_lower):
            score += points
            breakdown.append(f"+{points}: {reason}")

    # Skills count bonus
    skill_count = len(skills)
    if skill_count >= 10:
        score += 10
        breakdown.append(f"+10: Strong skills section ({skill_count} skills)")
    elif skill_count >= 5:
        score += 5
        breakdown.append(f"+5: Good skills section ({skill_count} skills)")

    # Penalty signals
    for pattern, penalty, reason in ATS_PENALTY_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            score -= penalty
            penalties.append(f"-{penalty}: {reason}")

    # Length check
    word_count = len(text.split())
    if word_count < 200:
        score -= 10
        penalties.append("-10: Resume too short (less than 200 words)")
    elif word_count > 800:
        score -= 5
        penalties.append("-5: Resume may be too long for ATS parsing")

    score = max(0, min(100, score))
    return {
        "current_ats_score": score,
        "breakdown": breakdown,
        "penalties": penalties,
        "word_count": word_count,
        "skill_count": skill_count,
    }


# ============================================================
# STRUCTURED DATA EXTRACTION (for rebuilding)
# ============================================================
def extract_structured_data(text: str) -> dict:
    """
    Extracts structured data from resume text for rebuilding.
    Conservative approach — only extracts what it's confident about.
    LLM improvement in enhance-and-build will fill gaps.
    """
    data = {
        "name": "", "email": "", "phone": "",
        "location": "", "linkedin": "", "github": "",
        "summary": "", "experience": [], "education": [],
        "skills": [], "projects": [], "certifications": [],
        "achievements": [], "publications": [],
    }

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Email — reliable regex
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        data["email"] = email_match.group()

    # Phone — Indian/international format
    phone_match = re.search(r'(\+91[\s-]?)?[6-9]\d{9}|\+\d{1,3}[\s-]?\d{10}', text)
    if phone_match:
        data["phone"] = phone_match.group().strip()

    # LinkedIn — reliable
    linkedin_match = re.search(r'linkedin\.com/in/[\w-]+', text, re.IGNORECASE)
    if linkedin_match:
        data["linkedin"] = linkedin_match.group()

    # GitHub — reliable
    github_match = re.search(r'github\.com/[\w-]+', text, re.IGNORECASE)
    if github_match:
        data["github"] = github_match.group()

    # Name — first short line that is NOT contact info
    for line in lines[:8]:
        clean = line.strip()
        if (1 <= len(clean.split()) <= 5 and
            not re.search(r'@|linkedin|github|\d{7,}|http|www\.', clean.lower()) and
            not any(kw in clean.lower() for kw in
                    ['resume', 'cv', 'curriculum', 'engineer', 'developer',
                     'manager', 'analyst', 'designer', 'objective', 'summary'])):
            data["name"] = clean
            break

    # DO NOT attempt to extract skills, education, experience via regex
    # — too error-prone (causes "bernetes" type corruption).
    # Instead, return minimal data and let LLM fill the rest
    # via use_llm_parse=True in enhance-and-build.
    data["_extraction_note"] = (
        "Basic extraction only (name, email, phone, linkedin, github). "
        "Set use_llm_parse=true in enhance-and-build for complete extraction."
    )

    return data


# ============================================================
# MAIN ANALYSIS FUNCTION
# ============================================================
def analyze_resume_and_suggest(text: str, extracted_skills: list) -> dict:
    """
    Main function: takes resume text + extracted skills,
    returns domain, level, ATS score, and template suggestion.
    """
    domain, domain_confidence, domain_scores = detect_domain(text)
    level, level_reason = detect_level(text)
    ats_data = calculate_ats_score(text, extracted_skills)
    structured_data = extract_structured_data(text)

    # Use parser skills if available, else analyzer's
    if extracted_skills:
        structured_data["skills"] = extracted_skills

    # Best template suggestion
    suggested_design = DOMAIN_DESIGN_MAP.get(domain, "modern")

    # Estimate improved ATS score after rebuild
    estimated_improvement = min(95, ats_data["current_ats_score"] + 20)

    # Top missing sections
    missing = []
    text_lower = text.lower()
    if "summary" not in text_lower and "objective" not in text_lower:
        missing.append("Add a Professional Summary/Objective section")
    if "certif" not in text_lower:
        missing.append("Add Certifications section")
    if not re.search(r'\d+[%x]|\d+\+', text_lower):
        missing.append("Quantify your achievements (add numbers/percentages)")
    if len(extracted_skills) < 8:
        missing.append("Expand your Skills section (aim for 8+ relevant skills)")

    return {
        # Detection results
        "detected_domain":      domain,
        "domain_confidence":    domain_confidence,
        "domain_label":         _domain_label(domain),
        "detected_level":       level,
        "level_label":          _level_label(level),
        "level_reason":         level_reason,

        # ATS analysis
        "current_ats_score":    ats_data["current_ats_score"],
        "estimated_ats_after":  estimated_improvement,
        "ats_breakdown":        ats_data["breakdown"],
        "ats_penalties":        ats_data["penalties"],
        "improvements_needed":  missing,

        # Template suggestion
        "suggested_template": {
            "design":       suggested_design,
            "level":        level,
            "domain":       domain,
            "template_id":  f"{suggested_design}_{level}_{domain}",
        },

        # Extracted data (for rebuilding)
        "extracted_data": structured_data,

        # Meta
        "word_count":     ats_data["word_count"],
        "skills_found":   extracted_skills[:15],
    }


def _domain_label(domain: str) -> str:
    labels = {
        "software":"Software Engineering", "data_science":"Data Science",
        "aiml":"AI/ML Engineering", "devops":"DevOps/Cloud",
        "cybersecurity":"Cybersecurity", "marketing":"Marketing",
        "hr":"Human Resources", "finance":"Finance & Banking",
        "product":"Product Management", "design":"UI/UX Design",
        "business_analyst":"Business Analyst", "sales":"Sales & BD",
        "general":"General",
    }
    return labels.get(domain, domain)

def _level_label(level: str) -> str:
    labels = {
        "fresher":"Fresher (0 years)", "junior":"Junior (0-2 years)",
        "mid":"Mid-Level (2-5 years)", "senior":"Senior (5-8 years)",
        "lead":"Lead/Principal (8+ years)",
    }
    return labels.get(level, level)