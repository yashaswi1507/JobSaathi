from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.schemas import FraudCheckRequest, FraudCheckResponse
from app.preprocessing import (
    clean_text, is_suspicious_salary, has_scam_keywords, missing_company_profile,
    is_unrealistic_salary, has_payment_request,
    check_email_signal, check_url_signal, check_phone_signal,
    check_html_signal, check_logo_signal, check_company_domain_consistency_signal,
    KNOWN_LOGO_PATHS,
)
import pickle
import numpy as np
import shap
from scipy.sparse import hstack, csr_matrix

router = APIRouter()

def _rule_based_score(job_desc: str, job_title: str = "", company: str = "", salary: str = "") -> float:
    """
    Strong rule-based fraud scoring when ML model is unavailable.
    Returns probability 0.0 - 1.0
    """
    text = f"{job_desc} {job_title} {company} {salary}".lower()
    score = 0.0

    # High risk signals
    HIGH = [
        "whatsapp", "registration fee", "joining fee", "deposit",
        "earn from home", "work from home earn", "no experience required",
        "daily payment", "weekly payment", "per day earn",
        "100% genuine", "guaranteed job", "immediate joining",
        "any graduate apply", "housewife welcome", "google pay", "phonepe",
        "paytm payment", "data entry", "copy paste", "form filling",
        "typing job", "earn money online", "part time earn",
        "50000 per month", "1 lakh per month", "unlimited earning",
        "no interview", "direct selection", "urgent requirement 500",
    ]
    # Medium risk signals
    MED = [
        "work from home", "wfh", "remote earn", "part time job",
        "freshers only", "no experience", "simple job", "easy job",
        "call now", "contact immediately", "limited seats",
        "apply fast", "hurry", "last date today",
    ]
    # Low risk signals (these are LEGIT indicators - reduce score)
    LEGIT = [
        "lpa", "per annum", "health insurance", "pf", "esic",
        "bachelor degree", "b.tech", "b.e.", "mba", "m.tech",
        "team collaboration", "agile", "scrum", "performance review",
        "code review", "system design", "aws certified",
    ]

    for kw in HIGH:
        if kw in text:
            score += 0.18

    for kw in MED:
        if kw in text:
            score += 0.08

    for kw in LEGIT:
        if kw in text:
            score -= 0.06

    # Extra signals
    if text.count("!") >= 3:    score += 0.10
    if text.count("₹") >= 2:    score += 0.08
    if len(company.strip()) < 3: score += 0.15
    if "pvt ltd" in text or "private limited" in text: score -= 0.05
    if any(d in text for d in ["naukri", "linkedin", "indeed", "glassdoor"]): score -= 0.10

    return round(min(max(score, 0.0), 0.95), 2)


# --- Load models lazily ---
fraud_model        = None   # primary (best fraud-recall model from training)
fraud_model_backup = None   # backup (2nd best — used for cross-check AND
                             # as the sole model if primary fails to load)
tfidf               = None
shap_explainer      = None  # SHAP explainer for the primary model (built once)
metadata_feature_names = [
    "suspicious_salary", "missing_profile", "scam_keywords",
    "duplicate_posting", "unrealistic_salary", "payment_request",
]

import os
import os

# fraud.py is at: backend/app/routes/fraud.py
# Find ml_models folder — search multiple locations
def _find_ml_dir():
    _f    = os.path.abspath(__file__)
    _routes = os.path.dirname(_f)
    _app    = os.path.dirname(_routes)
    _back   = os.path.dirname(_app)
    _root   = os.path.dirname(_back)
    candidates = [
        os.path.join(_app,  'ml_models'),   # backend/app/ml_models/ ← correct
        os.path.join(_back, 'ml_models'),   # backend/ml_models/
        os.path.join(_root, 'ml_models'),   # project/ml_models/
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]  # default

ML_DIR            = _find_ml_dir()
VECTORIZER_PATH   = os.path.join(ML_DIR, 'tfidf_vectorizer.pkl')
FRAUD_MODEL_PATH  = os.path.join(ML_DIR, 'xgboost_fraud_model.pkl')
BACKUP_MODEL_PATH = os.path.join(ML_DIR, 'fraud_model_backup.pkl')
print(f"[fraud] ML_DIR: {ML_DIR} | exists: {os.path.exists(ML_DIR)}")


