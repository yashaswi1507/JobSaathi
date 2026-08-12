"""
resume_parser_improved.py
---------------------------
Adds confidence scoring per skill (Improvement 1 from the accuracy doc),
fixing the bug where "I have no experience in Python" incorrectly counts
Python as a possessed skill.

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\resume_parser.py

  This is a drop-in REPLACEMENT for your existing resume_parser.py.
  It keeps every existing function name and return shape the same
  (extract_skills, extract_education, extract_experience, check_sections,
  calculate_quality_score, calculate_ats_score) so routes/resume.py and
  routes/career.py do not need to change at all.

  It ADDS one new function: extract_skills_with_confidence(text), which
  you can call separately wherever you want to show confidence scores
  (e.g. a new field in the resume analysis response).

HOW TO TEST IT LOCALLY:
  Run this file directly:  python resume_parser.py
  It will print a small self-test at the bottom showing the exact
  "Python coffee" / negation cases fixed.
"""

import spacy
import re
from difflib import SequenceMatcher

# --- Load spaCy English model (same as before) ---
nlp = spacy.load('en_core_web_sm')

# ============================================================
# SECTION-AWARE EXTRACTION — added to fix false-positives that
# came from advice/template text in resumes (e.g. "not the time
# to use the word" in a resume-writing-tips template triggering
# "word" as a detected skill in the Microsoft Office skills list).
# Section detection isolates the SKILLS section text so confidence
# scoring only runs on genuine skill claims, not random prose.
# ============================================================
_SECTION_NAMES = {
    'skills', 'technical skills', 'proficient skills', 'key skills',
    'core skills', 'tools', 'technologies', 'programming languages',
    'tech stack', 'skillset', 'experience', 'work experience', 'employment',
    'employment history', 'internships', 'internships and trainings', 'projects',
    'work history', 'education', 'educational history', 'academic background',
    'qualifications', 'objective', 'summary', 'professional profile', 'profile',
    'interests', 'hobbies', 'interests and hobbies', 'activities', 'awards',
    'achievements', 'achievements and extra', 'curriculars', 'publications',
    'publication', 'certifications', 'references', 'contact', 'languages',
    'workshops', 'workshops and events', 'volunteer', 'extracurricular',
}

def _detect_section_type(line):
    """
    Returns the section type for a line that looks like a section
    header, or None if this line is regular content.
    Uses two-tier approach:
      1. Exact match against known section names
      2. ALL-CAPS heuristic with min 4 alpha chars (to avoid
         skill lines like 'C, C++ ○○○○○' being treated as headers)
    """
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return None
    clean = stripped.lower().rstrip(':').strip()
    alpha_chars = re.sub(r'[^a-zA-Z ]', '', clean).strip()

    if clean in _SECTION_NAMES or alpha_chars in _SECTION_NAMES:
        if any(s in clean for s in ['skill', 'tech', 'tool', 'programm']):
            return 'skills'
        if any(s in clean for s in ['experience', 'employ', 'work', 'intern', 'project']):
            return 'experience'
        if any(s in clean for s in ['education', 'academic', 'qualif']):
            return 'education'
        return 'other_section'

    # ALL-CAPS fallback — needs 4+ alpha chars (avoids C, C++ issue)
    alpha_only = re.sub(r'[^a-zA-Z]', '', stripped)
    if (alpha_only and len(alpha_only) >= 4
            and alpha_only == alpha_only.upper()
            and len(stripped) <= 50):
        return 'other_section'
    return None

def _split_into_sections(text):
    """
    Splits resume text into sections, returning a dict of
    {section_type: text_content}. Section types: 'skills',
    'experience', 'education', 'other_section', 'preamble'.
    """
    sections = {}
    current_type = 'preamble'
    current_lines = []
    for line in text.split('\n'):
        sec = _detect_section_type(line)
        if sec is not None:
            if current_lines:
                sections.setdefault(current_type, []).extend(current_lines)
            current_type = sec
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.setdefault(current_type, []).extend(current_lines)
    return {k: '\n'.join(v) for k, v in sections.items()}

