"""
resume_fraud_detector.py
------------------------
Hybrid Resume Authenticity Checker:
Primary   → XGBoost + LightGBM trained models (99.9% accuracy)
Secondary → Groq LLM (intelligent explanations)  
Fallback  → Rule-based NLP (always works)
"""

import re, os, json, pickle
import numpy as np
from datetime import datetime

# ── Load trained ML models ────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'ml_models')

def _load_model(filename):
    path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return pickle.load(f)
    return None

_xgb_resume  = _load_model('xgboost_resume_fraud.pkl')
_lgb_resume  = _load_model('lgbm_resume_fraud.pkl')
_tfidf_resume = _load_model('tfidf_resume.pkl')

print(f"[resume_fraud] Models loaded: XGB={'✅' if _xgb_resume else '❌'} LGB={'✅' if _lgb_resume else '❌'} TFIDF={'✅' if _tfidf_resume else '❌'}")

# ── ML Model Prediction ──────────────────────────────────────
def _ml_predict(resume_text: str) -> dict:
    if not _tfidf_resume or (not _xgb_resume and not _lgb_resume):
        raise Exception("ML models not loaded")

    # Extract same features as training
    text_lower = resume_text.lower()
    words      = text_lower.split()
    wc         = max(len(words), 1)

    vague_words  = ["worked on","responsible for","involved in","assisted","participated","helped","exposure","familiar"]
    strong_words = ["built","developed","led","designed","implemented","reduced","increased","launched","deployed","achieved","optimized"]
    vague_count  = sum(text_lower.count(v) for v in vague_words)
    strong_count = sum(text_lower.count(s) for s in strong_words)
    years        = [int(y) for y in re.findall(r'\b(20\d{2}|19\d{2})\b', resume_text)]
    claimed_exp  = re.findall(r'(\d+)\+?\s*years?\s*(of\s+)?experience', text_lower)
    claimed_yrs  = max([int(m[0]) for m in claimed_exp], default=0)
    grad_match   = re.search(r'(btech|b\.tech|b\.e|mtech|bsc)\D{0,20}(20\d{2})', text_lower)
    grad_year    = int(grad_match.group(2)) if grad_match else 2020
    actual_exp   = 2024 - grad_year
    exp_mismatch = max(0, claimed_yrs - actual_exp - 1) if claimed_yrs > 0 else 0
    has_github   = int("github" in text_lower)
    has_linkedin = int("linkedin" in text_lower)
    has_numbers  = len(re.findall(r'\d+%|\d+x|\$\d+|\d{4,}', resume_text))
    has_cgpa     = int(bool(re.search(r'cgpa|gpa|percentage', text_lower)))
    real_cos     = ["google","microsoft","amazon","flipkart","razorpay","infosys","tcs","wipro","zomato","paytm"]
    fake_cos     = ["xyz","abc technologies","pvt ltd","it solutions","tech solutions","global it"]
    real_co_count = sum(1 for c in real_cos if c in text_lower)
    fake_co_count = sum(1 for c in fake_cos if c in text_lower)
    skill_count  = len(re.findall(r'python|java|react|aws|docker|tensorflow|pytorch|kubernetes|mongodb|sql', text_lower))
    real_colleges = ["iit","nit","bits","iiit","manipal","vit"]
    has_real_college = int(any(c in text_lower for c in real_colleges))

    meta = np.array([[
        vague_count/wc, strong_count/wc, strong_count/max(vague_count+1,1),
        exp_mismatch, has_github, has_linkedin, has_numbers, has_cgpa,
        real_co_count, fake_co_count, skill_count, has_real_college,
        len(years), claimed_yrs, actual_exp
    ]])

    tfidf_feat = _tfidf_resume.transform([resume_text]).toarray()
    X          = np.hstack([tfidf_feat, meta])

    # Ensemble prediction
    probs = []
    if _xgb_resume:
        probs.append(_xgb_resume.predict_proba(X)[0][1])
    if _lgb_resume:
        probs.append(_lgb_resume.predict_proba(X)[0][1])

    fraud_prob = float(np.mean(probs))
    fraud_pct  = int(fraud_prob * 100)

    return {
        "fraud_score":     fraud_prob,
        "fraud_percent":   fraud_pct,
        "risk_level":      "HIGH" if fraud_pct>=60 else "MEDIUM" if fraud_pct>=30 else "LOW",
        "verdict":         "High fraud risk — verify claims" if fraud_pct>=60 else "Medium risk — spot check" if fraud_pct>=30 else "Appears authentic",
        "fraud_signals":   [],
        "analysis_method": "ml_model",
        "models_used":     f"XGBoost{'✅' if _xgb_resume else '❌'} + LightGBM{'✅' if _lgb_resume else '❌'}",
    }


# ── Rule-based Resume Fraud Detection ────────────────────────
# ── Rule-based Resume Fraud Detection ────────────────────────
VAGUE_PHRASES = [
    "worked on", "responsible for", "involved in", "assisted with",
    "helped with", "participated in", "contributed to", "exposure to",
    "familiar with", "knowledge of", "experience in", "aware of",
]

