/**
 * CareerShield AI — Content Script
 * Runs on job pages — extracts job data from DOM
 * Works on: LinkedIn, Naukri, Indeed, Shine, Foundit, Internshala, Unstop
 */

const SITE = window.location.hostname;

// ── Site-specific extractors ──────────────────────────────────
const EXTRACTORS = {

  'www.linkedin.com': () => {
    // Click "Show more" to expand description
    const showMore = document.querySelector(
      '.show-more-less-html__button--more, .jobs-description__footer-button'
    );
    if (showMore) showMore.click();

    return {
      job_title:    getText([
        '.job-details-jobs-unified-top-card__job-title h1',
        '.jobs-unified-top-card__job-title',
        'h1.t-24'
      ]),
      company_name: getText([
        '.job-details-jobs-unified-top-card__company-name a',
        '.jobs-unified-top-card__company-name',
        '.topcard__org-name-link'
      ]),
      job_description: getText([
        '.jobs-description__content .jobs-box__html-content',
        '.jobs-description-content__text',
        '.description__text',
        '#job-details'
      ]),
      salary_range: getText([
        '.job-details-jobs-unified-top-card__job-insight span',
        '.compensation__salary'
      ]),
    };
  },

  'www.naukri.com': () => {
    return {
      job_title:    getText([
        '.jd-header-title h1',
        '[class*="title"] h1',
        'h1'
      ]),
      company_name: getText([
        '.jd-header-comp-name a',
        '[class*="comp-name"]',
        '.comp-name'
      ]),
      job_description: getText([
        '.job-desc',
        '[class*="job-desc"]',
        '.dang-inner-html',
        '#job_description'
      ]),
      salary_range: getText([
        '[class*="salary"]',
        '.salary'
      ]),
    };
  },

  'www.indeed.com': () => {
    return {
      job_title:    getText(['h1.jobsearch-JobInfoHeader-title', 'h1[data-testid="jobsearch-JobInfoHeader-title"]']),
      company_name: getText(['[data-testid="inlineHeader-companyName"] a', '.jobsearch-CompanyInfoWithoutHeaderImage']),
      job_description: getText(['#jobDescriptionText', '[id="jobDescriptionText"]']),
      salary_range: getText(['[id="salaryInfoAndJobType"]', '.jobsearch-JobMetadataHeader-item']),
    };
  },

  'www.shine.com': () => ({
    job_title:       getText(['h1.job-title', 'h1']),
    company_name:    getText(['.company-name', '.comp-name']),
    job_description: getText(['.jd-desc', '.job-description', '#jobDescription']),
    salary_range:    getText(['.salary-range', '.salary']),
  }),

  'www.foundit.in': () => ({
    job_title:       getText(['h1', '.job-title']),
    company_name:    getText(['.company-name']),
    job_description: getText(['.job-desc', '.description']),
    salary_range:    getText(['.salary']),
  }),

  'internshala.com': () => ({
    job_title:       getText(['.profile h3', 'h1', '.job-title']),
    company_name:    getText(['.company-name a', '.company_name']),
    job_description: getText(['.internship_other_details_container', '.job-description', '#about-company']),
    salary_range:    getText(['.stipend span', '.salary']),
  }),

  'unstop.com': () => ({
    job_title:       getText(['h1', '.opportunity-title']),
    company_name:    getText(['.company-name', '.org-name']),
    job_description: getText(['.description', '.opportunity-description']),
    salary_range:    getText(['.salary', '.stipend']),
  }),
};

// ── Helper — get text from first matching selector ────────────
function getText(selectors) {
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el && el.innerText.trim().length > 0) {
      return el.innerText.trim();
    }
  }
  return '';
}

// ── Extract job data ──────────────────────────────────────────
function extractJobData() {
  const extractor = EXTRACTORS[SITE];
  if (!extractor) {
    return { error: `Site ${SITE} not supported` };
  }

  const data = extractor();

  // Validate we got meaningful content
  if (!data.job_description || data.job_description.length < 50) {
    return {
      error: 'Could not extract job description. Page may not have loaded fully.',
      partial: data,
    };
  }

  return {
    success:         true,
    site:            SITE,
    url:             window.location.href,
    job_title:       data.job_title       || document.title,
    company_name:    data.company_name    || '',
    job_description: data.job_description || '',
    salary_range:    data.salary_range    || '',
  };
}

// ── Listen for message from popup ────────────────────────────
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractJob') {
    // Wait a bit for dynamic content
    setTimeout(() => {
      const data = extractJobData();
      sendResponse(data);
    }, 1500);
    return true; // Keep message channel open for async
  }
});

// ── Auto-detect and show badge ────────────────────────────────
window.addEventListener('load', () => {
  setTimeout(() => {
    const data = extractJobData();
    if (data.success && data.job_description.length > 50) {
      // Notify extension that job data is available
      chrome.runtime.sendMessage({
        action: 'jobDetected',
        site:   SITE,
        title:  data.job_title,
      });
    }
  }, 2000);
});
