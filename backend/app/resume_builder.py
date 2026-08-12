"""
resume_builder.py — HTML/CSS + WeasyPrint Resume Builder
=========================================================
13 domains × 6 designs × 2 levels × 5 layouts = 156 combinations
Gap fix: removed min-height causing whitespace issues.
"""

import io
try:
    from weasyprint import HTML as WP_HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WP_HTML = None
    WEASYPRINT_AVAILABLE = False
    print("WeasyPrint not available - resume PDF builder disabled")

# ============================================================
# DESIGNS
# ============================================================
DESIGNS = {
    "classic":   {"name":"Classic",   "description":"Black & white, max ATS",        "accent":"#1A1A1A","header_bg":"#1A1A1A","header_fg":"#FFFFFF","sidebar_bg":"#F5F5F5","sidebar_fg":"#1A1A1A","sub":"#555555"},
    "modern":    {"name":"Modern",    "description":"Teal accent, clean professional","accent":"#0D7377","header_bg":"#0D7377","header_fg":"#FFFFFF","sidebar_bg":"#E8F4F4","sidebar_fg":"#0D7377","sub":"#444444"},
    "minimal":   {"name":"Minimal",   "description":"Navy blue, ultra-clean",         "accent":"#1B3A6B","header_bg":"#1B3A6B","header_fg":"#FFFFFF","sidebar_bg":"#EEF2F8","sidebar_fg":"#1B3A6B","sub":"#444444"},
    "executive": {"name":"Executive", "description":"Charcoal + gold, premium",       "accent":"#D4AF37","header_bg":"#2C2C2C","header_fg":"#D4AF37","sidebar_bg":"#2C2C2C","sidebar_fg":"#D4AF37","sub":"#555555"},
    "creative":  {"name":"Creative",  "description":"Purple, bold distinctive",       "accent":"#6B2D8B","header_bg":"#6B2D8B","header_fg":"#FFFFFF","sidebar_bg":"#F3EAF8","sidebar_fg":"#6B2D8B","sub":"#555555"},
    "academic":  {"name":"Academic",  "description":"Dark red, publication style",    "accent":"#8B0000","header_bg":"#8B0000","header_fg":"#FFFFFF","sidebar_bg":"#FDF0F0","sidebar_fg":"#8B0000","sub":"#555555"},
}