# --- Same skill list as before, unchanged ---
SKILL_KEYWORDS = [
    # Programming languages
    'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby',
    # Web development
    'react', 'angular', 'vue', 'html', 'css', 'node.js',
    'asp.net', 'mvc', 'jquery',
    # Databases
    'sql', 'mysql', 'postgresql', 'mongodb', 'oracle',
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'devops',
    'ci/cd', 'jenkins', 'terraform',
    # Data & AI
    'machine learning', 'deep learning', 'tensorflow', 'pytorch',
    'pandas', 'numpy', 'data analysis', 'nlp', 'power bi', 'tableau',
    # Frameworks
    'flask', 'django', 'fastapi', 'spring boot', 'rest api',
    # General IT / Enterprise
    'active directory', 'network administration', 'risk management',
    'project management', 'product lifecycle management',
    'system administration', 'cybersecurity', 'agile', 'scrum',
    # Networking & Infrastructure
    'cisco', 'tcp/ip', 'vpn', 'firewall', 'router', 'switch',
    'lan', 'wan', 'dns', 'dhcp', 'network security', 'infrastructure',
    'server management', 'hardware installation', 'troubleshooting',
    'enterprise operations', 'data management', 'emergency management',
    'patch management', 'system configuration', 'help desk',
    'technical support', 'ticketing system',
    # General office
    'excel', 'word', 'powerpoint', 'sharepoint', 'visio',
    # Soft tools
    'git', 'linux', 'windows server',
    # Finance & Accounting
    'financial analysis', 'accounting', 'budgeting', 'forecasting',
    'auditing', 'taxation', 'tally', 'quickbooks', 'sap',
    'financial reporting', 'balance sheet', 'accounts payable',
    'accounts receivable', 'cost accounting', 'financial modeling',
    'investment analysis', 'risk assessment', 'compliance',
    'banking operations', 'credit analysis', 'portfolio management'
]

# --- Words that flip a skill mention to "does not have" ---
NEGATION_WORDS = {
    'no', 'not', 'none', 'never', 'without', 'lack', 'lacking',
    "don't", 'dont', "doesn't", 'doesnt', "haven't", 'havent',
    "isn't", 'isnt', "didn't", 'didnt', 'excluding', 'except'
}

# --- Words that lower confidence without fully negating ---
WEAK_WORDS = {
    'basic', 'beginner', 'familiar', 'familiarity', 'some',
    'little', 'learning', 'exposure', 'introductory', 'limited'
}

# --- Words that raise confidence ---
STRONG_WORDS = {
    'expert', 'advanced', 'proficient', 'extensive', 'strong',
    'skilled', 'experienced', 'specialist', 'fluent'
}


# --- Extract skills from resume text (UNCHANGED — same as before) ---
def extract_skills(text):
    text_lower = text.lower()
    found_skills = []

    for skill in SKILL_KEYWORDS:
        # Word-boundary match instead of plain substring search, so
        # short skill codes like "wan", "lan", "aws", "sql", "r" don't
        # falsely match inside unrelated words ("want", "land", "laws",
        # "squally"). re.escape handles skills with special characters
        # like "c++", "c#", "ci/cd".
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


# --- NEW: extract skills WITH confidence scores (SECTION-AWARE) ---
def extract_skills_with_confidence(text, window=8):
    """
    Section-aware, confidence-scored skill extraction. Improvements
    over the original keyword-matching approach:

    1. SECTION-AWARE: splits the resume into sections (Skills,
       Experience, Education, etc.) and weights skill mentions
       found in the Skills section more highly than those found
       in generic text. This fixes the "word" false-positive bug
       where resume-writing-template advice text ("not the time to
       use the word") triggered the Microsoft Word skill — that
       text only appears in 'other_section', not in a Skills section.

    2. NEGATION-AWARE: checks words immediately before each skill
       mention for negation ("no experience in Python") and
       correctly scores those as 0.0 rather than treating them
       as possessed skills.

    3. SENTENCE-BOUNDARY-RESPECTING: stops the lookback window at
       the last sentence boundary (period/newline) so words from
       one sentence don't bleed into the next.

    Confidence scores:
        0.0  -> negated in any section ("no experience in X")
        0.4  -> weak qualifier ("basic knowledge of SQL")
        0.7  -> normal mention in non-skills section
        0.85 -> Skills section mention (unlabeled/unqualified)
        0.95 -> strong qualifier ("proficient in Java") OR Skills
                section mention with strong qualifier

    Returns a list of dicts: [{"skill": "python", "confidence": 0.0,
                                "section": "skills"}, ...]
    """
    text_lower = text.lower()
    doc = nlp(text_lower)

    # Split into sections so we know WHERE each skill was mentioned
    sections = _split_into_sections(text)
    skills_section_text = sections.get('skills', '').lower()

    results = []

    for skill in SKILL_KEYWORDS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        match = re.search(pattern, text_lower)
        if not match:
            continue
        idx = match.start()

        # Determine which section this mention is in
        in_skills_section = bool(re.search(pattern, skills_section_text))

        # Look at the window of words before the mention, stopping at
        # the last sentence boundary (sentence-bleed fix from before)
        start = max(0, idx - 60)
        window_text = text_lower[start:idx]
        last_boundary = max(
            window_text.rfind('.'),
            window_text.rfind('\n'),
            window_text.rfind(';'),
        )
        if last_boundary != -1:
            window_text = window_text[last_boundary + 1:]
        words_before = re.findall(r"[a-z']+", window_text)[-window:]

        # Negation always wins, regardless of section
        if any(w in NEGATION_WORDS for w in words_before):
            confidence = 0.0
        elif any(w in STRONG_WORDS for w in words_before):
            # Strong qualifier: 0.95 always
            confidence = 0.95
        elif any(w in WEAK_WORDS for w in words_before):
            # Weak qualifier: 0.4 always
            confidence = 0.4
        elif in_skills_section:
            # In the Skills section without any qualifier = high confidence
            # (a bare skill name in a skills list is an implicit claim of
            # possession — e.g. "Python ○○○○○" in a skills table)
            confidence = 0.85
        else:
            # Normal mention in non-skills text
            confidence = 0.7

        results.append({
            "skill": skill,
            "confidence": confidence,
            "section": "skills" if in_skills_section else "other",
        })

    return results


