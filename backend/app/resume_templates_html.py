"""
resume_templates_html.py
------------------------
7 distinct HTML resume templates using WeasyPrint.
No LaTeX/MiKTeX required — works on any server.

Templates:
  jakescv    - Clean single column, ATS-friendly
  altacv     - Two column with colored sidebar
  moderncv   - Timeline style with accent bar
  awesomecv  - Bold header, section dividers
  deedycv    - Dark sidebar, two column
  elegant    - Minimal, double ruled sections
  skillbars  - Visual skill progress bars
"""

from weasyprint import HTML, CSS


# ── Common helpers ────────────────────────────────────────────
def _skills(data):
    return data.get("skills", [])

def _exp(data):
    return data.get("experience", [])

def _edu(data):
    return data.get("education", [])

def _proj(data):
    return data.get("projects", [])

def _certs(data):
    return data.get("certifications", [])

def _ach(data):
    return data.get("achievements", [])

def _contact_row(data):
    parts = []
    if data.get("email"):    parts.append(f'✉ {data["email"]}')
    if data.get("phone"):    parts.append(f'☎ {data["phone"]}')
    if data.get("location"): parts.append(f'📍 {data["location"]}')
    if data.get("linkedin"): parts.append(f'🔗 {data["linkedin"]}')
    if data.get("github"):   parts.append(f'⌥ {data["github"]}')
    return "  |  ".join(parts)

def _bullets(bullets):
    if not bullets: return ""
    items = "".join(f"<li>{b}</li>" for b in bullets if b and b.strip())
    return f"<ul>{items}</ul>" if items else ""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 1 — Jake's CV (Clean ATS single column)