# ============================================================
# DOMAIN CONFIGURATIONS
# ============================================================
DOMAINS = {
    # Original 5
    "software": {
        "label":"Software Engineering",
        "skills_label":"Technical Skills",
        "projects_label":"Projects",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups": None,  # simple bullet list
        "layout_fresher":"two_column",
        "layout_exp":"timeline",
        "section_order_fresher":["summary","skills","projects","education","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","certifications","education","achievements"],
    },
    "data_science": {
        "label":"Data Science",
        "skills_label":"Technical Skills & Tools",
        "projects_label":"Research & Projects",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "ML/AI":      {"machine learning","deep learning","tensorflow","pytorch","keras","scikit-learn","sklearn","nlp","computer vision","neural network","xgboost","lightgbm","catboost","bert","transformers"},
            "Programming":{"python","r","sql","java","scala","julia","c++","matlab"},
            "Libraries":  {"pandas","numpy","matplotlib","seaborn","scipy","flask","fastapi","streamlit","plotly","opencv","nltk","spacy"},
            "Tools":      {"aws","gcp","azure","docker","spark","hadoop","tableau","power bi","git","jupyter","mlflow","airflow","databricks"},
        },
        "layout_fresher":"two_column",
        "layout_exp":"sidebar",
        "section_order_fresher":["summary","skills","projects","education","experience","certifications","achievements","publications"],
        "section_order_exp":["summary","experience","skills","projects","publications","certifications","education","achievements"],
    },
    "marketing": {
        "label":"Marketing",
        "skills_label":"Marketing Skills & Tools",
        "projects_label":"Campaigns & Initiatives",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":None,
        "layout_fresher":"single_column",
        "layout_exp":"compact",
        "section_order_fresher":["summary","education","skills","projects","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","achievements","projects","certifications","education"],
    },
    "hr": {
        "label":"Human Resources",
        "skills_label":"Core Competencies",
        "projects_label":"HR Initiatives",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":None,
        "layout_fresher":"single_column",
        "layout_exp":"compact",
        "section_order_fresher":["summary","education","skills","experience","projects","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","achievements","certifications","education"],
    },
    "general": {
        "label":"General",
        "skills_label":"Skills",
        "projects_label":"Projects",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":None,
        "layout_fresher":"single_column",
        "layout_exp":"timeline",
        "section_order_fresher":["summary","education","skills","projects","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","certifications","education","achievements"],
    },
    # New 8 domains
    "aiml": {
        "label":"AI/ML Engineer",
        "skills_label":"AI/ML Skills & Frameworks",
        "projects_label":"Research & ML Projects",
        "exp_label_fresher":"Research & Internship",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Research Objective",
        "summary_exp":"AI/ML Professional Summary",
        "skills_groups":{
            "Deep Learning":  {"tensorflow","pytorch","keras","neural network","cnn","rnn","lstm","transformer","bert","gpt","diffusion","gan"},
            "ML Frameworks":  {"scikit-learn","sklearn","xgboost","lightgbm","catboost","hugging face","langchain","llamaindex"},
            "Programming":    {"python","r","julia","c++","cuda","java"},
            "MLOps & Tools":  {"mlflow","wandb","kubeflow","airflow","docker","kubernetes","aws sagemaker","gcp vertex","azure ml","git"},
            "Data & Analysis":{"pandas","numpy","scipy","matplotlib","seaborn","sql","spark","databricks","jupyter"},
        },
        "layout_fresher":"two_column",
        "layout_exp":"sidebar",
        "section_order_fresher":["summary","skills","projects","education","experience","publications","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","publications","certifications","education","achievements"],
    },
    "devops": {
        "label":"DevOps/Cloud Engineer",
        "skills_label":"DevOps & Cloud Skills",
        "projects_label":"Infrastructure & Projects",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "Cloud Platforms":{"aws","gcp","azure","digitalocean","heroku","cloudflare"},
            "Containers & Orchestration":{"docker","kubernetes","helm","istio","openshift","rancher"},
            "CI/CD":          {"jenkins","github actions","gitlab ci","circleci","travis ci","argocd","spinnaker"},
            "IaC & Config":   {"terraform","ansible","puppet","chef","cloudformation","pulumi"},
            "Monitoring":     {"prometheus","grafana","datadog","splunk","elk","pagerduty","new relic"},
            "Programming":    {"python","bash","go","ruby","groovy","yaml"},
        },
        "layout_fresher":"two_column",
        "layout_exp":"timeline",
        "section_order_fresher":["summary","skills","projects","education","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","certifications","education","achievements"],
    },
    "cybersecurity": {
        "label":"Cybersecurity",
        "skills_label":"Security Skills & Tools",
        "projects_label":"Security Projects & CTF",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "Offensive Security":{"penetration testing","ethical hacking","metasploit","burp suite","kali linux","nmap","sqlmap","wireshark"},
            "Defensive Security":{"siem","soc","ids/ips","firewall","dlp","edr","xdr","threat intelligence"},
            "Cloud Security":    {"aws security","azure security","gcp security","iam","waf","zero trust"},
            "Frameworks":        {"nist","iso 27001","pci dss","gdpr","owasp","cis"},
            "Programming":       {"python","bash","powershell","c","c++","assembly"},
        },
        "layout_fresher":"two_column",
        "layout_exp":"sidebar",
        "section_order_fresher":["summary","skills","projects","education","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","certifications","education","achievements"],
    },
    "finance": {
        "label":"Finance & Banking",
        "skills_label":"Financial Skills & Tools",
        "projects_label":"Financial Projects & Analysis",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "Financial Analysis":{"financial modeling","valuation","dcf","lbo","m&a","equity research","risk management","derivatives"},
            "Tools":             {"bloomberg","excel","vba","python","r","tableau","power bi","sql","sap"},
            "Accounting":        {"ifrs","gaap","taxation","auditing","cost accounting","financial reporting"},
            "Banking":           {"credit analysis","loan structuring","trade finance","treasury","forex"},
        },
        "layout_fresher":"single_column",
        "layout_exp":"compact",
        "section_order_fresher":["summary","education","skills","experience","projects","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","achievements","certifications","education"],
    },
    "product": {
        "label":"Product Management",
        "skills_label":"Product & Management Skills",
        "projects_label":"Products & Initiatives",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "Product Skills":  {"product roadmap","agile","scrum","kanban","user stories","okr","kpi","a/b testing","product analytics"},
            "Tools":           {"jira","confluence","figma","notion","miro","amplitude","mixpanel","google analytics","productboard"},
            "Technical":       {"sql","python","api","data analysis","wireframing","prototyping"},
            "Soft Skills":     {"stakeholder management","cross-functional","prioritization","go-to-market","user research"},
        },
        "layout_fresher":"single_column",
        "layout_exp":"compact",
        "section_order_fresher":["summary","education","skills","projects","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","achievements","certifications","education"],
    },
    "design": {
        "label":"UI/UX Design",
        "skills_label":"Design Skills & Tools",
        "projects_label":"Design Projects & Case Studies",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Design Objective",
        "summary_exp":"Design Professional Summary",
        "skills_groups":{
            "Design Tools":   {"figma","sketch","adobe xd","invision","zeplin","principle","framer","canva","illustrator","photoshop"},
            "Research":       {"user research","usability testing","a/b testing","heatmaps","surveys","personas","journey mapping"},
            "Frontend":       {"html","css","react","javascript","tailwind","bootstrap","responsive design"},
            "Methodologies":  {"design thinking","human centered design","agile","lean ux","atomic design","design systems"},
        },
        "layout_fresher":"two_column",
        "layout_exp":"sidebar",
        "section_order_fresher":["summary","skills","projects","education","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","certifications","education","achievements"],
    },
    "business_analyst": {
        "label":"Business Analyst",
        "skills_label":"Analysis & Business Skills",
        "projects_label":"Business Analysis Projects",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "Analysis":     {"requirements gathering","gap analysis","process mapping","bpmn","use cases","user stories","feasibility"},
            "Tools":        {"jira","confluence","ms visio","lucidchart","excel","power bi","tableau","sql","salesforce"},
            "Methodologies":{"agile","scrum","waterfall","six sigma","lean","brd","frd"},
            "Soft Skills":  {"stakeholder management","communication","problem solving","presentation","documentation"},
        },
        "layout_fresher":"single_column",
        "layout_exp":"compact",
        "section_order_fresher":["summary","education","skills","projects","experience","certifications","achievements"],
        "section_order_exp":["summary","experience","skills","projects","achievements","certifications","education"],
    },
    "sales": {
        "label":"Sales & Business Development",
        "skills_label":"Sales Skills & Tools",
        "projects_label":"Sales Campaigns & Initiatives",
        "exp_label_fresher":"Internship & Experience",
        "exp_label_exp":"Work Experience",
        "summary_fresher":"Objective",
        "summary_exp":"Professional Summary",
        "skills_groups":{
            "Sales Skills":  {"b2b sales","b2c sales","lead generation","cold calling","negotiation","account management","crm"},
            "Tools":         {"salesforce","hubspot","zoho","linkedin sales navigator","outreach","pipedrive","excel"},
            "Methodologies": {"solution selling","spin selling","challenger sale","sandler","consultative selling"},
        },
        "layout_fresher":"single_column",
        "layout_exp":"compact",
        "section_order_fresher":["summary","education","skills","experience","achievements","projects","certifications"],
        "section_order_exp":["summary","experience","achievements","skills","certifications","education"],
    },
}