# Weighted boosts for live-only rule checks (email/URL/phone). These
# signals can't be learned from EMSCAD training data (it has almost no
# real emails/phones, and its URLs are anonymized hashes — verified:
# 1 email, 0 phones, 0 real domains in 17,880 rows), so instead of
# being trained model features, they're applied as independent boosts
# on top of the model's prediction at request time. Multiple triggers
# stack additively rather than just OR-ing to a flat flag, so "all
# three present" is treated as meaningfully more suspicious than "just
# one" — capped at 1.0 since probability can't exceed that.
EMAIL_BOOST = 0.15
URL_BOOST   = 0.15
PHONE_BOOST = 0.10

# Boosts for the 3 advanced proof-of-concept signals (HTML, logo,
# domain-consistency). These are deliberately smaller than the core
# email/URL/phone boosts above, since these signals are less
# battle-tested (small synthetic logo database, HTML check only
# applies to a future browser-extension scenario, domain-consistency
# only catches obvious mismatches) — a moderate boost reflects
# meaningful-but-not-yet-fully-proven confidence.
HTML_BOOST           = 0.10
LOGO_BOOST            = 0.15
DOMAIN_MISMATCH_BOOST = 0.10



# ── LLM Explanation for Fraud Results ───────────────────────
def _llm_explain_fraud(job_text: str, fraud_score: float, signals: list) -> dict:
    try:
        import os
        from groq import Groq
        key = os.environ.get("GROQ_API_KEY", "")
        if not key or fraud_score < 0.3:
            return {}
        client = Groq(api_key=key)
        signals_text = ", ".join(signals[:5]) if signals else "Multiple suspicious patterns"
        prompt = f"""Job has {int(fraud_score*100)}% fraud probability. Signals: {signals_text}
Job: {job_text[:400]}
In 2 sentences explain WHY this looks fraudulent to a job seeker. Plain text only."""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}],
            max_tokens=120, temperature=0.3,
        )
        return {"llm_explanation": response.choices[0].message.content.strip()}
    except Exception:
        return {}


def load_models():
    """
    Loads the primary model, the backup model, and the shared vectorizer.
    Also builds a SHAP TreeExplainer for the primary model, used to
    surface which features actually drove a given prediction.
    If the PRIMARY model fails to load (corrupt file, missing file,
    version mismatch, etc.), this does NOT crash the app — it logs a
    warning and continues with backup-only mode. The backup model is
    expected to always load successfully; if even that fails, the
    exception is raised, since at that point fraud checking genuinely
    cannot run.
    """
    global fraud_model, fraud_model_backup, tfidf, shap_explainer

    if tfidf is None:
        with open(VECTORIZER_PATH, 'rb') as f:
            tfidf = pickle.load(f)

    if fraud_model is None:
        try:
            with open(FRAUD_MODEL_PATH, 'rb') as f:
                fraud_model = pickle.load(f)
        except Exception as e:
            print(f"[fraud.py] WARNING: primary model failed to load ({e}). "
                  f"Falling back to backup-only mode.")
            fraud_model = False  # sentinel: "tried and failed", not "not yet tried"

    if fraud_model_backup is None:
        with open(BACKUP_MODEL_PATH, 'rb') as f:
            fraud_model_backup = pickle.load(f)

    if shap_explainer is None and fraud_model is not False:
        try:
            # TreeExplainer works for LightGBM/XGBoost/RandomForest/
            # ExtraTrees/GradientBoosting/CatBoost — i.e. every model our
            # auto-select pipeline can choose as primary. If the primary
            # ever ends up being something TreeExplainer doesn't support
            # (shouldn't happen given our candidate list, but just in
            # case), explanations are skipped rather than crashing the
            # whole fraud check over a missing "why" field.
            shap_explainer = shap.TreeExplainer(fraud_model)
        except Exception as e:
            print(f"[fraud.py] WARNING: could not build SHAP explainer "
                  f"({e}). Explanations will be skipped, predictions "
                  f"will still work normally.")
            shap_explainer = False


