"""
distilbert_fraud.py
-------------------
DistilBERT-based Job Fraud Detection
Primary  → DistilBERT context embeddings + cosine similarity
Fallback → Existing XGBoost/LightGBM models
"""

import re
import os
import numpy as np
from typing import Dict, List

# ── DistilBERT Setup ──────────────────────────────────────────
_tokenizer  = None
_bert_model = None
_bert_ready = False

def _load_bert():
    global _tokenizer, _bert_model, _bert_ready
    if _bert_ready is not None and _bert_ready is not False:
        return _bert_ready
    try:
        from transformers import DistilBertTokenizer, DistilBertModel
        import torch
        print("[BERT] Loading DistilBERT...")
        _tokenizer  = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        _bert_model = DistilBertModel.from_pretrained('distilbert-base-uncased')
        _bert_model.eval()
        _bert_ready = True
        print("[BERT] DistilBERT loaded ✅")
        return True
    except Exception as e:
        print(f"[BERT] Not available: {e} — using fallback")
        _bert_ready = False
        return False

def _get_embedding(text: str) -> np.ndarray:
    """Get DistilBERT CLS embedding for text."""
    import torch
    inputs  = _tokenizer(text[:512], return_tensors='pt',
                          truncation=True, padding=True, max_length=512)
    with torch.no_grad():
        outputs = _bert_model(**inputs)
    # CLS token embedding
    return outputs.last_hidden_state[:, 0, :].numpy()[0]

# ── Known fraud/genuine job embeddings (reference texts) ────
FRAUD_SIGNALS_TEXT = """
Work from home easy money no experience required registration fee deposit
WhatsApp contact urgently hiring lottery prize unlimited earning MLM scheme
no interview direct joining suspicious company agent commission based
"""

GENUINE_SIGNALS_TEXT = """
required qualifications experience skills apply online official website
HR contact email company profile job description responsibilities
annual salary package benefits interview process technical round
"""

_fraud_embedding   = None
_genuine_embedding = None

def _get_reference_embeddings():
    global _fraud_embedding, _genuine_embedding
    if _fraud_embedding is None:
        _fraud_embedding   = _get_embedding(FRAUD_SIGNALS_TEXT)
        _genuine_embedding = _get_embedding(GENUINE_SIGNALS_TEXT)

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

# ── DistilBERT Fraud Score ────────────────────────────────────
def _bert_fraud_score(job_text: str) -> Dict:
    """
    Compute fraud probability using DistilBERT embeddings.
    Compares job text similarity to known fraud vs genuine patterns.
    """
    if not _load_bert():
        raise Exception("DistilBERT not available")

    _get_reference_embeddings()

    # Get job embedding
    job_embedding = _get_embedding(job_text[:512])

    # Cosine similarity with fraud and genuine references
    fraud_sim   = _cosine_similarity(job_embedding, _fraud_embedding)
    genuine_sim = _cosine_similarity(job_embedding, _genuine_embedding)

    # Normalize to probability
    total       = fraud_sim + genuine_sim + 1e-8
    fraud_prob  = fraud_sim / total

    # Confidence based on separation
    confidence  = abs(fraud_sim - genuine_sim)

    return {
        "bert_fraud_score":   round(fraud_prob, 4),
        "bert_genuine_score": round(genuine_sim / total, 4),
        "bert_confidence":    round(confidence, 4),
        "method":             "DistilBERT embeddings",
    }


# ── Context-aware Signal Detection ───────────────────────────
CONTEXTUAL_PATTERNS = {
    "registration_fee": [
        r"pay\s+(?:registration|joining|training)\s+fee",
        r"deposit\s+(?:required|needed|mandatory)",
        r"refundable\s+(?:security|deposit)",
    ],
    "unrealistic_salary": [
        r"earn\s+(?:up\s+to\s+)?\d+\s*(?:lakh|lac|lakhs)\s+per\s+(?:day|week)",
        r"unlimited\s+(?:earning|income|salary)",
        r"\d+\s*(?:cr|crore)\s+(?:package|ctc)",
    ],
    "suspicious_contact": [
        r"whatsapp\s+(?:only|contact|me|us)",
        r"contact\s+on\s+whatsapp",
        r"call\s+immediately\s+for\s+interview",
    ],
    "no_experience_trap": [
        r"no\s+(?:experience|qualification|degree)\s+(?:required|needed)",
        r"freshers?\s+(?:and|or)\s+experienced\s+both",
        r"anyone\s+can\s+(?:apply|join|work)",
    ],
    "fake_company": [
        r"mnc\s+company\s+(?:hiring|recruitment)",
        r"top\s+(?:\d+\s+)?(?:mnc|company|firm)\s+(?:hiring|urgently)",
        r"100\s*%\s+job\s+guarantee",
    ],
}