# ============================================================
# LEVEL CONFIGURATIONS
# ============================================================
# Maps each level to its labels and layout preferences.
# Domains can override layout per level via DOMAIN_LAYOUT_OVERRIDES.
LEVELS = {
    "fresher": {
        "exp_label":    "Internship & Experience",
        "sum_label":    "Objective",
        "layout_pref":  "two_column",   # default, domain may override
        "section_order":["summary","skills","projects","education","experience","certifications","achievements","publications"],
    },
    "junior": {
        "exp_label":    "Work Experience",
        "sum_label":    "Objective",
        "layout_pref":  "two_column",
        "section_order":["summary","skills","experience","projects","education","certifications","achievements"],
    },
    "mid": {
        "exp_label":    "Work Experience",
        "sum_label":    "Professional Summary",
        "layout_pref":  "timeline",
        "section_order":["summary","experience","skills","projects","certifications","education","achievements"],
    },
    "senior": {
        "exp_label":    "Work Experience",
        "sum_label":    "Senior Professional Summary",
        "layout_pref":  "sidebar",
        "section_order":["summary","experience","achievements","skills","projects","certifications","education"],
    },
    "lead": {
        "exp_label":    "Leadership & Work Experience",
        "sum_label":    "Leadership Profile",
        "layout_pref":  "compact",
        "section_order":["summary","experience","achievements","skills","certifications","projects","education"],
    },
}