def get_fraud_probability(features):
    """
    Returns (probability, mode_used) where mode_used is one of:
      "ensemble"        -> both models worked, probability is their average
      "backup_only"      -> primary failed (at load time or at predict time),
                            backup model's probability used alone
    """
    global fraud_model, fraud_model_backup

    backup_prob = float(fraud_model_backup.predict_proba(features)[0][1])

    if fraud_model is False:
        return backup_prob, "backup_only"

    try:
        primary_prob = float(fraud_model.predict_proba(features)[0][1])
    except Exception as e:
        print(f"[fraud.py] WARNING: primary model failed during prediction "
              f"({e}). Using backup model only for this request.")
        return backup_prob, "backup_only"

    combined_prob = (primary_prob + backup_prob) / 2
    return combined_prob, "ensemble"


def get_shap_explanation(features, top_n=3):
    """
    Returns the top_n features that contributed most toward the
    fraud prediction for THIS specific posting, e.g.
        [{"feature": "missing_profile", "impact": "increases fraud risk"},
         {"feature": "registration", "impact": "increases fraud risk"}]
    Falls back to an empty list (rather than crashing) if SHAP couldn't
    be built for the loaded primary model, or if explanation fails for
    any other reason on this particular input.
    """
    global shap_explainer, tfidf

    if not shap_explainer:
        return []

    try:
        tfidf_feature_names = tfidf.get_feature_names_out().tolist()
        all_feature_names = tfidf_feature_names + metadata_feature_names
        num_tfidf = len(tfidf_feature_names)

        features_dense = features.toarray()
        shap_values = shap_explainer.shap_values(features_dense)

        if isinstance(shap_values, list):
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            sv = shap_values[0]

        contributions = []
        for i, (name, val) in enumerate(zip(all_feature_names, sv)):
            if val <= 0:
                continue  # only keep features pushing TOWARD fraud
            if i >= num_tfidf:
                # This is one of the 6 binary metadata features — only
                # report it if it's actually TRIGGERED (value 1), not
                # just because SHAP assigned it a positive contribution
                # while it was 0 (which can happen due to tree-interaction
                # effects and would be a confusing "reason" to show a user
                # for a flag that wasn't even raised on their input).
                if features_dense[0][i] == 0:
                    continue
            contributions.append((name, val))

        contributions.sort(key=lambda x: x[1], reverse=True)

        return [
            {"feature": name, "impact": "increases fraud risk", "weight": round(float(val), 4)}
            for name, val in contributions[:top_n]
        ]
    except Exception as e:
        print(f"[fraud.py] WARNING: SHAP explanation failed for this "
              f"request ({e}). Continuing without explanation.")
        return []


