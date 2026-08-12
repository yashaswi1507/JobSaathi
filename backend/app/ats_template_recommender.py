"""
ats_template_recommender.py
-----------------------------
Recommends the best resume template based on ATS score range.
Suggests templates that will maximize ATS score improvement.

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\ats_template_recommender.py
"""

# ============================================================
# ATS SCORE RANGES
# ============================================================
ATS_RANGES = {
    "critical":  (0,   50),   # Needs immediate help
    "average":   (50,  70),   # Can be improved
    "good":      (70,  80),   # Minor improvements
    "excellent": (80,  100),  # Already strong
}

# ============================================================
# TEMPLATE ATS FRIENDLINESS SCORES
# (Based on layout characteristics)
# ============================================================
# Why certain templates score higher for ATS:
# - single_column: ATS reads top-to-bottom, no confusion
# - two_column: ATS may miss sidebar content
# - compact: dense keywords, good for ATS
# - timeline: clear chronology, ATS-friendly
# - sidebar: ATS may skip sidebar entirely

TEMPLATE_ATS_SCORES = {
    # design → layout → ats_friendliness (1-10)
    "classic":   {"single_column": 10, "timeline": 9, "compact": 9, "two_column": 7, "sidebar": 6},
    "academic":  {"single_column": 10, "timeline": 9, "compact": 9, "two_column": 7, "sidebar": 6},
    "executive": {"single_column": 9,  "timeline": 9, "compact": 8, "two_column": 7, "sidebar": 6},
    "modern":    {"single_column": 8,  "timeline": 8, "compact": 8, "two_column": 6, "sidebar": 5},
    "minimal":   {"single_column": 8,  "timeline": 8, "compact": 8, "two_column": 6, "sidebar": 5},
    "creative":  {"single_column": 7,  "timeline": 7, "compact": 7, "two_column": 5, "sidebar": 4},
}

# Domain layout overrides (from resume_builder.py)
DOMAIN_LAYOUT_MAP = {
    ("fresher",     "software"):     "two_column",
    ("fresher",     "data_science"): "two_column",
    ("fresher",     "aiml"):         "two_column",
    ("fresher",     "devops"):       "two_column",
    ("fresher",     "cybersecurity"):"two_column",
    ("fresher",     "marketing"):    "single_column",
    ("fresher",     "hr"):           "single_column",
    ("fresher",     "finance"):      "single_column",
    ("fresher",     "product"):      "single_column",
    ("fresher",     "design"):       "two_column",
    ("fresher",     "business_analyst"): "single_column",
    ("fresher",     "sales"):        "single_column",
    ("fresher",     "general"):      "single_column",
    ("junior",      "software"):     "two_column",
    ("junior",      "data_science"): "two_column",
    ("junior",      "aiml"):         "two_column",
    ("junior",      "devops"):       "two_column",
    ("junior",      "cybersecurity"):"two_column",
    ("junior",      "marketing"):    "single_column",
    ("junior",      "hr"):           "single_column",
    ("junior",      "finance"):      "single_column",
    ("junior",      "product"):      "single_column",
    ("junior",      "design"):       "two_column",
    ("junior",      "business_analyst"): "single_column",
    ("junior",      "sales"):        "single_column",
    ("junior",      "general"):      "two_column",
    ("mid",         "software"):     "timeline",
    ("mid",         "data_science"): "sidebar",
    ("mid",         "aiml"):         "sidebar",
    ("mid",         "devops"):       "timeline",
    ("mid",         "cybersecurity"):"sidebar",
    ("mid",         "marketing"):    "compact",
    ("mid",         "hr"):           "compact",
    ("mid",         "finance"):      "compact",
    ("mid",         "product"):      "compact",
    ("mid",         "design"):       "sidebar",
    ("mid",         "business_analyst"): "compact",
    ("mid",         "sales"):        "compact",
    ("mid",         "general"):      "timeline",
    ("senior",      "software"):     "sidebar",
    ("senior",      "data_science"): "sidebar",
    ("senior",      "aiml"):         "sidebar",
    ("senior",      "devops"):       "sidebar",
    ("senior",      "cybersecurity"):"sidebar",
    ("senior",      "marketing"):    "compact",
    ("senior",      "hr"):           "compact",
    ("senior",      "finance"):      "compact",
    ("senior",      "product"):      "compact",
    ("senior",      "design"):       "sidebar",
    ("senior",      "business_analyst"): "compact",
    ("senior",      "sales"):        "compact",
    ("senior",      "general"):      "sidebar",
    ("lead",        "software"):     "compact",
    ("lead",        "data_science"): "compact",
    ("lead",        "aiml"):         "compact",
    ("lead",        "devops"):       "compact",
    ("lead",        "cybersecurity"):"compact",
    ("lead",        "marketing"):    "compact",
    ("lead",        "hr"):           "compact",
    ("lead",        "finance"):      "compact",
    ("lead",        "product"):      "compact",
    ("lead",        "design"):       "compact",
    ("lead",        "business_analyst"): "compact",
    ("lead",        "sales"):        "compact",
    ("lead",        "general"):      "compact",
}


def get_ats_range(score: float) -> str:
    """Returns the ATS range category for a score."""
    if score < 50:  return "critical"
    if score < 70:  return "average"
    if score < 80:  return "good"
    return "excellent"