# Per-domain layout overrides per level
# Format: {domain: {level: layout}}
DOMAIN_LAYOUT_OVERRIDES = {
    "software":        {"fresher":"two_column", "junior":"two_column", "mid":"timeline",  "senior":"sidebar", "lead":"compact"},
    "data_science":    {"fresher":"two_column", "junior":"two_column", "mid":"sidebar",   "senior":"sidebar", "lead":"compact"},
    "aiml":            {"fresher":"two_column", "junior":"two_column", "mid":"sidebar",   "senior":"sidebar", "lead":"compact"},
    "devops":          {"fresher":"two_column", "junior":"two_column", "mid":"timeline",  "senior":"sidebar", "lead":"compact"},
    "cybersecurity":   {"fresher":"two_column", "junior":"two_column", "mid":"sidebar",   "senior":"sidebar", "lead":"compact"},
    "marketing":       {"fresher":"single_column","junior":"single_column","mid":"compact","senior":"compact","lead":"compact"},
    "hr":              {"fresher":"single_column","junior":"single_column","mid":"compact","senior":"compact","lead":"compact"},
    "finance":         {"fresher":"single_column","junior":"single_column","mid":"compact","senior":"compact","lead":"compact"},
    "product":         {"fresher":"single_column","junior":"single_column","mid":"compact","senior":"compact","lead":"compact"},
    "design":          {"fresher":"two_column", "junior":"two_column", "mid":"sidebar",   "senior":"sidebar", "lead":"compact"},
    "business_analyst":{"fresher":"single_column","junior":"single_column","mid":"compact","senior":"compact","lead":"compact"},
    "sales":           {"fresher":"single_column","junior":"single_column","mid":"compact","senior":"compact","lead":"compact"},
    "general":         {"fresher":"single_column","junior":"two_column", "mid":"timeline", "senior":"sidebar","lead":"compact"},
}

# ============================================================
# BASE CSS (gap fixed — no min-height)
# ============================================================
def _base_css(d):
    return f"""
    @page {{ size: A4; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 9.5pt;
        color: #222;
        background: white;
        width: 210mm;
    }}
    .header {{
        background: {d['header_bg']};
        color: {d['header_fg']};
        padding: 16px 24px 12px;
        text-align: center;
        width: 100%;
    }}
    .header h1 {{
        font-size: 22pt;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
        color: {d['header_fg']};
    }}
    .header .contact {{
        font-size: 8pt;
        color: {d['header_fg']};
        opacity: 0.9;
        line-height: 1.4;
    }}
    .header .contact span {{ margin: 0 4px; opacity: 0.5; }}
    .main-content {{ padding: 10px 18px; }}
    .section {{ margin-bottom: 7px; }}
    .section-title {{
        font-size: 9pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {d['accent']};
        margin-bottom: 2px;
        padding-bottom: 2px;
        border-bottom: 1.5px solid {d['accent']};
    }}
    .role-row {{
        display: flex;
        justify-content: space-between;
        margin-top: 4px;
    }}
    .role-title {{ font-size: 9.5pt; font-weight: 700; color: #111; }}
    .role-date  {{ font-size: 8pt; color: {d['accent']}; font-weight: 600; white-space: nowrap; margin-left: 8px; }}
    .company    {{ font-size: 8pt; color: {d['sub']}; margin: 1px 0 2px; }}
    ul {{ padding-left: 12px; margin: 1px 0 4px; }}
    li {{ margin-bottom: 1px; line-height: 1.35; font-size: 9pt; }}
    .skill-group {{ margin-bottom: 2px; line-height: 1.35; font-size: 9pt; }}
    .skill-group b {{ color: #111; }}
    .project-name {{ font-size: 9.5pt; font-weight: 700; color: #111; margin-top: 4px; }}
    .project-tech {{ font-size: 8pt; color: {d['sub']}; font-style: italic; margin: 1px 0; }}
    .cert-item, .ach-item, .pub-item {{ margin-bottom: 2px; line-height: 1.35; font-size: 9pt; }}
    p {{ line-height: 1.4; font-size: 9pt; }}
    """

