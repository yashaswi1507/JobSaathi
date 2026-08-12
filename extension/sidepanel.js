/**
 * JobSaathi AI — Side Panel Script
 * Auto-detects job pages and shows fraud analysis
 */

const API = 'http://localhost:8000';
const SITES = ['linkedin.com','naukri.com','indeed.com','shine.com','foundit.in','internshala.com','unstop.com'];

let currentTabId = null;

// ── Render functions ──────────────────────────────────────────
function setApp(html) {
  document.getElementById('app').innerHTML = html;
}

function renderWelcome() {
  setApp(`
    <div class="welcome">
      <div class="welcome-icon">🛡️</div>
      <div class="welcome-title">JobSaathi AI is ready!</div>
      <div class="welcome-desc">
        Navigate to a job posting to automatically detect fraud.
        Supported sites:
      </div>
      <div>
        ${['LinkedIn','Naukri','Indeed','Internshala','Unstop','Shine'].map(s =>
          `<span class="site-chip">${s}</span>`).join('')}
      </div>
      <div style="margin-top:20px">
        <button class="btn btn-analyze" id="btnAnalyze">🔍 Analyze Current Page</button>
        <button class="btn btn-outline" id="btnOpen">Open JobSaathi AI →</button>
      </div>
    </div>`);
  bindButtons();
}

function renderLoading(msg, sub='') {
  setApp(`
    <div class="loading">
      <div class="spinner"></div>
      <div class="loading-text">${msg}</div>
      ${sub ? `<div class="loading-sub">${sub}</div>` : ''}
    </div>`);
}

function renderBackendError() {
  setApp(`
    <div class="error-card">
      <div class="error-icon">⚠️</div>
      <div class="error-title">Backend Not Running</div>
      <div class="error-desc">
        Start JobSaathi AI backend:<br/>
        <code>cd backend</code><br/>
        <code>uvicorn app.main:app --reload</code><br/>
        on <strong>localhost:8000</strong>
      </div>
    </div>
    <button class="btn btn-outline" id="btnAnalyze">🔄 Retry</button>
    <button class="btn btn-primary" id="btnOpen">Open JobSaathi AI →</button>`);
  bindButtons();
}

function renderNotJobSite() {
  setApp(`
    <div class="welcome">
      <div class="welcome-icon">🔍</div>
      <div class="welcome-title">Not a Job Page</div>
      <div class="welcome-desc">
        Go to a job posting on LinkedIn, Naukri, Indeed,
        Internshala, or Unstop to analyze it for fraud.
      </div>
      <button class="btn btn-primary" id="btnLinkedIn">Go to LinkedIn Jobs →</button>
      <button class="btn btn-outline" id="btnOpen">Open JobSaathi AI →</button>
    </div>`);
  bindButtons();
}

function renderResult(score, data) {
  const pct     = Math.round(score * 100);
  const isHigh  = pct >= 65;
  const isMed   = pct >= 35;
  const cls     = isHigh ? 'danger' : isMed ? 'medium' : 'safe';
  const color   = isHigh ? '#EF4444' : isMed ? '#F59E0B' : '#10B981';
  const label   = isHigh ? '🚨 High Fraud Risk' : isMed ? '⚠️ Medium Risk' : '✅ Looks Genuine';
  const advice  = isHigh
    ? 'Multiple fraud signals — avoid applying!'
    : isMed ? 'Verify company details before applying.'
    : 'No major red flags detected.';

  const signals  = (data.fraud_signals || data.reasons || []).slice(0, 5);
  const llmText  = data.llm_explanation || '';
  const method   = data.analysis_method || 'ML Model';

  setApp(`
    <!-- Job Info -->
    <div class="job-info">
      <div class="job-title">${data.job_title || 'Job Posting'}</div>
      <div class="job-company">${data.company_name || 'Company not detected'}</div>
    </div>

    <!-- Score -->
    <div class="score-card ${cls}">
      <div class="score-num" style="color:${color}">${pct}%</div>
      <div class="score-label" style="color:${color}">${label}</div>
      <div class="score-desc">${advice}</div>
    </div>

    <!-- AI Explanation -->
    ${llmText ? `
    <div class="ai-explain">
      <div class="ai-explain-title">🤖 AI Analysis</div>
      <div class="ai-explain-text">${llmText}</div>
    </div>` : ''}

    <!-- Signals -->
    ${signals.length > 0 ? `
    <div style="margin-bottom:14px">
      <div class="signals-title">Risk Signals Found (${signals.length})</div>
      ${signals.map(s => `
        <div class="signal-item">
          <div class="signal-dot"></div>
          <span>${s}</span>
        </div>`).join('')}
    </div>` : `
    <div style="margin-bottom:12px">
      <div class="signals-title">Positive Signs</div>
      <div class="signal-item">
        <div class="signal-dot ok"></div>
        <span>No major fraud signals detected</span>
      </div>
    </div>`}

    <!-- Method badge -->
    <div class="method-badge">🔬 ${method}</div>

    <!-- Actions -->
    <button class="btn btn-analyze" id="btnAnalyze">🔄 Re-analyze</button>
    <button class="btn btn-primary" id="btnOpen">Full Analysis on JobSaathi →</button>`);
  bindButtons();
}