# --- Check job posting for fraud ---
@router.post("/check", response_model=FraudCheckResponse)
def check_fraud(data: FraudCheckRequest):
    load_models()                                      # load only when needed

    full_text = f"{data.job_description} {data.company_profile or ''}"

    # --- 6 TRAINABLE metadata flags (matches notebooks_09_fraud_model_full_signals.py) ---
    suspicious_salary  = is_suspicious_salary(data.salary_range)
    scam_words          = has_scam_keywords(data.job_description)
    missing_profile      = missing_company_profile(data.company_profile)
    unrealistic_salary   = is_unrealistic_salary(data.salary_range)
    payment_request       = has_payment_request(data.job_description)
    # duplicate_posting needs a corpus of prior postings to compare
    # against (see check_duplicate_signal_live in preprocessing_v2.py).
    # Without a history table wired in here yet, default to 0 — this
    # is a known gap to close once Day 15 (history tracking) exists.
    duplicate_posting = 0

    # clean and convert text to TF-IDF features
    clean_desc    = clean_text(data.job_description)
    text_features = tfidf.transform([clean_desc])      # 500 features

    # combine text + 6 metadata = 506 features (matches training script)
    expected = fraud_model_backup.n_features_in_
    tfidf_size = text_features.shape[1]
    meta_size = expected - tfidf_size
    if meta_size == 3:
        meta = np.array([[suspicious_salary, missing_profile, scam_words]])
    else:
        meta = np.array([[suspicious_salary, missing_profile, scam_words,duplicate_posting, unrealistic_salary, payment_request]])
    features = hstack([text_features, csr_matrix(meta)])

    # predict fraud probability — combines primary + backup, or falls
    # back to backup-only automatically if the primary model fails
    try:
        base_prob, mode_used = get_fraud_probability(features)
    except Exception:
        base_prob = _rule_based_score(
            data.job_description, data.job_title or "",
            data.company_profile or "", data.salary_range or ""
        )
        mode_used = "rule_based_fallback" 

    # --- LIVE-ONLY rule checks (email/URL/phone) — NOT trained model
    # features (EMSCAD has almost no real emails/phones/URLs to learn
    # from), applied as independent weighted boosts on top of the
    # model's prediction instead. ---
    email_flag, email_detail = check_email_signal(full_text)
    url_flag, url_detail     = check_url_signal(full_text)
    phone_flag, phone_detail = check_phone_signal(full_text)

    rule_boost = (
        (EMAIL_BOOST if email_flag else 0)
        + (URL_BOOST if url_flag else 0)
        + (PHONE_BOOST if phone_flag else 0)
    )

    # --- ADVANCED proof-of-concept signals (HTML/logo/domain) — only
    # run when the relevant optional input was actually provided.
    # Each safely returns (0, []) when its input is absent, so these
    # are always safe to call regardless of what the request included. ---
    html_flag, html_details = check_html_signal(data.html_content)
    logo_flag, logo_details = check_logo_signal(data.logo_path, KNOWN_LOGO_PATHS)
    domain_flag, domain_details = check_company_domain_consistency_signal(
        data.company_name, data.company_domain
    )

    advanced_boost = (
        (HTML_BOOST if html_flag else 0)
        + (LOGO_BOOST if logo_flag else 0)
        + (DOMAIN_MISMATCH_BOOST if domain_flag else 0)
    )

    prob = min(base_prob + rule_boost + advanced_boost, 1.0)

    advanced_signals = []
    for flag, details, signal_name in [
        (html_flag, html_details, "html_hidden_link"),
        (logo_flag, logo_details, "logo_match"),
        (domain_flag, domain_details, "domain_mismatch"),
    ]:
        if details:  # only report signals that actually had something to say
            advanced_signals.append({
                "signal": signal_name,
                "flagged": bool(flag),
                "details": details,
            })

    # SHAP explanation — top contributing features for THIS prediction,
    # straight from the trained model (separate from the rule-based
    # reasons list below, which covers metadata flags + live rules).
    shap_explanation = get_shap_explanation(features, top_n=3)

    reasons = []
    if missing_profile:    reasons.append("Missing company profile")
    if suspicious_salary:  reasons.append("Salary not specified")
    if unrealistic_salary: reasons.append("Unrealistic salary for stated time period")
    if payment_request:    reasons.append("Posting asks for an upfront payment/fee")
    if scam_words:          reasons.append("Scam keywords detected")
    if email_flag:          reasons.append(email_detail)
    if url_flag:            reasons.append(url_detail)
    if phone_flag:          reasons.append(phone_detail)
    if html_flag:            reasons.extend(html_details)
    if logo_flag:            reasons.extend(logo_details)
    if domain_flag:          reasons.extend(domain_details)
    if base_prob > 0.7:     reasons.append("Suspicious job description language")
    if mode_used == "backup_only":
        reasons.append("Note: primary model unavailable, backup model used")

    return {
        "fraud_probability": round(float(prob), 2),
        "fraud_score":        round(float(prob), 2),
        "is_fraud":           prob > 0.3,
        "risk_level":         "High" if prob > 0.65 else "Medium" if prob > 0.35 else "Low",
        "reasons":            reasons,
        "fraud_signals":      reasons,
        "shap_explanation":   shap_explanation,
        "advanced_signals":   advanced_signals,
        "signals": {
            "email_signal":       bool(email_flag),
            "url_signal":         bool(url_flag),
            "phone_signal":       bool(phone_flag),
            "payment_request":    bool(payment_request),
            "suspicious_salary":  bool(suspicious_salary),
            "missing_company":    bool(missing_profile),
        },
    }


# ============================================================
# URL-BASED FRAUD CHECK
# ============================================================
from pydantic import BaseModel as _BaseModel

class UrlFraudRequest(_BaseModel):
    url: str
    # Optional overrides (if scraping misses something)
    company_name:   str = ""
    company_domain: str = ""