def _sidebar_css(d):
    return f"""
    .two-col {{
        display: flex;
        min-height: calc(297mm - 80px);
    }}
    .sidebar {{
        width: 31%;
        background: {d['sidebar_bg']};
        padding: 14px 12px;
        flex-shrink: 0;
    }}
    .sidebar .section-title {{
        color: {d['sidebar_fg']};
        border-bottom-color: {d['sidebar_fg']};
        font-size: 8.5pt;
    }}
    .sidebar .skill-group b {{ color: {d['sidebar_fg']}; }}
    .sidebar .cert-item, .sidebar .ach-item {{ font-size: 8.5pt; }}
    .main {{ width: 69%; padding: 14px 16px; }}
    """

# ============================================================
# HTML HELPERS
# ============================================================
def _contact(data):
    parts = [x for x in [data.get("email"), data.get("phone"),
             data.get("location"), data.get("linkedin"), data.get("github")] if x]
    return " <span>|</span> ".join(parts)

def _skills_html(data, domain_cfg, sidebar=False):
    skills = data.get("skills", [])
    if not skills:
        return ""
    groups = domain_cfg.get("skills_groups")
    if groups:
        html = ""
        buckets = {g: [] for g in groups}
        buckets["Other"] = []
        for s in skills:
            sl = s.lower()
            placed = False
            for grp, terms in groups.items():
                if any(t in sl for t in terms):
                    buckets[grp].append(s)
                    placed = True
                    break
            if not placed:
                buckets["Other"].append(s)
        for grp, items in buckets.items():
            if items:
                html += f'<div class="skill-group"><b>{grp}:</b> {", ".join(items)}</div>'
        return html
    else:
        if sidebar:
            return "".join(f'<div class="cert-item">• {s}</div>' for s in skills)
        return f'<div>{" &nbsp;•&nbsp; ".join(skills)}</div>'

def _exp_html(data):
    html = ""
    for exp in data.get("experience", []):
        html += f'''<div class="role-row">
            <span class="role-title">{exp.get("title","")}</span>
            <span class="role-date">{exp.get("duration","")}</span>
        </div>
        <div class="company">{exp.get("company","")}</div>
        <ul>{"".join(f"<li>{b}</li>" for b in exp.get("bullets",[]))}</ul>'''
    return html

def _edu_html(data):
    html = ""
    for edu in data.get("education", []):
        gpa = f' &nbsp;|&nbsp; GPA: {edu["gpa"]}' if edu.get("gpa") else ""
        html += f'''<div class="role-row">
            <span class="role-title">{edu.get("degree","")}</span>
            <span class="role-date">{edu.get("year","")}</span>
        </div>
        <div class="company">{edu.get("institution","")}{gpa}</div>'''
    return html

def _edu_sidebar(data):
    html = ""
    for edu in data.get("education", []):
        gpa = f'<br><small>GPA: {edu["gpa"]}</small>' if edu.get("gpa") else ""
        html += f'<div style="margin-bottom:5px"><b>{edu.get("degree","")}</b><br>{edu.get("institution","")}<br>{edu.get("year","")}{gpa}</div>'
    return html

