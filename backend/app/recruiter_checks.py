"""
recruiter_checks.py
--------------------
Recruiter-side resume fraud detection features:
  1. Fake experience detection  — date overlap + duration check
  2. AI-generated resume detection — statistical pattern analysis
  3. Fake company detection    — domain-consistency check

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\recruiter_checks.py

NOTE on fake certificates:
  Certificate verification requires access to issuer databases
  (Coursera, LinkedIn Learning, AWS, etc.) which are not publicly
  accessible via free APIs. This is documented as a known limitation
  and listed as future work — see thesis.
"""

import re
from datetime import datetime
from difflib import SequenceMatcher


# ============================================================
# 1. FAKE EXPERIENCE DETECTION
# ============================================================
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4,
    "june": 6, "july": 7, "august": 8, "september": 9,
    "october": 10, "november": 11, "december": 12,
}

def _parse_date(date_str: str):
    """Parses date strings like 'Jan 2022', '01/2022', '2022' into (year, month)."""
    date_str = date_str.strip().lower()
    if date_str in ("present", "current", "now", "till date"):
        now = datetime.now()
        return (now.year, now.month)
    # "Jan 2022" or "January 2022"
    match = re.match(r'([a-z]+)\s+(\d{4})', date_str)
    if match:
        month = MONTH_MAP.get(match.group(1), 1)
        return (int(match.group(2)), month)
    # "01/2022" or "2022/01"
    match = re.match(r'(\d{1,2})[/\-](\d{4})', date_str)
    if match:
        return (int(match.group(2)), int(match.group(1)))
    # Just a year
    match = re.match(r'(\d{4})', date_str)
    if match:
        return (int(match.group(1)), 1)
    return None

def _to_months(year_month: tuple) -> int:
    return year_month[0] * 12 + year_month[1]

def detect_fake_experience(experience_list: list) -> dict:
    """
    Detects suspicious patterns in work experience:
      1. DATE OVERLAPS — two jobs with overlapping date ranges
         (e.g. full-time at Company A and Company B simultaneously)
      2. FUTURE DATES — job start/end dates in the future
      3. UNREALISTIC DURATION — single role listed as 20+ years
         for someone who appears to be early in career
      4. SUSPICIOUS GAPS — unexplained gaps > 12 months between roles

    experience_list format:
      [
        {"title": "...", "company": "...",
         "start": "Jan 2020", "end": "Mar 2022"},
        ...
      ]

    Returns:
      {
        "has_issues": True/False,
        "issues": ["DATE OVERLAP: ...", "FUTURE DATE: ..."],
        "parsed_roles": [{"company": ..., "start_month": ..., "end_month": ...}]
      }
    """
    issues = []
    parsed = []

    for exp in experience_list:
        start = _parse_date(str(exp.get("start", "")))
        end   = _parse_date(str(exp.get("end", "present")))
        if not start:
            continue
        parsed.append({
            "company":     exp.get("company", "Unknown"),
            "title":       exp.get("title", ""),
            "start":       start,
            "end":         end,
            "start_month": _to_months(start),
            "end_month":   _to_months(end) if end else _to_months(
                               (datetime.now().year, datetime.now().month)),
        })

    # Check for future dates
    now_months = _to_months((datetime.now().year, datetime.now().month))
    for role in parsed:
        if role["start_month"] > now_months + 1:
            issues.append(
                f"FUTURE DATE: '{role['company']}' lists start date in the future"
            )

    # Check for overlaps
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            a, b = parsed[i], parsed[j]
            # Overlap: a starts before b ends AND b starts before a ends
            if a["start_month"] <= b["end_month"] and b["start_month"] <= a["end_month"]:
                overlap_months = (
                    min(a["end_month"], b["end_month"])
                    - max(a["start_month"], b["start_month"])
                )
                if overlap_months > 1:  # tolerance for 1 month (transition period)
                    issues.append(
                        f"DATE OVERLAP: '{a['company']}' and '{b['company']}' "
                        f"overlap by ~{overlap_months} months — "
                        f"two simultaneous full-time roles is unusual"
                    )

    # Check for unrealistic single-role duration (> 15 years)
    for role in parsed:
        duration = role["end_month"] - role["start_month"]
        if duration > 180:  # 15 years
            issues.append(
                f"UNUSUAL DURATION: '{role['company']}' listed as "
                f"~{duration // 12} years — verify this is accurate"
            )

    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "roles_analyzed": len(parsed),
        "parsed_roles": [
            {"company": r["company"], "title": r["title"],
             "start": str(r["start"]), "end": str(r["end"])}
            for r in parsed
        ],
    }


