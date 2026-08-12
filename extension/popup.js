/**
 * JobSaathi AI Extension — Popup Script
 */

const API_BASE = 'http://localhost:8000';

const SUPPORTED_SITES = [
  'linkedin.com', 'naukri.com', 'indeed.com',
  'shine.com', 'foundit.in', 'internshala.com', 'unstop.com'
];

function renderNotJobSite() {
  document.getElementById('app').innerHTML = `
    <div style="text-align:center; padding:24px 16px">
      <div style="font-size:40px; margin-bottom:12px">🔍</div>
      <div style="font-size:14px; font-weight:700; color:#fff; margin-bottom:8px">Not a Job Page</div>
      <div style="font-size:12px; color:rgba(255,255,255,0.55); line-height:1.6; margin-bottom:16px">
        Navigate to a job posting on LinkedIn, Naukri, Indeed, Internshala, or Unstop to use fraud detection.
      </div>
      <button class="btn btn-primary" onclick="window.open('http://localhost:3000','_blank')">
        Open JobSaathi AI →
      </button>
    </div>`;
}

function renderLoading(msg) {
  document.getElementById('app').innerHTML = `
    <div class="loading">
      <div class="spinner"></div>
      <div style="font-size:13px;color:rgba(255,255,255,0.6)">${msg}</div>
    </div>`;
}

function renderBackendError() {
  document.getElementById('app').innerHTML = `
    <div class="backend-error">
      <div class="icon">⚠️</div>
      <div class="title">Backend Not Running</div>
      <div class="desc">
        Start the JobSaathi AI backend first:<br/>
        <code style="color:#0EA5E9">uvicorn app.main:app --reload</code><br/>
        on <strong>localhost:8000</strong>
      </div>
    </div>
    <button class="btn btn-outline" onclick="analyzeCurrentTab()">🔄 Retry</button>
    <button class="btn btn-primary" onclick="window.open('http://localhost:3000','_blank')">
      Open JobSaathi AI →
    </button>`;
}

function renderError(msg) {
  document.getElementById('app').innerHTML = `
    <div class="status-card">
      <div class="status-icon">⚠️</div>
      <div class="status-text">${msg}</div>
    </div>
    <button class="btn btn-outline" onclick="analyzeCurrentTab()">🔄 Try Again</button>
    <button class="btn btn-primary" onclick="window.open('http://localhost:3000','_blank')">
      Use JobSaathi AI →
    </button>`;
}

function renderResult(score, data) {
  const pct     = Math.round(score * 100);
  const isHigh  = pct >= 65;
  const isMed   = pct >= 35 && pct < 65;
  const cardCls = isHigh ? 'danger' : isMed ? 'medium' : 'safe';
  const color   = isHigh ? '#EF4444' : isMed ? '#F59E0B' : '#10B981';
  const label   = isHigh ? '🚨 High Risk' : isMed ? '⚠️ Medium Risk' : '✅ Low Risk';
  const advice  = isHigh
    ? 'Be very careful! Multiple fraud signals detected.'
    : isMed
    ? 'Proceed with caution. Verify company details.'
    : 'Looks genuine! Standard caution advised.';

  const reasons = (data.fraud_signals || data.reasons || []).slice(0, 4);
  const llmExplain = data.llm_explanation || '';

  document.getElementById('app').innerHTML = `
    <!-- Job info -->
    <div style="margin-bottom:12px; padding:10px 14px;
      background:rgba(255,255,255,0.05); border-radius:10px;
      border:1px solid rgba(255,255,255,0.08)">
      <div style="font-size:13px; font-weight:700; color:#fff; margin-bottom:3px">
        ${data.job_title || 'Job Posting'}
      </div>
      <div style="font-size:11px; color:rgba(255,255,255,0.5)">
        ${data.company_name || 'Unknown Company'}
      </div>
    </div>

    <!-- Score -->
    <div class="score-card ${cardCls}">
      <div class="score-num" style="color:${color}">${pct}</div>
      <div class="score-label" style="color:${color}">${label}</div>
      <div style="font-size:11px; color:rgba(255,255,255,0.6)">${advice}</div>
    </div>

    <!-- LLM Explanation -->
    ${llmExplain ? `
    <div class="llm-explain">
      <strong>🤖 AI Analysis</strong>
      ${llmExplain}
    </div>` : ''}

    <!-- Fraud signals -->
    ${reasons.length > 0 ? `
    <div class="reasons">
      <div style="font-size:11px; font-weight:700; color:rgba(255,255,255,0.5);
        text-transform:uppercase; letter-spacing:1px; margin-bottom:8px">
        Risk Signals Found
      </div>
      ${reasons.map(r => `
        <div class="reason-item">
          <div class="reason-dot"></div>
          <span>${r}</span>
        </div>`).join('')}
    </div>` : ''}

    <!-- Analysis method -->
    <div style="font-size:10px; color:rgba(255,255,255,0.3); text-align:right; margin-bottom:10px">
      🔬 ${data.analysis_method || 'ML Model'}
    </div>

    <!-- Actions -->
    <button class="btn btn-primary"
      onclick="window.open('http://localhost:3000','_blank')">
      View Full Analysis →
    </button>
    <button class="btn btn-outline" onclick="analyzeCurrentTab()">
      🔄 Refresh Analysis
    </button>`;
}

async function analyzeCurrentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url   = tab.url || '';

  const isJobSite = SUPPORTED_SITES.some(s => url.includes(s));
  if (!isJobSite) { renderNotJobSite(); return; }

  renderLoading('Extracting job details...');

  try {
    // Check backend is running first
    // Check backend health
    let backendOk = false;
    try {
      const health = await fetch(`${API_BASE}/docs`, {
        signal: AbortSignal.timeout(4000),
        mode: 'no-cors'  // Bypass CORS for health check
      });
      backendOk = true;
    } catch(e) {
      // Try alternate check
      try {
        await fetch(`${API_BASE}/fraud/check`, {
          method:'OPTIONS',
          signal: AbortSignal.timeout(3000)
        });
        backendOk = true;
      } catch(e2) {
        backendOk = false;
      }
    }

    if (!backendOk) { renderBackendError(); return; }

    const jobData = await chrome.tabs.sendMessage(tab.id, { action: 'extractJob' });

    if (!jobData || jobData.error || !jobData.success) {
      renderError(jobData?.error || 'Could not extract job data. Make sure the page is fully loaded.');
      return;
    }

    renderLoading('Analyzing for fraud...');

    const response = await fetch(`${API_BASE}/fraud/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_title:       jobData.job_title,
        job_description: jobData.job_description,
        company_profile: jobData.company_name,
        salary_range:    jobData.salary_range || '',
      }),
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);

    const result = await response.json();
    renderResult(
      result.fraud_probability || result.fraud_score || 0,
      {
        job_title:        jobData.job_title,
        company_name:     jobData.company_name,
        fraud_signals:    result.fraud_signals || result.reasons || [],
        llm_explanation:  result.llm_explanation || '',
        analysis_method:  result.analysis_method || '',
      }
    );

  } catch (err) {
    if (err.message.includes('Could not establish connection')) {
      renderError('Refresh the job page and try again.');
    } else if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
      renderBackendError();
    } else {
      renderError(`Error: ${err.message}`);
    }
  }
}

analyzeCurrentTab();
