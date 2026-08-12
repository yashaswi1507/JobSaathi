"""
resume_features.py
-------------------
3 non-LLM resume features:
  1. Grammar Fix          — LanguageTool (free, local Java server)
  2. Keyword Optimization — missing keywords from JD vs resume
  3. Keyword Stuffing     — density-based detection (recruiter-side)

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\resume_features.py

DEPENDENCIES (add to requirements.txt):
  language_tool_python   — pip install language_tool_python
  (First run downloads LanguageTool JAR ~200MB, then works offline)
  Java JRE 8+ must be installed on the system.
"""

import re
from collections import Counter


# ============================================================
# 1. GRAMMAR FIX
# ============================================================
def check_grammar(text: str) -> dict:
    """
    Checks grammar of resume/cover-letter text using LanguageTool
    (free, runs locally via Java, no API key needed).

    Returns:
      {
        "issues": [
          {
            "message": "Use 'for' instead of 'since' with duration",
            "context": "...worked in python since 5 years...",
            "suggestions": ["for"],
            "offset": 30,
            "length": 5
          }
        ],
        "issue_count": 3,
        "corrected_text": "..."   # auto-corrected version
      }

    NOTE: First call downloads ~200MB LanguageTool JAR (one-time).
    Subsequent calls are instant (local server).
    """
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(text)

        issues = []
        for m in matches:
            issues.append({
                "message": m.message,
                "context": m.context.strip(),
                "suggestions": m.replacements[:3],
                "offset": m.offset,
                "length": getattr(m, 'errorLength', getattr(m, 'error_length', 0)),
                "rule_id": m.ruleId,
            })

        corrected = language_tool_python.utils.correct(text, matches)

        return {
            "issues": issues,
            "issue_count": len(issues),
            "corrected_text": corrected,
        }

    except ImportError:
        return {
            "issues": [],
            "issue_count": 0,
            "corrected_text": text,
            "error": "language_tool_python not installed. Run: pip install language_tool_python"
        }
    except Exception as e:
        return {
            "issues": [],
            "issue_count": 0,
            "corrected_text": text,
            "error": f"Grammar check failed: {str(e)}"
        }


# ============================================================
# 2. KEYWORD OPTIMIZATION
# ============================================================
def get_keyword_optimization(resume_text: str, job_description: str) -> dict:
    """
    Compares resume against job description and returns:
      - missing_keywords: important JD words not in resume
      - present_keywords: JD words already in resume
      - optimization_score: % of JD keywords covered
      - suggestions: specific phrases to add to resume

    This extends the existing ATS score by giving ACTIONABLE
    suggestions (which exact keywords to add) rather than just
    a percentage.
    """
    def extract_keywords(text: str, min_length: int = 4) -> set:
        text = text.lower()
        # Remove common stop words
        stop_words = {
            'with', 'this', 'that', 'have', 'will', 'from', 'they',
            'been', 'were', 'when', 'your', 'more', 'also', 'into',
            'some', 'than', 'then', 'over', 'such', 'very', 'just',
            'each', 'about', 'which', 'there', 'their', 'other',
            'would', 'these', 'those', 'after', 'while', 'should',
            'could', 'being', 'every', 'where', 'through', 'before',
        }
        words = re.findall(r'\b[a-zA-Z]{%d,}\b' % min_length, text)
        return {w for w in words if w not in stop_words}

    jd_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)

    # Also extract meaningful multi-word phrases from JD
    # (e.g. "machine learning", "project management", "data analysis")
    jd_phrases = set()
    jd_lower = job_description.lower()
    COMMON_PHRASES = [
        'machine learning', 'deep learning', 'data analysis', 'data science',
        'project management', 'team player', 'problem solving', 'communication skills',
        'attention to detail', 'software development', 'agile methodology',
        'rest api', 'cloud computing', 'version control', 'unit testing',
        'database management', 'object oriented', 'continuous integration',
        'natural language processing', 'computer vision', 'big data',
    ]
    for phrase in COMMON_PHRASES:
        if phrase in jd_lower:
            jd_phrases.add(phrase)

    resume_lower = resume_text.lower()
    missing_phrases = {p for p in jd_phrases if p not in resume_lower}
    present_phrases = {p for p in jd_phrases if p in resume_lower}

    missing_words = jd_keywords - resume_keywords
    present_words = jd_keywords & resume_keywords

    total_jd = len(jd_keywords) + len(jd_phrases)
    present_total = len(present_words) + len(present_phrases)
    score = round((present_total / total_jd * 100) if total_jd > 0 else 0, 1)

    # Sort missing keywords by frequency in JD (most-repeated = most important)
    jd_word_counts = Counter(re.findall(r'\b[a-zA-Z]{4,}\b', job_description.lower()))
    missing_sorted = sorted(
        missing_words,
        key=lambda w: jd_word_counts.get(w, 0),
        reverse=True
    )

    return {
        "optimization_score": score,
        "missing_keywords": missing_sorted[:15],       # top 15 most important
        "present_keywords": sorted(list(present_words))[:15],
        "missing_phrases": sorted(list(missing_phrases)),
        "present_phrases": sorted(list(present_phrases)),
        "suggestions": [
            f"Add '{kw}' to your resume — mentioned {jd_word_counts.get(kw,1)} time(s) in the JD"
            for kw in missing_sorted[:5]
        ] + [
            f"Include the phrase '{p}' — key requirement in this JD"
            for p in list(missing_phrases)[:3]
        ]
    }


