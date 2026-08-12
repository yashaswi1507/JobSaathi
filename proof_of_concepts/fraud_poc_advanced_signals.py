"""
fraud_poc_advanced_signals.py
---------------------------------
PROOF-OF-CONCEPT implementations of 3 advanced fraud signals that were
explicitly scoped OUT of the main production pipeline (see
preprocessing_v2.py / notebooks_09_fraud_model_full_signals.py), since
they need infrastructure or have legal/ToS constraints beyond a
thesis timeline. These are demonstrable, working code — but NOT wired
into the live /fraud/check endpoint, and NOT trained/validated at the
scale the rest of the pipeline was.

Be explicit about this distinction if presenting these in a thesis:
"proof-of-concept showing the approach is feasible" is an honest and
defensible claim. "Production-ready feature" is not — say so clearly.

==============================================================
1. HTML / hidden-link detection
==============================================================
Only useful if raw HTML is available (e.g. a future browser-extension
reading the live page DOM). The current /fraud/check endpoint accepts
plain text (copy-pasted job descriptions), where HTML has already
been stripped by the time the user pastes it — so this function has
no live caller in the current architecture. Included to show the
approach works, for a future browser-extension version of the product.

==============================================================
2. Image / logo fraud detection
==============================================================
Uses perceptual hashing (phash) to detect when an uploaded company
logo is a near-identical copy of a KNOWN, real company's logo —
catching wholesale logo theft (a common scam pattern: stealing a real
company's branding to look legitimate).

HONEST LIMITATIONS:
- Needs a database of real company logos to compare against. This
  PoC uses 3 hand-made test images; production would need thousands
  of real logos (a separate data-collection effort).
- Perceptual hashing only catches near-identical images (resized,
  cropped, recolored versions of the SAME image). It will NOT catch
  a logo redrawn from scratch to look similar — that needs a trained
  CNN embedding model, well beyond this PoC's scope.
- Does not verify the posting's claimed company name against which
  real company the logo belongs to — that's a separate lookup step,
  not implemented here.

==============================================================
3. Company domain-consistency check (STRENGTHENED — replaces the
   original weak "search the web for company name" approach)
==============================================================
The original web-search approach was tested live and found genuinely
weak for generic company names: searching "TechCorp Bangalore careers
jobs official site" still returned unrelated international companies
with no Bangalore-specific result. Adding location keywords did not
fix the core ambiguity problem.

STRENGTHENED VERSION: instead of searching the open web (which can't
disambiguate generic names), this checks SELF-CONSISTENCY within the
posting — does the domain mentioned in the posting actually resemble
the company name claimed in the SAME posting? E.g. claiming to be
"Infosys" but linking to "totallydifferent.com" is a self-consistency
failure, regardless of how generic or distinctive "Infosys" is as a
name. This sidesteps the disambiguation problem entirely.

HONEST LIMITATIONS:
- Only useful when the posting mentions a domain at all — many
  legitimate postings don't include one, so absence of a domain is
  neutral, not suspicious.
- A scammer could simply register a domain that DOES closely resemble
  a fake company name they invent ("Infosys Solutions Group" with
  domain infosys-solutions-group.com) — this catches OBVIOUS mismatches
  (claim X, link to Y), not a consistently-fake invented identity.
- String-similarity is a heuristic, not a verified ownership check —
  it does not confirm the domain is actually registered TO that
  company, only that the name and domain text resemble each other.
"""

import re
from difflib import SequenceMatcher