def _proj_html(data, domain_cfg):
    html = ""
    for proj in data.get("projects", []):
        name = proj.get("name","")
        if proj.get("link"): name += f' &nbsp;·&nbsp; <span style="font-weight:400;font-size:8pt">{proj["link"]}</span>'
        html += f'<div class="project-name">{name}</div>'
        if proj.get("tech"): html += f'<div class="project-tech">Tech: {proj["tech"]}</div>'
        if proj.get("description"): html += f'<div style="margin-bottom:2px">{proj["description"]}</div>'
        if proj.get("metrics"): html += f'<ul><li>{proj["metrics"]}</li></ul>'
    return html

def _sec(title, content):
    if not content.strip():
        return ""
    return f'<div class="section"><div class="section-title">{title}</div>{content}</div>'

def _list_items(items):
    return "".join(f'<div class="cert-item">• {i}</div>' for i in items) if items else ""

# ============================================================
# LAYOUT BUILDERS
# ============================================================
def _build_sections(data, domain_cfg, level, sections, page_width="full"):
    dc = domain_cfg
    html = ""
    lc = LEVELS.get(level, LEVELS["fresher"])
    exp_label = lc["exp_label"]
    sum_label  = lc["sum_label"]

    for sec in sections:
        if   sec=="summary"        and data.get("summary"):
            html += _sec(sum_label, f'<p style="line-height:1.5">{data["summary"]}</p>')
        elif sec=="experience"     and data.get("experience"):
            html += _sec(exp_label, _exp_html(data))
        elif sec=="education"      and data.get("education"):
            html += _sec("Education", _edu_html(data))
        elif sec=="skills"         and data.get("skills"):
            html += _sec(dc["skills_label"], _skills_html(data, dc))
        elif sec=="projects"       and data.get("projects"):
            html += _sec(dc["projects_label"], _proj_html(data, dc))
        elif sec=="certifications" and data.get("certifications"):
            html += _sec("Certifications", _list_items(data["certifications"]))
        elif sec=="achievements"   and data.get("achievements"):
            html += _sec("Achievements & Awards", _list_items(data["achievements"]))
        elif sec=="publications"   and data.get("publications"):
            html += _sec("Publications & Research", _list_items(data["publications"]))
    return html

def _build_sidebar_content(data, domain_cfg, level):
    dc = domain_cfg
    html = ""
    if data.get("skills"):
        html += f'<div class="section"><div class="section-title">{dc["skills_label"]}</div>{_skills_html(data, dc, sidebar=True)}</div>'
    if data.get("education"):
        html += f'<div class="section"><div class="section-title">Education</div>{_edu_sidebar(data)}</div>'
    if data.get("certifications"):
        html += f'<div class="section"><div class="section-title">Certifications</div>{_list_items(data["certifications"])}</div>'
    if data.get("achievements"):
        html += f'<div class="section"><div class="section-title">Achievements</div>{_list_items(data["achievements"])}</div>'
    return html

# ============================================================
# 5 LAYOUT TEMPLATES
# ============================================================
def _single_column(data, d, dc, level):
    lc2 = LEVELS.get(level, LEVELS["fresher"])
    sections_html = _build_sections(data, dc, level, lc2["section_order"])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>{_base_css(d)}</style></head><body>
    <div class="header"><h1>{data.get("name","Your Name")}</h1>
    <div class="contact">{_contact(data)}</div></div>
    <div class="main-content">{sections_html}</div></body></html>'''

def _two_column(data, d, dc, level):
    lc2 = LEVELS.get(level, LEVELS["fresher"])
    sidebar_w = "32%"
    main_w = "68%"
    sidebar_html = _build_sidebar_content(data, dc, level)
    # Main: summary + projects + experience + publications
    main_sections = [s for s in lc2["section_order"] if s not in ("skills","education","certifications","achievements")]
    main_html = _build_sections(data, dc, level, main_sections)
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>{_base_css(d)}{_sidebar_css(d)}</style></head><body>
    <div class="header"><h1>{data.get("name","Your Name")}</h1>
    <div class="contact">{_contact(data)}</div></div>
    <div class="two-col">
        <div class="sidebar">{sidebar_html}</div>
        <div class="main">{main_html}</div>
    </div></body></html>'''