// ── Button binding (innerHTML onclick doesn't work in extensions) ──
function bindButtons() {
  const btnAnalyze  = document.getElementById('btnAnalyze');
  const btnOpen     = document.getElementById('btnOpen');
  const btnLinkedIn = document.getElementById('btnLinkedIn');

  if (btnAnalyze)  btnAnalyze.addEventListener('click',  () => analyzeTab());
  if (btnOpen) btnOpen.addEventListener('click', async () => {
    // Check if user is logged in via localStorage
    const result = await chrome.storage.local.get('jobsaathi_token');
    if (result.jobsaathi_token) {
      chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
    } else {
      chrome.tabs.create({ url: 'http://localhost:3000/login' });
    }
  });
  if (btnLinkedIn) btnLinkedIn.addEventListener('click', () => chrome.tabs.create({ url: 'https://www.linkedin.com/jobs' }));
}

// ── Core Analysis ─────────────────────────────────────────────
async function analyzeTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const tab  = tabs[0];
  if (!tab) return;

  currentTabId = tab.id;
  const url    = tab.url || '';
  const isJob  = SITES.some(s => url.includes(s));

  if (!isJob) { renderNotJobSite(); return; }

  renderLoading('Checking backend...', 'Connecting to JobSaathi AI');

  // Backend health check
  try {
    await fetch(`${API}/docs`, { mode:'no-cors', signal: AbortSignal.timeout(3000) });
  } catch(e) {
    renderBackendError(); return;
  }

  renderLoading('Extracting job details...', tab.title?.slice(0, 50) || '');

  try {
    const jobData = await chrome.tabs.sendMessage(tab.id, { action:'extractJob' });

    if (!jobData?.success) {
      renderLoading('Analyzing visible page...', 'Using page content');
      // Fallback — use page title as job title
      const fallback = {
        success: true,
        job_title: tab.title || 'Job Posting',
        job_description: tab.title || '',
        company_name: '',
      };
      await runFraudCheck(fallback);
      return;
    }

    renderLoading('Running fraud analysis...', 'ML Model + AI');
    await runFraudCheck(jobData);

  } catch(e) {
    if (e.message?.includes('Could not establish connection')) {
      renderLoading('Analyzing page...', 'Using page title');
      await runFraudCheck({
        success: true,
        job_title: tab.title || 'Job Posting',
        job_description: tab.title || 'Job posting',
        company_name: '',
      });
    } else {
      renderBackendError();
    }
  }
}

async function runFraudCheck(jobData) {
  try {
    const res = await fetch(`${API}/fraud/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_title:       jobData.job_title || '',
        job_description: jobData.job_description || jobData.job_title || '',
        company_profile: jobData.company_name || '',
        salary_range:    jobData.salary || '',
      }),
    });

    if (!res.ok) throw new Error(`API ${res.status}`);
    const result = await res.json();

    renderResult(
      result.fraud_probability || result.fraud_score || 0,
      {
        job_title:       jobData.job_title,
        company_name:    jobData.company_name,
        fraud_signals:   result.fraud_signals || result.reasons || [],
        llm_explanation: result.llm_explanation || '',
        analysis_method: result.analysis_method || '',
      }
    );

  } catch(e) {
    if (e.message?.includes('Failed to fetch')) {
      renderBackendError();
    } else {
      setApp(`
        <div class="error-card">
          <div class="error-icon">⚠️</div>
          <div class="error-title">Analysis Failed</div>
          <div class="error-desc">${e.message}</div>
        </div>
        <button class="btn btn-outline" onclick="analyzeTab()">🔄 Retry</button>`);
    }
  }
}

// ── Auto-detect when tab changes ─────────────────────────────
chrome.tabs.onActivated.addListener(async (info) => {
  const tab = await chrome.tabs.get(info.tabId);
  const isJob = SITES.some(s => (tab.url||'').includes(s));
  if (isJob) {
    document.getElementById('autoBadge').textContent = '🟢 Job Detected';
    analyzeTab();
  } else {
    document.getElementById('autoBadge').textContent = '🔍 Auto';
    renderWelcome();
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (info.status === 'complete') {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tabs[0]?.id === tabId) {
      const isJob = SITES.some(s => (tab.url||'').includes(s));
      if (isJob) {
        document.getElementById('autoBadge').textContent = '🟢 Job Detected';
        setTimeout(analyzeTab, 1500); // Wait for page to fully load
      }
    }
  }
});

// ── Init ─────────────────────────────────────────────────────
// Sync auth token from page
async function syncToken() {
  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab  = tabs[0];
    if (!tab) return;
    // Try to get token from page's localStorage
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => localStorage.getItem('token') || localStorage.getItem('access_token') || '',
    }).then(results => {
      const token = results?.[0]?.result;
      if (token) chrome.storage.local.set({ jobsaathi_token: token });
    }).catch(() => {});
  } catch(e) {}
}

syncToken();
analyzeTab();
