"""
url_scraper.py — URL-based job scraping
Primary: Selenium (handles JS-rendered pages like LinkedIn, Naukri)
Fallback: requests + BeautifulSoup (static pages)
"""

import os, re, time, requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

# ── Site detection ────────────────────────────────────────────
def _detect_site(url: str) -> str:
    url = url.lower()
    if 'linkedin.com'    in url: return 'linkedin'
    if 'naukri.com'      in url: return 'naukri'
    if 'indeed.com'      in url: return 'indeed'
    if 'foundit.in'      in url: return 'foundit'
    if 'shine.com'       in url: return 'shine'
    if 'glassdoor.com'   in url: return 'glassdoor'
    if 'internshala.com' in url: return 'internshala'
    if 'unstop.com'      in url: return 'unstop'
    if 'wellfound.com'   in url: return 'wellfound'
    return 'generic'

# ── Selenium scraper ──────────────────────────────────────────
def _scrape_with_selenium(url: str, site: str) -> dict:
    """Use Selenium to scrape JS-rendered pages."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'user-agent={HEADERS["User-Agent"]}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # Try to find ChromeDriver
        driver = None
        try:
            # Try webdriver-manager first
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            # Fallback to system ChromeDriver
            driver = webdriver.Chrome(options=options)

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"[selenium] Opening {site}: {url[:60]}...")
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 15)

        job_title = ''
        company   = ''
        job_desc  = ''

        if site == 'linkedin':
            try:
                # Click "Show more" if present
                try:
                    show_more = driver.find_element(By.CLASS_NAME, 'show-more-less-html__button')
                    driver.execute_script("arguments[0].click();", show_more)
                    time.sleep(1)
                except: pass

                job_title = driver.find_element(By.CLASS_NAME, 'job-details-jobs-unified-top-card__job-title').text
                company   = driver.find_element(By.CLASS_NAME, 'job-details-jobs-unified-top-card__company-name').text
                desc_el   = driver.find_element(By.CLASS_NAME, 'jobs-description__content')
                job_desc  = desc_el.text
            except Exception as e:
                # Try alternative selectors
                try:
                    job_title = driver.find_element(By.TAG_NAME, 'h1').text
                    job_desc  = driver.find_element(By.CLASS_NAME, 'description').text
                except: pass

        elif site == 'naukri':
            try:
                job_title = driver.find_element(By.CLASS_NAME, 'jd-header-title').text
                company   = driver.find_element(By.CLASS_NAME, 'jd-header-comp-name').text
                job_desc  = driver.find_element(By.CLASS_NAME, 'job-desc').text
            except:
                try:
                    job_title = driver.find_element(By.TAG_NAME, 'h1').text
                    job_desc  = driver.find_element(By.ID, 'job_description').text
                except: pass

        elif site == 'indeed':
            try:
                wait.until(EC.presence_of_element_located((By.ID, 'jobDescriptionText')))
                job_title = driver.find_element(By.CLASS_NAME, 'jobsearch-JobInfoHeader-title').text
                company   = driver.find_element(By.CLASS_NAME, 'jobsearch-CompanyInfoWithoutHeaderImage').text
                job_desc  = driver.find_element(By.ID, 'jobDescriptionText').text
            except: pass

        else:
            # Generic — get all text
            time.sleep(3)
            body_text = driver.find_element(By.TAG_NAME, 'body').text
            job_title = driver.title
            job_desc  = body_text[:3000]

        driver.quit()

        if not job_desc or len(job_desc.strip()) < 50:
            return {
                'success': False,
                'site': site,
                'error': f'Could not extract job content from {site}. '
                         f'Page may require login. Please copy-paste job description.'
            }

        print(f"[selenium] ✅ Scraped {site} — {len(job_desc)} chars")
        return {
            'success':         True,
            'site':            site,
            'job_title':       job_title.strip(),
            'company_name':    company.strip(),
            'job_description': job_desc.strip()[:5000],
        }

    except ImportError:
        print("[selenium] ❌ Selenium not installed — pip install selenium webdriver-manager")
        return {'success': False, 'site': site,
                'error': 'Selenium not installed. Run: pip install selenium webdriver-manager'}
    except Exception as e:
        print(f"[selenium] ❌ Error: {e}")
        return {'success': False, 'site': site, 'error': str(e)}


# ── Requests fallback ─────────────────────────────────────────
def _scrape_with_requests(url: str, site: str) -> dict:
    """Fallback for static/simple pages."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {'success': False, 'site': site,
                    'error': f'HTTP {r.status_code}'}

        soup = BeautifulSoup(r.text, 'html.parser')

        # Remove noise
        for tag in soup(['script','style','nav','footer','header','aside']):
            tag.decompose()

        job_title = ''
        company   = ''
        job_desc  = ''

        # Try common selectors
        h1 = soup.find('h1')
        if h1: job_title = h1.get_text(strip=True)

        for sel in ['job-description','jobDescriptionText','job_description',
                    'description','job-desc','jd-desc']:
            el = soup.find(id=sel) or soup.find(class_=sel)
            if el:
                job_desc = el.get_text(separator=' ', strip=True)
                break

        if not job_desc:
            main = soup.find('main') or soup.find('article') or soup.find('body')
            if main:
                job_desc = main.get_text(separator=' ', strip=True)[:4000]

        if len(job_desc.strip()) < 50:
            return {'success': False, 'site': site,
                    'error': 'Content too short — page likely JS-rendered'}

        return {
            'success':         True,
            'site':            site,
            'job_title':       job_title,
            'company_name':    company,
            'job_description': job_desc[:5000],
        }

    except Exception as e:
        return {'success': False, 'site': site, 'error': str(e)}


# ── Main function ─────────────────────────────────────────────
def scrape_job_url(url: str) -> dict:
    """
    Scrape job posting from URL.
    Uses Selenium for JS-rendered sites, requests for others.
    """
    if not url or not url.startswith('http'):
        return {'success': False, 'error': 'Invalid URL — must start with http/https'}

    site = _detect_site(url)
    print(f"[url_scraper] Site: {site} | URL: {url[:60]}")

    # JS-rendered sites — use Selenium
    JS_SITES = ['linkedin', 'naukri', 'indeed', 'foundit', 'glassdoor', 'wellfound']

    if site in JS_SITES:
        result = _scrape_with_selenium(url, site)
        # If Selenium fails, inform user clearly
        if not result['success']:
            return {
                'success':      False,
                'site':         site,
                'cannot_analyze': True,
                'error':        result.get('error', ''),
                'message':      (
                    f"{site.title()} uses JavaScript rendering. "
                    f"Selenium attempted but failed: {result.get('error','')}. "
                    f"Please copy-paste the job description in 'Paste Text' tab."
                )
            }
        return result
    else:
        # Try requests first for static sites
        result = _scrape_with_requests(url, site)
        if not result['success']:
            # Try Selenium as fallback
            print(f"[url_scraper] Requests failed — trying Selenium for {site}")
            result = _scrape_with_selenium(url, site)
        return result


# Alias for backward compatibility
scrape_job_from_url = scrape_job_url