def _sidebar_layout(data, d, dc, level):
    lc2 = LEVELS.get(level, LEVELS["fresher"])
    sidebar_html = _build_sidebar_content(data, dc, level)
    main_sections = [s for s in lc2["section_order"] if s not in ("skills","education","certifications")]
    main_html = _build_sections(data, dc, level, main_sections)
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>{_base_css(d)}{_sidebar_css(d)}</style></head><body>
    <div class="header"><h1>{data.get("name","Your Name")}</h1>
    <div class="contact">{_contact(data)}</div></div>
    <div class="two-col">
        <div class="sidebar">{sidebar_html}</div>
        <div class="main">{main_html}</div>
    </div></body></html>'''

def _timeline(data, d, dc, level):
    lc2 = LEVELS.get(level, LEVELS["fresher"])
    lc = lc2
    exp_label = lc["exp_label"]
    sum_label  = lc["sum_label"]

    timeline_css = f"""
    .tl-item {{ display: flex; margin-bottom: 8px; }}
    .tl-left {{ width: 48px; min-width: 48px; text-align: center; padding-top: 2px; }}
    .tl-year {{ font-size: 8pt; font-weight: 700; color: {d['accent']}; }}
    .tl-dot {{ width: 9px; height: 9px; border-radius: 50%; background: {d['accent']}; margin: 3px auto 0; }}
    .tl-body {{ flex: 1; padding-left: 10px; }}
    """

    exp_html = ""
    for exp in data.get("experience", []):
        yr = exp.get("duration","").split("-")[0].strip()[-4:] if exp.get("duration") else ""
        bullets = "".join(f"<li>{b}</li>" for b in exp.get("bullets",[]))
        exp_html += f'''<div class="tl-item">
            <div class="tl-left"><div class="tl-year">{yr}</div><div class="tl-dot"></div></div>
            <div class="tl-body">
                <div class="role-row"><span class="role-title">{exp.get("title","")}</span>
                <span class="role-date">{exp.get("duration","")}</span></div>
                <div class="company">{exp.get("company","")}</div>
                <ul>{bullets}</ul>
            </div></div>'''

    # Build other sections
    other_sections = [s for s in lc2["section_order"] if s != "experience"]
    other_html = _build_sections(data, dc, level, other_sections)

    sections_html = ""
    if data.get("summary"):
        sections_html += _sec(sum_label, f'<p style="line-height:1.5">{data["summary"]}</p>')
    if data.get("experience"):
        sections_html += _sec(exp_label, exp_html)
    sections_html += other_html

    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>{_base_css(d)}{timeline_css}</style></head><body>
    <div class="header"><h1>{data.get("name","Your Name")}</h1>
    <div class="contact">{_contact(data)}</div></div>
    <div class="main-content">{sections_html}</div></body></html>'''

