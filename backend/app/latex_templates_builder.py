"""
latex_templates_builder.py
---------------------------
7 Overleaf-quality LaTeX resume templates.
Each template supports fresher + experienced layouts with different
section orders, skill visualizations, and domain-specific content.

Templates:
  1. jakescv    — Jake's Resume (single column, max ATS)
  2. altacv     — AltaCV (two column, skill tags)
  3. moderncv   — ModernCV (timeline sidebar)
  4. awesomecv  — Awesome CV (colored sections)
  5. deedycv    — Deedy CV (dark sidebar)
  6. elegant    — Elegant (double rule, formal)
  7. skillbars  — Skill Bars (progress bar visualization)

Usage:
  from latex_templates_builder import build_template_pdf
  pdf_bytes = build_template_pdf(data, template="jakescv", level="fresher", domain="aiml")
"""

import subprocess

# ── MiKTeX / LaTeX engine path finder (Windows) ──────────────
import shutil as _shutil, platform as _platform, subprocess as _sp

def _find_latex_engine(engine: str) -> str:
    """
    Find LaTeX engine — fast, no directory walk.
    Priority: PATH → MiKTeX registry → common install paths
    """
    # 0. Check .env override — LATEX_PATH=C:\Users\HP\...\miktex\bin\x64
    import os as _os
    env_latex_dir = _os.environ.get("LATEX_PATH", "").strip()
    if env_latex_dir:
        exe = _os.path.join(env_latex_dir, f"{engine}.exe") if _platform.system() == "Windows" else _os.path.join(env_latex_dir, engine)
        if _os.path.isfile(exe):
            print(f"[latex] Using LATEX_PATH env: {exe}")
            return exe

    # 1. Already in PATH (Linux/Mac/Windows if MiKTeX added to PATH)
    found = _shutil.which(engine)
    if found:
        print(f"[latex] {engine} found in PATH: {found}")
        return found

    if _platform.system() != "Windows":
        print(f"[latex] WARNING: {engine} not in PATH on Linux/Mac")
        return engine

    import os, winreg

    # 2. Try Windows registry — MiKTeX stores install path here
    reg_paths = [
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\MiKTeX.org\MiKTeX"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\MiKTeX.org\MiKTeX"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\MiKTeX.org\MiKTeX"),
    ]
    for hive, reg_path in reg_paths:
        try:
            key = winreg.OpenKey(hive, reg_path)
            install_root, _ = winreg.QueryValueEx(key, "PathPrefix")
            winreg.CloseKey(key)
            candidate = os.path.join(install_root, "miktex", "bin", "x64", f"{engine}.exe")
            if os.path.isfile(candidate):
                print(f"[latex] Found via registry: {candidate}")
                return candidate
        except Exception:
            pass

    # 3. Common install paths — fast direct check, no walk
    local = os.environ.get("LOCALAPPDATA", "")
    prog  = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    prog86= os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")

    candidates = [
        # MiKTeX per-user (most common on Windows 10/11)
        os.path.join(local, "Programs", "MiKTeX", "miktex", "bin", "x64", f"{engine}.exe"),
        os.path.join(local, "Programs", "MiKTeX", "miktex", "bin", f"{engine}.exe"),
        # MiKTeX system-wide
        os.path.join(prog,   "MiKTeX", "miktex", "bin", "x64", f"{engine}.exe"),
        os.path.join(prog86, "MiKTeX", "miktex", "bin", "x64", f"{engine}.exe"),
        os.path.join(prog,   "MiKTeX 2.9", "miktex", "bin", "x64", f"{engine}.exe"),
        r"C:\MiKTeX\miktexind\" + f"{engine}.exe",
        # TeX Live
        r"C:	exlive4in\windows\" + f"{engine}.exe",
        r"C:	exlive3in\windows\" + f"{engine}.exe",
    ]

    for c in candidates:
        if os.path.isfile(c):
            print(f"[latex] Found at: {c}")
            return c

    # 4. Last resort — try `where` command on Windows
    try:
        result = _sp.run(["where", engine], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            path = result.stdout.strip().splitlines()[0]
            print(f"[latex] Found via `where`: {path}")
            return path
    except Exception:
        pass

    print(f"[latex] WARNING: {engine} not found anywhere — will fail if not in PATH")
    return engine
import tempfile
import os
import re


# ============================================================
# LEVEL CONFIGS
# ============================================================
LEVEL_CONFIG = {
    "fresher": {
        "summary_label": "Objective",
        "exp_label": "Internship \\& Experience",
        "section_order": ["summary", "skills", "projects", "education", "experience", "certifications", "achievements"],
        "summary_tone": "Seeking entry-level opportunity to apply",
        "skill_level": 0.75,  # max bar level for fresher
    },
    "junior": {
        "summary_label": "Objective",
        "exp_label": "Work Experience",
        "section_order": ["summary", "skills", "experience", "projects", "education", "certifications"],
        "summary_tone": "Building expertise in",
        "skill_level": 0.80,
    },
    "mid": {
        "summary_label": "Professional Summary",
        "exp_label": "Work Experience",
        "section_order": ["summary", "experience", "skills", "projects", "education", "certifications", "achievements"],
        "summary_tone": "Experienced professional delivering impact in",
        "skill_level": 0.88,
    },
    "senior": {
        "summary_label": "Senior Professional Summary",
        "exp_label": "Work Experience",
        "section_order": ["summary", "experience", "projects", "skills", "certifications", "education", "achievements"],
        "summary_tone": "Senior engineer with proven track record in",
        "skill_level": 0.92,
    },
    "lead": {
        "summary_label": "Leadership Profile",
        "exp_label": "Leadership \\& Work Experience",
        "section_order": ["summary", "experience", "achievements", "skills", "certifications", "education"],
        "summary_tone": "Engineering leader driving technical strategy in",
        "skill_level": 0.96,
    },
}

# ============================================================
# HELPERS
# ============================================================
def _e(text):
    """Escape LaTeX special characters."""
    if not text:
        return ""
    text = str(text)
    for old, new in [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"), ("%", "\\%"), ("$", "\\$"),
        ("#", "\\#"), ("_", "\\_"), ("{", "\\{"),
        ("}", "\\}"), ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]:
        text = text.replace(old, new)
    return text


def _compile(latex, engine="pdflatex"):
    """Compile LaTeX to PDF, return bytes."""
    # Find engine path (handles Windows MiKTeX locations)
    engine_path = _find_latex_engine(engine)
    print(f"[latex_templates_builder] Compiling with {engine} -> {engine_path}")

    with tempfile.TemporaryDirectory() as tmp:
        tex = os.path.join(tmp, "resume.tex")
        pdf = os.path.join(tmp, "resume.pdf")
        with open(tex, "w", encoding="utf-8") as f:
            f.write(latex)

        cmd = [engine_path, "-interaction=nonstopmode", "-output-directory", tmp, tex]

        env = os.environ.copy()
        # Add MiKTeX bin to PATH so LaTeX can find its own tools
        engine_dir = os.path.dirname(engine_path) if os.path.isabs(engine_path) else ""
        if engine_dir:
            env["PATH"] = engine_dir + os.pathsep + env.get("PATH", "")

        for _ in range(2):
            r = subprocess.run(cmd, capture_output=True, timeout=120, env=env)
            print(f"[latex] Return code: {r.returncode}")

        if not os.path.exists(pdf):
            stdout = r.stdout.decode(errors='ignore')[-1000:]
            stderr = r.stderr.decode(errors='ignore')[-500:]
            raise RuntimeError(
                f"{engine} compilation failed.\n"
                f"Engine path: {engine_path}\n"
                f"Output: {stdout}\n"
                f"Stderr: {stderr}"
            )
        print(f"[latex] PDF generated successfully ({os.path.getsize(pdf)} bytes)")
        return open(pdf, "rb").read()


def _skills_list(data):
    return data.get("skills", [])


def _contact_line(data, sep=" $|$ "):
    parts = [p for p in [
        _e(data.get("email", "")),
        _e(data.get("phone", "")),
        _e(data.get("location", "")),
        _e(data.get("linkedin", "")),
        _e(data.get("github", "")),
    ] if p]
    return sep.join(parts)


def _exp_blocks(data, lc, small="\\small", footnote="\\footnotesize"):
    """Generate experience blocks for a template."""
    exps = data.get("experience", [])
    if not exps:
        return ""
    out = ""
    for exp in exps:
        title   = _e(exp.get("title", ""))
        company = _e(exp.get("company", ""))
        dur     = _e(exp.get("duration", ""))
        bullets = exp.get("bullets", [])
        blist   = "\n".join(f"  \\item {_e(b)}" for b in bullets)
        out += f"""
{{{small}\\bfseries {title}}} \\hfill {{{footnote} {dur}}}\\\\
{{{footnote}\\itshape {company}}}
\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=2pt,parsep=0pt]{small}
{blist}
\\end{{itemize}}
\\vspace{{3pt}}
"""
    return out


def _proj_blocks(data, small="\\small", footnote="\\footnotesize"):
    projs = data.get("projects", [])
    if not projs:
        return ""
    out = ""
    for p in projs:
        name    = _e(p.get("name", ""))
        tech    = _e(p.get("tech", ""))
        desc    = _e(p.get("description", ""))
        metrics = _e(p.get("metrics", ""))
        out += f"""
{{{small}\\bfseries {name}}} \\hfill {{{footnote}\\color{{light}} {tech}}}\\\\
{{{small} {desc}}}\\\\
{f"{{{footnote}\\color{{light}} {metrics}}}\\\\" if metrics else ""}
\\vspace{{3pt}}
"""
    return out


def _edu_blocks(data, small="\\small", footnote="\\footnotesize"):
    edus = data.get("education", [])
    if not edus:
        return ""
    out = ""
    for e in edus:
        deg  = _e(e.get("degree", ""))
        inst = _e(e.get("institution", ""))
        year = _e(e.get("year", ""))
        gpa  = f" $|$ GPA: {_e(e.get('gpa',''))}" if e.get("gpa") else ""
        out += f"""{{{small}\\bfseries {deg}}} \\hfill {{{footnote} {year}}}\\\\
{{{footnote}\\color{{light}} {inst}{gpa}}}\\\\[3pt]
"""
    return out


def _list_items(items, small="\\small"):
    if not items:
        return ""
    return "\n".join(f"{{{small}\\textbullet\\ {_e(i)}}}\\\\" for i in items)


# ============================================================
# TEMPLATE 1: JAKE'S CV
# ============================================================
def _build_jakescv(data, level, domain):
    lc = LEVEL_CONFIG[level]
    name = _e(data.get("name", "Your Name"))
    contact = _contact_line(data)
    summary = _e(data.get("summary", ""))
    skills = _skills_list(data)
    skills_str = ", ".join(_e(s) for s in skills)

    # Skills table grouped
    skill_rows = _e(", ".join(skills[:8]))
    ml_skills  = [s for s in skills if any(t in s.lower() for t in
                   ["tensorflow","pytorch","keras","scikit","ml","ai","nlp","deep"])]
    prog_skills = [s for s in skills if any(t in s.lower() for t in
                    ["python","java","go","c++","javascript","sql","r"])]
    tool_skills = [s for s in skills if any(t in s.lower() for t in
                    ["docker","git","aws","azure","gcp","fastapi","flask"])]
    other_skills = [s for s in skills if s not in ml_skills + prog_skills + tool_skills]

    def skill_line(label, items):
        if not items:
            return ""
        return f"  \\textbf{{{label}}}{{: {_e(', '.join(items))}}} \\\\\n"

    skill_section = (
        skill_line("Programming", prog_skills) +
        skill_line("ML / AI", ml_skills) +
        skill_line("Tools", tool_skills) +
        skill_line("Other", other_skills)
    ) or f"  \\textbf{{Skills}}{{: {skills_str}}} \\\\\n"

    # Build sections based on level
    sections = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            sections += f"""
\\section{{{lc['summary_label']}}}
\\resumeSubHeadingListStart
\\small{{\\item{{{summary}}}}}
\\resumeSubHeadingListEnd
"""
        elif sec == "skills" and skills:
            sections += f"""
\\section{{Technical Skills}}
\\resumeSubHeadingListStart
\\small{{\\item{{
{skill_section}
}}}}
\\resumeSubHeadingListEnd
"""
        elif sec == "experience" and data.get("experience"):
            sections += f"\\section{{{lc['exp_label']}}}\n\\resumeSubHeadingListStart\n"
            for exp in data["experience"]:
                blist = "\n".join(f"    \\resumeItem{{{_e(b)}}}"
                                   for b in exp.get("bullets", []))
                sections += f"""  \\resumeSubheading
    {{{_e(exp.get('title',''))}}}{{{_e(exp.get('duration',''))}}}
    {{{_e(exp.get('company',''))}}}{{{_e(exp.get('location',''))}}}
  \\resumeItemListStart
{blist}
  \\resumeItemListEnd
"""
            sections += "\\resumeSubHeadingListEnd\n"

        elif sec == "projects" and data.get("projects"):
            sections += "\\section{Projects}\n\\resumeSubHeadingListStart\n"
            for p in data["projects"]:
                tech = _e(p.get("tech", ""))
                blist = f"    \\resumeItem{{{_e(p.get('description',''))}}}\n"
                if p.get("metrics"):
                    blist += f"    \\resumeItem{{{_e(p.get('metrics',''))}}}\n"
                sections += f"""  \\resumeProjectHeading
    {{\\textbf{{{_e(p.get('name',''))}}} $|$ \\emph{{{tech}}}}}{{}}
  \\resumeItemListStart
{blist}  \\resumeItemListEnd
"""
            sections += "\\resumeSubHeadingListEnd\n"

        elif sec == "education" and data.get("education"):
            sections += "\\section{Education}\n\\resumeSubHeadingListStart\n"
            for e in data["education"]:
                gpa = f" $|$ GPA: {_e(e.get('gpa',''))}" if e.get("gpa") else ""
                sections += f"""  \\resumeSubheading
    {{{_e(e.get('degree',''))}}}{{{_e(e.get('year',''))}}}
    {{{_e(e.get('institution',''))}{gpa}}}{{}}
"""
            sections += "\\resumeSubHeadingListEnd\n"

        elif sec == "certifications" and data.get("certifications"):
            certs = "\n".join(f"    \\resumeItem{{{_e(c)}}}" for c in data["certifications"])
            sections += f"""\\section{{Certifications}}
\\resumeSubHeadingListStart
\\resumeItemListStart
{certs}
\\resumeItemListEnd
\\resumeSubHeadingListEnd
"""
        elif sec == "achievements" and data.get("achievements"):
            achs = "\n".join(f"    \\resumeItem{{{_e(a)}}}" for a in data["achievements"])
            sections += f"""\\section{{Achievements}}
\\resumeSubHeadingListStart
\\resumeItemListStart
{achs}
\\resumeItemListEnd
\\resumeSubHeadingListEnd
"""

    return rf"""
\documentclass[letterpaper,10pt]{{article}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec,enumitem,hyperref,tabularx,xcolor,fancyhdr}}
\setmainfont{{Lato}}
\pagestyle{{fancy}}\fancyhf{{}}\fancyfoot{{}}
\renewcommand{{\headrulewidth}}{{0pt}}\renewcommand{{\footrulewidth}}{{0pt}}
\addtolength{{\oddsidemargin}}{{-0.5in}}\addtolength{{\evensidemargin}}{{-0.5in}}
\addtolength{{\textwidth}}{{1in}}\addtolength{{\topmargin}}{{-.5in}}\addtolength{{\textheight}}{{1in}}
\raggedbottom\raggedright\setlength{{\tabcolsep}}{{0in}}
\definecolor{{light}}{{HTML}}{{666666}}
\titleformat{{\section}}{{\vspace{{-4pt}}\scshape\raggedright\large}}{{}}{{0em}}{{}}[\color{{black}}\titlerule\vspace{{-5pt}}]
\hypersetup{{hidelinks}}
\newcommand{{\resumeItem}}[1]{{\item\small{{#1\vspace{{-2pt}}}}}}
\newcommand{{\resumeSubheading}}[4]{{\vspace{{-2pt}}\item
  \begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}
    \textbf{{#1}} & #2 \\ \textit{{\small#3}} & \textit{{\small #4}}
  \end{{tabular*}}\vspace{{-7pt}}}}
\newcommand{{\resumeProjectHeading}}[2]{{\item
  \begin{{tabular*}}{{0.97\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
    \small#1 & #2
  \end{{tabular*}}\vspace{{-7pt}}}}
\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0.15in,label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-5pt}}}}
\begin{{document}}
\begin{{center}}
  {{\Huge\scshape {name}}}\\[5pt]
  \small {contact}
\end{{center}}
{sections}
\end{{document}}
"""


# ============================================================
# TEMPLATE 2: ALTACV
# ============================================================
def _build_altacv(data, level, domain):
    lc = LEVEL_CONFIG[level]
    name = _e(data.get("name", ""))
    email = _e(data.get("email", ""))
    phone = _e(data.get("phone", ""))
    location = _e(data.get("location", ""))
    linkedin = _e(data.get("linkedin", ""))
    github = _e(data.get("github", ""))
    summary = _e(data.get("summary", ""))
    skills = _skills_list(data)

    tags = "\n".join(
        f"\\cvtag{{{_e(s)}}}" + ("\\\\[3pt]" if (i+1) % 2 == 0 else "")
        for i, s in enumerate(skills[:14])
    )

    edu_sidebar = ""
    for e in data.get("education", []):
        edu_sidebar += f"""
\\cvevent{{{_e(e.get('degree',''))}}}{{{_e(e.get('institution',''))}}}{{{_e(e.get('year',''))}}}
"""

    certs = "\n".join(f"\\small {_e(c)}\\\\" for c in data.get("certifications", []))

    # Main sections
    main = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            main += f"""
\\cvsection{{{lc['summary_label']}}}
\\small {summary}
"""
        elif sec == "experience" and data.get("experience"):
            main += f"\\cvsection{{{lc['exp_label']}}}\n"
            for exp in data["experience"]:
                blist = "\n".join(f"  \\item {_e(b)}" for b in exp.get("bullets", []))
                main += f"""
\\cvevent{{{_e(exp.get('title',''))}}}{{{_e(exp.get('company',''))}}}{{{_e(exp.get('duration',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=2pt,topsep=0pt]\\small
{blist}
\\end{{itemize}}
"""
        elif sec == "projects" and data.get("projects"):
            main += "\\cvsection{Projects}\n"
            for p in data["projects"]:
                main += f"""
\\cvevent{{{_e(p.get('name',''))}}}{{{_e(p.get('tech',''))}}}{{}}
\\begin{{itemize}}[leftmargin=*,itemsep=2pt,topsep=0pt]\\small
  \\item {_e(p.get('description',''))}
  {f"\\item {_e(p.get('metrics',''))}" if p.get('metrics') else ''}
\\end{{itemize}}
"""
        elif sec == "achievements" and data.get("achievements"):
            main += "\\cvsection{Achievements}\n"
            for a in data["achievements"]:
                main += f"\\small \\textbullet\\ {_e(a)}\\\\\n"

    return rf"""
\documentclass[10pt,a4paper]{{article}}
\usepackage[top=1.5cm,bottom=1.5cm,left=1.5cm,right=1.5cm]{{geometry}}
\usepackage{{fontspec,xcolor,paracol,enumitem,parskip,hyperref,tikz}}
\usetikzlibrary{{calc}}
\setmainfont{{Lato}}
\definecolor{{accent}}{{HTML}}{{0077B5}}
\definecolor{{emphasis}}{{HTML}}{{1A1A2E}}
\definecolor{{body}}{{HTML}}{{2E2E2E}}
\definecolor{{sidebar}}{{HTML}}{{F0F4F8}}
\definecolor{{tag}}{{HTML}}{{E3F0FF}}
\definecolor{{light}}{{HTML}}{{666666}}
\hypersetup{{colorlinks,urlcolor=accent}}
\pagestyle{{empty}}\setlength{{\parindent}}{{0pt}}\setlength{{\parskip}}{{2pt}}
\newcommand{{\cvsection}}[1]{{\vspace{{6pt}}{{\color{{accent}}\rule{{\linewidth}}{{1.5pt}}}}\\[-5pt]{{\large\bfseries\color{{emphasis}} #1}}\vspace{{3pt}}\\}}
\newcommand{{\cvtag}}[1]{{\colorbox{{tag}}{{\small\color{{accent}}\strut\ #1\ }}\hspace{{2pt}}}}
\newcommand{{\cvevent}}[3]{{\\{{\small\bfseries\color{{emphasis}} #1}}\\{{\footnotesize\color{{accent}} #2}}\ifx&#3&\else{{ \small\color{{body!60}}$|$ #3}}\fi\\[3pt]}}
\begin{{document}}
\columnratio{{0.33}}\setlength{{\columnsep}}{{14pt}}
\begin{{paracol}}{{2}}
\begin{{leftcolumn}}
\begin{{tikzpicture}}[remember picture,overlay]
  \fill[sidebar] (current page.north west) rectangle ($(current page.north west)+(0.355\paperwidth,-\paperheight)$);
\end{{tikzpicture}}
\vspace{{6pt}}
{{\LARGE\bfseries\color{{emphasis}} {name}}}\\[4pt]
{{\normalsize\color{{accent}} {_e(domain.replace('_',' ').title())} Professional}}\\[8pt]
{{\footnotesize\color{{body}} \textbf{{\color{{emphasis}}Email}}\\ {email}\\[4pt]\textbf{{\color{{emphasis}}Phone}}\\ {phone}\\[4pt]\textbf{{\color{{emphasis}}Location}}\\ {location}\\[4pt]\textbf{{\color{{emphasis}}LinkedIn}}\\ {linkedin}\\[4pt]\textbf{{\color{{emphasis}}GitHub}}\\ {github}\\}}
\vspace{{6pt}}
{{\color{{accent}}\rule{{\linewidth}}{{1.5pt}}}}\\[-5pt]{{\large\bfseries\color{{emphasis}} Skills}}\vspace{{3pt}}\\
{tags}
\vspace{{6pt}}
{{\color{{accent}}\rule{{\linewidth}}{{1.5pt}}}}\\[-5pt]{{\large\bfseries\color{{emphasis}} Education}}\vspace{{3pt}}\\
{edu_sidebar}
{(chr(10) + "{\\color{accent}\\rule{\\linewidth}{1.5pt}}\\\\[-5pt]{\\large\\bfseries\\color{emphasis} Certifications}\\vspace{3pt}\\\\" + chr(10) + certs) if certs else ""}
\end{{leftcolumn}}
\switchcolumn
\begin{{rightcolumn}}
{main}
\end{{rightcolumn}}
\end{{paracol}}
\end{{document}}
"""


# ============================================================
# TEMPLATE 3: MODERNCV
# ============================================================
def _build_moderncv(data, level, domain):
    lc = LEVEL_CONFIG[level]
    name = _e(data.get("name", ""))
    email = _e(data.get("email", ""))
    phone = _e(data.get("phone", ""))
    location = _e(data.get("location", ""))
    linkedin = _e(data.get("linkedin", ""))
    github = _e(data.get("github", ""))
    summary = _e(data.get("summary", ""))
    skills = _skills_list(data)

    def tlitem(date1, date2, org, content):
        return rf"""
\noindent\begin{{minipage}}[t]{{0.18\linewidth}}
  \raggedleft{{\footnotesize\color{{lt}} {date1}}}\\[1pt]
  \raggedleft{{\tiny\color{{lt}} {date2}}}
\end{{minipage}}\hspace{{6pt}}\begin{{minipage}}[t]{{0.03\linewidth}}
  \centering\textcolor{{accent}}{{\rule{{1pt}}{{28pt}}}}\vspace{{-28pt}}\textcolor{{accent}}{{$\bullet$}}
\end{{minipage}}\hspace{{6pt}}\begin{{minipage}}[t]{{0.75\linewidth}}
{content}
\end{{minipage}}\\[4pt]
"""

    edu_tl = ""
    for e in data.get("education", []):
        year = _e(e.get("year", ""))
        edu_tl += tlitem(year, "", _e(e.get("institution", "")),
            f"{{\\small\\bfseries {_e(e.get('degree',''))}}}\\\\"
            f"{{\\footnotesize\\color{{lt}} {_e(e.get('institution',''))}"
            f"{'  GPA: ' + _e(e.get('gpa','')) if e.get('gpa') else ''}}}")

    main_content = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            main_content += f"""
\\mh{{{lc['summary_label']}}}
\\small {summary}
"""
        elif sec == "experience" and data.get("experience"):
            main_content += f"\\mh{{{lc['exp_label']}}}\n"
            for exp in data["experience"]:
                dur = _e(exp.get("duration", ""))
                parts = dur.split("--") if "--" in dur else [dur, ""]
                blist = "\n".join(f"  \\item {_e(b)}" for b in exp.get("bullets", []))
                main_content += tlitem(
                    parts[0].strip(), parts[1].strip() if len(parts) > 1 else "",
                    _e(exp.get("company", "")),
                    f"{{\\small\\bfseries\\color{{dk}} {_e(exp.get('title',''))}}}\\\\"
                    f"{{\\footnotesize\\color{{lt}}\\itshape {_e(exp.get('company',''))}}}\n"
                    f"\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=1pt,parsep=0pt]\\small\n"
                    f"{blist}\n\\end{{itemize}}"
                )
        elif sec == "projects" and data.get("projects"):
            main_content += "\\mh{Projects}\n"
            for p in data["projects"]:
                main_content += f"""
{{\\small\\bfseries\\color{{dk}} {_e(p.get('name',''))}}}\\hfill{{\\footnotesize\\color{{accent}} {_e(p.get('tech',''))}}}\\\\
{{\\small {_e(p.get('description',''))}}}\\\\
{f"{{\\footnotesize\\color{{lt}} {_e(p.get('metrics',''))}}}\\\\" if p.get('metrics') else ''}
\\vspace{{3pt}}
"""
        elif sec == "skills" and skills:
            main_content += "\\mh{Technical Skills}\n"
            main_content += "\\begin{tabular}{@{}ll@{}}\n"
            for i in range(0, min(len(skills), 10), 2):
                pair = " & ".join(f"\\small {_e(skills[j])}" for j in range(i, min(i+2, len(skills))))
                main_content += pair + " \\\\\n"
            main_content += "\\end{tabular}\n"

    sidebar_content = f"""
\\mh{{{lc['summary_label']}}}
{{\\small {summary}}}

\\mh{{Education}}
{edu_tl}
"""

    return rf"""
\documentclass[10pt,a4paper]{{article}}
\usepackage[top=0pt,bottom=1cm,left=0pt,right=0pt]{{geometry}}
\usepackage{{fontspec,xcolor,paracol,enumitem,parskip,hyperref}}
\usepackage[most]{{tcolorbox}}
\usepackage{{tikz}}\usetikzlibrary{{calc}}
\setmainfont{{Lato}}
\definecolor{{accent}}{{HTML}}{{215B8E}}
\definecolor{{hdr}}{{HTML}}{{1A3A5C}}
\definecolor{{lt}}{{HTML}}{{7A8EA8}}
\definecolor{{sb}}{{HTML}}{{EEF2F7}}
\definecolor{{dk}}{{HTML}}{{1A202C}}
\definecolor{{light}}{{HTML}}{{7A8EA8}}
\hypersetup{{colorlinks,urlcolor=accent}}
\pagestyle{{empty}}\setlength{{\parindent}}{{0pt}}\setlength{{\parskip}}{{0pt}}
\newcommand{{\mh}}[1]{{\vspace{{5pt}}{{\footnotesize\bfseries\color{{hdr}}\MakeUppercase{{#1}}}}\par\vspace{{-3pt}}\textcolor{{accent}}{{\rule{{\linewidth}}{{1.2pt}}}}\par\vspace{{3pt}}}}
\begin{{document}}
\begin{{tcolorbox}}[enhanced,arc=0pt,colback=hdr,colframe=hdr,
  boxrule=0pt,left=20pt,right=20pt,top=14pt,bottom=14pt,
  width=\paperwidth,enlarge left by=-1in-\hoffset-\oddsidemargin,
  enlarge right by=-\paperwidth+\textwidth+1in+\hoffset+\oddsidemargin]
\begin{{minipage}}{{0.6\linewidth}}
  {{\fontsize{{22pt}}{{26pt}}\selectfont\bfseries\color{{white}} {name}}}\\[3pt]
  {{\normalsize\color{{white!70!hdr}} {_e(domain.replace('_',' ').title())} Professional}}
\end{{minipage}}\begin{{minipage}}{{0.4\linewidth}}
  \raggedleft{{\footnotesize\color{{white!80!hdr}}
    {phone}\\ {email}\\ {linkedin}\\ {github}\\ {location}
  }}
\end{{minipage}}
\end{{tcolorbox}}
\columnratio{{0.36}}\setlength{{\columnsep}}{{0pt}}
\begin{{paracol}}{{2}}
\begin{{leftcolumn}}
\begin{{tikzpicture}}[remember picture,overlay]
  \fill[sb] (current page.south west) rectangle ($(current page.north west)+(0.38\paperwidth,0)$);
\end{{tikzpicture}}
\hspace{{10pt}}\begin{{minipage}}{{\dimexpr\linewidth-14pt}}
\vspace{{8pt}}
{sidebar_content}
\end{{minipage}}
\end{{leftcolumn}}
\switchcolumn
\begin{{rightcolumn}}
\hspace{{10pt}}\begin{{minipage}}{{\dimexpr\linewidth-14pt}}
\vspace{{8pt}}
{main_content}
\end{{minipage}}
\end{{rightcolumn}}
\end{{paracol}}
\end{{document}}
"""


# ============================================================
# TEMPLATE 4: AWESOME CV
# ============================================================
def _build_awesomecv(data, level, domain):
    lc = LEVEL_CONFIG[level]
    name = _e(data.get("name", ""))
    name_parts = name.split()
    name_first = name_parts[0] if name_parts else name
    name_last  = name_parts[-1] if len(name_parts) > 1 else ""
    email = _e(data.get("email", ""))
    phone = _e(data.get("phone", ""))
    location = _e(data.get("location", ""))
    linkedin = _e(data.get("linkedin", ""))
    github = _e(data.get("github", ""))
    summary = _e(data.get("summary", ""))
    skills = _skills_list(data)

    def acvsec(title):
        return rf"""
\vspace{{7pt}}
\begin{{tcolorbox}}[enhanced,arc=0pt,colback=awesome,colframe=awesome,
  boxrule=0pt,left=4pt,right=4pt,top=2pt,bottom=2pt]
  {{\footnotesize\bfseries\color{{white}}\MakeUppercase{{{title}}}}}
\end{{tcolorbox}}
\vspace{{2pt}}
"""

    def acventry(title, sub, right):
        return f"""
\\noindent{{\\small\\bfseries\\color{{dark}} {title}}}\\hfill{{\\small\\color{{awesome}} {right}}}\\\\
{{\\footnotesize\\color{{gray}}\\itshape {sub}}}\\\\[2pt]
"""

    sections = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            sections += acvsec(lc["summary_label"])
            sections += f"{{\\small\\color{{dark}} {summary}}}\n"
        elif sec == "education" and data.get("education"):
            sections += acvsec("Education")
            for e in data["education"]:
                gpa = f" | GPA: {_e(e.get('gpa',''))}" if e.get("gpa") else ""
                sections += acventry(
                    _e(e.get("degree", "")),
                    f"{_e(e.get('institution',''))}{gpa}",
                    _e(e.get("year", ""))
                )
        elif sec == "experience" and data.get("experience"):
            sections += acvsec(lc["exp_label"])
            for exp in data["experience"]:
                blist = "\n".join(f"  \\item {_e(b)}" for b in exp.get("bullets", []))
                sections += acventry(
                    _e(exp.get("title", "")),
                    _e(exp.get("company", "")),
                    _e(exp.get("duration", ""))
                )
                sections += f"\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=1pt]\\small\n{blist}\n\\end{{itemize}}\n"
        elif sec == "projects" and data.get("projects"):
            sections += acvsec("Projects")
            for p in data["projects"]:
                blist = f"  \\item {_e(p.get('description',''))}\n"
                if p.get("metrics"):
                    blist += f"  \\item {_e(p.get('metrics',''))}\n"
                sections += acventry(
                    _e(p.get("name", "")),
                    _e(p.get("tech", "")), ""
                )
                sections += f"\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=1pt]\\small\n{blist}\\end{{itemize}}\n"
        elif sec == "skills" and skills:
            sections += acvsec("Technical Skills")
            for i in range(0, min(len(skills), 14), 3):
                row = " \\quad\\textbullet\\quad ".join(_e(skills[j]) for j in range(i, min(i+3, len(skills))))
                sections += f"{{\\small {row}}}\\\\\n"
        elif sec == "certifications" and data.get("certifications"):
            sections += acvsec("Certifications")
            for c in data["certifications"]:
                sections += f"{{\\small \\textbullet\\ {_e(c)}}}\\\\\n"
        elif sec == "achievements" and data.get("achievements"):
            sections += acvsec("Achievements")
            for a in data["achievements"]:
                sections += f"{{\\small \\textbullet\\ {_e(a)}}}\\\\\n"

    return rf"""
\documentclass[10pt,a4paper]{{article}}
\usepackage[top=1.4cm,bottom=1.4cm,left=1.6cm,right=1.6cm]{{geometry}}
\usepackage{{fontspec,xcolor,enumitem,parskip,hyperref,tabularx}}
\usepackage[most]{{tcolorbox}}
\setmainfont{{Lato}}
\definecolor{{awesome}}{{HTML}}{{C0392B}}
\definecolor{{dark}}{{HTML}}{{1A1A2E}}
\definecolor{{gray}}{{HTML}}{{808080}}
\hypersetup{{colorlinks,urlcolor=awesome}}
\pagestyle{{empty}}\setlength{{\parindent}}{{0pt}}\setlength{{\parskip}}{{0pt}}
\begin{{document}}
\begin{{center}}
  {{\fontsize{{24pt}}{{28pt}}\selectfont\color{{dark}}\textbf{{{name_first}}} {{\color{{awesome}}\textbf{{{name_last}}}}}}}\\[5pt]
  {{\large\color{{gray}} {_e(domain.replace('_',' ').title())} Professional}}\\[5pt]
  {{\small\color{{gray}} {phone} \textbar\ {email} \textbar\ {linkedin} \textbar\ {github} \textbar\ {location}}}
\end{{center}}
{{\color{{awesome}}\rule{{\linewidth}}{{2pt}}}}
\vspace{{-4pt}}{{\color{{awesome!30}}\rule{{\linewidth}}{{0.5pt}}}}
\vspace{{2pt}}
{sections}
\end{{document}}
"""


# ============================================================
# TEMPLATE 5: DEEDY CV
# ============================================================
def _build_deedycv(data, level, domain):
    lc = LEVEL_CONFIG[level]
    name = _e(data.get("name", ""))
    _np = name.split()
    name_first = _np[0] if _np else name
    name_last  = _np[-1] if len(_np) > 1 else ""
    email = _e(data.get("email", ""))
    phone = _e(data.get("phone", ""))
    location = _e(data.get("location", ""))
    linkedin = _e(data.get("linkedin", ""))
    github = _e(data.get("github", ""))
    summary = _e(data.get("summary", ""))
    skills = _skills_list(data)

    edu_sidebar = ""
    for e in data.get("education", []):
        edu_sidebar += (
            f"{{\\small\\bfseries\\color{{stext}} {_e(e.get('degree',''))}}}\\\\\n"
            f"{{\\footnotesize\\color{{stlt}} {_e(e.get('institution',''))}}}\\\\\n"
            f"{{\\footnotesize\\color{{bright}} {_e(e.get('year',''))}"
            + (f" $|$ {_e(e.get('gpa',''))}" if e.get("gpa") else "")
            + "}\\\\\n[4pt]\n"
        )

    certs_sidebar = "\n".join(
        f"{{\\footnotesize\\color{{stext}} \\textbullet\\ {_e(c)}}}\\\\"
        for c in data.get("certifications", [])
    )

    skills_sidebar = ""
    categories = [
        ("Languages", ["python","java","go","c++","javascript","kotlin","scala","r"]),
        ("ML / DL", ["tensorflow","pytorch","keras","scikit","neural","xgboost","lightgbm"]),
        ("Tools", ["docker","kubernetes","git","aws","gcp","azure","fastapi","flask","kafka"]),
        ("Data", ["pandas","numpy","sql","mongodb","postgresql","elasticsearch"]),
    ]
    for cat, terms in categories:
        matched = [s for s in skills if any(t in s.lower() for t in terms)]
        if matched:
            skills_sidebar += (
                f"{{\\footnotesize\\bfseries\\color{{white}} {cat}}}\\\\\n"
                f"{{\\footnotesize\\color{{stext}} {', '.join(_e(s) for s in matched[:4])}}}\\\\\n[3pt]\n"
            )
    remaining = [s for s in skills if not any(
        any(t in s.lower() for t in terms) for _, terms in categories
    )]
    if remaining:
        skills_sidebar += (
            f"{{\\footnotesize\\bfseries\\color{{white}} Other}}\\\\\n"
            f"{{\\footnotesize\\color{{stext}} {', '.join(_e(s) for s in remaining[:4])}}}\\\\\n"
        )

    main_content = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            main_content += f"""
\\mh{{{lc['summary_label']}}}
{{\\small {summary}}}
"""
        elif sec == "experience" and data.get("experience"):
            main_content += f"\\mh{{{lc['exp_label']}}}\n"
            for exp in data["experience"]:
                blist = "\n".join(f"  \\item {_e(b)}" for b in exp.get("bullets", []))
                main_content += f"""
{{\\small\\bfseries\\color{{dark}} {_e(exp.get('title',''))}}}\\hfill{{\\footnotesize\\color{{accent}} {_e(exp.get('duration',''))}}}\\\\
{{\\footnotesize\\color{{bright}}\\itshape {_e(exp.get('company',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=2pt,parsep=0pt]\\small
{blist}
\\end{{itemize}}\\vspace{{3pt}}
"""
        elif sec == "projects" and data.get("projects"):
            main_content += "\\mh{Projects}\n"
            for p in data["projects"]:
                main_content += f"""
{{\\small\\bfseries\\color{{dark}} {_e(p.get('name',''))}}}\\hfill{{\\footnotesize\\color{{accent}} {_e(p.get('tech',''))}}}\\\\
{{\\small {_e(p.get('description',''))}}}\\\\
{f"{{\\footnotesize\\color{{bright}} {_e(p.get('metrics',''))}}}\\\\" if p.get("metrics") else ""}
\\vspace{{3pt}}
"""
        elif sec == "achievements" and data.get("achievements"):
            main_content += "\\mh{Achievements}\n"
            for a in data["achievements"]:
                main_content += f"{{\\small \\textbullet\\ {_e(a)}}}\\\\\n"

    return rf"""
\documentclass[10pt,a4paper]{{article}}
\usepackage[top=1cm,bottom=1cm,left=1cm,right=1cm]{{geometry}}
\usepackage{{fontspec,xcolor,paracol,enumitem,parskip,hyperref,tikz}}
\usetikzlibrary{{calc}}
\setmainfont{{Lato}}
\definecolor{{dark}}{{HTML}}{{1A1A2E}}
\definecolor{{accent}}{{HTML}}{{4A4E69}}
\definecolor{{bright}}{{HTML}}{{9A8C98}}
\definecolor{{sbg}}{{HTML}}{{1A1A2E}}
\definecolor{{stext}}{{HTML}}{{E8E8E8}}
\definecolor{{stlt}}{{HTML}}{{AAAAAA}}
\hypersetup{{colorlinks,urlcolor=bright}}
\pagestyle{{empty}}\setlength{{\parindent}}{{0pt}}\setlength{{\parskip}}{{0pt}}
\newcommand{{\sh}}[1]{{\vspace{{5pt}}{{\footnotesize\bfseries\color{{stext}}\MakeUppercase{{#1}}}}\par\vspace{{-2pt}}{{\color{{bright}}\rule{{\linewidth}}{{0.5pt}}}}\par\vspace{{3pt}}}}
\newcommand{{\mh}}[1]{{\vspace{{6pt}}{{\normalsize\bfseries\color{{dark}}\MakeUppercase{{#1}}}}\par\vspace{{-3pt}}{{\color{{accent}}\rule{{\linewidth}}{{1.5pt}}}}\par\vspace{{3pt}}}}
\begin{{document}}
\begin{{tikzpicture}}[remember picture,overlay]
  \fill[sbg] (current page.north west) rectangle ($(current page.north west)+(0.34\paperwidth,-\paperheight)$);
\end{{tikzpicture}}
\columnratio{{0.30}}\setlength{{\columnsep}}{{10pt}}
\begin{{paracol}}{{2}}
\begin{{leftcolumn}}
\hspace{{8pt}}\begin{{minipage}}{{\dimexpr\linewidth-10pt}}
\vspace{{10pt}}
\begin{{center}}
  {{\LARGE\bfseries\color{{white}} {name_first}}}\\[2pt]
  {{\LARGE\color{{bright}} {name_last}}}\\[5pt]
  {{\tiny\color{{stlt}} {_e(domain.upper().replace('_',' '))} PROFESSIONAL}}
\end{{center}}
\vspace{{8pt}}
\sh{{Contact}}
{{\footnotesize\color{{stext}} {email}\\[2pt]{phone}\\[2pt]{location}\\[2pt]{linkedin}\\[2pt]{github}\\}}
\sh{{Education}}
{edu_sidebar}
\sh{{Skills}}
{skills_sidebar}
{(chr(10)+"\\sh{Certifications}"+chr(10)+certs_sidebar) if certs_sidebar else ""}
\end{{minipage}}
\end{{leftcolumn}}
\switchcolumn
\begin{{rightcolumn}}
\begin{{minipage}}{{\linewidth}}
\vspace{{8pt}}
{main_content}
\end{{minipage}}
\end{{rightcolumn}}
\end{{paracol}}
\end{{document}}
"""


# ============================================================
# TEMPLATE 6: ELEGANT
# ============================================================
def _build_elegant(data, level, domain):
    lc = LEVEL_CONFIG[level]
    name = _e(data.get("name", ""))
    email = _e(data.get("email", ""))
    phone = _e(data.get("phone", ""))
    location = _e(data.get("location", ""))
    linkedin = _e(data.get("linkedin", ""))
    github = _e(data.get("github", ""))
    summary = _e(data.get("summary", ""))
    skills = _skills_list(data)

    def cvsec(title):
        return (
            f"\\vspace{{8pt}}\n"
            f"\\noindent{{\\color{{primary}}\\rule{{\\linewidth}}{{1.5pt}}}}\\\\[-6pt]\n"
            f"\\noindent{{\\color{{secondary}}\\rule{{\\linewidth}}{{0.5pt}}}}\\\\[2pt]\n"
            f"{{\\normalsize\\bfseries\\color{{primary}}\\MakeUppercase{{{title}}}}}\\\\[-4pt]\n"
            f"{{\\color{{secondary}}\\rule{{\\linewidth}}{{0.5pt}}}}\n"
            f"\\vspace{{4pt}}\n"
        )

    def cvjob(title, sub, right):
        return (
            f"\\noindent\\begin{{tabularx}}{{\\linewidth}}{{Xr}}\n"
            f"{{\\small\\bfseries\\color{{primary}} {title}}} & {{\\small\\color{{secondary}} {right}}}\\\\\n"
            f"{{\\small\\color{{lt}}\\itshape {sub}}} & \\\\\n"
            f"\\end{{tabularx}}\n"
            f"\\vspace{{-4pt}}\n"
        )

    sections = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            sections += cvsec(lc["summary_label"])
            sections += f"{{\\small\\color{{lt}} {summary}}}\n"
        elif sec == "education" and data.get("education"):
            sections += cvsec("Education")
            for e in data["education"]:
                gpa = f" | GPA: {_e(e.get('gpa',''))}" if e.get("gpa") else ""
                sections += cvjob(
                    _e(e.get("degree", "")),
                    f"{_e(e.get('institution',''))}{gpa}",
                    _e(e.get("year", ""))
                )
        elif sec == "experience" and data.get("experience"):
            sections += cvsec(lc["exp_label"])
            for exp in data["experience"]:
                sections += cvjob(
                    _e(exp.get("title", "")),
                    _e(exp.get("company", "")),
                    _e(exp.get("duration", ""))
                )
                blist = "\n".join(
                    f"  \\item[\\color{{secondary}}\\small$\\triangleright$] {{\\small {_e(b)}}}"
                    for b in exp.get("bullets", [])
                )
                sections += f"\\begin{{itemize}}[leftmargin=*,itemsep=2pt,topsep=2pt,parsep=0pt]\n{blist}\n\\end{{itemize}}\n"
        elif sec == "projects" and data.get("projects"):
            sections += cvsec("Projects")
            for p in data["projects"]:
                sections += cvjob(_e(p.get("name", "")), _e(p.get("tech", "")), "")
                desc = f"{{\\small\\color{{lt}} {_e(p.get('description',''))}}}\\\\\n"
                if p.get("metrics"):
                    desc += f"{{\\small\\color{{secondary}} {_e(p.get('metrics',''))}}}\\\\\n"
                sections += desc
        elif sec == "skills" and skills:
            sections += cvsec("Technical Skills")
            grps = {}
            for s in skills:
                sl = s.lower()
                if any(t in sl for t in ["python","java","go","c++","scala"]): grp = "Languages"
                elif any(t in sl for t in ["tensorflow","pytorch","keras","scikit","ml","nlp"]): grp = "ML / AI"
                elif any(t in sl for t in ["aws","gcp","azure","docker","kubernetes"]): grp = "Cloud / DevOps"
                else: grp = "Other"
                grps.setdefault(grp, []).append(s)
            for grp, items in grps.items():
                sections += f"{{\\small\\bfseries\\color{{primary}} {grp}:}} {{\\small {', '.join(_e(s) for s in items)}}}\\\\\n"
        elif sec == "certifications" and data.get("certifications"):
            sections += cvsec("Certifications")
            for c in data["certifications"]:
                sections += f"{{\\small \\textcolor{{secondary}}{{$\\triangleright$}} {_e(c)}}}\\\\\n"
        elif sec == "achievements" and data.get("achievements"):
            sections += cvsec("Achievements")
            for a in data["achievements"]:
                sections += f"{{\\small \\textcolor{{secondary}}{{$\\triangleright$}} {_e(a)}}}\\\\\n"

    return rf"""
\documentclass[10pt,a4paper]{{article}}
\usepackage[top=1.5cm,bottom=1.5cm,left=2cm,right=2cm]{{geometry}}
\usepackage{{fontspec,xcolor,enumitem,parskip,hyperref,tabularx}}
\setmainfont{{Lato}}
\definecolor{{primary}}{{HTML}}{{2E4057}}
\definecolor{{secondary}}{{HTML}}{{048A81}}
\definecolor{{lt}}{{HTML}}{{555555}}
\hypersetup{{colorlinks,urlcolor=secondary}}
\pagestyle{{empty}}\setlength{{\parindent}}{{0pt}}\setlength{{\parskip}}{{0pt}}
\begin{{document}}
\begin{{center}}
  {{\fontsize{{22pt}}{{26pt}}\selectfont\bfseries\color{{primary}} {name}}}\\[4pt]
  {{\normalsize\color{{secondary}} {_e(domain.replace('_',' ').title())} Professional}}\\[4pt]
  {{\small\color{{lt}} {phone} \quad\textbullet\quad {email} \quad\textbullet\quad {location}\\[2pt]
  {linkedin} \quad\textbullet\quad {github}}}
\end{{center}}
{sections}
\end{{document}}
"""


# ============================================================
# TEMPLATE 7: SKILL BARS
# ============================================================
def _build_skillbars(data, level, domain):
    lc   = LEVEL_CONFIG[level]
    name = _e(data.get("name", ""))
    email= _e(data.get("email", ""))
    phone= _e(data.get("phone", ""))
    location= _e(data.get("location",""))
    linkedin= _e(data.get("linkedin",""))
    github  = _e(data.get("github",""))
    summary = _e(data.get("summary",""))
    skills  = _skills_list(data)

    max_bar  = lc["skill_level"]
    bar_step = max_bar / max(len(skills[:10]), 1)

    bars = ""
    for i, s in enumerate(skills[:10]):
        pct = max(max_bar - i * 0.04, 0.45)
        bars += (
            f"{{\\footnotesize\\color{{dk}} {_e(s)}}}\\\\[-2pt]\n"
            f"\\begin{{tikzpicture}}[baseline]\n"
            f"  \\fill[acl] (0,0) rectangle (3.5cm,4pt);\n"
            f"  \\fill[acc] (0,0) rectangle ({pct:.2f}*3.5cm,4pt);\n"
            f"\\end{{tikzpicture}}\\\\[3pt]\n"
        )

    edu_sidebar = ""
    for e in data.get("education", []):
        edu_sidebar += (
            f"{{\\footnotesize\\bfseries\\color{{dk}} {_e(e.get('degree',''))}}}\\\\\n"
            f"{{\\tiny {_e(e.get('institution',''))}}}\\\\\n"
            f"{{\\tiny\\color{{lt}} {_e(e.get('year',''))}"
            + (f" | GPA: {_e(e.get('gpa',''))}" if e.get("gpa") else "")
            + "}\\\\\n[4pt]\n"
        )

    certs_s = "\n".join(
        f"{{\\footnotesize\\textbullet\\ {_e(c)}}}\\\\"
        for c in data.get("certifications", [])
    )

    main_content = ""
    for sec in lc["section_order"]:
        if sec == "summary" and summary:
            main_content += f"""
\\mh{{{lc['summary_label']}}}
{{\\small {summary}}}
"""
        elif sec == "experience" and data.get("experience"):
            main_content += f"\\mh{{{lc['exp_label']}}}\n"
            for exp in data["experience"]:
                blist = "\n".join(f"  \\item {_e(b)}" for b in exp.get("bullets",[]))
                main_content += f"""
{{\\small\\bfseries\\color{{dk}} {_e(exp.get('title',''))}}}\\hfill{{\\footnotesize\\color{{lt}} {_e(exp.get('duration',''))}}}\\\\
{{\\footnotesize {_e(exp.get('company',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=2pt,parsep=0pt]\\small
{blist}
\\end{{itemize}}\\vspace{{3pt}}
"""
        elif sec == "projects" and data.get("projects"):
            main_content += "\\mh{Projects}\n"
            for p in data["projects"]:
                main_content += f"""
{{\\small\\bfseries\\color{{dk}} {_e(p.get('name',''))}}}\\hfill{{\\footnotesize\\color{{lt}} {_e(p.get('tech',''))}}}\\\\
{{\\small {_e(p.get('description',''))}}}\\\\
{f"{{\\footnotesize\\color{{lt}} {_e(p.get('metrics',''))}}}\\\\" if p.get("metrics") else ""}
\\vspace{{3pt}}
"""
        elif sec == "achievements" and data.get("achievements"):
            main_content += "\\mh{Achievements}\n"
            for a in data["achievements"]:
                main_content += f"{{\\small \\textbullet\\ {_e(a)}}}\\\\\n"
        elif sec == "skills" and skills:
            main_content += "\\mh{Technical Skills}\n"
            main_content += "\\begin{tabular}{@{}ll@{}}\n"
            for i in range(0, min(len(skills),14),2):
                row = " & ".join(f"\\small {_e(skills[j])}" for j in range(i, min(i+2,len(skills))))
                main_content += row + " \\\\\n"
            main_content += "\\end{tabular}\n"

    return rf"""
\documentclass[10pt,a4paper]{{article}}
\usepackage[top=0pt,bottom=1cm,left=0pt,right=0pt]{{geometry}}
\usepackage{{fontspec,xcolor,paracol,enumitem,parskip,hyperref,tikz}}
\usetikzlibrary{{calc}}
\setmainfont{{Lato}}
\definecolor{{acc}}{{HTML}}{{2D6A4F}}
\definecolor{{acl}}{{HTML}}{{D8F3DC}}
\definecolor{{dk}}{{HTML}}{{1B4332}}
\definecolor{{lt}}{{HTML}}{{74C69D}}
\definecolor{{sb}}{{HTML}}{{F0FBF4}}
\hypersetup{{colorlinks,urlcolor=acc}}
\pagestyle{{empty}}\setlength{{\parindent}}{{0pt}}\setlength{{\parskip}}{{0pt}}
\newcommand{{\mh}}[1]{{\vspace{{6pt}}{{\small\bfseries\color{{dk}}\MakeUppercase{{#1}}}}\par\vspace{{-3pt}}\textcolor{{acc}}{{\rule{{\linewidth}}{{1pt}}}}\par\vspace{{3pt}}}}
\newcommand{{\sh}}[1]{{\vspace{{5pt}}{{\footnotesize\bfseries\color{{acc}}\MakeUppercase{{#1}}}}\par\vspace{{-2pt}}\textcolor{{acc}}{{\rule{{\linewidth}}{{0.5pt}}}}\par\vspace{{3pt}}}}
\begin{{document}}
\begin{{tikzpicture}}[remember picture,overlay]
  \fill[dk] (current page.north west) rectangle ($(current page.north east)+(0,-2.5cm)$);
  \fill[acc] (current page.north west) rectangle ($(current page.north west)+(0.305\paperwidth,-\paperheight)$);
  \fill[sb] ($(current page.north west)+(0.305\paperwidth,0)$) rectangle ($(current page.north east)+(0,-\paperheight)$);
\end{{tikzpicture}}
\vspace{{-0.05cm}}
\begin{{minipage}}{{\paperwidth}}
\hspace{{18pt}}\begin{{minipage}}{{0.52\paperwidth}}
  \vspace{{13pt}}
  {{\fontsize{{20pt}}{{24pt}}\selectfont\bfseries\color{{white}} {name}}}\\[3pt]
  {{\normalsize\color{{lt}} {_e(lc['summary_label'].split()[0])} | {_e(domain.replace('_',' ').title())}}}
  \vspace{{13pt}}
\end{{minipage}}\begin{{minipage}}{{0.43\paperwidth}}
  \vspace{{13pt}}
  {{\footnotesize\color{{white!75!dk}} {email}\\ {phone} | {location}\\ {linkedin}\\ {github}}}
  \vspace{{13pt}}
\end{{minipage}}
\end{{minipage}}
\columnratio{{0.305}}\setlength{{\columnsep}}{{0pt}}
\begin{{paracol}}{{2}}
\begin{{leftcolumn}}
\hspace{{8pt}}\begin{{minipage}}{{\dimexpr\linewidth-12pt}}
\vspace{{8pt}}
\sh{{Skill Level}}
{bars}
\sh{{Education}}
{edu_sidebar}
{(chr(10)+"\\sh{Certifications}"+chr(10)+certs_s) if certs_s else ""}
\end{{minipage}}
\end{{leftcolumn}}
\switchcolumn
\begin{{rightcolumn}}
\hspace{{10pt}}\begin{{minipage}}{{\dimexpr\linewidth-14pt}}
\vspace{{8pt}}
{main_content}
\end{{minipage}}
\end{{rightcolumn}}
\end{{paracol}}
\end{{document}}
"""


# ============================================================
# MAIN ENTRY POINT
# ============================================================
TEMPLATE_BUILDERS = {
    "jakescv":  (_build_jakescv,  "pdflatex"),
    "altacv":   (_build_altacv,   "xelatex"),
    "moderncv": (_build_moderncv, "xelatex"),
    "awesomecv":(_build_awesomecv,"xelatex"),
    "deedycv":  (_build_deedycv,  "xelatex"),
    "elegant":  (_build_elegant,  "xelatex"),
    "skillbars":(_build_skillbars,"xelatex"),
}

TEMPLATE_INFO = {
    "jakescv":   {"name": "Jake's Resume",  "engine": "pdflatex", "ats": 10, "visual": 4},
    "altacv":    {"name": "AltaCV",         "engine": "xelatex",  "ats": 7,  "visual": 7},
    "moderncv":  {"name": "ModernCV",       "engine": "xelatex",  "ats": 7,  "visual": 8},
    "awesomecv": {"name": "Awesome CV",     "engine": "xelatex",  "ats": 6,  "visual": 9},
    "deedycv":   {"name": "Deedy CV",       "engine": "xelatex",  "ats": 6,  "visual": 9},
    "elegant":   {"name": "Elegant",        "engine": "xelatex",  "ats": 8,  "visual": 7},
    "skillbars": {"name": "Skill Bars",     "engine": "xelatex",  "ats": 5,  "visual": 10},
}


def build_template_pdf(
    data: dict,
    template: str = "jakescv",
    level: str = "fresher",
    domain: str = "software",
) -> bytes:
    """
    Build a resume PDF using the specified Overleaf-quality template.

    Args:
        data: Resume data dict with keys:
              name, email, phone, location, linkedin, github,
              summary, experience, education, skills,
              projects, certifications, achievements
        template: One of jakescv/altacv/moderncv/awesomecv/deedycv/elegant/skillbars
        level: fresher/junior/mid/senior/lead
        domain: software/aiml/data_science/devops/marketing/hr/finance/product/design/business_analyst/sales/general

    Returns:
        PDF bytes
    """
    if template not in TEMPLATE_BUILDERS:
        raise ValueError(f"Unknown template: {template}. Choose from: {list(TEMPLATE_BUILDERS.keys())}")
    if level not in LEVEL_CONFIG:
        raise ValueError(f"Unknown level: {level}. Choose from: {list(LEVEL_CONFIG.keys())}")

    builder, engine = TEMPLATE_BUILDERS[template]
    latex = builder(data, level, domain)
    return _compile(latex, engine)


def get_all_templates() -> list:
    """Returns list of all available Overleaf-style templates."""
    return [
        {
            "template_id": tid,
            "template_name": info["name"],
            "engine": info["engine"],
            "ats_friendliness": info["ats"],
            "visual_appeal": info["visual"],
            "tier": "overleaf",
        }
        for tid, info in TEMPLATE_INFO.items()
    ]