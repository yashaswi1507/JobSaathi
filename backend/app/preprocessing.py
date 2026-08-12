import re
import string
import pandas as pd
import whois
from datetime import datetime
from difflib import SequenceMatcher

# --- Remove special characters and extra spaces from text ---
def clean_text(text):
    if not isinstance(text, str):   # if value is not a string (e.g. NaN)
        return ''                   # return empty string
    text = text.lower()             # convert to lowercase
    text = re.sub(r'\n', ' ', text) # replace newlines with space
    text = re.sub(r'[^a-z0-9\s]', '', text)  # remove special characters
    text = re.sub(r'\s+', ' ', text)  # remove extra spaces
    return text.strip()             # remove leading/trailing spaces

# --- Check if salary range looks suspicious (fraud signal) ---
def is_suspicious_salary(salary):
    if salary == 'Not Specified':   # missing salary is suspicious
        return 1                    # return 1 meaning suspicious
    return 0                        # return 0 meaning normal

# --- Check if email domain looks suspicious ---
def is_suspicious_email(email):
    if not isinstance(email, str):  # if no email provided
        return 1                    # suspicious
    # common free email domains used in scams
    suspicious = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    for domain in suspicious:       # check each suspicious domain
        if domain in email.lower(): # if domain found in email
            return 1                # suspicious
    return 0                        # looks legitimate

# --- Check if text contains urgency/scam keywords ---
def has_scam_keywords(text):
    if not isinstance(text, str):   # if no text provided
        return 0                    # no scam keywords
    # common words used in fake job postings (international + Indian-
    # context patterns, matching notebooks_07_fraud_model_combined_dataset.py
    # so the live API recognizes the same signals the model was trained on)
    keywords = [
        # original (international) keywords
        'urgent', 'immediate', 'work from home',
        'no experience', 'earn money', 'guaranteed',
        'apply now', 'limited slots', 'easy money',
        # Indian-context additions
        'upi', 'google pay', 'whatsapp interview', 'whatsapp for further',
        'telegram group', 'telegram channel', 'registration fee',
        'security deposit', 'refundable', 'aadhaar', 'aadhar',
        'starter kit', 'id card fee', 'send your bank details',
        'daily payment', 'captcha entry', 'ad posting job',
        'copy paste work', 'data entry job', 'pan india',
    ]
    text = text.lower()             # lowercase for comparison
    for word in keywords:           # check each keyword
        if word in text:            # if keyword found
            return 1                # scam keyword detected
    return 0                        # no scam keywords found

# --- Check if company profile is missing ---
def missing_company_profile(profile):
    if not isinstance(profile, str):  # if no profile
        return 1                      # missing = suspicious
    if profile.strip() == '':        # if empty string
        return 1                      # missing = suspicious
    return 0                          # profile exists


# ============================================================
# NEW SIGNAL 1 — Email extraction + free-domain check (live rule)
# ============================================================
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
FREE_EMAIL_DOMAINS = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
                      'rediffmail.com', 'ymail.com']

def extract_emails(text):
    """Finds all email addresses mentioned in a block of text."""
    if not isinstance(text, str):
        return []
    return re.findall(EMAIL_PATTERN, text)

def check_email_signal(text):
    """
    Live rule-based check: does the posting mention an email on a free
    provider (gmail/yahoo/etc) instead of a company domain?
    Returns (flag: 0 or 1, detail: str or None).
    NOTE: this is a RULE, not a trained model feature — EMSCAD's
    training data contains almost no real email addresses (verified:
    1 out of 17,880 rows), so this signal can't be learned from that
    data. It's applied independently at prediction time instead.
    """
    emails = extract_emails(text)
    if not emails:
        return 0, None
    for email in emails:
        domain = email.split('@')[-1].lower()
        if domain in FREE_EMAIL_DOMAINS:
            return 1, f"Free email domain used ({domain})"
    return 0, None