def _compact(data, d, dc, level):
    lc2 = LEVELS.get(level, LEVELS["fresher"])
    compact_css = """
    body { font-size: 9pt; }
    .section { margin-bottom: 6px; }
    .section-title { font-size: 8.5pt; padding-bottom: 2px; margin-bottom: 2px; }
    .role-row { margin-top: 3px; }
    ul { margin: 2px 0 3px; }
    li { margin-bottom: 1px; }
    .inline-item { margin-bottom: 2px; }
    """
    sections_html = _build_sections(data, dc, level, lc2["section_order"])
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>{_base_css(d)}{compact_css}</style></head><body>
    <div class="header"><h1>{data.get("name","Your Name")}</h1>
    <div class="contact">{_contact(data)}</div></div>
    <div class="main-content">{sections_html}</div></body></html>'''

# ============================================================
# MAIN ENTRY POINT
# ============================================================
def build_resume_pdf(data: dict, design: str = "modern",
                     level: str = "fresher", domain: str = "software") -> bytes:
    """
    Builds a professional PDF resume.

    Engine routing:
      jakescv, altacv, moderncv, awesomecv, deedycv, elegant, skillbars
                              → latex_templates_builder (Overleaf quality)
      classic, academic, executive
                              → latex_resume_builder (pdflatex)
      altacv, skillbars, colorbox, premium
                              → latex_premium_builder (xelatex premium)
      modern, minimal, creative
                              → WeasyPrint (colorful HTML/CSS)

    Falls back to WeasyPrint if LaTeX not installed.
    """
    # ── Overleaf-style templates (new) ──────────────────────
    OVERLEAF_DESIGNS = {"jakescv","altacv","moderncv","awesomecv","deedycv","elegant","skillbars"}
    if design in OVERLEAF_DESIGNS:
        # Try LaTeX first (best quality)
        try:
            from latex_templates_builder import build_template_pdf
            return build_template_pdf(data, template=design, level=level, domain=domain)
        except Exception as e:
            print(f"[resume_builder] LaTeX failed ({e}), trying HTML templates...")

        # Fallback: HTML templates (WeasyPrint) — works without LaTeX
        try:
            from resume_templates_html import build_html_template_pdf
            return build_html_template_pdf(data, template=design)
        except Exception as e2:
            print(f"[resume_builder] HTML template failed ({e2}), falling back to generic WeasyPrint")

    # ── Standard LaTeX (pdflatex) ────────────────────────────
    LATEX_DESIGNS = {"classic", "academic", "executive"}
    if design in LATEX_DESIGNS:
        try:
            from latex_resume_builder import build_latex_resume
            return build_latex_resume(data, design=design, level=level, domain=domain)
        except Exception as e:
            print(f"[resume_builder] LaTeX failed ({e}), falling back to WeasyPrint")

    # ── Premium xelatex ─────────────────────────────────────
    PREMIUM_DESIGNS = {"colorbox", "premium"}
    if design in PREMIUM_DESIGNS:
        try:
            from latex_premium_builder import build_premium_pdf
            return build_premium_pdf(data, design=design, level=level, domain=domain)
        except Exception as e:
            print(f"[resume_builder] Premium LaTeX failed ({e}), falling back to WeasyPrint")

    # WeasyPrint path
    d   = DESIGNS.get(design, DESIGNS["modern"])
    dc  = DOMAINS.get(domain, DOMAINS["general"])
    lc  = LEVELS.get(level, LEVELS["fresher"])
    overrides = DOMAIN_LAYOUT_OVERRIDES.get(domain, {})
    layout = overrides.get(level, lc["layout_pref"])
    builders = {
        "single_column": _single_column,
        "two_column":    _two_column,
        "sidebar":       _sidebar_layout,
        "timeline":      _timeline,
        "compact":       _compact,
    }
    html_str = builders.get(layout, _single_column)(data, d, dc, level)
    return WP_HTML(string=html_str).write_pdf()

def get_available_templates() -> list:
    """Returns all available templates — standard + overleaf + premium."""
    try:
        from latex_premium_builder import get_premium_templates
        premium = get_premium_templates()
    except ImportError:
        premium = []

    try:
        from latex_templates_builder import get_all_templates
        overleaf = get_all_templates()
    except ImportError:
        overleaf = []

    LATEX_DESIGNS = {"classic", "academic", "executive"}

    level_labels = {
        "fresher": "Fresher",
        "junior":  "Junior (0-2 yrs)",
        "mid":     "Mid-Level (2-5 yrs)",
        "senior":  "Senior (5-8 yrs)",
        "lead":    "Lead/Principal (8+ yrs)",
    }

    # Standard WeasyPrint + LaTeX templates
    standard = [
        {"id": f"{ds}_{lv}_{dm}",
         "design": ds,
         "design_name": DESIGNS[ds]["name"],
         "design_description": DESIGNS[ds]["description"],
         "level": lv,
         "level_label": level_labels.get(lv, lv),
         "domain": dm,
         "domain_label": DOMAINS[dm]["label"],
         "layout": DOMAIN_LAYOUT_OVERRIDES.get(dm, {}).get(lv,
                   LEVELS.get(lv, LEVELS["fresher"])["layout_pref"]),
         "engine": "LaTeX (Overleaf quality)" if ds in LATEX_DESIGNS else "WeasyPrint (colorful)",
         "tier": "standard"}
        for ds in DESIGNS
        for lv in LEVELS
        for dm in DOMAINS
    ]

    return standard + overleaf + premium