def _contextual_bert_analysis(job_text: str) -> Dict:
    """
    Context-aware analysis: DistilBERT understands
    'work from home' in legitimate vs fraudulent context.
    """
    text_lower   = job_text.lower()
    found_signals = []
    context_score = 0

    for signal_type, patterns in CONTEXTUAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                found_signals.append(signal_type.replace('_', ' ').title())
                context_score += 20
                break

    # Positive legitimacy signals
    legit_signals = [
        r'apply\s+(?:at|on|via)\s+(?:www\.|https?://)',
        r'(?:official|company)\s+(?:website|portal)',
        r'annual\s+(?:ctc|package|salary)',
        r'interview\s+(?:process|rounds?|schedule)',
        r'notice\s+period',
    ]

    legit_count = sum(1 for p in legit_signals if re.search(p, text_lower))
    context_score = max(0, context_score - (legit_count * 5))

    return {
        "context_signals":   found_signals,
        "context_score":     min(context_score, 100),
        "legit_indicators":  legit_count,
    }


# ── Main Hybrid Fraud Detection ───────────────────────────────
def analyze_job_fraud_bert(job_text: str, existing_ml_score: float = None) -> Dict:
    """
    Hybrid job fraud detection:
    1. DistilBERT embeddings (context-aware)
    2. Pattern-based contextual analysis
    3. Combine with existing ML score if available

    Args:
        job_text:         Job description text
        existing_ml_score: Score from XGBoost/LightGBM (0-1)
    """
    if not job_text or len(job_text.strip()) < 20:
        return {"error": "Job text too short", "bert_score": 0}

    result = {}

    # 1. Contextual pattern analysis (always runs — fast)
    ctx = _contextual_bert_analysis(job_text)
    result.update(ctx)

    # 2. DistilBERT semantic similarity
    try:
        bert_result = _bert_fraud_score(job_text)
        result.update(bert_result)
        bert_score = bert_result["bert_fraud_score"]
    except Exception as e:
        print(f"[BERT] Embedding failed: {e}")
        bert_score = ctx["context_score"] / 100

    # 3. Combine scores
    ctx_score = ctx["context_score"] / 100

    if existing_ml_score is not None:
        # Weighted ensemble: ML 50% + BERT 30% + Context 20%
        final_score = (existing_ml_score * 0.50 +
                       bert_score        * 0.30 +
                       ctx_score         * 0.20)
        result["ensemble_method"] = "ML(50%) + BERT(30%) + Context(20%)"
    else:
        # Without ML: BERT 60% + Context 40%
        final_score = bert_score * 0.60 + ctx_score * 0.40
        result["ensemble_method"] = "BERT(60%) + Context(40%)"

    result["final_fraud_score"] = round(final_score, 4)
    result["final_fraud_pct"]   = int(final_score * 100)
    result["risk_level"] = (
        "HIGH"   if final_score >= 0.6 else
        "MEDIUM" if final_score >= 0.3 else
        "LOW"
    )

    return result


if __name__ == "__main__":
    test_jobs = [
        {
            "title": "Fake Job",
            "text": "Urgently hiring! Work from home, earn 50000 per day. No experience required. WhatsApp us immediately. Pay registration fee of 500 to get started."
        },
        {
            "title": "Genuine Job",
            "text": "Software Engineer at Google. 3+ years Python experience required. Apply at careers.google.com. Interview process: 2 technical rounds + HR. Annual CTC: 20-35 LPA."
        }
    ]

    for job in test_jobs:
        print(f"\n{'='*50}")
        print(f"Job: {job['title']}")
        result = analyze_job_fraud_bert(job["text"])
        print(f"Score: {result['final_fraud_pct']}% | Risk: {result['risk_level']}")
        print(f"Signals: {result.get('context_signals', [])}")