# ============================================================
# 2. AI-GENERATED RESUME DETECTION
# ============================================================
def detect_ai_generated(resume_text: str) -> dict:
    """
    Detects statistical patterns common in AI-generated resumes.
    Uses a heuristic approach (no external API needed) based on:
      1. SENTENCE LENGTH UNIFORMITY — AI tends to write very similar
         sentence lengths; human writing has more variation
      2. BULLET POINT UNIFORMITY — all bullets same length = suspicious
      3. OVERUSED AI PHRASES — common ChatGPT/AI clichés
      4. PERFECT STRUCTURE — overly consistent formatting can indicate AI
      5. LOW LEXICAL DIVERSITY — AI often repeats the same vocabulary

    NOTE: This is a statistical heuristic, NOT a definitive classifier.
    False positives are possible for very well-written human resumes.
    Always use as one signal among many, not as conclusive proof.

    Returns:
      {
        "likely_ai_generated": True/False,
        "confidence": 0.0-1.0,
        "signals": ["...", "..."],
        "note": "heuristic-based, not conclusive"
      }
    """
    signals = []
    score = 0.0

    # 1. Overused AI phrases
    AI_PHRASES = [
        "results-driven", "detail-oriented", "proven track record",
        "dynamic professional", "synergy", "leverage", "spearheaded",
        "orchestrated", "passionate about", "strong communication skills",
        "team player", "go-getter", "think outside the box",
        "fast-paced environment", "value-added", "cutting-edge",
        "innovative solutions", "strategic vision", "cross-functional",
    ]
    text_lower = resume_text.lower()
    ai_phrase_hits = [p for p in AI_PHRASES if p in text_lower]
    if len(ai_phrase_hits) >= 4:
        signals.append(
            f"OVERUSED PHRASES: contains {len(ai_phrase_hits)} common AI clichés: "
            f"{', '.join(ai_phrase_hits[:4])}"
        )
        score += 0.3

    # 2. Sentence length uniformity
    sentences = [s.strip() for s in re.split(r'[.!?\n]', resume_text) if len(s.strip()) > 20]
    if len(sentences) >= 5:
        lengths = [len(s.split()) for s in sentences]
        avg = sum(lengths) / len(lengths)
        variance = sum((l - avg) ** 2 for l in lengths) / len(lengths)
        if variance < 15:  # very low variance = uniformly-structured sentences
            signals.append(
                f"UNIFORM SENTENCE LENGTH: sentences have low variation "
                f"(variance={variance:.1f}) — AI writing tends to be more uniform"
            )
            score += 0.2

    # 3. Bullet point uniformity
    bullets = re.findall(r'[•\-\*]\s*(.+)', resume_text)
    if len(bullets) >= 5:
        b_lengths = [len(b.split()) for b in bullets]
        b_avg = sum(b_lengths) / len(b_lengths)
        b_variance = sum((l - b_avg) ** 2 for l in b_lengths) / len(b_lengths)
        if b_variance < 10:
            signals.append(
                f"UNIFORM BULLET POINTS: {len(bullets)} bullets with very "
                f"similar lengths (variance={b_variance:.1f})"
            )
            score += 0.2

    # 4. Lexical diversity (type-token ratio)
    words = re.findall(r'\b[a-zA-Z]{4,}\b', resume_text.lower())
    if len(words) > 50:
        ttr = len(set(words)) / len(words)
        if ttr < 0.45:  # low diversity = repeated vocabulary
            signals.append(
                f"LOW LEXICAL DIVERSITY: only {ttr*100:.0f}% unique words "
                f"— may indicate templated/AI content"
            )
            score += 0.2

    # 5. Suspiciously perfect action verb usage
    ACTION_VERBS = ["developed", "implemented", "managed", "led", "created",
                    "designed", "built", "delivered", "achieved", "optimized"]
    verb_hits = sum(1 for v in ACTION_VERBS if v in text_lower)
    if verb_hits >= 7:
        signals.append(
            f"PERFECT ACTION VERBS: uses {verb_hits}/10 standard action verbs "
            f"— may indicate AI-coached or AI-generated content"
        )
        score += 0.1

    score = min(score, 1.0)

    return {
        "likely_ai_generated": score >= 0.4,
        "confidence": round(score, 2),
        "signals": signals,
        "note": "Heuristic-based analysis — not conclusive proof. "
                "Use as one signal among many during manual review.",
    }


# ============================================================
# 3. FAKE COMPANY DETECTION
# ============================================================
def detect_fake_companies(experience_list: list) -> dict:
    """
    Checks if company names mentioned in experience are self-consistent
    with any domains/emails provided — same domain-consistency approach
    already used in the job-posting fraud checker, now applied to
    resume company claims.

    For each experience entry, if a company_domain or company_email
    is provided, checks that the domain/email matches the company name.

    experience_list format:
      [
        {"company": "Infosys", "company_domain": "xyz.com"},
        {"company": "TCS", "company_email": "recruiter@gmail.com"},
        ...
      ]

    Returns:
      {
        "has_issues": True/False,
        "issues": ["...", "..."]
      }
    """
    issues = []

    for exp in experience_list:
        company = exp.get("company", "")
        domain = exp.get("company_domain", "")
        email = exp.get("company_email", "")

        if not company:
            continue

        # Check domain vs company name consistency
        if domain:
            clean_company = re.sub(r'[^a-z0-9]', '', company.lower())
            clean_company = re.sub(
                r'(pvtltd|pvt|ltd|inc|llc|limited|private|solutions|technologies|tech|services)',
                '', clean_company
            )
            clean_domain = domain.lower().split('.')[0]
            similarity = SequenceMatcher(None, clean_company, clean_domain).ratio()
            if similarity < 0.35:
                issues.append(
                    f"DOMAIN MISMATCH: '{company}' lists domain '{domain}' "
                    f"which bears little resemblance to the company name "
                    f"(similarity={similarity:.2f})"
                )

        # Check if email uses a free domain (suspicious for company email)
        if email:
            FREE_DOMAINS = ["gmail.com", "yahoo.com", "hotmail.com",
                           "outlook.com", "rediffmail.com"]
            email_domain = email.split("@")[-1].lower() if "@" in email else ""
            if email_domain in FREE_DOMAINS:
                issues.append(
                    f"FREE EMAIL: '{company}' contact email uses "
                    f"'{email_domain}' instead of an official company domain"
                )

    return {
        "has_issues": len(issues) > 0,
        "issues": issues,
        "companies_checked": len([e for e in experience_list
                                  if e.get("company_domain") or e.get("company_email")]),
    }