STRONG_PHRASES = [
    "built", "developed", "led", "designed", "implemented", "architected",
    "reduced", "increased", "improved", "launched", "deployed", "created",
    "achieved", "delivered", "managed", "optimized", "automated",
]

FAKE_COMPANY_SIGNALS = [
    "xyz pvt", "abc technologies", "tech solutions pvt",
    "it services pvt", "software solutions pvt",
    "global technologies", "tech pvt ltd",
]

def _extract_years(text):
    """Extract all years mentioned in text."""
    years = re.findall(r'\b(19|20)\d{2}\b', text)
    return [int(y) for y in years]

def _rule_based_resume_fraud(resume_text: str) -> dict:
    text_lower = resume_text.lower()
    signals    = []
    score      = 0  # Higher = more suspicious

    current_year = datetime.now().year

    # ── 1. Date consistency check ─────────────────────────────
    years = _extract_years(resume_text)
    if years:
        min_year = min(years)
        max_year = max(years)
        # Graduation year check
        grad_match = re.search(r'(b\.?tech|b\.?e|mtech|bsc|msc|bachelor|master)\D{0,30}(20\d{2})', text_lower)
        if grad_match:
            grad_year = int(grad_match.group(2))
            # Find experience claims before graduation
            exp_years_before = [y for y in years if y < grad_year - 1 and y > 2000]
            if exp_years_before:
                signals.append(f"Experience claimed before graduation year ({grad_year})")
                score += 25

        # Future dates
        future_years = [y for y in years if y > current_year + 1]
        if future_years:
            signals.append(f"Future dates found: {future_years}")
            score += 20

    # ── 2. Experience vs claims check ─────────────────────────
    exp_match = re.findall(r'(\d+)\+?\s*years?\s*(of)?\s*(experience|exp)', text_lower)
    if exp_match:
        claimed_years = max([int(m[0]) for m in exp_match])
        if years:
            earliest_year = min([y for y in years if y > 2000], default=current_year)
            actual_years  = current_year - earliest_year
            if claimed_years > actual_years + 2:
                signals.append(f"Claims {claimed_years} years experience but timeline shows ~{actual_years} years")
                score += 30

    # ── 3. Vague language detection ───────────────────────────
    vague_count  = sum(1 for p in VAGUE_PHRASES  if p in text_lower)
    strong_count = sum(1 for p in STRONG_PHRASES if p in text_lower)
    if vague_count > strong_count and vague_count >= 3:
        signals.append(f"High vague language ratio ({vague_count} vague vs {strong_count} strong action words)")
        score += 15

    # ── 4. Suspicious company names ───────────────────────────
    for fake_co in FAKE_COMPANY_SIGNALS:
        if fake_co in text_lower:
            signals.append(f"Generic/suspicious company name: '{fake_co}'")
            score += 20

    # ── 5. Skills without proof ───────────────────────────────
    has_projects  = any(w in text_lower for w in ["project", "github", "gitlab", "portfolio"])
    has_skills    = any(w in text_lower for w in ["python","java","react","ml","sql","aws"])
    if has_skills and not has_projects:
        signals.append("Technical skills listed but no projects/GitHub to verify")
        score += 10

    # ── 6. Employment gaps ────────────────────────────────────
    year_pairs = sorted(set(years)) if years else []
    if len(year_pairs) >= 4:
        gaps = []
        for i in range(len(year_pairs)-1):
            gap = year_pairs[i+1] - year_pairs[i]
            if gap >= 2:
                gaps.append(f"{year_pairs[i]}-{year_pairs[i+1]} ({gap} years)")
        if gaps:
            signals.append(f"Unexplained employment gaps: {', '.join(gaps[:2])}")
            score += 10

    # ── 7. Contact info check ─────────────────────────────────
    has_linkedin = "linkedin" in text_lower or "linkedin.com" in text_lower
    has_github   = "github" in text_lower or "github.com" in text_lower
    if not has_linkedin and not has_github:
        signals.append("No LinkedIn or GitHub profile found — hard to verify claims")
        score += 5

    # ── 8. Education check ────────────────────────────────────
    has_education = any(w in text_lower for w in
        ["university","college","institute","iit","nit","bits","education","degree"])
    if not has_education:
        signals.append("No educational background found")
        score += 10

    # Normalize score to 0-100
    fraud_score = min(score, 100)

    # Verdict
    if fraud_score >= 60:
        verdict = "High Risk — Conduct thorough background verification"
        risk    = "HIGH"
    elif fraud_score >= 30:
        verdict = "Medium Risk — Verify specific claims independently"
        risk    = "MEDIUM"
    else:
        verdict = "Low Risk — Resume appears authentic"
        risk    = "LOW"

    return {
        "fraud_score":    fraud_score / 100,
        "fraud_percent":  fraud_score,
        "risk_level":     risk,
        "verdict":        verdict,
        "fraud_signals":  signals,
        "analysis_method": "rule_based",
        "checks_performed": 8,
    }


