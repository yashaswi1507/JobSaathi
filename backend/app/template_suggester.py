"""
template_suggester.py
---------------------
Suggests the best resume template based on:
  - Career level (fresher/junior/mid/senior/lead)
  - Domain (software/aiml/marketing etc.)
  - ATS score
  - Job description keywords
"""

# ============================================================
# TEMPLATE CATALOG
# ============================================================
TEMPLATES = {
    "jakescv": {
        "name": "Jake's Resume",
        "description": "Clean single column — maximum ATS compatibility",
        "style": "minimal",
        "ats_score": 10,
        "visual_score": 4,
        "best_for_levels": ["fresher", "junior", "mid", "senior", "lead"],
        "best_for_domains": ["software", "devops", "cybersecurity", "finance", "general"],
        "layout": "single_column",
        "has_visualization": False,
        "inspired_by": "Jake Gutierrez — Overleaf #1",
    },
    "altacv": {
        "name": "AltaCV",
        "description": "Two column with skill tags — modern and clean",
        "style": "modern",
        "ats_score": 7,
        "visual_score": 7,
        "best_for_levels": ["fresher", "junior", "mid"],
        "best_for_domains": ["aiml", "data_science", "software", "product", "design"],
        "layout": "two_column",
        "has_visualization": False,
        "inspired_by": "AltaCV — Overleaf",
    },
    "moderncv": {
        "name": "ModernCV",
        "description": "Timeline sidebar — shows career progression clearly",
        "style": "professional",
        "ats_score": 7,
        "visual_score": 8,
        "best_for_levels": ["mid", "senior"],
        "best_for_domains": ["software", "devops", "aiml", "product", "hr"],
        "layout": "sidebar_timeline",
        "has_visualization": False,
        "inspired_by": "ModernCV — Overleaf",
    },
    "awesomecv": {
        "name": "Awesome CV",
        "description": "Colored section bars — bold and distinctive",
        "style": "creative",
        "ats_score": 6,
        "visual_score": 9,
        "best_for_levels": ["junior", "mid", "senior"],
        "best_for_domains": ["marketing", "design", "product", "sales", "aiml"],
        "layout": "single_column_colored",
        "has_visualization": False,
        "inspired_by": "Awesome-CV — GitHub",
    },
    "deedycv": {
        "name": "Deedy CV",
        "description": "Dark sidebar + light main — authority and expertise",
        "style": "executive",
        "ats_score": 6,
        "visual_score": 9,
        "best_for_levels": ["senior", "lead"],
        "best_for_domains": ["software", "aiml", "devops", "cybersecurity", "data_science"],
        "layout": "dark_sidebar",
        "has_visualization": False,
        "inspired_by": "Deedy-Resume — Overleaf",
    },
    "elegant": {
        "name": "Elegant",
        "description": "Double rule sections, teal accents — formal and professional",
        "style": "formal",
        "ats_score": 8,
        "visual_score": 7,
        "best_for_levels": ["mid", "senior", "lead"],
        "best_for_domains": ["finance", "business_analyst", "hr", "general", "marketing"],
        "layout": "single_column_elegant",
        "has_visualization": False,
        "inspired_by": "sb2nov — Overleaf",
    },
    "skillbars": {
        "name": "Skill Bars",
        "description": "Progress bar visualization — shows expertise level visually",
        "style": "visual",
        "ats_score": 5,
        "visual_score": 10,
        "best_for_levels": ["fresher", "junior", "mid", "senior"],
        "best_for_domains": ["aiml", "data_science", "software", "devops", "design"],
        "layout": "sidebar_with_bars",
        "has_visualization": True,
        "inspired_by": "Custom skill visualization",
    },
}


# ============================================================
# LEVEL → PRIMARY TEMPLATE MAPPING
# ============================================================
LEVEL_PRIMARY = {
    "fresher": ["skillbars", "jakescv", "altacv"],
    "junior":  ["altacv",    "jakescv", "awesomecv"],
    "mid":     ["moderncv",  "elegant", "altacv"],
    "senior":  ["deedycv",   "elegant", "moderncv"],
    "lead":    ["elegant",   "deedycv", "awesomecv"],
}

# ============================================================
# DOMAIN → STYLE PREFERENCE
# ============================================================
DOMAIN_STYLE_PREF = {
    "software":        ["jakescv", "deedycv", "moderncv"],
    "data_science":    ["altacv",  "skillbars", "moderncv"],
    "aiml":            ["altacv",  "skillbars", "deedycv"],
    "devops":          ["jakescv", "deedycv", "moderncv"],
    "cybersecurity":   ["jakescv", "deedycv", "elegant"],
    "marketing":       ["awesomecv", "altacv", "elegant"],
    "hr":              ["elegant",   "moderncv", "jakescv"],
    "finance":         ["elegant",   "jakescv",  "moderncv"],
    "product":         ["moderncv",  "altacv",   "awesomecv"],
    "design":          ["awesomecv", "skillbars", "altacv"],
    "business_analyst":["elegant",   "moderncv",  "jakescv"],
    "sales":           ["awesomecv", "elegant",   "altacv"],
    "general":         ["jakescv",   "elegant",   "altacv"],
}