@router.post("/check-url")
async def check_fraud_from_url(request: UrlFraudRequest):
    """
    Fetches a job posting from a URL and runs fraud detection.

    Supports:
      - Naukri job pages (works well without login)
      - Indeed job pages (works well)
      - LinkedIn job pages (limited — requires login, use browser
        extension instead for LinkedIn)
      - Any generic job portal URL

    Returns same response as /fraud/check plus:
      - scraped_data: what was extracted from the URL
      - scrape_success: True/False
      - scrape_note: explanation if scraping was limited

    Send:
    {
      "url": "https://www.naukri.com/job-listings-python-developer-..."
    }
    """
    from app.url_scraper import scrape_job_from_url

    # Scrape the URL
    scraped = scrape_job_from_url(request.url)

    if not scraped.get("success"):
        scrape_error = scraped.get("error", "Could not fetch URL")
        url_text = request.url.lower()
        site = scraped.get("site", "unknown")

        # Analyze URL structure for obvious fraud signals
        suspicious_url_patterns = [
            "bit.ly", "tinyurl", "shorturl", "free-job",
            "earn-money", "work-from-home-earn", "no-experience-job",
        ]
        legit_portals = ["naukri.com", "linkedin.com", "indeed.com",
                         "shine.com", "foundit.in", "unstop.com",
                         "internshala.com", "glassdoor.com"]

        is_legit_portal = any(p in url_text for p in legit_portals)
        is_suspicious_url = any(p in url_text for p in suspicious_url_patterns)

        if is_legit_portal:
            # Naukri/LinkedIn/Indeed — scraping blocked but URL is legit portal
            # Cannot determine fraud without content
            return {
                "fraud_probability": None,
                "fraud_score":       None,
                "is_fraud":          None,
                "scrape_success":    False,
                "scrape_note":       scrape_error,
                "site":              site,
                "cannot_analyze":    True,
                "reasons":           [],
                "signals":           {},
                "message":           (
                    f"{site.title()} pages cannot be scraped automatically "
                    f"(JavaScript-rendered / login required). "
                    f"Please COPY the job description text and use "
                    f"'Paste Text' tab instead for accurate analysis."
                ),
            }
        elif is_suspicious_url:
            return {
                "fraud_probability": 0.85,
                "fraud_score":       0.85,
                "is_fraud":          True,
                "scrape_success":    False,
                "scrape_note":       scrape_error,
                "risk_level":        "High",
                "reasons":           ["Suspicious URL pattern detected", scrape_error],
                "fraud_signals":     ["Suspicious URL pattern detected"],
                "signals":           {"url_signal": True},
            }
        else:
            return {
                "fraud_probability": None,
                "fraud_score":       None,
                "is_fraud":          None,
                "scrape_success":    False,
                "scrape_note":       scrape_error,
                "cannot_analyze":    True,
                "reasons":           [],
                "signals":           {},
                "message":           (
                    f"Could not fetch job content from this URL. "
                    f"Error: {scrape_error}. "
                    f"Please copy-paste the job description text in the 'Paste Text' tab."
                ),
            }

    # Use scraped data for fraud check
    job_description  = scraped.get("job_description", "")
    job_title        = scraped.get("job_title", "")
    company_name     = request.company_name or scraped.get("company_name", "")
    company_domain   = request.company_domain or scraped.get("company_domain", "")
    salary_range     = scraped.get("salary_range", "Not Specified")
    html_content     = scraped.get("html_content", "")

    # Run full fraud detection pipeline
    full_text = f"{job_description} {job_title} {company_name}"

    suspicious_salary  = is_suspicious_salary(salary_range)
    scam_words         = has_scam_keywords(job_description)
    missing_profile    = missing_company_profile(company_name)
    unrealistic_salary = is_unrealistic_salary(salary_range)
    payment_request    = has_payment_request(job_description)
    duplicate_posting  = 0

    clean_desc = clean_text(job_description)
    try:
        text_features = tfidf.transform([clean_desc])
        # Check what size model expects
        expected = fraud_model_backup.n_features_in_
        tfidf_size = text_features.shape[1]
        meta_size = expected - tfidf_size

        if meta_size == 3:
            meta = np.array([[suspicious_salary, missing_profile, scam_words]])
        else:
            meta = np.array([[suspicious_salary, missing_profile, scam_words,duplicate_posting, unrealistic_salary, payment_request]])
            
        features = hstack([text_features, csr_matrix(meta)])
        
        primary_prob = float(fraud_model.predict_proba(features)[0][1])
        backup_prob  = float(fraud_model_backup.predict_proba(features)[0][1])
        base_prob    = (primary_prob + backup_prob) / 2
    except Exception:
        # Strong rule-based fallback when ML model unavailable
        base_prob = _rule_based_score(
            job_description, job_title, company_name, salary_range
        )

    # Rule-based boosts
    email_flag, email_detail = check_email_signal(full_text)
    url_flag,   url_detail   = check_url_signal(full_text)
    phone_flag, phone_detail = check_phone_signal(full_text)
    rule_boost = (
        (EMAIL_BOOST if email_flag else 0) +
        (URL_BOOST   if url_flag   else 0) +
        (PHONE_BOOST if phone_flag else 0)
    )

    # Advanced PoC signals
    html_flag,   html_details   = check_html_signal(html_content)
    logo_flag,   logo_details   = check_logo_signal("", KNOWN_LOGO_PATHS)
    domain_flag, domain_details = check_company_domain_consistency_signal(
        company_name, company_domain
    )
    advanced_boost = (
        (HTML_BOOST           if html_flag   else 0) +
        (LOGO_BOOST           if logo_flag   else 0) +
        (DOMAIN_MISMATCH_BOOST if domain_flag else 0)
    )

    prob = min(base_prob + rule_boost + advanced_boost, 1.0)

    reasons = []
    if missing_profile:    reasons.append("Missing company profile")
    if suspicious_salary:  reasons.append("Salary not specified")
    if unrealistic_salary: reasons.append("Unrealistic salary")
    if payment_request:    reasons.append("Posting asks for upfront payment/fee")
    if scam_words:         reasons.append("Scam keywords detected")
    if email_flag:         reasons.append(email_detail)
    if url_flag:           reasons.append(url_detail)
    if phone_flag:         reasons.append(phone_detail)
    if html_flag:          reasons.extend(html_details)
    if domain_flag:        reasons.extend(domain_details)
    if base_prob > 0.7:    reasons.append("Suspicious job description language")

    # SHAP
    shap_explanation = []
    try:
        shap_values = shap_explainer.shap_values(features)
        if isinstance(shap_values, list):
            sv = shap_values[1][0]
        else:
            sv = shap_values[0] if shap_values.ndim > 1 else shap_values
        feature_names = tfidf.get_feature_names_out().tolist() + metadata_feature_names
        shap_pairs = sorted(
            zip(feature_names, sv), key=lambda x: abs(x[1]), reverse=True
        )
        for fname, fval in shap_pairs[:5]:
            if fname in metadata_feature_names:
                idx = metadata_feature_names.index(fname)
                if meta[0][idx] == 0:
                    continue
            if abs(fval) > 0.01:
                shap_explanation.append({
                    "feature": fname,
                    "shap_value": round(float(fval), 3),
                })
            if len(shap_explanation) >= 3:
                break
    except Exception:
        pass

    advanced_signals = []
    for flag, details, signal_name in [
        (html_flag,   html_details,   "html_hidden_link"),
        (logo_flag,   logo_details,   "logo_match"),
        (domain_flag, domain_details, "domain_mismatch"),
    ]:
        if details:
            advanced_signals.append({
                "signal": signal_name,
                "flagged": bool(flag),
                "details": details,
            })

    return {
        "fraud_probability": round(float(prob), 2),
        "is_fraud":          prob > 0.3,
        "reasons":           reasons,
        "shap_explanation":  shap_explanation,
        "advanced_signals":  advanced_signals,
        "scrape_success":    True,
        "scrape_note":       f"Successfully scraped from {scraped.get('site','unknown')}",
        "scraped_data": {
            "job_title":    scraped.get("job_title", ""),
            "company_name": scraped.get("company_name", ""),
            "location":     scraped.get("location", ""),
            "salary_range": scraped.get("salary_range", ""),
            "site":         scraped.get("site", ""),
        },
    }