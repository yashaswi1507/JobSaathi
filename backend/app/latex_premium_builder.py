"""
latex_premium_builder.py
-------------------------
Premium LaTeX resume templates with advanced features:
  - altacv: Two-column sidebar, Lato font (AltaCV style)
  - skillbars: Skill progress bars, Open Sans font
  - colorbox: Colored header box, tcolorbox sections
  - premium: All features combined — ultimate template
"""

import subprocess, tempfile, os, re, shutil, platform

def _find_latex_engine(engine: str) -> str:
    # 1. PATH check
    found = shutil.which(engine)
    if found:
        return found
    if platform.system() != "Windows":
        return engine
    import winreg
    # 2. Registry
    for hive, rp in [(winreg.HKEY_CURRENT_USER, r"SOFTWARE\MiKTeX.org\MiKTeX"),
                     (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\MiKTeX.org\MiKTeX")]:
        try:
            key = winreg.OpenKey(hive, rp)
            root, _ = winreg.QueryValueEx(key, "PathPrefix")
            winreg.CloseKey(key)
            c = os.path.join(root, "miktex", "bin", "x64", f"{engine}.exe")
            if os.path.isfile(c):
                print(f"[latex_premium] Registry: {c}")
                return c
        except Exception:
            pass
    # 3. Common paths
    local = os.environ.get("LOCALAPPDATA", "")
    prog  = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    for c in [
        os.path.join(local, "Programs", "MiKTeX", "miktex", "bin", "x64", f"{engine}.exe"),
        os.path.join(local, "Programs", "MiKTeX", "miktex", "bin", f"{engine}.exe"),
        os.path.join(prog,  "MiKTeX", "miktex", "bin", "x64", f"{engine}.exe"),
        os.path.join("C:\", "MiKTeX", "miktex", "bin", "x64", f"{engine}.exe"),
        os.path.join("C:\", "texlive", "2024", "bin", "windows", f"{engine}.exe"),
    ]:
        if os.path.isfile(c):
            print(f"[latex_premium] Found: {c}")
            return c
    # 4. `where` command
    try:
        r = __import__("subprocess").run(["where", engine], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return engine


def _escape(text):
    if not text: return ""
    text = str(text)
    for old, new in [("&","\\&"),("%","\\%"),("$","\\$"),("#","\\#"),
                     ("_","\\_"),("{","\\{"),("}","\\}"),("~","\\textasciitilde{}"),
                     ("^","\\textasciicircum{}"),("\\","\\textbackslash{}")]:
        text = text.replace(old, new)
    return text


def _compile_xelatex(latex_doc, tries=2):
    """Compile with xelatex (supports system fonts like Lato)."""
    engine_path = _find_latex_engine("xelatex")
    print(f"[latex_premium] Using xelatex: {engine_path}")
    with tempfile.TemporaryDirectory() as tmp:
        tex = os.path.join(tmp, "resume.tex")
        pdf = os.path.join(tmp, "resume.pdf")
        with open(tex, "w", encoding="utf-8") as f:
            f.write(latex_doc)
        for _ in range(tries):
            r = subprocess.run(
                [engine_path, "-interaction=nonstopmode", "-output-directory", tmp, tex],
                capture_output=True, timeout=60
            )
        if not os.path.exists(pdf):
            raise RuntimeError(r.stdout.decode()[-800:])
        return open(pdf, "rb").read()


def _compile_pdflatex(latex_doc, tries=2):
    """Compile with pdflatex (faster, standard fonts)."""
    engine_path = _find_latex_engine("pdflatex")
    print(f"[latex_premium] Using pdflatex: {engine_path}")
    with tempfile.TemporaryDirectory() as tmp:
        tex = os.path.join(tmp, "resume.tex")
        pdf = os.path.join(tmp, "resume.pdf")
        with open(tex, "w", encoding="utf-8") as f:
            f.write(latex_doc)
        for _ in range(tries):
            r = subprocess.run(
                [engine_path, "-interaction=nonstopmode", "-output-directory", tmp, tex],
                capture_output=True, timeout=60
            )
        if not os.path.exists(pdf):
            raise RuntimeError(r.stdout.decode()[-800:])
        return open(pdf, "rb").read()


# ──────────────────────────────────────────────
# TEMPLATE 1: ALTACV STYLE (Two-column, Lato)
# ──────────────────────────────────────────────
def build_altacv_template(data, level, domain, accent="0D7377"):
    """
    AltaCV-inspired two-column layout using minipage.
    Left: skills, education, certs | Right: summary, experience, projects
    Font: Lato
    """
    name     = _escape(data.get("name","Your Name"))
    email    = _escape(data.get("email",""))
    phone    = _escape(data.get("phone",""))
    location = _escape(data.get("location",""))
    linkedin = _escape(data.get("linkedin",""))
    github   = _escape(data.get("github",""))
    summary  = _escape(data.get("summary",""))

    skills   = data.get("skills", [])
    skills_tex = "\n".join(f"  {{\\small\\color{{darktext}} {_escape(s)}}}\\\\[2pt]" for s in skills[:14])

    edu_tex = ""
    for edu in data.get("education", []):
        gpa = f" GPA: {_escape(edu.get('gpa',''))}" if edu.get("gpa") else ""
        edu_tex += f"{{\\small\\bfseries {_escape(edu.get('degree',''))}}}\\\\{{\\tiny {_escape(edu.get('institution',''))} {_escape(edu.get('year',''))}{gpa}}}\\\\[5pt]"

    cert_tex = "\n".join(f"{{\\tiny \\textbullet\\ {_escape(c)}\\\\[1pt]}}" for c in data.get("certifications",[]))
    ach_tex  = "\n".join(f"{{\\tiny \\textbullet\\ {_escape(a)}\\\\[1pt]}}" for a in data.get("achievements",[]))

    exp_label = "Work Experience" if level in ("mid","senior","lead") else "Internship \\& Experience"
    exp_tex = ""
    for exp in data.get("experience", []):
        bullets = "\n".join(f"  \\item {_escape(b)}" for b in exp.get("bullets",[]))
        exp_tex += f"""{{\\small\\bfseries\\color{{darktext}} {_escape(exp.get('title',''))}}} \\hfill {{\\small\\color{{accent}} {_escape(exp.get('duration',''))}}}\\\\
{{\\small\\color{{lighttext}}\\itshape {_escape(exp.get('company',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=0pt,topsep=1pt]\\small
{bullets}
\\end{{itemize}}\\vspace{{3pt}}
"""

    proj_tex = ""
    for proj in data.get("projects", []):
        metrics = _escape(proj.get("metrics",""))
        proj_tex += f"""{{\\small\\bfseries {_escape(proj.get('name',''))}}} {{\\small\\color{{accent}} | {_escape(proj.get('tech',''))}}}\\\\
{{\\small {_escape(proj.get('description',''))}}}\\\\
{"{{\\small\\color{{lighttext}} " + metrics + "}}" if metrics else ""}\\vspace{{3pt}}
"""

    sum_label = "Objective" if level in ("fresher","junior") else "Professional Summary"

    return f"""\\documentclass[10pt,a4paper]{{article}}
\\usepackage[top=0pt,bottom=1cm,left=0pt,right=0pt]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\usepackage{{enumitem}}
\\usepackage{{parskip}}
\\usepackage{{hyperref}}

\\setmainfont{{Lato}}

\\definecolor{{accent}}{{HTML}}{{{accent}}}
\\definecolor{{darktext}}{{HTML}}{{2D3748}}
\\definecolor{{lighttext}}{{HTML}}{{718096}}

\\hypersetup{{colorlinks=true,urlcolor=accent}}
\\pagestyle{{empty}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{1pt}}

\\newcommand{{\\sechead}}[1]{{{{\\small\\bfseries\\color{{accent}}\\MakeUppercase{{#1}}}}\\\\[-2pt]{{\\color{{accent}}\\rule{{\\linewidth}}{{0.7pt}}}}\\\\[3pt]}}

\\begin{{document}}

% Header
\\colorbox{{accent}}{{\\parbox{{\\paperwidth}}{{\\vspace{{10pt}}\\centering
  {{\\LARGE\\bfseries\\color{{white}} {name}}}\\\\[4pt]
  {{\\small\\color{{white!80!accent}} {email} $\\cdot$ {phone} $\\cdot$ {location}\\\\{linkedin} $\\cdot$ {github}}}
\\vspace{{10pt}}}}}}

% Two columns via minipage
\\begin{{minipage}}[t]{{0.30\\paperwidth}}
\\colorbox{{gray!12}}{{\\parbox{{\\dimexpr0.30\\paperwidth\\relax}}{{\\vspace{{6pt}}
\\hspace{{6pt}}\\begin{{minipage}}{{0.86\\linewidth}}

\\sechead{{Skills}}
{skills_tex}

\\sechead{{Education}}
{edu_tex}

{("\\sechead{{Certifications}}" + cert_tex) if cert_tex else ""}
{("\\sechead{{Achievements}}" + ach_tex) if ach_tex else ""}

\\end{{minipage}}\\vspace{{6pt}}}}}}
\\end{{minipage}}%
\\begin{{minipage}}[t]{{0.70\\paperwidth}}
\\hspace{{10pt}}\\begin{{minipage}}{{\\dimexpr0.70\\paperwidth-20pt\\relax}}
\\vspace{{8pt}}

{("\\sechead{{" + sum_label + "}}{{\\small " + summary + "}}\\vspace{{4pt}}") if summary else ""}

{("\\sechead{{" + exp_label + "}}" + exp_tex) if exp_tex else ""}

{("\\sechead{{Research \\& Projects}}" + proj_tex) if proj_tex else ""}

\\end{{minipage}}
\\end{{minipage}}

\\end{{document}}
"""


def build_skillbars_template(data, level, domain, accent="6B2D8B"):
    """
    Resume with visual skill rating bars (●●●●○ style).
    Clean Open Sans font, professional layout.
    """
    name    = _escape(data.get("name","Your Name"))
    email   = _escape(data.get("email",""))
    phone   = _escape(data.get("phone",""))
    loc     = _escape(data.get("location",""))
    lin     = _escape(data.get("linkedin",""))
    git     = _escape(data.get("github",""))
    summary = _escape(data.get("summary",""))

    # Skill bars — assign ratings based on order (first = expert)
    skills = data.get("skills", [])
    skill_ratings = []
    for i, s in enumerate(skills[:12]):
        if i < 3:   dots = "\\filledcirc\\filledcirc\\filledcirc\\filledcirc\\filledcirc"
        elif i < 6: dots = "\\filledcirc\\filledcirc\\filledcirc\\filledcirc\\emptycirc"
        elif i < 9: dots = "\\filledcirc\\filledcirc\\filledcirc\\emptycirc\\emptycirc"
        else:       dots = "\\filledcirc\\filledcirc\\emptycirc\\emptycirc\\emptycirc"
        skill_ratings.append(f"  {_escape(s)} & {dots} \\\\[3pt]")

    skills_tex = "\n".join(skill_ratings)

    # Experience
    exp_label = "Work Experience" if level in ("mid","senior","lead") else "Internship \\& Experience"
    exp_tex = ""
    for exp in data.get("experience", []):
        bullets = "\n".join(f"  \\item {_escape(b)}" for b in exp.get("bullets",[]))
        exp_tex += f"""
\\noindent{{\\bfseries\\color{{darktext}} {_escape(exp.get('title',''))}}} \\hfill {{\\color{{accent}}\\small {_escape(exp.get('duration',''))}}}\\\\
{{\\small\\color{{lighttext}}\\itshape {_escape(exp.get('company',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=1pt,topsep=2pt]
{bullets}
\\end{{itemize}}
\\vspace{{3pt}}
"""

    # Projects
    proj_tex = ""
    for proj in data.get("projects",[]):
        metrics = _escape(proj.get("metrics",""))
        proj_tex += f"""
\\noindent{{\\bfseries\\color{{darktext}} {_escape(proj.get('name',''))}}} \\hfill {{\\small\\color{{lighttext}} {_escape(proj.get('tech',''))}}}\\\\
{{\\small {_escape(proj.get('description',''))}}}\\\\
{"{{\\small\\color{{accent}} " + metrics + "}}" if metrics else ""}
\\vspace{{4pt}}
"""

    # Education
    edu_tex = ""
    for edu in data.get("education",[]):
        gpa = f" $\\cdot$ GPA: {_escape(edu.get('gpa',''))}" if edu.get("gpa") else ""
        edu_tex += f"\\noindent{{\\bfseries\\small {_escape(edu.get('degree',''))}}} \\hfill {{\\color{{accent}}\\small {_escape(edu.get('year',''))}}}\\\\{{\\small\\color{{lighttext}} {_escape(edu.get('institution',''))}{gpa}}}\\\\[4pt]\n"

    # Certs
    cert_tex = "\n".join(f"\\item {_escape(c)}" for c in data.get("certifications",[]))
    ach_tex  = "\n".join(f"\\item {_escape(a)}" for a in data.get("achievements",[]))

    section_order = (
        ["summary","experience","projects","certifications","achievements","education"]
        if level in ("mid","senior","lead")
        else ["summary","education","experience","projects","certifications","achievements"]
    )

    main_content = ""
    for sec in section_order:
        if sec == "summary" and summary:
            main_content += f"\\resumesec{{{'Objective' if level in ('fresher','junior') else 'Professional Summary'}}}\n{summary}\n\n"
        elif sec == "experience" and exp_tex:
            main_content += f"\\resumesec{{{exp_label}}}\n{exp_tex}\n"
        elif sec == "projects" and proj_tex:
            main_content += f"\\resumesec{{Research \\& Projects}}\n{proj_tex}\n"
        elif sec == "education" and edu_tex:
            main_content += f"\\resumesec{{Education}}\n{edu_tex}\n"
        elif sec == "certifications" and cert_tex:
            main_content += f"\\resumesec{{Certifications}}\n\\begin{{itemize}}[leftmargin=*,itemsep=1pt]\n{cert_tex}\n\\end{{itemize}}\n"
        elif sec == "achievements" and ach_tex:
            main_content += f"\\resumesec{{Achievements \\& Awards}}\n\\begin{{itemize}}[leftmargin=*,itemsep=1pt]\n{ach_tex}\n\\end{{itemize}}\n"

    return f"""\\documentclass[10pt,a4paper]{{article}}
\\usepackage[margin=1.4cm]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\usepackage{{tabularx}}
\\usepackage{{enumitem}}
\\usepackage{{tikz}}
\\usepackage{{paracol}}
\\usepackage{{parskip}}
\\usepackage{{hyperref}}

\\setmainfont{{Lato}}

\\definecolor{{accent}}{{HTML}}{{{accent}}}
\\definecolor{{darktext}}{{HTML}}{{1A202C}}
\\definecolor{{lighttext}}{{HTML}}{{718096}}
\\definecolor{{sidebar}}{{HTML}}{{EDF2F7}}

\\hypersetup{{colorlinks=true,urlcolor=accent}}
\\pagestyle{{empty}}
\\setlength{{\\parskip}}{{2pt}}
\\setlength{{\\parindent}}{{0pt}}

\\newcommand{{\\filledcirc}}{{\\textcolor{{accent}}{{\\large$\\bullet$}}}}
\\newcommand{{\\emptycirc}}{{\\textcolor{{lighttext}}{{\\large$\\circ$}}}}

\\newcommand{{\\resumesec}}[1]{{%
  \\vspace{{6pt}}
  {{\\normalsize\\bfseries\\color{{accent}}\\MakeUppercase{{#1}}}}\\\\[-3pt]
  {{\\color{{accent}}\\rule{{\\linewidth}}{{1pt}}}}\\\\[3pt]
}}

\\begin{{document}}

% ── Header ──
\\begin{{tikzpicture}}[remember picture,overlay]
  \\fill[accent!90!black] (current page.north west) rectangle ([yshift=-2.6cm]current page.north east);
\\end{{tikzpicture}}
\\vspace{{-1.2cm}}
\\begin{{center}}
  {{\\LARGE\\bfseries\\color{{white}} {name}}}\\\\[4pt]
  {{\\small\\color{{white!85!accent}} {email} $\\cdot$ {phone} $\\cdot$ {loc}}}\\\\
  {{\\small\\color{{white!85!accent}} {lin} $\\cdot$ {git}}}
\\end{{center}}
\\vspace{{1.2cm}}

\\columnratio{{0.30}}
\\begin{{paracol}}{{2}}

% ── SIDEBAR ──
\\begin{{leftcolumn}}
\\begin{{tikzpicture}}[remember picture,overlay]
  \\fill[sidebar] (current page.south west) rectangle ([xshift=0.32\\paperwidth]current page.north west);
\\end{{tikzpicture}}
\\hspace{{4pt}}\\begin{{minipage}}{{0.92\\linewidth}}

{{\\small\\bfseries\\color{{accent}}\\MakeUppercase{{Skills}}}}\\\\[-2pt]
{{\\color{{accent}}\\rule{{\\linewidth}}{{0.8pt}}}}\\\\[4pt]
\\begin{{tabular}}{{@{{}}l r@{{}}}}
{skills_tex}
\\end{{tabular}}

\\end{{minipage}}
\\end{{leftcolumn}}

\\switchcolumn

% ── MAIN ──
\\begin{{rightcolumn}}
{main_content}
\\end{{rightcolumn}}
\\end{{paracol}}

\\end{{document}}
"""


# ──────────────────────────────────────────────
# TEMPLATE 3: COLORBOX HEADER
# ──────────────────────────────────────────────
def build_colorbox_template(data, level, domain, accent="1B3A6B"):
    """
    Premium template with tcolorbox sections,
    colored header, clean typography.
    """
    name    = _escape(data.get("name","Your Name"))
    email   = _escape(data.get("email",""))
    phone   = _escape(data.get("phone",""))
    loc     = _escape(data.get("location",""))
    lin     = _escape(data.get("linkedin",""))
    git     = _escape(data.get("github",""))
    summary = _escape(data.get("summary",""))

    def make_section(title, content):
        return f"""
\\begin{{tcolorbox}}[enhanced,arc=0pt,outer arc=0pt,
  boxrule=0pt,toprule=1.5pt,
  colframe=accent,colback=white,
  fonttitle=\\bfseries\\color{{accent}}\\small,
  title=\\MakeUppercase{{{title}}},
  left=4pt,right=4pt,top=3pt,bottom=3pt]
{content}
\\end{{tcolorbox}}
\\vspace{{4pt}}
"""

    # Experience
    exp_label = "Work Experience" if level in ("mid","senior","lead") else "Internship \\& Experience"
    exp_content = ""
    for exp in data.get("experience",[]):
        bullets = "\n".join(f"  \\item {_escape(b)}" for b in exp.get("bullets",[]))
        exp_content += f"""{{\\small\\bfseries\\color{{darktext}} {_escape(exp.get('title',''))}}} \\hfill {{\\small\\color{{accent}} {_escape(exp.get('duration',''))}}}\\\\
{{\\small\\color{{lighttext}}\\itshape {_escape(exp.get('company',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=0pt,topsep=2pt,parsep=0pt]
{bullets}
\\end{{itemize}}\\vspace{{3pt}}
"""

    # Skills
    skills = data.get("skills",[])
    skills_content = "{\\small " + " $\\cdot$ ".join(_escape(s) for s in skills) + "}"

    # Projects
    proj_content = ""
    for proj in data.get("projects",[]):
        metrics = _escape(proj.get("metrics",""))
        proj_content += f"""{{\\small\\bfseries {_escape(proj.get('name',''))}}} {{\\small\\color{{accent}} | {_escape(proj.get('tech',''))}}}\\\\
{{\\small {_escape(proj.get('description',''))}}}\\\\
{"{{\\small\\color{{accent}} " + metrics + "}}" if metrics else ""}\\vspace{{3pt}}
"""

    # Education
    edu_content = ""
    for edu in data.get("education",[]):
        gpa = f" | GPA: {_escape(edu.get('gpa',''))}" if edu.get("gpa") else ""
        edu_content += f"{{\\small\\bfseries {_escape(edu.get('degree',''))}}} \\hfill {{\\small\\color{{accent}} {_escape(edu.get('year',''))}}}\\\\{{\\small\\color{{lighttext}} {_escape(edu.get('institution',''))}{gpa}}}\\\\[3pt]\n"

    # Certs + Achievements
    cert_items = "\n".join(f"\\item {_escape(c)}" for c in data.get("certifications",[]))
    ach_items  = "\n".join(f"\\item {_escape(a)}" for a in data.get("achievements",[]))

    certs_content = f"\\begin{{itemize}}[leftmargin=*,itemsep=0pt]\\small\n{cert_items}\n\\end{{itemize}}" if cert_items else ""
    ach_content   = f"\\begin{{itemize}}[leftmargin=*,itemsep=0pt]\\small\n{ach_items}\n\\end{{itemize}}" if ach_items else ""

    sum_label = "Objective" if level in ("fresher","junior") else "Professional Summary"
    proj_label = "Research \\& Projects"

    if level in ("mid","senior","lead"):
        sections = [
            make_section(sum_label, f"{{\\small {summary}}}") if summary else "",
            make_section(exp_label, exp_content) if exp_content else "",
            make_section("Technical Skills", skills_content),
            make_section(proj_label, proj_content) if proj_content else "",
            make_section("Education", edu_content) if edu_content else "",
            make_section("Certifications", certs_content) if certs_content else "",
            make_section("Achievements \\& Awards", ach_content) if ach_content else "",
        ]
    else:
        sections = [
            make_section(sum_label, f"{{\\small {summary}}}") if summary else "",
            make_section("Technical Skills", skills_content),
            make_section(proj_label, proj_content) if proj_content else "",
            make_section("Education", edu_content) if edu_content else "",
            make_section(exp_label, exp_content) if exp_content else "",
            make_section("Certifications", certs_content) if certs_content else "",
            make_section("Achievements \\& Awards", ach_content) if ach_content else "",
        ]

    return f"""\\documentclass[10pt,a4paper]{{article}}
\\usepackage[top=0cm,bottom=1cm,left=1.3cm,right=1.3cm]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\usepackage[most]{{tcolorbox}}
\\usepackage{{enumitem}}
\\usepackage{{tikz}}
\\usepackage{{parskip}}
\\usepackage{{hyperref}}

\\setmainfont{{Lato}}

\\definecolor{{accent}}{{HTML}}{{{accent}}}
\\definecolor{{darktext}}{{HTML}}{{1A202C}}
\\definecolor{{lighttext}}{{HTML}}{{4A5568}}

\\hypersetup{{colorlinks=true,urlcolor=accent}}
\\pagestyle{{empty}}
\\setlength{{\\parskip}}{{1pt}}
\\setlength{{\\parindent}}{{0pt}}

\\begin{{document}}

% ── Header Box ──
\\begin{{tcolorbox}}[enhanced,arc=0pt,
  colback=accent,colframe=accent,
  boxrule=0pt, left=14pt,right=14pt,top=12pt,bottom=12pt]
  {{\\Huge\\bfseries\\color{{white}} {name}}}\\\\[4pt]
  {{\\small\\color{{white!80!accent}}
    {email} $\\quad\\cdot\\quad$ {phone} $\\quad\\cdot\\quad$ {loc}\\\\
    {lin} $\\quad\\cdot\\quad$ {git}
  }}
\\end{{tcolorbox}}
\\vspace{{6pt}}

{"".join(s for s in sections if s)}

\\end{{document}}
"""


# ──────────────────────────────────────────────
# TEMPLATE 4: PREMIUM COMBINED
# (Sidebar + Skill dots + Colorbox header + Lato)
# ──────────────────────────────────────────────
def build_premium_template(data, level, domain, accent="0D7377"):
    """
    Premium template — combines all features:
    - Colored header with name
    - Two-column layout
    - Skill dots in sidebar
    - tcolorbox section headers
    - Lato font
    """
    name    = _escape(data.get("name","Your Name"))
    email   = _escape(data.get("email",""))
    phone   = _escape(data.get("phone",""))
    loc     = _escape(data.get("location",""))
    lin     = _escape(data.get("linkedin",""))
    git     = _escape(data.get("github",""))
    summary = _escape(data.get("summary",""))

    # Skill dots
    skills = data.get("skills",[])
    skill_rows = []
    for i, s in enumerate(skills[:14]):
        if i < 4:   filled, empty = 5, 0
        elif i < 8: filled, empty = 4, 1
        else:       filled, empty = 3, 2
        dots = "\\fc " * filled + "\\ec " * empty
        skill_rows.append(f"  \\small {_escape(s)} & {dots.strip()} \\\\[3pt]")
    skills_tex = "\n".join(skill_rows)

    # Education sidebar
    edu_tex = ""
    for edu in data.get("education",[]):
        gpa = f"\\\\{{\\tiny GPA: {_escape(edu.get('gpa',''))}}}" if edu.get("gpa") else ""
        edu_tex += f"{{\\small\\bfseries {_escape(edu.get('degree',''))}}}\\\\{{\\small\\color{{gray}} {_escape(edu.get('institution',''))} $\\cdot$ {_escape(edu.get('year',''))}}}{gpa}\\\\[6pt]\n"

    # Certs sidebar
    cert_tex = "\n".join(f"\\item\\small {_escape(c)}" for c in data.get("certifications",[]))
    ach_tex  = "\n".join(f"\\item\\small {_escape(a)}" for a in data.get("achievements",[]))

    # Experience main
    exp_label = "Work Experience" if level in ("mid","senior","lead") else "Internship \\& Experience"
    exp_tex = ""
    for exp in data.get("experience",[]):
        bullets = "\n".join(f"  \\item {_escape(b)}" for b in exp.get("bullets",[]))
        exp_tex += f"""
\\begin{{tcolorbox}}[enhanced,arc=2pt,
  colback=white,colframe=accent!30!white,
  boxrule=0.5pt,left=4pt,right=4pt,top=2pt,bottom=2pt]
{{\\small\\bfseries\\color{{darktext}} {_escape(exp.get('title',''))}}} \\hfill {{\\small\\color{{accent}} {_escape(exp.get('duration',''))}}}\\\\
{{\\small\\color{{gray}}\\itshape {_escape(exp.get('company',''))}}}
\\begin{{itemize}}[leftmargin=*,itemsep=0pt,topsep=2pt]
{bullets}
\\end{{itemize}}
\\end{{tcolorbox}}
\\vspace{{2pt}}
"""

    # Projects
    proj_tex = ""
    for proj in data.get("projects",[]):
        metrics = _escape(proj.get("metrics",""))
        proj_tex += f"""
\\begin{{tcolorbox}}[enhanced,arc=2pt,
  colback=accent!4!white,colframe=accent!30!white,
  boxrule=0.5pt,left=4pt,right=4pt,top=2pt,bottom=2pt]
{{\\small\\bfseries {_escape(proj.get('name',''))}}} $\\cdot$ {{\\small\\color{{accent}}\\itshape {_escape(proj.get('tech',''))}}}\\\\
{{\\small {_escape(proj.get('description',''))}}}\\\\
{"{{\\small\\bfseries\\color{{accent}} " + metrics + "}}" if metrics else ""}
\\end{{tcolorbox}}
\\vspace{{2pt}}
"""

    sum_label = "Objective" if level in ("fresher","junior") else "Professional Summary"

    main_sections = []
    if summary:
        main_sections.append(f"{{\\small\\color{{darktext}} {summary}}}\\vspace{{4pt}}")
    if exp_tex:
        main_sections.append(exp_tex)
    if proj_tex:
        main_sections.append(proj_tex)

    main_content = "\n".join(main_sections)

    return f"""\\documentclass[10pt,a4paper]{{article}}
\\usepackage[top=0cm,bottom=1cm,left=0cm,right=1cm]{{geometry}}
\\usepackage{{fontspec}}
\\usepackage{{xcolor}}
\\usepackage[most]{{tcolorbox}}
\\usepackage{{paracol}}
\\usepackage{{enumitem}}
\\usepackage{{tikz}}
\\usepackage{{parskip}}
\\usepackage{{hyperref}}

\\setmainfont{{Lato}}

\\definecolor{{accent}}{{HTML}}{{{accent}}}
\\definecolor{{darktext}}{{HTML}}{{1A202C}}
\\definecolor{{gray}}{{HTML}}{{718096}}
\\definecolor{{sidebar}}{{HTML}}{{F7FAFC}}

\\newcommand{{\\fc}}{{\\textcolor{{accent}}{{$\\bullet$}} }}
\\newcommand{{\\ec}}{{\\textcolor{{gray!50}}{{$\\circ$}} }}

\\hypersetup{{colorlinks=true,urlcolor=accent}}
\\pagestyle{{empty}}
\\setlength{{\\parskip}}{{1pt}}
\\setlength{{\\parindent}}{{0pt}}

\\newcommand{{\\sechead}}[1]{{%
  \\vspace{{6pt}}
  {{\\small\\bfseries\\color{{accent}}\\MakeUppercase{{#1}}}}\\\\[-2pt]
  {{\\color{{accent}}\\rule{{\\linewidth}}{{0.8pt}}}}\\\\[3pt]
}}

\\begin{{document}}

% ── Header ──
\\begin{{tcolorbox}}[enhanced,arc=0pt,
  colback=accent,colframe=accent,
  boxrule=0pt,left=14pt,right=14pt,top=10pt,bottom=10pt]
  {{\\Huge\\bfseries\\color{{white}} {name}}}\\\\[3pt]
  {{\\small\\color{{white!80!accent}}
    {email} $\\cdot$ {phone} $\\cdot$ {loc}\\\\
    {lin} $\\cdot$ {git}
  }}
\\end{{tcolorbox}}

\\columnratio{{0.30}}
\\begin{{paracol}}{{2}}

% ── SIDEBAR ──
\\begin{{leftcolumn}}
\\begin{{tikzpicture}}[remember picture,overlay]
  \\fill[sidebar] (current page.south west) rectangle ([xshift=0.32\\paperwidth]current page.north west);
\\end{{tikzpicture}}
\\hspace{{6pt}}\\begin{{minipage}}{{0.90\\linewidth}}

\\sechead{{Skills}}
\\begin{{tabular}}{{@{{}}l r@{{}}}}
{skills_tex}
\\end{{tabular}}

\\sechead{{Education}}
{edu_tex}

{"\\sechead{Certifications}\\begin{itemize}[leftmargin=*,itemsep=0pt]\\small" + cert_tex + "\\end{itemize}" if cert_tex else ""}

{"\\sechead{Achievements}\\begin{itemize}[leftmargin=*,itemsep=0pt]\\small" + ach_tex + "\\end{itemize}" if ach_tex else ""}

\\end{{minipage}}
\\end{{leftcolumn}}

\\switchcolumn

% ── MAIN ──
\\begin{{rightcolumn}}
\\vspace{{4pt}}

{"\\sechead{" + sum_label + "}" if summary else ""}
{main_content}
\\end{{rightcolumn}}
\\end{{paracol}}

\\end{{document}}
"""


# ──────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────
PREMIUM_DESIGNS = {
    "altacv":    {"name": "AltaCV",   "description": "Two-column sidebar, Lato font — AltaCV style",       "accent": "0D7377", "builder": build_altacv_template},
    "skillbars": {"name": "SkillBars","description": "Visual skill rating dots, Open Sans font",            "accent": "6B2D8B", "builder": build_skillbars_template},
    "colorbox":  {"name": "ColorBox", "description": "Premium tcolorbox sections, colored header",          "accent": "1B3A6B", "builder": build_colorbox_template},
    "premium":   {"name": "Premium",  "description": "All features combined — ultimate professional look",  "accent": "0D7377", "builder": build_premium_template},
}

def build_premium_pdf(data: dict, design: str, level: str = "fresher", domain: str = "software") -> bytes:
    """Build a premium LaTeX resume PDF."""
    cfg = PREMIUM_DESIGNS.get(design)
    if not cfg:
        raise ValueError(f"Unknown premium design: {design}")

    accent  = cfg.get("accent", "0D7377")
    builder = cfg["builder"]
    latex   = builder(data, level, domain, accent)
    return _compile_xelatex(latex)


def get_premium_templates() -> list:
    """Returns list of premium template options."""
    levels  = ["fresher", "junior", "mid", "senior", "lead"]
    domains = ["software", "data_science", "aiml", "devops", "cybersecurity",
               "marketing", "hr", "finance", "product", "design", "business_analyst", "sales", "general"]
    return [
        {"id": f"{ds}_{lv}_{dm}",
         "design": ds,
         "design_name": PREMIUM_DESIGNS[ds]["name"],
         "design_description": PREMIUM_DESIGNS[ds]["description"],
         "level": lv, "domain": dm,
         "engine": "LaTeX/XeLaTeX (Premium)",
         "tier": "premium"}
        for ds in PREMIUM_DESIGNS
        for lv in levels
        for dm in domains
    ]