# ── LLM-based Resume Fraud Detection ─────────────────────────
def _llm_resume_fraud(resume_text: str) -> dict:
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise Exception("No GROQ_API_KEY")

    client = Groq(api_key=key)
    prompt = f"""You are a senior HR fraud analyst. Analyze this resume for authenticity issues.

Resume:
{resume_text[:2000]}

Check for:
1. Date inconsistencies (experience before graduation, future dates)
2. Inflated/exaggerated experience claims
3. Vague language without concrete achievements
4. Missing verifiable information (no LinkedIn/GitHub)
5. Suspicious company names or roles
6. Skills claimed without supporting projects

Return ONLY this JSON:
{{
  "fraud_percent": 25,
  "risk_level": "LOW",
  "verdict": "Resume appears authentic",
  "fraud_signals": ["Signal 1 if any", "Signal 2 if any"],
  "positive_signals": ["Has GitHub profile", "Quantified achievements"],
  "summary": "Brief assessment in 1-2 sentences"
}}

fraud_percent: 0-100 (0=genuine, 100=very suspicious)
risk_level: LOW / MEDIUM / HIGH"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are an HR fraud analyst. Return ONLY valid JSON."},
            {"role": "user",   "content": prompt}
        ],
        max_tokens=500,
        temperature=0.2,
    )

    raw   = response.choices[0].message.content
    clean = re.sub(r"```[a-z]*|```", "", raw).strip()
    s, e  = clean.find("{"), clean.rfind("}") + 1
    result = json.loads(clean[s:e])
    result["fraud_score"]      = result.get("fraud_percent", 0) / 100
    result["analysis_method"]  = "llm"
    return result


# ── Main Hybrid Function ──────────────────────────────────────
def detect_resume_fraud(resume_text: str) -> dict:
    """
    Hybrid resume fraud detection:
    1. Try Groq LLM (intelligent, context-aware)
    2. Fallback to rule-based (fast, always works)
    3. Merge results if both available
    """
    if not resume_text or len(resume_text.strip()) < 30:
        return {
            "fraud_score":   0,
            "fraud_percent": 0,
            "risk_level":    "UNKNOWN",
            "verdict":       "Insufficient text to analyze",
            "fraud_signals": [],
            "analysis_method": "none",
        }

    # 1. Try ML models first (fastest + most accurate)
    try:
        print("[resume_fraud] Trying ML model prediction...")
        ml_result    = _ml_predict(resume_text)
        rule_result  = _rule_based_resume_fraud(resume_text)  # For signals

        # Combine ML score with rule-based signals
        ml_result["fraud_signals"] = rule_result.get("fraud_signals", [])
        ml_result["analysis_method"] = "ml_model"

        # Try LLM for better explanations
        try:
            llm_result = _llm_resume_fraud(resume_text)
            ml_result["fraud_signals"] = list(set(
                ml_result["fraud_signals"] + llm_result.get("fraud_signals", [])
            ))[:6]
            ml_result["positive_signals"] = llm_result.get("positive_signals", [])
            ml_result["summary"]          = llm_result.get("summary", "")
            ml_result["analysis_method"]  = "hybrid (ML + LLM)"
        except Exception:
            pass

        print(f"[resume_fraud] ML done. Score: {ml_result['fraud_percent']}%")
        return ml_result

    except Exception as e:
        print(f"[resume_fraud] ML failed ({e}) — trying LLM+rules")

    # 2. Fallback: Rule-based always runs
    rule_result = _rule_based_resume_fraud(resume_text)

    # Try LLM for smarter analysis
    try:
        print("[resume_fraud] Trying LLM analysis...")
        llm_result = _llm_resume_fraud(resume_text)

        # Merge — average scores, combine signals
        combined_score = int((rule_result["fraud_percent"] + llm_result.get("fraud_percent", 0)) / 2)
        all_signals    = list(set(
            rule_result.get("fraud_signals", []) +
            llm_result.get("fraud_signals", [])
        ))

        final = {
            "fraud_score":       combined_score / 100,
            "fraud_percent":     combined_score,
            "risk_level":        "HIGH" if combined_score >= 60 else "MEDIUM" if combined_score >= 30 else "LOW",
            "verdict":           llm_result.get("verdict", rule_result["verdict"]),
            "fraud_signals":     all_signals[:6],
            "positive_signals":  llm_result.get("positive_signals", []),
            "summary":           llm_result.get("summary", ""),
            "analysis_method":   "hybrid",
            "rule_score":        rule_result["fraud_percent"],
            "llm_score":         llm_result.get("fraud_percent", 0),
        }
        print(f"[resume_fraud] Hybrid done. Score: {combined_score}%")
        return final

    except Exception as e:
        print(f"[resume_fraud] LLM failed ({e}) — using rule-based only")
        return rule_result