def get_template_ats_score(design: str, level: str, domain: str) -> int:
    """Returns ATS friendliness score (1-10) for a template combination."""
    layout = DOMAIN_LAYOUT_MAP.get((level, domain), "single_column")
    design_scores = TEMPLATE_ATS_SCORES.get(design, TEMPLATE_ATS_SCORES["modern"])
    return design_scores.get(layout, 7)


def recommend_templates(
    current_ats_score: float,
    level: str,
    domain: str,
    breakdown: dict = None,
) -> dict:
    """
    Recommends best templates based on ATS score range.

    Returns:
    {
      "current_score": 62,
      "score_range": "average",
      "score_label": "Average — Can be improved",
      "target_range": "70-80",
      "recommendations": [
        {
          "rank": 1,
          "design": "classic",
          "level": "mid",
          "domain": "software",
          "template_id": "classic_mid_software",
          "ats_friendliness": 9,
          "engine": "LaTeX",
          "why": "Classic single-column LaTeX — ATS parsers read top-to-bottom perfectly",
          "expected_ats_boost": "+12-18 points",
        }
      ],
      "content_improvements": [...],  # things to fix regardless of template
      "message": "..."
    }
    """
    score_range = get_ats_range(current_ats_score)

    # ─── Score labels and targets ───
    range_info = {
        "critical": {
            "label": "Critical — Needs immediate improvement",
            "target": "50-70",
            "message": "Your resume needs significant improvements. Switch to an ATS-optimized template and add more keywords.",
        },
        "average": {
            "label": "Average — Can be improved",
            "target": "70-80",
            "message": "Good start! Switching to a more ATS-friendly template and adding missing keywords can push you to 70-80 range.",
        },
        "good": {
            "label": "Good — Minor improvements needed",
            "target": "80-90",
            "message": "You're doing well! Small tweaks to template and content can get you to 80+.",
        },
        "excellent": {
            "label": "Excellent — Already ATS optimized",
            "target": "90+",
            "message": "Great ATS score! Your current template is working well.",
        },
    }

    info = range_info[score_range]

    # ─── Find best ATS templates for this level+domain ───
    all_designs = ["classic", "academic", "executive", "modern", "minimal", "creative"]
    # For ATS, LaTeX designs (classic, academic, executive) with single_column are best

    # Score each design for ATS friendliness
    scored = []
    for design in all_designs:
        ats_score = get_template_ats_score(design, level, domain)
        layout = DOMAIN_LAYOUT_MAP.get((level, domain), "single_column")
        engine = "LaTeX (Overleaf quality)" if design in {"classic", "academic", "executive"} else "WeasyPrint"

        # Why this template helps ATS
        why_map = {
            "classic":   "Black & white, ATS parsers love simple formatting",
            "academic":  "Traditional layout, clean section structure",
            "executive": "Professional single-column, high keyword density",
            "modern":    "Clean structure, good for modern ATS systems",
            "minimal":   "Minimal formatting, no ATS-confusing elements",
            "creative":  "Bold design — some ATS may struggle with graphics",
        }

        # Estimated ATS boost based on current score and template
        boost_map = {
            10: "+15-20 points",
            9:  "+12-18 points",
            8:  "+8-14 points",
            7:  "+5-10 points",
            6:  "+2-6 points",
            5:  "+0-3 points",
            4:  "May reduce score",
        }

        scored.append({
            "design":          design,
            "level":           level,
            "domain":          domain,
            "template_id":     f"{design}_{level}_{domain}",
            "ats_friendliness": ats_score,
            "layout":          layout,
            "engine":          engine,
            "why":             why_map[design],
            "expected_ats_boost": boost_map.get(ats_score, "+5-10 points"),
        })

    # Sort by ATS friendliness
    scored.sort(key=lambda x: x["ats_friendliness"], reverse=True)

    # Add rank
    for i, t in enumerate(scored):
        t["rank"] = i + 1

    # ─── Content improvements from breakdown ───
    content_improvements = []
    if breakdown:
        struct = breakdown.get("structure", {})
        missing_sections = struct.get("missing", [])
        for s in missing_sections:
            content_improvements.append(f"Add '{s}' to your resume")

        quant = breakdown.get("quantification", {})
        if quant.get("count", 0) < 5:
            content_improvements.append("Add more numbers/metrics (40% faster, 10K users, saved Rs 2Cr)")

        verbs = breakdown.get("action_verbs", {})
        if verbs.get("points_earned", 0) < 7:
            content_improvements.append("Start bullet points with action verbs: Built, Led, Improved, Deployed")

        skills = breakdown.get("skills", {})
        missing_skills = skills.get("missing", [])
        if missing_skills:
            content_improvements.append(f"Add missing skills: {', '.join(missing_skills[:5])}")

    return {
        "current_score":       current_ats_score,
        "score_range":         score_range,
        "score_label":         info["label"],
        "target_range":        info["target"],
        "message":             info["message"],
        "recommendations":     scored[:4],          # top 4 templates
        "best_template":       scored[0],           # #1 recommendation
        "content_improvements": content_improvements,
        "estimated_score_after": min(95, current_ats_score + scored[0]["ats_friendliness"] * 1.5),
    }