# ======================================================================
# 1. HTML / hidden-link detection
# ======================================================================
def check_html_signal(html_text):
    """
    Detects suspicious HTML patterns in a job posting, if raw HTML is
    available (e.g. read from a live page's DOM by a future browser
    extension — NOT applicable to plain-text paste, which is what the
    current /fraud/check endpoint accepts).

    Checks for:
      - hidden elements (display:none, visibility:hidden, opacity:0)
      - "Apply"/"Click here"/"Register" link text pointing to a
        URL-shortener domain instead of a direct, visible URL

    Returns (flag: 0 or 1, details: list of str).
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return 0, ["BeautifulSoup not installed — run: pip install beautifulsoup4"]

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


# ======================================================================
# 2. Image / logo fraud detection
# ======================================================================
def check_logo_signal(uploaded_logo_path, known_legitimate_logos, max_match_distance=8, min_margin=2):
    """
    STRENGTHENED VERSION: compares an uploaded logo against ALL known
    legitimate logos and reports the BEST (closest) match, rather than
    just listing every match under a fixed threshold.

    Why this is stronger than a simple threshold: testing against a
    10-company logo set showed that several unrelated company logos
    can land within a small hash-distance of each other (e.g. two
    different "blue rectangle with white text" style logos scored
    distance=2 and distance=4 from a stolen-Infosys-logo test case,
    alongside the correct match at distance=0) — a naive "flag
    anything under threshold X" approach would report multiple
    conflicting matches. This version instead:
      1. Finds the closest match overall
      2. Only flags it if that match is convincingly close
         (<= max_match_distance) AND clearly closer than the next-best
         match by at least min_margin — i.e. confident, unambiguous
         matches only, not "vaguely similar to several logos".

    Args:
      uploaded_logo_path: path to the logo image from the job posting
      known_legitimate_logos: dict of {company_name: logo_path}
      max_match_distance: max phash distance to consider a match at all
      min_margin: minimum gap between best and 2nd-best match needed
        to trust the result as unambiguous

    Returns (flag: 0 or 1, details: list of str).

    HONEST LIMITATION (unchanged from before): perceptual hashing
    catches near-identical copies (resized/cropped/recolored), not a
    logo redrawn from scratch to look similar — that needs a trained
    CNN embedding model, beyond this PoC's scope. Also: a database of
    only a few logos with very similar simple geometry (as in this
    PoC's synthetic test set) can still produce close distances for
    unrelated companies — the margin check above is what protects
    against over-confident false positives in that case, but a real
    deployment needs a genuinely large, diverse real-logo database
    for this to be reliable at scale.
    """
    try:
        from PIL import Image
        import imagehash
    except ImportError:
        return 0, ["Pillow/imagehash not installed — run: pip install pillow imagehash"]

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
        return 0, ["No known logos available to compare against."]

    distances.sort(key=lambda x: x[1])
    best_name, best_distance = distances[0]

    if len(distances) == 1:
        margin = float("inf")
    else:
        second_name, second_distance = distances[1]
        margin = second_distance - best_distance

    if best_distance <= max_match_distance and margin >= min_margin:
        return 1, [
            f'Uploaded logo closely and UNAMBIGUOUSLY matches the known logo '
            f'for "{best_name}" (distance={best_distance}/64, margin over next-'
            f'closest match={margin}) — verify the posting\'s claimed company '
            f"name actually matches {best_name}"
        ]
    elif best_distance <= max_match_distance:
        return 0, [
            f'Uploaded logo is somewhat close to multiple known logos '
            f'(closest: "{best_name}" at distance={best_distance}, but margin '
            f'over next-closest is only {margin}) — too ambiguous to confidently '
            f"flag; consider this inconclusive rather than a confirmed match"
        ]
    return 0, []


# ======================================================================
# 3. Web-presence cross-check (search API, NOT scraping)
# ======================================================================
def check_company_domain_consistency_signal(company_name, mentioned_domain):
    """
    STRENGTHENED VERSION, replacing the earlier weak "search the web for
    this company name" approach. The earlier version was tested live
    and found genuinely weak: searching "TechCorp Bangalore careers
    jobs official site" still returned unrelated companies (a US AV-
    equipment firm, a New Jersey staffing firm, an Indeed company
    page) with no Bangalore-specific result — adding location/intent
    keywords did not fix the core problem that generic company names
    are inherently ambiguous on the open web.

    This version sidesteps that problem entirely by NOT searching the
    web at all. Instead, it checks SELF-CONSISTENCY within the
    posting itself: does the domain mentioned in the posting
    (e.g. "apply at techcorpsolutions.com") plausibly match the
    company name claimed in the SAME posting (e.g. "TechCorp
    Solutions Pvt Ltd")? This works equally well for generic and
    distinctive names, since it never needs to disambiguate which of
    several same-named real companies is meant — it only checks
    whether THIS posting is internally consistent.

    Returns (flag: 0 or 1, details: list of str, similarity_score: float).
    flag=1 means a MISMATCH was found (suspicious — claims to be
    "Infosys" but links to a domain with zero resemblance to "infosys").
    """
    if not mentioned_domain:
        return 0, ["No company domain mentioned in posting to check — "
                   "this is neutral, not suspicious, since many legitimate "
                   "postings simply don't include a website link."]

    clean_name = re.sub(r'[^a-z0-9]', '', company_name.lower())
    clean_name = re.sub(r'(pvtltd|pvt|ltd|inc|llc|limited|private)$', '', clean_name)
    clean_domain = mentioned_domain.lower().split('.')[0]

    similarity = SequenceMatcher(None, clean_name, clean_domain).ratio()

    if similarity < 0.4:
        return 1, [
            f'Posting claims to be "{company_name}" but links to domain '
            f'"{mentioned_domain}", which bears little resemblance to the '
            f"claimed company name (similarity={similarity:.2f}) — possible "
            f"mismatch between claimed identity and actual destination"
        ]
    return 0, [f'Domain "{mentioned_domain}" is reasonably consistent with '
              f'claimed company name "{company_name}" (similarity={similarity:.2f})']


if __name__ == "__main__":
    print("=== Self-test 1: HTML hidden-link detection ===")
    test_html = '''
    <a href="https://realcompany.com/apply">Apply Here</a>
    <a href="https://bit.ly/3xYzAbC" style="display:none">Click here to apply</a>
    <div style="visibility: hidden;">Hidden tracking pixel</div>
    '''
    flag, details = check_html_signal(test_html)
    print(f"Flag: {flag}")
    for d in details:
        print(f"  - {d}")

    print("\n=== Self-test 2: Logo similarity detection (10-company database) ===")
    try:
        known = {
            name: f"fraud_poc_assets/known_logos/{name}.png"
            for name in ["Infosys", "TCS", "Wipro", "Accenture", "Capgemini",
                        "HCL", "TechMahindra", "Cognizant", "IBM", "Microsoft"]
        }
        f1, d1 = check_logo_signal("fraud_poc_assets/stolen_logo_test.png", known)
        print(f"Stolen Infosys-style logo -> flag={f1}")
        for d in d1:
            print(f"  - {d}")
        f2, d2 = check_logo_signal("fraud_poc_assets/logo_different.png", known)
        print(f"Genuinely different logo -> flag={f2} (should be 0)")
    except Exception as e:
        print(f"  (skipped — {e})")

    print("\n=== Self-test 3: Domain-consistency check ===")
    flag3, details3 = check_company_domain_consistency_signal("Infosys", "infosys.com")
    print(f"Matching domain -> flag={flag3}")
    for d in details3:
        print(f"  - {d}")

    flag4, details4 = check_company_domain_consistency_signal("Infosys", "totallydifferent.com")
    print(f"Mismatched domain -> flag={flag4}")
    for d in details4:
        print(f"  - {d}")

    flag5, details5 = check_company_domain_consistency_signal("Generic Company", None)
    print(f"No domain mentioned -> flag={flag5}")
    for d in details5:
        print(f"  - {d}")