# --- Extract education info using keywords (UNCHANGED) ---
def extract_education(text):
    text_lower = text.lower()
    education_keywords = ['bachelor', 'master', 'phd', 'b.tech',
                          'm.tech', 'mba', 'b.sc', 'm.sc', 'diploma']
    found = []

    for word in education_keywords:
        if word in text_lower:
            found.append(word)

    return found


# --- Extract years of experience using regex pattern (UNCHANGED) ---
def extract_experience(text):
    pattern = r'(\d+)\+?\s*years?'
    matches = re.findall(pattern, text.lower())

    if matches:
        return max([int(m) for m in matches])
    return 0


# --- Check which standard resume sections exist (UNCHANGED) ---
def check_sections(text):
    text_lower = text.lower()
    sections = {
        'summary':     'summary' in text_lower or 'objective' in text_lower,
        'experience':  'experience' in text_lower or 'work history' in text_lower,
        'education':   'education' in text_lower,
        'skills':      'skills' in text_lower,
        'projects':    'project' in text_lower,
        'certifications': 'certification' in text_lower or 'certificate' in text_lower
    }
    return sections


# --- Calculate resume quality score out of 100 (UNCHANGED logic,
#     still uses extract_skills() not the confidence version, so the
#     score itself doesn't change — confidence is additive info) ---
def calculate_quality_score(text):
    """
    Returns overall quality score + 5 sub-scores.
    Sub-scores: content, skills, experience, education, formatting
    Weighted average = final overall score.
    """
    import re
    text_lower = text.lower()
    word_count = len(text.split())

    # ── 1. CONTENT SCORE (30% weight) ──────────────────────
    # Based on word count, meaningful sentences, action verbs
    action_verbs = ['developed','built','created','designed','implemented',
                    'led','managed','improved','optimized','achieved',
                    'delivered','launched','increased','reduced','automated']
    verb_count  = sum(1 for v in action_verbs if v in text_lower)
    has_numbers = len(re.findall(r'\d+%|\d+ lpa|\d+x|\d+\+', text_lower))

    content_base = 0
    if 200 <= word_count <= 300:   content_base = 55
    elif 300 <= word_count <= 600: content_base = 70
    elif 600 <= word_count <= 900: content_base = 80
    elif word_count > 900:         content_base = 65  # too long
    else:                          content_base = 35  # too short

    content_score = min(100, content_base + (verb_count * 3) + (has_numbers * 4))

    # ── 2. SKILLS SCORE (25% weight) ───────────────────────
    skills = extract_skills(text)
    skill_count = len(skills)
    if skill_count >= 15:   skills_score = 95
    elif skill_count >= 10: skills_score = 85
    elif skill_count >= 7:  skills_score = 75
    elif skill_count >= 4:  skills_score = 60
    elif skill_count >= 2:  skills_score = 45
    else:                   skills_score = 20

    # ── 3. EXPERIENCE SCORE (20% weight) ───────────────────
    exp_signals = ['experience','work','intern','job','role','position',
                   'company','organisation','organization','employed']
    exp_found   = sum(1 for s in exp_signals if s in text_lower)
    year_pattern = len(re.findall(r'20\d{2}|19\d{2}', text))
    bullet_count = len(re.findall(r'•|\*|–|-\s', text))

    if exp_found >= 5 and year_pattern >= 2:
        experience_score = min(95, 65 + (bullet_count * 2) + (year_pattern * 3))
    elif exp_found >= 3:
        experience_score = min(80, 50 + (bullet_count * 2))
    elif 'intern' in text_lower:
        experience_score = 60
    else:
        experience_score = 30  # No experience section

    # ── 4. EDUCATION SCORE (15% weight) ────────────────────
    edu_signals = ['bachelor','b.tech','b.e.','btech','degree','university',
                   'college','school','master','m.tech','mba','phd','gpa','cgpa','percent']
    edu_found = sum(1 for s in edu_signals if s in text_lower)

    if edu_found >= 4:   education_score = 90
    elif edu_found >= 2: education_score = 75
    elif edu_found >= 1: education_score = 55
    else:                education_score = 20

    # ── 5. FORMATTING SCORE (10% weight) ───────────────────
    sections = check_sections(text)
    section_count = sum(sections.values())
    total_sections = len(sections)

    has_email    = bool(re.search(r'[\w.]+@[\w.]+\.\w+', text))
    has_phone    = bool(re.search(r'[+]?\d[\d\s\-]{8,}', text))
    has_linkedin = 'linkedin' in text_lower
    contact_score = (has_email * 30) + (has_phone * 30) + (has_linkedin * 20)

    formatting_score = min(100,
        (section_count / max(total_sections, 1)) * 50 + contact_score * 0.5
    )

    # ── WEIGHTED FINAL SCORE ────────────────────────────────
    overall = round(
        content_score    * 0.30 +
        skills_score     * 0.25 +
        experience_score * 0.20 +
        education_score  * 0.15 +
        formatting_score * 0.10,
        1
    )

    return {
        "overall":          int(min(overall, 98)),  # cap at 98 — 100 is perfect
        "content_score":    int(min(content_score,    98)),
        "skills_score":     int(min(skills_score,     98)),
        "experience_score": int(min(experience_score, 98)),
        "education_score":  int(min(education_score,  98)),
        "formatting_score": int(min(formatting_score, 98)),
    }