# ============================================================
# ATS SCORE → TEMPLATE FILTER
# ============================================================
def get_ats_preference(ats_score: float):
    """
    Returns (prefer_ats, prefer_visual) flags.
    Low ATS score → prefer ATS-friendly templates.
    High ATS score → visual templates also okay.
    """
    if ats_score < 50:
        return True, False   # must use ATS-friendly
    elif ats_score < 70:
        return True, False   # prefer ATS-friendly
    elif ats_score < 80:
        return False, False  # balanced — both ok
    else:
        return False, True   # score is fine, visual ok


# ============================================================
# MAIN SUGGESTION FUNCTION
# ============================================================
def suggest_templates(
    level: str,
    domain: str,
    ats_score: float = 60,
    breakdown: dict = None,
) -> dict:
    """
    Suggests best templates based on level, domain, and ATS score.

    Returns:
    {
      "primary": {...},        # #1 recommendation
      "alternatives": [...],  # top 3 alternatives
      "reasoning": "...",     # why this template
      "fresher_note": "...",  # if fresher, special note
      "level_differences": {...}  # how template differs by level
    }
    """
    prefer_ats, prefer_visual = get_ats_preference(ats_score)

    # Step 1: Get level-preferred templates
    level_templates = LEVEL_PRIMARY.get(level, LEVEL_PRIMARY["mid"])

    # Step 2: Get domain-preferred templates
    domain_templates = DOMAIN_STYLE_PREF.get(domain, DOMAIN_STYLE_PREF["general"])

    # Step 3: Score each template
    scored = []
    for tid, t in TEMPLATES.items():
        score = 0

        # Level match
        if level in t["best_for_levels"]:
            score += 30
        if tid in level_templates:
            score += 20 - (level_templates.index(tid) * 5)

        # Domain match
        if domain in t["best_for_domains"]:
            score += 20
        if tid in domain_templates:
            score += 15 - (domain_templates.index(tid) * 4)

        # ATS preference
        if prefer_ats and t["ats_score"] >= 8:
            score += 20
        elif prefer_ats and t["ats_score"] >= 6:
            score += 10
        elif prefer_ats and t["ats_score"] < 6:
            score -= 15

        if prefer_visual and t["visual_score"] >= 9:
            score += 15

        scored.append((tid, score, t))

    scored.sort(key=lambda x: x[1], reverse=True)
    primary_id, _, primary = scored[0]
    alternatives = [
        {**t, "template_id": tid, "score": s}
        for tid, s, t in scored[1:4]
    ]

    # Reasoning text
    reasoning_parts = []
    if level == "fresher":
        reasoning_parts.append(f"As a fresher, {primary['name']} works best because it emphasizes Projects and Skills over experience")
    elif level in ("senior", "lead"):
        reasoning_parts.append(f"For senior level, {primary['name']} gives authority and emphasizes your leadership experience")
    else:
        reasoning_parts.append(f"{primary['name']} balances visual appeal with ATS compatibility for {level} level")

    if prefer_ats:
        reasoning_parts.append(f"your ATS score ({ats_score:.0f}%) is low — ATS-friendly template recommended")
    if domain in primary["best_for_domains"]:
        reasoning_parts.append(f"suits {domain} domain")

    # Level differences explanation
    level_differences = {
        "fresher": {
            "section_order": "Objective → Skills → Projects → Education → Internship",
            "focus": "Projects and Skills prominent (less experience)",
            "summary_tone": "Seeking opportunity, eager to learn",
            "skill_bars": "Shows potential and learning (60-80% bars)",
        },
        "junior": {
            "section_order": "Summary → Skills → Projects → Experience → Education",
            "focus": "Skills + early experience balanced",
            "summary_tone": "Building expertise, growing fast",
            "skill_bars": "Shows growing competence (70-85% bars)",
        },
        "mid": {
            "section_order": "Summary → Experience → Skills → Projects → Education",
            "focus": "Experience now leads",
            "summary_tone": "Delivering impact, taking ownership",
            "skill_bars": "Shows solid expertise (75-90% bars)",
        },
        "senior": {
            "section_order": "Summary → Experience → Projects → Skills → Education",
            "focus": "Leadership and impact metrics prominent",
            "summary_tone": "Led teams, architected systems, delivered business value",
            "skill_bars": "Shows mastery (85-95% bars)",
        },
        "lead": {
            "section_order": "Profile → Experience → Achievements → Skills → Education",
            "focus": "Strategic impact, mentoring, organizational contribution",
            "summary_tone": "Driving engineering culture and technical direction",
            "skill_bars": "Expert-level (90-100% bars)",
        },
    }

    return {
        "primary": {
            **primary,
            "template_id": primary_id,
        },
        "alternatives": alternatives,
        "reasoning": " | ".join(reasoning_parts),
        "ats_note": f"Current ATS: {ats_score:.0f}% → {'Use ATS-friendly template' if prefer_ats else 'Visual templates also okay'}",
        "level_differences": level_differences,
        "current_level_info": level_differences.get(level, {}),
    }