# ============================================================
# 3. KEYWORD STUFFING DETECTION (Recruiter-side)
# ============================================================
def detect_keyword_stuffing(resume_text: str) -> dict:
    """
    RECRUITER-SIDE feature: detects when a candidate has
    artificially inflated their resume with repeated keywords
    (a common tactic to game ATS systems).

    Checks:
      1. Overall keyword density — any word appearing more than
         expected relative to resume length is suspicious
      2. Skill/tech-term repetition — same skill mentioned 3+
         times in a short resume is unusual
      3. Hidden text patterns — extremely short sentences that
         are just keyword lists (no verbs, no context)

    Returns:
      {
        "is_stuffed": True/False,
        "confidence": 0.0-1.0,
        "stuffed_keywords": ["python", "machine learning", ...],
        "reasons": ["'python' appears 8 times in 400 words", ...],
        "overall_density_score": 0.85
      }
    """
    words = re.findall(r'\b[a-zA-Z]{3,}\b', resume_text.lower())
    total_words = len(words)

    if total_words < 50:
        return {
            "is_stuffed": False,
            "confidence": 0.0,
            "stuffed_keywords": [],
            "reasons": ["Resume too short to analyze"],
            "overall_density_score": 0.0,
        }

    word_counts = Counter(words)

    # Stop words to exclude from density check
    stop_words = {
        'and', 'the', 'for', 'with', 'have', 'this', 'that', 'from',
        'are', 'was', 'will', 'has', 'had', 'been', 'not', 'but',
        'also', 'more', 'into', 'than', 'then', 'over', 'such',
        'very', 'just', 'each', 'they', 'when', 'your', 'all',
    }

    # Expected max frequency: ~2% of total words for any single term
    # (e.g. in a 500-word resume, seeing "python" 10+ times = stuffing)
    max_expected = max(3, int(total_words * 0.02))

    stuffed_keywords = []
    reasons = []

    for word, count in word_counts.most_common(30):
        if word in stop_words or len(word) < 4:
            continue
        if count > max_expected:
            stuffed_keywords.append(word)
            reasons.append(
                f"'{word}' appears {count} times in {total_words} words "
                f"(expected max ~{max_expected})"
            )

    # Check for keyword-list sentences (short, no verbs, just nouns)
    sentences = re.split(r'[.!\n]', resume_text)
    keyword_list_sentences = 0
    for sent in sentences:
        sent = sent.strip()
        words_in_sent = sent.split()
        if 2 <= len(words_in_sent) <= 6:
            # Very short sentence — check if it has any verb-like words
            has_verb = any(w.lower().endswith(('ed', 'ing', 'ize', 'ise', 'ify'))
                          for w in words_in_sent)
            if not has_verb:
                keyword_list_sentences += 1

    if keyword_list_sentences > 5:
        reasons.append(
            f"{keyword_list_sentences} very short keyword-list-style "
            f"sentences detected (no action verbs)"
        )

    # Density score: how "stuffed" is this resume overall
    # 0.0 = normal, 1.0 = heavily stuffed
    density_score = min(1.0, len(stuffed_keywords) / 5.0)

    is_stuffed = len(stuffed_keywords) >= 2 or density_score >= 0.4

    return {
        "is_stuffed": is_stuffed,
        "confidence": round(density_score, 2),
        "stuffed_keywords": stuffed_keywords[:10],
        "reasons": reasons[:5],
        "overall_density_score": round(density_score, 2),
    }


# ============================================================
# SELF-TEST
# ============================================================
if __name__ == "__main__":

    print("=== Test 1: Grammar Fix ===")
    sample = "I have worked in python since 5 years and done many project."
    result = check_grammar(sample)
    print(f"Issues found: {result['issue_count']}")
    for issue in result['issues'][:3]:
        print(f"  - {issue['message']}")
        if issue['suggestions']:
            print(f"    Suggest: {issue['suggestions'][0]}")
    if 'error' in result:
        print(f"  Note: {result['error']}")

    print()
    print("=== Test 2: Keyword Optimization ===")
    resume = "Experienced Python developer with SQL and machine learning skills."
    jd = "Looking for a Python engineer with deep learning, TensorFlow, machine learning, and data analysis experience. Must have REST API and cloud computing skills."
    result2 = get_keyword_optimization(resume, jd)
    print(f"Optimization score: {result2['optimization_score']}%")
    print(f"Missing keywords: {result2['missing_keywords'][:5]}")
    print(f"Missing phrases: {result2['missing_phrases']}")
    print(f"Suggestions:")
    for s in result2['suggestions'][:3]:
        print(f"  - {s}")

    print()
    print("=== Test 3: Keyword Stuffing Detection ===")
    stuffed_resume = """
    Python Python Python developer with Python skills.
    Machine learning machine learning machine learning expert.
    Data science data science data science professional.
    Python machine learning data science artificial intelligence.
    Python Python machine learning deep learning NLP.
    """
    normal_resume = """
    Experienced software engineer with 3 years of Python development.
    Built machine learning pipelines for e-commerce recommendations.
    Led a team of 4 engineers to deliver the data science platform on time.
    """
    r3_stuffed = detect_keyword_stuffing(stuffed_resume)
    r3_normal = detect_keyword_stuffing(normal_resume)
    print(f"Stuffed resume -> is_stuffed={r3_stuffed['is_stuffed']}, "
          f"confidence={r3_stuffed['confidence']}")
    print(f"  Keywords: {r3_stuffed['stuffed_keywords'][:5]}")
    print(f"Normal resume -> is_stuffed={r3_normal['is_stuffed']}, "
          f"confidence={r3_normal['confidence']}")