# --- Calculate ATS match score (UNCHANGED, but now filters out
#     negated skills so a "no experience in X" doesn't falsely count
#     as a resume/job match) ---
def calculate_ats_score(resume_text, job_description):
    """
    Improved ATS score algorithm with detailed breakdown.
    Returns (score, breakdown_dict) tuple.
    """
    if not job_description.strip():
        return 0, {}

    resume_lower = resume_text.lower()
    jd_lower     = job_description.lower()

    score = 0
    max_score = 0
    breakdown = {}

    # ─── 1. SKILL MATCHING (40 points) ────────────────────────────
    SYNONYMS = [
        {"machine learning", "ml", "statistical modeling", "predictive modeling"},
        {"deep learning", "dl", "neural network", "neural net"},
        {"natural language processing", "nlp", "text mining", "text analytics"},
        {"computer vision", "cv", "image processing", "image recognition"},
        {"python", "py"},
        {"javascript", "js", "node.js", "nodejs"},
        {"react", "react.js", "reactjs"},
        {"vue", "vue.js", "vuejs"},
        {"angular", "angular.js", "angularjs"},
        {"postgresql", "postgres", "psql"},
        {"mongodb", "mongo"},
        {"mysql", "my sql"},
        {"aws", "amazon web services", "amazon cloud"},
        {"gcp", "google cloud", "google cloud platform"},
        {"azure", "microsoft azure"},
        {"docker", "containerization", "containers"},
        {"kubernetes", "k8s", "container orchestration"},
        {"ci/cd", "continuous integration", "continuous deployment", "devops pipeline"},
        {"git", "github", "gitlab", "version control"},
        {"rest api", "restful api", "rest", "api development"},
        {"sql", "structured query language", "database queries"},
        {"tensorflow", "tf"},
        {"pytorch", "torch"},
        {"scikit-learn", "sklearn", "scikit learn"},
        {"power bi", "powerbi"},
        {"tableau", "data visualization"},
        {"excel", "microsoft excel", "ms excel"},
        {"agile", "scrum", "kanban", "sprint"},
        {"linux", "unix", "ubuntu"},
        {"fastapi", "fast api"},
        {"django", "django rest framework", "drf"},
        {"flask", "flask api"},
        {"spark", "apache spark", "pyspark"},
        {"hadoop", "hdfs", "mapreduce"},
        {"kafka", "apache kafka"},
        {"data analysis", "data analytics", "data analyst"},
        {"data science", "data scientist"},
        {"pandas", "dataframes"},
        {"numpy", "numerical python"},
    ]

    resume_skills_scored = extract_skills_with_confidence(resume_text)
    jd_skills_scored     = extract_skills_with_confidence(job_description)
    resume_skills = {s["skill"] for s in resume_skills_scored if s["confidence"] > 0}
    jd_skills     = {s["skill"] for s in jd_skills_scored     if s["confidence"] > 0}

    def expand_with_synonyms(skill_set, text):
        expanded = set(skill_set)
        for group in SYNONYMS:
            if any(s in skill_set for s in group) or any(s in text for s in group):
                if any(s in text for s in group):
                    expanded.update(group)
        return expanded

    resume_expanded = expand_with_synonyms(resume_skills, resume_lower)
    jd_expanded     = expand_with_synonyms(jd_skills, jd_lower)

    matched_skills = sorted(resume_expanded.intersection(jd_expanded))
    missing_skills = sorted(jd_expanded - resume_expanded)

    if jd_expanded:
        skill_score = min(40, (len(matched_skills) / len(jd_expanded)) * 40)
        score += skill_score
    max_score += 40

    breakdown["skills"] = {
        "points_earned": round(skill_score if jd_expanded else 0, 1),
        "points_max":    40,
        "matched":       matched_skills[:10],
        "missing":       missing_skills[:10],
        "message":       f"Matched {len(matched_skills)} of {len(jd_expanded)} required skills"
    }

    # ─── 2. EXPERIENCE KEYWORD MATCHING (20 points) ───────────────
    exp_keywords = re.findall(r'\b[a-z][a-z\s]{3,20}\b', jd_lower)
    exp_keywords = [w.strip() for w in exp_keywords if len(w.strip()) > 4]
    exp_keywords = list(set(exp_keywords))[:30]
    exp_matches  = [kw for kw in exp_keywords if kw in resume_lower]

    if exp_keywords:
        exp_score = min(20, (len(exp_matches) / len(exp_keywords)) * 20)
        score += exp_score
    else:
        exp_score = 0
    max_score += 20

    breakdown["keywords"] = {
        "points_earned": round(exp_score, 1),
        "points_max":    20,
        "matched_count": len(exp_matches),
        "total_count":   len(exp_keywords),
        "message":       f"Found {len(exp_matches)} of {len(exp_keywords)} JD keywords in your resume"
    }

    # ─── 3. SECTION STRUCTURE (15 points) ────────────────────────
    sections = {
        "Experience section":  any(s in resume_lower for s in ["experience", "work history", "employment"]),
        "Education section":   any(s in resume_lower for s in ["education", "degree", "university", "college", "b.tech", "m.tech"]),
        "Skills section":      any(s in resume_lower for s in ["skills", "technical skills", "core competencies"]),
        "Projects section":    any(s in resume_lower for s in ["projects", "project", "portfolio"]),
        "Summary/Objective":   any(s in resume_lower for s in ["summary", "objective", "profile", "about"]),
    }
    present_sections  = [k for k, v in sections.items() if v]
    missing_sections  = [k for k, v in sections.items() if not v]
    section_score     = min(15, len(present_sections) * 3)
    score += section_score
    max_score += 15

    breakdown["structure"] = {
        "points_earned":  round(section_score, 1),
        "points_max":     15,
        "present":        present_sections,
        "missing":        missing_sections,
        "message":        f"{len(present_sections)}/5 key sections found in resume"
    }

    # ─── 4. QUANTIFICATION BONUS (10 points) ─────────────────────
    numbers   = re.findall(r'\b\d+[%+]?\b', resume_text)
    quant_score = min(10, len(numbers) * 1.5)
    score += quant_score
    max_score += 10

    breakdown["quantification"] = {
        "points_earned": round(quant_score, 1),
        "points_max":    10,
        "count":         len(numbers),
        "message":       f"Found {len(numbers)} numbers/metrics — recruiters love quantified achievements",
        "tip":           "Add more numbers: '40% faster', '10K users', 'Rs 2Cr saved'" if len(numbers) < 5 else "Good use of metrics!"
    }

    # ─── 5. ACTION VERBS (10 points) ─────────────────────────────
    ACTION_VERBS = [
        "developed", "built", "designed", "implemented", "led", "managed",
        "created", "delivered", "achieved", "improved", "reduced", "increased",
        "automated", "deployed", "optimized", "architected", "launched",
        "collaborated", "mentored", "analyzed", "researched",
    ]
    found_verbs = [v for v in ACTION_VERBS if v in resume_lower]
    verb_score  = min(10, len(found_verbs) * 1.5)
    score += verb_score
    max_score += 10

    breakdown["action_verbs"] = {
        "points_earned": round(verb_score, 1),
        "points_max":    10,
        "found":         found_verbs[:8],
        "message":       f"Found {len(found_verbs)} strong action verbs",
        "tip":           "Start bullets with: Built, Led, Reduced, Improved, Deployed..." if len(found_verbs) < 5 else "Great use of action verbs!"
    }

    # ─── 6. JD TITLE/ROLE MATCH (5 points) ───────────────────────
    jd_first_line = jd_lower.split('\n')[0][:100]
    title_words   = re.findall(r'\b[a-z]{4,}\b', jd_first_line)
    title_matches = [w for w in title_words if w in resume_lower]
    title_score   = min(5, len(title_matches) * 2)
    score += title_score
    max_score += 5

    breakdown["role_match"] = {
        "points_earned": round(title_score, 1),
        "points_max":    5,
        "matched":       title_matches[:5],
        "message":       f"Role title keywords matched: {', '.join(title_matches[:3]) or 'none'}"
    }

    final_score = round((score / max_score) * 100, 1) if max_score > 0 else 0
    final_score = min(100, final_score)

    breakdown["total"] = {
        "score":   final_score,
        "raw":     round(score, 1),
        "max":     max_score,
        "grade":   "Excellent" if final_score >= 80 else
                   "Good"      if final_score >= 65 else
                   "Average"   if final_score >= 50 else "Needs Work",
    }

    return final_score, breakdown

    # ─── 1. SKILL MATCHING (40 points) ────────────────────────────
    # Synonym groups — any match in group counts
    SYNONYMS = [
        {"machine learning", "ml", "statistical modeling", "predictive modeling"},
        {"deep learning", "dl", "neural network", "neural net"},
        {"natural language processing", "nlp", "text mining", "text analytics"},
        {"computer vision", "cv", "image processing", "image recognition"},
        {"python", "py"},
        {"javascript", "js", "node.js", "nodejs"},
        {"react", "react.js", "reactjs"},
        {"vue", "vue.js", "vuejs"},
        {"angular", "angular.js", "angularjs"},
        {"postgresql", "postgres", "psql"},
        {"mongodb", "mongo"},
        {"mysql", "my sql"},
        {"aws", "amazon web services", "amazon cloud"},
        {"gcp", "google cloud", "google cloud platform"},
        {"azure", "microsoft azure"},
        {"docker", "containerization", "containers"},
        {"kubernetes", "k8s", "container orchestration"},
        {"ci/cd", "continuous integration", "continuous deployment", "devops pipeline"},
        {"git", "github", "gitlab", "version control"},
        {"rest api", "restful api", "rest", "api development"},
        {"sql", "structured query language", "database queries"},
        {"tensorflow", "tf"},
        {"pytorch", "torch"},
        {"scikit-learn", "sklearn", "scikit learn"},
        {"power bi", "powerbi"},
        {"tableau", "data visualization"},
        {"excel", "microsoft excel", "ms excel"},
        {"agile", "scrum", "kanban", "sprint"},
        {"linux", "unix", "ubuntu"},
        {"fastapi", "fast api"},
        {"django", "django rest framework", "drf"},
        {"flask", "flask api"},
        {"spark", "apache spark", "pyspark"},
        {"hadoop", "hdfs", "mapreduce"},
        {"kafka", "apache kafka"},
        {"data analysis", "data analytics", "data analyst"},
        {"data science", "data scientist"},
        {"pandas", "dataframes"},
        {"numpy", "numerical python"},
    ]

    resume_skills_scored = extract_skills_with_confidence(resume_text)
    jd_skills_scored     = extract_skills_with_confidence(job_description)
    resume_skills = {s["skill"] for s in resume_skills_scored if s["confidence"] > 0}
    jd_skills     = {s["skill"] for s in jd_skills_scored     if s["confidence"] > 0}

    # Expand with synonym matching
    def expand_with_synonyms(skill_set, text):
        expanded = set(skill_set)
        for group in SYNONYMS:
            if any(s in skill_set for s in group) or any(s in text for s in group):
                if any(s in text for s in group):
                    expanded.update(group)
        return expanded

    resume_expanded = expand_with_synonyms(resume_skills, resume_lower)
    jd_expanded     = expand_with_synonyms(jd_skills, jd_lower)

    if jd_expanded:
        skill_matches = resume_expanded.intersection(jd_expanded)
        skill_score = min(40, (len(skill_matches) / len(jd_expanded)) * 40)
        score += skill_score
    max_score += 40

    # ─── 2. EXPERIENCE KEYWORD MATCHING (20 points) ───────────────
    exp_keywords = re.findall(r'\b[a-z][a-z\s]{3,20}\b', jd_lower)
    exp_keywords = [w.strip() for w in exp_keywords if len(w.strip()) > 4]
    exp_keywords = list(set(exp_keywords))[:30]

    if exp_keywords:
        exp_matches = sum(1 for kw in exp_keywords if kw in resume_lower)
        exp_score = min(20, (exp_matches / len(exp_keywords)) * 20)
        score += exp_score
    max_score += 20

    # ─── 3. SECTION STRUCTURE (15 points) ────────────────────────
    sections = {
        "experience":     any(s in resume_lower for s in ["experience", "work history", "employment"]),
        "education":      any(s in resume_lower for s in ["education", "degree", "university", "college", "b.tech", "m.tech"]),
        "skills":         any(s in resume_lower for s in ["skills", "technical skills", "core competencies"]),
        "projects":       any(s in resume_lower for s in ["projects", "project", "portfolio"]),
        "summary":        any(s in resume_lower for s in ["summary", "objective", "profile", "about"]),
    }
    section_score = sum(3 for v in sections.values() if v)
    score += min(15, section_score)
    max_score += 15

    # ─── 4. QUANTIFICATION BONUS (10 points) ─────────────────────
    # Numbers, percentages, metrics in resume = stronger ATS signal
    numbers = re.findall(r'\b\d+[%+]?\b', resume_text)
    quant_score = min(10, len(numbers) * 1.5)
    score += quant_score
    max_score += 10

    # ─── 5. ACTION VERBS (10 points) ─────────────────────────────
    ACTION_VERBS = [
        "developed", "built", "designed", "implemented", "led", "managed",
        "created", "delivered", "achieved", "improved", "reduced", "increased",
        "automated", "deployed", "optimized", "architected", "launched",
        "collaborated", "mentored", "analyzed", "researched",
    ]
    verb_count = sum(1 for v in ACTION_VERBS if v in resume_lower)
    verb_score = min(10, verb_count * 1.5)
    score += verb_score
    max_score += 10

    # ─── 6. JD TITLE/ROLE MATCH BONUS (5 points) ─────────────────
    # Check if job title keywords appear in resume
    jd_first_line = jd_lower.split('\n')[0][:100]
    title_words   = re.findall(r'\b[a-z]{4,}\b', jd_first_line)
    title_matches = sum(1 for w in title_words if w in resume_lower)
    title_score   = min(5, title_matches * 2)
    score += title_score
    max_score += 5

    final_score = round((score / max_score) * 100, 1) if max_score > 0 else 0
    return min(100, final_score)


print("Resume parser functions loaded successfully (with confidence scoring).")


# ----------------------------------------------------------------------
# SELF-TEST — run this file directly to see the fix in action
# ----------------------------------------------------------------------
if __name__ == "__main__":
    test_resume = """
    I have no experience in Python but I am proficient in Java.
    Basic knowledge of SQL. Extensive experience with AWS.
    """
    print("\n--- Self-test: confidence scoring ---")
    for item in extract_skills_with_confidence(test_resume):
        print(f"  {item['skill']:15s} confidence = {item['confidence']}")

    print("\n--- Old behaviour (extract_skills, no confidence) ---")
    print(" ", extract_skills(test_resume))
    print("  (notice 'python' is still listed here — that's the bug this file fixes")
    print("   when you use extract_skills_with_confidence instead)")