# ============================================================
# NEW SIGNAL 2 — URL extraction + domain-age check (live rule)
# ============================================================
URL_PATTERN = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?|www\.([a-zA-Z0-9-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?'

def extract_domains(text):
    """Finds all domains mentioned in URLs within a block of text."""
    if not isinstance(text, str):
        return []
    matches = re.findall(URL_PATTERN, text)
    domains = [m[0] or m[1] for m in matches if (m[0] or m[1])]
    return list(set(domains))

def check_url_signal(text, min_age_days=180):
    """
    Live rule-based check: does the posting link to a very recently
    registered domain? New domains (<6 months old) are a common
    scam-site pattern, since setting up a fake site is cheap and fast.
    Returns (flag: 0 or 1, detail: str or None).
    NOTE: same caveat as email — EMSCAD's URLs are anonymized hashes
    (#URL_xxxx#), not real domains, so this can't be trained on that
    data either. Applied live, at prediction time, on real user input.
    Requires internet access (whois lookup) and may be slow/rate-limited
    — wrapped in try/except so a lookup failure never crashes the
    fraud check itself.
    """
    domains = extract_domains(text)
    if not domains:
        return 0, None
    for domain in domains:
        try:
            w = whois.whois(domain)
            creation_date = w.creation_date
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if creation_date is None:
                continue
            age_days = (datetime.now() - creation_date).days
            if age_days < min_age_days:
                return 1, f"Domain '{domain}' registered only {age_days} days ago"
        except Exception:
            # whois lookup failed (rate-limited, invalid domain, no
            # internet, etc.) — skip silently rather than crash the
            # whole fraud check over one unreachable domain.
            continue
    return 0, None


# ============================================================
# NEW SIGNAL 3 — Phone number pattern check (live rule)
# ============================================================
# Indian mobile numbers: 10 digits starting 6-9, optionally with +91
PHONE_PATTERN = r'(?:\+91[-\s]?)?\b[6-9]\d{9}\b'

def check_phone_signal(text):
    """
    Live rule-based check: does the posting include a personal mobile
    number directly in the text? Legitimate companies usually direct
    applicants to a website/portal/official email rather than a
    personal phone number for "WhatsApp interviews" etc.
    Returns (flag: 0 or 1, detail: str or None).
    """
    if not isinstance(text, str):
        return 0, None
    matches = re.findall(PHONE_PATTERN, text)
    if matches:
        return 1, f"Personal mobile number found in posting ({matches[0]})"
    return 0, None


# ============================================================
# NEW SIGNAL 4 — Duplicate posting detection (TRAINABLE feature)
# ============================================================
def add_duplicate_signal(df, text_column='clean_description'):
    """
    Trainable feature for the TRAINING SCRIPT (not used at live
    prediction time for a single posting, since duplicate detection
    needs a corpus to compare against). Flags postings whose cleaned
    description is an EXACT match to another posting in the dataset —
    a classic sign of the same scam template reused under different
    company names.
    Uses exact full-text matching rather than a partial signature
    (e.g. first 200 chars) — testing showed a 200-char signature
    flagged ~41% of EMSCAD as "duplicate" (too noisy, mostly
    coincidental similar openings like "We are hiring for..."), while
    exact full-text match flags ~26% with roughly double the fraud
    correlation (7.3% vs 4.0% baseline), a meaningfully stronger signal.
    """
    df = df.copy()
    text_series = df[text_column].fillna('')
    dup_counts = text_series.value_counts()
    df['duplicate_posting'] = text_series.map(
        lambda s: 1 if dup_counts.get(s, 0) > 1 else 0
    )
    return df

def check_duplicate_signal_live(new_description, known_descriptions, similarity_threshold=0.85):
    """
    Live-prediction version of duplicate detection: compares a NEW
    posting's description against a list of recently-seen postings
    (e.g. from your job_analysis history table) using simple sequence
    similarity. Returns (flag: 0 or 1, detail: str or None).
    This needs a live corpus to compare against (your SQLite history),
    so routes/fraud.py should pass in recent descriptions if available;
    if none are passed, this safely returns (0, None).
    """
    if not known_descriptions:
        return 0, None
    new_clean = clean_text(new_description)
    for old_desc in known_descriptions:
        old_clean = clean_text(old_desc)
        similarity = SequenceMatcher(None, new_clean[:300], old_clean[:300]).ratio()
        if similarity >= similarity_threshold:
            return 1, "Near-identical posting found in recent history"
    return 0, None


# ============================================================
# NEW SIGNAL 5 — Unrealistic salary check (TRAINABLE feature,
# upgrades suspicious_salary from "missing" to "missing OR absurd")
# ============================================================
def is_unrealistic_salary(salary_range):
    """
    Flags salaries that are wildly unrealistic for the stated time
    period (e.g. "Rs 50,000/day" for an entry-level role). Intentionally
    conservative — only catches extreme per-day/per-hour figures, since
    we don't have a full industry-benchmark salary table to compare
    against (that's a separate "Salary & Demand Table" feature).
    """
    if not isinstance(salary_range, str) or salary_range.strip() == '' or salary_range == 'Not Specified':
        return 0
    numbers = [int(n) for n in re.findall(r'\d+', salary_range.replace(',', ''))]
    if not numbers:
        return 0
    max_value = max(numbers)
    lower = salary_range.lower()
    if max_value > 5000 and ('day' in lower or 'daily' in lower):
        return 1
    if max_value > 1000 and ('hour' in lower or 'hourly' in lower):
        return 1
    return 0


# ============================================================
# NEW SIGNAL 6 — Generic upfront-payment-request detection
# (TRAINABLE feature — broader than the fixed scam_keywords list,
# catches phrasing variations like "pay X to secure", "deposit of Rs")
# ============================================================
PAYMENT_REQUEST_PATTERN = (
    r'(pay\s+(?:a\s+)?(?:small\s+)?(?:fee|amount|deposit)|'
    r'deposit\s+of|registration\s+(?:fee|charge)|'
    r'security\s+deposit|refundable\s+(?:fee|deposit|amount)|'
    r'starter\s+kit\s+(?:fee|charge)|id\s+card\s+fee)'
)

def has_payment_request(text):
    """
    Detects phrasing that asks the applicant to pay money upfront —
    broader pattern-match than the fixed scam_keywords list, so it
    catches reworded variations a scammer might use to dodge an exact
    keyword match.
    """
    if not isinstance(text, str):
        return 0
    return 1 if re.search(PAYMENT_REQUEST_PATTERN, text.lower()) else 0


# --- Apply all TRAINABLE features to fraud dataframe (used by the
# training script). Live-only rule checks (email/URL/phone) are NOT
# included here since they need to run per-request in routes/fraud.py,
# not as a fixed training column (see check_email_signal,
# check_url_signal, check_phone_signal above). ---
def add_fraud_features(df):
    df['clean_description'] = df['description'].apply(clean_text)       # clean description text
    df['clean_requirements'] = df['requirements'].apply(clean_text)     # clean requirements text
    df['suspicious_salary']  = df['salary_range'].apply(is_suspicious_salary)  # salary flag
    df['missing_profile']    = df['company_profile'].apply(missing_company_profile)  # profile flag
    df['scam_keywords']      = df['description'].apply(has_scam_keywords)  # scam keyword flag
    df['unrealistic_salary'] = df['salary_range'].apply(is_unrealistic_salary)  # NEW
    df['payment_request']    = df['description'].apply(has_payment_request)    # NEW
    df = add_duplicate_signal(df)                                              # NEW
    return df                       # return dataframe with new features

# ============================================================
# ADVANCED SIGNALS (proof-of-concept, now wired into production at
# the user's request — see honest limitations in each docstring,
# these are less battle-tested than the 6 core trainable signals
# and the 3 live email/URL/phone rules above)
# ============================================================

def check_html_signal(html_text):
    """
    Detects suspicious HTML patterns in a job posting, if raw HTML is
    available (e.g. read from a live page's DOM by a future browser
    extension — NOT applicable to plain-text paste). Checks for
    hidden elements and link-text/href mismatches pointing to URL
    shorteners. Returns (flag: 0 or 1, details: list of str).
    Returns (0, []) immediately if no HTML is provided — this is the
    expected, normal case for plain-text-paste submissions.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return 0, []

    if not html_text or '<' not in html_text:
        return 0, []

    soup = BeautifulSoup(html_text, 'html.parser')
    details = []

    for tag in soup.find_all(style=True):
        style = tag.get('style', '').lower().replace(' ', '')
        if 'display:none' in style or 'visibility:hidden' in style or 'opacity:0' in style:
            details.append(f"Hidden element found: <{tag.name}> with style hiding it from view")

    SUSPICIOUS_LINK_TEXT = ('apply', 'click here', 'register', 'verify')
    URL_SHORTENERS = ('bit.ly', 'tinyurl', 't.co', 'goo.gl', 'is.gd', 'ow.ly')

    for a in soup.find_all('a', href=True):
        link_text = a.get_text(strip=True).lower()
        href = a['href'].lower()
        if any(kw in link_text for kw in SUSPICIOUS_LINK_TEXT):
            if any(short in href for short in URL_SHORTENERS):
                details.append(
                    f'Link text "{a.get_text(strip=True)}" points to a '
                    f'URL shortener instead of a direct link: {href}'
                )

    return (1 if details else 0), details


def check_logo_signal(uploaded_logo_path, known_legitimate_logos=None, max_match_distance=8, min_margin=2):
    """
    Compares an uploaded logo against a small set of known legitimate
    logos using perceptual hashing, flagging only CONFIDENT,
    UNAMBIGUOUS matches (best match clearly closer than the
    next-closest, not just "vaguely similar to several logos").

    HONEST LIMITATION: known_legitimate_logos here is a tiny demo set
    (10 placeholder logos). A production deployment needs a genuinely
    large, diverse real-logo database for this to be reliable —
    testing during development showed simple/similar-shaped logos can
    produce close hash distances for UNRELATED companies, which is
    exactly why the margin check (not just a flat threshold) is used.

    Returns (flag: 0 or 1, details: list of str). Returns (0, []) if
    no logo_path was provided — this is the expected case when a user
    doesn't upload a logo image alongside their posting text.
    """
    if not uploaded_logo_path:
        return 0, []

    try:
        from PIL import Image
        import imagehash
    except ImportError:
        return 0, []

    if known_legitimate_logos is None:
        known_legitimate_logos = {}

    try:
        uploaded_hash = imagehash.phash(Image.open(uploaded_logo_path))
    except Exception as e:
        return 0, [f"Could not process uploaded logo: {e}"]

    distances = []
    for company_name, known_logo_path in known_legitimate_logos.items():
        try:
            known_hash = imagehash.phash(Image.open(known_logo_path))
        except Exception:
            continue
        distances.append((company_name, uploaded_hash - known_hash))

    if not distances:
        return 0, []

    distances.sort(key=lambda x: x[1])
    best_name, best_distance = distances[0]
    margin = float("inf") if len(distances) == 1 else (distances[1][1] - best_distance)

    if best_distance <= max_match_distance and margin >= min_margin:
        return 1, [
            f'Uploaded logo closely and unambiguously matches the known logo '
            f'for "{best_name}" (distance={best_distance}/64, margin={margin}) — '
            f"verify the posting's claimed company name actually matches {best_name}"
        ]
    return 0, []


def check_company_domain_consistency_signal(company_name, mentioned_domain):
    """
    Checks SELF-CONSISTENCY within the posting: does the domain
    mentioned in the posting resemble the company name claimed in
    the SAME posting? E.g. claiming "Infosys" but linking to an
    unrelated domain is a mismatch, regardless of how common/generic
    the company name is — this sidesteps the disambiguation problem
    a web-search-based check would have for generic names (tested:
    web-search for a generic company name returned multiple unrelated
    real companies even with location keywords added, confirming that
    approach doesn't reliably work — this self-consistency check
    avoids that problem entirely).

    HONEST LIMITATION: catches OBVIOUS mismatches (claims X, links to
    Y), not a scammer who invents a fake name AND registers a
    matching-looking fake domain — that requires the other signals
    (email domain, scam keywords, etc.) to catch.

    Returns (flag: 0 or 1, details: list of str). Returns (0, []) if
    no domain was mentioned — neutral, not suspicious, since many
    legitimate postings don't include a website link.
    """
    if not mentioned_domain or not company_name:
        return 0, []

    clean_name = re.sub(r'[^a-z0-9]', '', company_name.lower())
    clean_name = re.sub(r'(pvtltd|pvt|ltd|inc|llc|limited|private)$', '', clean_name)
    clean_domain = mentioned_domain.lower().split('.')[0]

    similarity = SequenceMatcher(None, clean_name, clean_domain).ratio()

    if similarity < 0.4:
        return 1, [
            f'Posting claims to be "{company_name}" but links to domain '
            f'"{mentioned_domain}", which bears little resemblance to the '
            f"claimed company name (similarity={similarity:.2f})"
        ]
    return 0, []


# Small demo database of known legitimate logos for check_logo_signal.
# HONEST LIMITATION: these are synthetic placeholder images (simple
# colored shapes), not real company logos, since real logos are
# copyrighted and a production system would need a properly-licensed
# or self-collected real logo database — see fraud_poc_assets/known_logos/
# for the actual image files this dict should point to.
KNOWN_LOGO_PATHS = {
    "Infosys": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\Infosys.png",
    "TCS": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\TCS.png",
    "Wipro": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\Wipro.png",
    "Accenture": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\Accenture.png",
    "Capgemini": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\Capgemini.png",
    "HCL": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\HCL.png",
    "TechMahindra": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\TechMahindra.png",
    "Cognizant": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\Cognizant.png",
    "IBM": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\IBM.png",
    "Microsoft": r"C:\CareerShieldAI\fraud_poc_assets\known_logos\Microsoft.png",
}

print("Preprocessing functions loaded successfully.")