# ══════════════════════════════════════════════════════════════
def _build_jakescv(data):
    name    = data.get("name", "")
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)
    certs   = _certs(data)

    exp_html = ""
    for e in exp:
        bullets = _bullets(e.get("bullets", []))
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <span class="entry-title">{e.get('title','')}</span>
            <span class="entry-right">{e.get('duration','')}</span>
          </div>
          <div class="entry-sub">{e.get('company','')} — {e.get('location','')}</div>
          {bullets}
        </div>"""

    edu_html = ""
    for e in edu:
        edu_html += f"""
        <div class="entry">
          <div class="entry-header">
            <span class="entry-title">{e.get('degree','')}</span>
            <span class="entry-right">{e.get('year','')}</span>
          </div>
          <div class="entry-sub">{e.get('institution','')}
            {f" — GPA: {e.get('gpa')}" if e.get('gpa') else ""}</div>
        </div>"""

    proj_html = ""
    for p in proj:
        proj_html += f"""
        <div class="entry">
          <div class="entry-header">
            <span class="entry-title">{p.get('name','')}
              <span class="tech"> | {p.get('tech','')}</span></span>
          </div>
          <p class="proj-desc">{p.get('description','')}</p>
          {f'<p class="metrics">📊 {p.get("metrics")}</p>' if p.get('metrics') else ''}
        </div>"""

    skills_html = " • ".join(f"<span>{s}</span>" for s in skills)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Times New Roman', serif; font-size: 10.5pt;
         color: #000; padding: 18px 22px; max-width: 700px; margin: auto; }}
  h1 {{ font-size: 22pt; text-align: center; letter-spacing: 1px; margin-bottom: 2px; }}
  .contact {{ text-align: center; font-size: 9pt; color: #333; margin-bottom: 10px; }}
  .section {{ margin-bottom: 10px; }}
  .section-title {{ font-size: 11pt; font-weight: bold; text-transform: uppercase;
    letter-spacing: 1px; border-bottom: 1.5px solid #000; margin-bottom: 5px; padding-bottom: 2px; }}
  .entry {{ margin-bottom: 7px; }}
  .entry-header {{ display: flex; justify-content: space-between; }}
  .entry-title {{ font-weight: bold; font-size: 10.5pt; }}
  .entry-right {{ font-size: 9.5pt; color: #333; }}
  .entry-sub {{ font-style: italic; font-size: 9.5pt; color: #444; margin-bottom: 2px; }}
  ul {{ margin-left: 16px; }}
  li {{ margin-bottom: 2px; font-size: 10pt; }}
  .tech {{ font-weight: normal; font-style: italic; }}
  .proj-desc {{ font-size: 9.5pt; margin-top: 2px; }}
  .metrics {{ font-size: 9pt; color: #555; margin-top: 2px; }}
  .skills-row {{ font-size: 10pt; line-height: 1.7; }}
  .summary {{ font-size: 10pt; line-height: 1.6; margin-bottom: 8px; }}
</style></head><body>
  <h1>{name}</h1>
  <div class="contact">{_contact_row(data)}</div>
  {f'<div class="summary">{summary}</div>' if summary else ''}

  {f'''<div class="section">
    <div class="section-title">Skills</div>
    <div class="skills-row">{skills_html}</div>
  </div>''' if skills else ''}

  {f'''<div class="section">
    <div class="section-title">Experience</div>
    {exp_html}
  </div>''' if exp else ''}

  {f'''<div class="section">
    <div class="section-title">Projects</div>
    {proj_html}
  </div>''' if proj else ''}

  {f'''<div class="section">
    <div class="section-title">Education</div>
    {edu_html}
  </div>''' if edu else ''}

  {f'''<div class="section">
    <div class="section-title">Certifications</div>
    {"".join(f"<div>• {c}</div>" for c in certs)}
  </div>''' if certs else ''}
</body></html>"""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 2 — AltaCV (Two column with teal sidebar)
# ══════════════════════════════════════════════════════════════
def _build_altacv(data):
    name    = data.get("name", "")
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)
    certs   = _certs(data)

    exp_html = ""
    for e in exp:
        exp_html += f"""
        <div class="entry">
          <div class="entry-title">{e.get('title','')} — <em>{e.get('company','')}</em></div>
          <div class="entry-date">{e.get('duration','')}</div>
          {_bullets(e.get('bullets',[]))}
        </div>"""

    proj_html = ""
    for p in proj:
        proj_html += f"""
        <div class="entry">
          <div class="entry-title">{p.get('name','')} <span class="tag">{p.get('tech','')}</span></div>
          <p>{p.get('description','')}</p>
        </div>"""

    skills_html = "".join(f'<div class="skill-tag">{s}</div>' for s in skills)

    edu_html = ""
    for e in edu:
        edu_html += f"""
        <div class="entry">
          <div class="entry-title">{e.get('degree','')}</div>
          <div class="entry-date">{e.get('institution','')} | {e.get('year','')}</div>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #2d2d2d; }}
  .container {{ display: flex; min-height: 100vh; }}
  .sidebar {{ width: 33%; background: #00796B; color: #fff; padding: 20px 14px; }}
  .main {{ width: 67%; padding: 20px 18px; }}
  h1 {{ font-size: 20pt; color: #fff; margin-bottom: 4px; }}
  .tagline {{ font-size: 10pt; color: #b2dfdb; margin-bottom: 16px; }}
  .side-section {{ margin-bottom: 16px; }}
  .side-title {{ font-size: 9pt; text-transform: uppercase; letter-spacing: 1.5px;
    color: #b2dfdb; border-bottom: 1px solid #4db6ac; margin-bottom: 6px; padding-bottom: 2px; }}
  .contact-item {{ font-size: 9pt; margin-bottom: 4px; color: #e0f2f1; }}
  .skill-tag {{ display: inline-block; background: rgba(255,255,255,0.15);
    color: #fff; padding: 2px 8px; border-radius: 10px; margin: 2px; font-size: 8.5pt; }}
  .section-title {{ font-size: 13pt; color: #00796B; border-bottom: 2px solid #00796B;
    margin-bottom: 10px; padding-bottom: 3px; margin-top: 14px; font-weight: bold; }}
  .section-title:first-child {{ margin-top: 0; }}
  .entry {{ margin-bottom: 10px; }}
  .entry-title {{ font-weight: bold; font-size: 10.5pt; }}
  .entry-date {{ font-size: 9pt; color: #777; font-style: italic; margin-bottom: 3px; }}
  ul {{ margin-left: 16px; }} li {{ margin-bottom: 2px; font-size: 9.5pt; }}
  .tag {{ font-size: 8.5pt; background: #e0f2f1; color: #00796B;
    padding: 1px 6px; border-radius: 8px; margin-left: 6px; }}
  p {{ font-size: 9.5pt; line-height: 1.5; margin-top: 3px; }}
</style></head><body>
<div class="container">
  <div class="sidebar">
    <h1>{name}</h1>
    <div class="tagline">{summary[:80] + '...' if len(summary) > 80 else summary}</div>
    <div class="side-section">
      <div class="side-title">Contact</div>
      {''.join(f'<div class="contact-item">{c}</div>' for c in [data.get("email",""), data.get("phone",""), data.get("location","")] if c)}
    </div>
    <div class="side-section">
      <div class="side-title">Skills</div>
      {skills_html}
    </div>
    {f'''<div class="side-section">
      <div class="side-title">Education</div>
      {edu_html}
    </div>''' if edu else ''}
    {f'''<div class="side-section">
      <div class="side-title">Certifications</div>
      {"".join(f'<div class="contact-item">• {c}</div>' for c in certs)}
    </div>''' if certs else ''}
  </div>
  <div class="main">
    {f'<div class="section-title">Experience</div>{exp_html}' if exp else ''}
    {f'<div class="section-title">Projects</div>{proj_html}' if proj else ''}
  </div>
</div>
</body></html>"""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 3 — ModernCV (Blue accent, timeline style)
# ══════════════════════════════════════════════════════════════
def _build_moderncv(data):
    name    = data.get("name", "")
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)
    certs   = _certs(data)

    def timeline_entry(left, right):
        return f"""<div class="tl-row"><div class="tl-left">{left}</div>
        <div class="tl-dot"></div><div class="tl-right">{right}</div></div>"""

    exp_html = "".join(timeline_entry(
        f"<div class='tl-date'>{e.get('duration','')}</div><div class='tl-place'>{e.get('company','')}</div>",
        f"<div class='tl-title'>{e.get('title','')}</div>{_bullets(e.get('bullets',[]))}"
    ) for e in exp)

    edu_html = "".join(timeline_entry(
        f"<div class='tl-date'>{e.get('year','')}</div><div class='tl-place'>{e.get('institution','')}</div>",
        f"<div class='tl-title'>{e.get('degree','')}</div>"
    ) for e in edu)

    proj_html = "".join(timeline_entry(
        f"<div class='tl-date'></div><div class='tl-place'>{p.get('tech','')}</div>",
        f"<div class='tl-title'>{p.get('name','')}</div><p>{p.get('description','')}</p>"
    ) for p in proj)

    skills_html = " &nbsp;·&nbsp; ".join(skills)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #333; padding: 20px 24px; }}
  .header {{ border-bottom: 3px solid #1565C0; padding-bottom: 10px; margin-bottom: 16px; }}
  h1 {{ font-size: 24pt; color: #1565C0; letter-spacing: 2px; }}
  .contact {{ font-size: 9pt; color: #555; margin-top: 4px; }}
  .section {{ margin-bottom: 16px; }}
  .section-title {{ font-size: 12pt; color: #1565C0; font-weight: bold;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .tl-row {{ display: flex; align-items: flex-start; margin-bottom: 8px; }}
  .tl-left {{ width: 130px; flex-shrink: 0; text-align: right; padding-right: 12px; }}
  .tl-dot {{ width: 10px; height: 10px; background: #1565C0; border-radius: 50%;
    margin-top: 3px; flex-shrink: 0; }}
  .tl-right {{ flex: 1; padding-left: 12px; }}
  .tl-date {{ font-size: 9pt; color: #1565C0; font-weight: bold; }}
  .tl-place {{ font-size: 9pt; color: #777; font-style: italic; }}
  .tl-title {{ font-weight: bold; font-size: 10pt; margin-bottom: 3px; }}
  ul {{ margin-left: 14px; }} li {{ font-size: 9.5pt; margin-bottom: 2px; }}
  .skills {{ font-size: 9.5pt; line-height: 1.8; color: #444; }}
  .summary {{ font-size: 10pt; line-height: 1.6; color: #555; margin-bottom: 14px; }}
  p {{ font-size: 9.5pt; line-height: 1.5; margin-top: 3px; }}
</style></head><body>
  <div class="header">
    <h1>{name}</h1>
    <div class="contact">{_contact_row(data)}</div>
  </div>
  {f'<div class="summary">{summary}</div>' if summary else ''}
  {f'<div class="section"><div class="section-title">Experience</div>{exp_html}</div>' if exp else ''}
  {f'<div class="section"><div class="section-title">Projects</div>{proj_html}</div>' if proj else ''}
  {f'<div class="section"><div class="section-title">Education</div>{edu_html}</div>' if edu else ''}
  {f'<div class="section"><div class="section-title">Skills</div><div class="skills">{skills_html}</div></div>' if skills else ''}
  {f'<div class="section"><div class="section-title">Certifications</div>{"".join(f"<div>• {c}</div>" for c in certs)}</div>' if certs else ''}
</body></html>"""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 4 — Awesome CV (Bold purple header)
# ══════════════════════════════════════════════════════════════
def _build_awesomecv(data):
    name    = data.get("name", "")
    title   = data.get("experience", [{}])[0].get("title", "Professional") if data.get("experience") else "Professional"
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)

    exp_html = ""
    for e in exp:
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <div>
              <span class="entry-title">{e.get('title','')}</span>
              <span class="entry-company"> @ {e.get('company','')}</span>
            </div>
            <span class="entry-date">{e.get('duration','')}</span>
          </div>
          {_bullets(e.get('bullets',[]))}
        </div>"""

    edu_html = ""
    for e in edu:
        edu_html += f"""
        <div class="entry">
          <div class="entry-header">
            <div>
              <span class="entry-title">{e.get('degree','')}</span>
              <span class="entry-company"> — {e.get('institution','')}</span>
            </div>
            <span class="entry-date">{e.get('year','')}</span>
          </div>
        </div>"""

    skills_html = "".join(f'<span class="skill">{s}</span>' for s in skills)

    proj_html = ""
    for p in proj:
        proj_html += f"""
        <div class="entry">
          <div class="entry-header">
            <span class="entry-title">{p.get('name','')}</span>
            <span class="entry-date">{p.get('tech','')}</span>
          </div>
          <p>{p.get('description','')}</p>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; color: #2d2d2d; }}
  .header {{ background: linear-gradient(135deg, #4A148C, #7B1FA2); color: white;
    padding: 24px 28px; margin-bottom: 18px; }}
  h1 {{ font-size: 26pt; letter-spacing: 3px; font-weight: 300; margin-bottom: 3px; }}
  .header-title {{ font-size: 11pt; letter-spacing: 2px; opacity: 0.85; margin-bottom: 10px; }}
  .contact {{ font-size: 9pt; opacity: 0.9; }}
  .body {{ padding: 0 28px; }}
  .section {{ margin-bottom: 16px; }}
  .section-title {{ font-size: 12pt; font-weight: bold; color: #4A148C;
    text-transform: uppercase; letter-spacing: 2px; border-bottom: 1.5px solid #4A148C;
    padding-bottom: 4px; margin-bottom: 10px; }}
  .entry {{ margin-bottom: 10px; }}
  .entry-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 3px; }}
  .entry-title {{ font-weight: bold; font-size: 10.5pt; color: #222; }}
  .entry-company {{ font-size: 10pt; color: #4A148C; }}
  .entry-date {{ font-size: 9pt; color: #888; }}
  ul {{ margin-left: 16px; }} li {{ margin-bottom: 2px; font-size: 9.5pt; }}
  .skill {{ display: inline-block; background: #f3e5f5; color: #4A148C;
    padding: 2px 10px; border-radius: 12px; margin: 2px; font-size: 9pt; }}
  .summary {{ font-size: 10pt; line-height: 1.6; color: #555; margin-bottom: 14px;
    padding: 10px; background: #f9f4fc; border-left: 3px solid #4A148C; }}
  p {{ font-size: 9.5pt; line-height: 1.5; color: #555; margin-top: 3px; }}
</style></head><body>
  <div class="header">
    <h1>{name}</h1>
    <div class="header-title">{title.upper()}</div>
    <div class="contact">{_contact_row(data)}</div>
  </div>
  <div class="body">
    {f'<div class="summary">{summary}</div>' if summary else ''}
    {f'<div class="section"><div class="section-title">Experience</div>{exp_html}</div>' if exp else ''}
    {f'<div class="section"><div class="section-title">Projects</div>{proj_html}</div>' if proj else ''}
    {f'<div class="section"><div class="section-title">Education</div>{edu_html}</div>' if edu else ''}
    {f'<div class="section"><div class="section-title">Technical Skills</div><div style="padding:6px 0">{skills_html}</div></div>' if skills else ''}
  </div>
</body></html>"""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 5 — Deedy CV (Dark navy sidebar)
# ══════════════════════════════════════════════════════════════
def _build_deedycv(data):
    name    = data.get("name", "")
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)
    certs   = _certs(data)

    exp_html = ""
    for e in exp:
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <b>{e.get('title','')}</b>
            <span class="date">{e.get('duration','')}</span>
          </div>
          <div class="company">{e.get('company','')}</div>
          {_bullets(e.get('bullets',[]))}
        </div>"""

    proj_html = ""
    for p in proj:
        proj_html += f"""
        <div class="entry">
          <b>{p.get('name','')}</b>
          <span class="tech-tag">{p.get('tech','')}</span>
          <p>{p.get('description','')}</p>
        </div>"""

    edu_html = ""
    for e in edu:
        edu_html += f"""
        <div style="margin-bottom:8px">
          <div style="font-weight:bold;font-size:9.5pt">{e.get('degree','')}</div>
          <div style="font-size:8.5pt;opacity:0.8">{e.get('institution','')}</div>
          <div style="font-size:8.5pt;opacity:0.7">{e.get('year','')}</div>
        </div>"""

    skills_chunks = [skills[i:i+4] for i in range(0, len(skills), 4)]
    skills_html = "".join(
        f'<div style="margin-bottom:4px">{" · ".join(chunk)}</div>'
        for chunk in skills_chunks
    )

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Arial, sans-serif; font-size: 10pt; color: #222; display: flex; }}
  .sidebar {{ width: 30%; background: #1a1a2e; color: #e0e0e0; padding: 20px 14px; min-height: 100vh; }}
  .main {{ width: 70%; padding: 20px 18px; }}
  .side-name {{ font-size: 16pt; color: #fff; font-weight: bold; margin-bottom: 2px;
    border-bottom: 2px solid #4fc3f7; padding-bottom: 6px; margin-bottom: 12px; }}
  .side-section {{ margin-bottom: 16px; }}
  .side-title {{ font-size: 8.5pt; text-transform: uppercase; letter-spacing: 1.5px;
    color: #4fc3f7; margin-bottom: 6px; }}
  .contact-item {{ font-size: 8.5pt; margin-bottom: 3px; color: #ccc; }}
  .section-title {{ font-size: 12pt; color: #1a1a2e; font-weight: bold;
    border-bottom: 2px solid #1a1a2e; padding-bottom: 3px; margin-bottom: 10px; }}
  .entry {{ margin-bottom: 10px; }}
  .entry-header {{ display: flex; justify-content: space-between; }}
  .date {{ font-size: 9pt; color: #777; }}
  .company {{ font-size: 9.5pt; color: #555; font-style: italic; margin-bottom: 3px; }}
  ul {{ margin-left: 15px; }} li {{ font-size: 9.5pt; margin-bottom: 2px; }}
  .tech-tag {{ font-size: 8pt; background: #e3f2fd; color: #1565c0;
    padding: 1px 6px; border-radius: 8px; margin-left: 6px; }}
  p {{ font-size: 9.5pt; line-height: 1.5; margin-top: 3px; color: #555; }}
  .section {{ margin-bottom: 16px; }}
</style></head><body>
  <div class="sidebar">
    <div class="side-name">{name}</div>
    <div class="side-section">
      <div class="side-title">Contact</div>
      {''.join(f'<div class="contact-item">{c}</div>' for c in [data.get("email",""), data.get("phone",""), data.get("location","")] if c)}
    </div>
    <div class="side-section">
      <div class="side-title">Skills</div>
      <div style="font-size:8.5pt;line-height:1.9;color:#ccc">{skills_html}</div>
    </div>
    {f'''<div class="side-section">
      <div class="side-title">Education</div>
      {edu_html}
    </div>''' if edu else ''}
    {f'''<div class="side-section">
      <div class="side-title">Certifications</div>
      {"".join(f'<div class="contact-item">• {c}</div>' for c in certs)}
    </div>''' if certs else ''}
  </div>
  <div class="main">
    {f'<div class="section"><div class="section-title">Experience</div>{exp_html}</div>' if exp else ''}
    {f'<div class="section"><div class="section-title">Projects</div>{proj_html}</div>' if proj else ''}
  </div>
</body></html>"""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 6 — Elegant (Minimal, double ruled)
# ══════════════════════════════════════════════════════════════
def _build_elegant(data):
    name    = data.get("name", "")
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)
    certs   = _certs(data)
    ach     = _ach(data)

    exp_html = ""
    for e in exp:
        exp_html += f"""
        <div class="entry">
          <table style="width:100%"><tr>
            <td><b>{e.get('title','')}</b>, <em>{e.get('company','')}</em></td>
            <td style="text-align:right;font-size:9pt;color:#555">{e.get('duration','')}</td>
          </tr></table>
          {_bullets(e.get('bullets',[]))}
        </div>"""

    edu_html = ""
    for e in edu:
        edu_html += f"""
        <div class="entry">
          <table style="width:100%"><tr>
            <td><b>{e.get('degree','')}</b>, {e.get('institution','')}</td>
            <td style="text-align:right;font-size:9pt;color:#555">{e.get('year','')}</td>
          </tr></table>
        </div>"""

    proj_html = ""
    for p in proj:
        proj_html += f"""
        <div class="entry">
          <b>{p.get('name','')}</b> <em>({p.get('tech','')})</em>
          <p>{p.get('description','')}</p>
        </div>"""

    skills_html = ", ".join(skills)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt;
    color: #1a1a1a; padding: 22px 28px; max-width: 700px; margin: auto; }}
  h1 {{ font-size: 22pt; text-align: center; font-weight: bold;
    letter-spacing: 3px; text-transform: uppercase; margin-bottom: 4px; }}
  .contact {{ text-align: center; font-size: 9pt; color: #555; margin-bottom: 8px; }}
  .rule {{ border: none; border-top: 1px solid #000; margin: 3px 0; }}
  .double-rule {{ border: none; border-top: 3px double #000; margin: 10px 0; }}
  .section-title {{ font-size: 10.5pt; font-weight: bold; text-transform: uppercase;
    letter-spacing: 2px; text-align: center; margin: 10px 0 4px; }}
  .entry {{ margin-bottom: 8px; }}
  ul {{ margin-left: 18px; }} li {{ margin-bottom: 2px; font-size: 10pt; }}
  .summary {{ font-size: 10pt; text-align: center; color: #444;
    font-style: italic; margin-bottom: 8px; line-height: 1.6; }}
  p {{ font-size: 9.5pt; line-height: 1.5; margin-top: 3px; }}
</style></head><body>
  <h1>{name}</h1>
  <div class="contact">{_contact_row(data)}</div>
  <hr class="rule"><hr class="rule">
  {f'<div class="summary">{summary}</div>' if summary else ''}

  {f'''<hr class="double-rule">
  <div class="section-title">Experience</div>
  <hr class="rule">
  {exp_html}''' if exp else ''}

  {f'''<hr class="double-rule">
  <div class="section-title">Projects</div>
  <hr class="rule">
  {proj_html}''' if proj else ''}

  {f'''<hr class="double-rule">
  <div class="section-title">Education</div>
  <hr class="rule">
  {edu_html}''' if edu else ''}

  {f'''<hr class="double-rule">
  <div class="section-title">Skills</div>
  <hr class="rule">
  <div style="font-size:10pt;line-height:1.8;text-align:center">{skills_html}</div>''' if skills else ''}

  {f'''<hr class="double-rule">
  <div class="section-title">Achievements</div>
  <hr class="rule">
  {"".join(f"<div style='margin-bottom:4px'>• {a}</div>" for a in ach)}''' if ach else ''}
</body></html>"""


# ══════════════════════════════════════════════════════════════
# TEMPLATE 7 — Skill Bars (Visual progress bars)
# ══════════════════════════════════════════════════════════════
def _build_skillbars(data):
    name    = data.get("name", "")
    summary = data.get("summary", "")
    skills  = _skills(data)
    exp     = _exp(data)
    edu     = _edu(data)
    proj    = _proj(data)
    certs   = _certs(data)

    # Generate skill bars with estimated proficiency
    skill_levels = [95, 90, 85, 80, 78, 75, 72, 70, 68, 65]
    skills_html = ""
    for i, skill in enumerate(skills[:10]):
        pct = skill_levels[i] if i < len(skill_levels) else 60
        skills_html += f"""
        <div style="margin-bottom:6px">
          <div style="display:flex;justify-content:space-between;margin-bottom:2px">
            <span style="font-size:9pt">{skill}</span>
            <span style="font-size:8.5pt;color:#777">{pct}%</span>
          </div>
          <div style="height:6px;background:#e0e0e0;border-radius:3px">
            <div style="height:100%;width:{pct}%;background:linear-gradient(90deg,#0277BD,#29B6F6);border-radius:3px"></div>
          </div>
        </div>"""

    exp_html = ""
    for e in exp:
        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <b>{e.get('title','')}</b>
            <span class="date">{e.get('duration','')}</span>
          </div>
          <div class="company">{e.get('company','')}</div>
          {_bullets(e.get('bullets',[]))}
        </div>"""

    edu_html = ""
    for e in edu:
        edu_html += f"""
        <div style="margin-bottom:8px;font-size:9.5pt">
          <b>{e.get('degree','')}</b><br>
          <span style="color:#555">{e.get('institution','')} | {e.get('year','')}</span>
        </div>"""

    proj_html = ""
    for p in proj:
        proj_html += f"""
        <div class="entry">
          <b>{p.get('name','')}</b>
          <span class="tech-badge">{p.get('tech','')}</span>
          <p>{p.get('description','')}</p>
        </div>"""

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; color: #2d2d2d; }}
  .header {{ background: #0277BD; color: white; padding: 20px 24px; }}
  h1 {{ font-size: 22pt; font-weight: 300; letter-spacing: 2px; margin-bottom: 4px; }}
  .contact {{ font-size: 9pt; opacity: 0.9; }}
  .layout {{ display: flex; }}
  .sidebar {{ width: 32%; background: #f5f5f5; padding: 16px 14px; border-right: 1px solid #e0e0e0; }}
  .main {{ width: 68%; padding: 16px 18px; }}
  .side-section {{ margin-bottom: 18px; }}
  .side-title {{ font-size: 9pt; font-weight: bold; text-transform: uppercase;
    letter-spacing: 1px; color: #0277BD; border-bottom: 1.5px solid #0277BD;
    padding-bottom: 3px; margin-bottom: 8px; }}
  .section {{ margin-bottom: 16px; }}
  .section-title {{ font-size: 12pt; font-weight: bold; color: #0277BD;
    border-bottom: 1.5px solid #0277BD; padding-bottom: 3px; margin-bottom: 10px; }}
  .entry {{ margin-bottom: 10px; }}
  .entry-header {{ display: flex; justify-content: space-between; }}
  .date {{ font-size: 9pt; color: #777; }}
  .company {{ font-size: 9.5pt; color: #555; font-style: italic; margin-bottom: 3px; }}
  ul {{ margin-left: 15px; }} li {{ font-size: 9.5pt; margin-bottom: 2px; }}
  .tech-badge {{ font-size: 8pt; background: #e3f2fd; color: #0277BD;
    padding: 1px 7px; border-radius: 9px; margin-left: 6px; }}
  .summary {{ font-size: 9.5pt; line-height: 1.6; color: #555;
    background: #e3f2fd; padding: 8px 10px; border-radius: 5px; margin-bottom: 14px; }}
  p {{ font-size: 9.5pt; line-height: 1.5; margin-top: 3px; color: #555; }}
</style></head><body>
  <div class="header">
    <h1>{name}</h1>
    <div class="contact">{_contact_row(data)}</div>
  </div>
  <div class="layout">
    <div class="sidebar">
      <div class="side-section">
        <div class="side-title">Skills</div>
        {skills_html}
      </div>
      {f'''<div class="side-section">
        <div class="side-title">Education</div>
        {edu_html}
      </div>''' if edu else ''}
      {f'''<div class="side-section">
        <div class="side-title">Certifications</div>
        {"".join(f'<div style="font-size:8.5pt;margin-bottom:3px">• {c}</div>' for c in certs)}
      </div>''' if certs else ''}
    </div>
    <div class="main">
      {f'<div class="summary">{summary}</div>' if summary else ''}
      {f'<div class="section"><div class="section-title">Experience</div>{exp_html}</div>' if exp else ''}
      {f'<div class="section"><div class="section-title">Projects</div>{proj_html}</div>' if proj else ''}
    </div>
  </div>
</body></html>"""


# ══════════════════════════════════════════════════════════════
# MAIN BUILD FUNCTION
# ══════════════════════════════════════════════════════════════
BUILDERS = {
    "jakescv":   _build_jakescv,
    "altacv":    _build_altacv,
    "moderncv":  _build_moderncv,
    "awesomecv": _build_awesomecv,
    "deedycv":   _build_deedycv,
    "elegant":   _build_elegant,
    "skillbars": _build_skillbars,
}

def build_html_template_pdf(data: dict, template: str = "jakescv") -> bytes:
    """
    Build PDF from HTML template using WeasyPrint.
    No LaTeX/MiKTeX required.
    """
    builder = BUILDERS.get(template, _build_jakescv)
    html_content = builder(data)

    css = CSS(string="""
        @page {
            size: A4;
            margin: 0;
        }
        body {
            margin: 0;
        }
    """)

    pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css])
    print(f"[resume_templates_html] Built {template} PDF — {len(pdf_bytes)} bytes")
    return pdf_bytes
