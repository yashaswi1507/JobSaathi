"""
latex_resume_builder.py
------------------------
LaTeX-based resume builder for Classic, Academic, Executive designs.
Generates professional Overleaf-quality PDFs using pdflatex.
"""

import subprocess
import tempfile
import os
import re


# ============================================================
# DESIGN THEMES FOR LATEX
# ============================================================
LATEX_DESIGNS = {
    "classic": {
        "accent": "1A1A1A",
        "dark":   "1A1A1A",
        "gray":   "555555",
    },
    "academic": {
        "accent": "8B0000",
        "dark":   "8B0000",
        "gray":   "555555",
    },
    "executive": {
        "accent": "D4AF37",
        "dark":   "2C2C2C",
        "gray":   "555555",
    },
}

LEVEL_LABELS = {
    "fresher":    "Objective",
    "junior":     "Objective",
    "mid":        "Professional Summary",
    "senior":     "Senior Professional Summary",
    "lead":       "Leadership Profile",
}

EXP_LABELS = {
    "fresher":    "Internship \\& Experience",
    "junior":     "Work Experience",
    "mid":        "Work Experience",
    "senior":     "Work Experience",
    "lead":       "Leadership \\& Work Experience",
}

SKILLS_LABELS = {
    "software":        "Technical Skills",
    "data_science":    "Technical Skills \\& Tools",
    "aiml":            "AI/ML Skills \\& Frameworks",
    "devops":          "DevOps \\& Cloud Skills",
    "cybersecurity":   "Security Skills \\& Tools",
    "marketing":       "Marketing Skills \\& Tools",
    "hr":              "Core Competencies",
    "finance":         "Financial Skills \\& Tools",
    "product":         "Product \\& Management Skills",
    "design":          "Design Skills \\& Tools",
    "business_analyst":"Analysis \\& Business Skills",
    "sales":           "Sales Skills \\& Tools",
    "general":         "Skills",
}

PROJECTS_LABELS = {
    "software":        "Projects",
    "data_science":    "Research \\& Projects",
    "aiml":            "Research \\& ML Projects",
    "devops":          "Infrastructure \\& Projects",
    "cybersecurity":   "Security Projects \\& CTF",
    "marketing":       "Campaigns \\& Initiatives",
    "hr":              "HR Initiatives",
    "finance":         "Financial Projects \\& Analysis",
    "product":         "Products \\& Initiatives",
    "design":          "Design Projects \\& Case Studies",
    "business_analyst":"Business Analysis Projects",
    "sales":           "Sales Campaigns \\& Initiatives",
    "general":         "Projects",
}


def _escape(text):
    """Escape special LaTeX characters."""
    if not text:
        return ""
    text = str(text)
    replacements = [
        ("&",  "\\&"),
        ("%",  "\\%"),
        ("$",  "\\$"),
        ("#",  "\\#"),
        ("_",  "\\_"),
        ("{",  "\\{"),
        ("}",  "\\}"),
        ("~",  "\\textasciitilde{}"),
        ("^",  "\\textasciicircum{}"),
        ("\\", "\\textbackslash{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _skills_section(data, domain, design_cfg):
    """Generate domain-specific skills section."""
    skills = data.get("skills", [])
    if not skills:
        return ""

    label = SKILLS_LABELS.get(domain, "Skills")

    # Data Science / AI/ML grouped skills
    if domain in ("data_science", "aiml"):
        ml_terms = {"tensorflow","pytorch","keras","bert","gpt","transformer",
                    "deep learning","neural network","nlp","computer vision",
                    "xgboost","lightgbm","scikit-learn","sklearn","langchain","huggingface"}
        prog_terms = {"python","r","sql","java","scala","julia","c++","matlab"}
        lib_terms  = {"pandas","numpy","matplotlib","seaborn","scipy",
                      "flask","fastapi","streamlit","opencv","spacy","nltk"}
        tool_terms = {"aws","gcp","azure","docker","kubernetes","spark","hadoop",
                      "tableau","git","jupyter","mlflow","airflow"}

        groups = {"ML/AI":[], "Programming":[], "Libraries":[], "Tools":[], "Other":[]}
        for s in skills:
            sl = s.lower()
            if   any(t in sl for t in ml_terms):   groups["ML/AI"].append(s)
            elif any(t in sl for t in prog_terms):  groups["Programming"].append(s)
            elif any(t in sl for t in lib_terms):   groups["Libraries"].append(s)
            elif any(t in sl for t in tool_terms):  groups["Tools"].append(s)
            else:                                   groups["Other"].append(s)

        rows = ""
        for grp, items in groups.items():
            if items:
                rows += f"  \\textbf{{{_escape(grp)}}} & {_escape(', '.join(items))} \\\\[2pt]\n"
        return f"""
\\section{{{label}}}
\\begin{{tabularx}}{{\\linewidth}}{{@{{}} l X @{{}}}}
{rows}\\end{{tabularx}}
"""

    elif domain == "devops":
        cloud = [s for s in skills if any(t in s.lower() for t in ["aws","gcp","azure","cloud"])]
        containers = [s for s in skills if any(t in s.lower() for t in ["docker","kubernetes","k8s","helm"])]
        cicd = [s for s in skills if any(t in s.lower() for t in ["jenkins","ci/cd","github actions","gitlab","terraform","ansible"])]
        monitoring = [s for s in skills if any(t in s.lower() for t in ["prometheus","grafana","datadog","elk","splunk"])]
        other = [s for s in skills if s not in cloud+containers+cicd+monitoring]

        rows = ""
        for grp, items in [("Cloud",cloud),("Containers",containers),("CI/CD",cicd),("Monitoring",monitoring),("Other",other)]:
            if items:
                rows += f"  \\textbf{{{grp}}} & {_escape(', '.join(items))} \\\\[2pt]\n"
        return f"""
\\section{{{label}}}
\\begin{{tabularx}}{{\\linewidth}}{{@{{}} l X @{{}}}}
{rows}\\end{{tabularx}}
"""

    else:
        # Simple bullet list
        skills_str = _escape("  •  ".join(skills))
        return f"""
\\section{{{label}}}
{skills_str}
"""


def build_latex_resume(data, design="classic", level="fresher", domain="software"):
    """
    Builds a LaTeX resume and returns PDF bytes.
    Uses pdflatex for compilation.
    """
    d = LATEX_DESIGNS.get(design, LATEX_DESIGNS["classic"])
    accent = d["accent"]
    dark   = d["dark"]
    gray   = d["gray"]

    # ─── HEADER ───
    name     = _escape(data.get("name", "Your Name"))
    email    = _escape(data.get("email", ""))
    phone    = _escape(data.get("phone", ""))
    location = _escape(data.get("location", ""))
    linkedin = _escape(data.get("linkedin", ""))
    github   = _escape(data.get("github", ""))

    contact_parts = [p for p in [email, phone, location, linkedin, github] if p]
    contact_line  = " \\quad|\\quad ".join(contact_parts)

    # ─── SUMMARY ───
    summary_label = LEVEL_LABELS.get(level, "Professional Summary")
    summary_tex = ""
    if data.get("summary"):
        summary_tex = f"""
\\section{{{summary_label}}}
{_escape(data['summary'])}
"""

    # ─── EXPERIENCE ───
    exp_label = EXP_LABELS.get(level, "Work Experience")
    exp_tex = ""
    if data.get("experience"):
        exp_items = ""
        for exp in data["experience"]:
            title    = _escape(exp.get("title", ""))
            company  = _escape(exp.get("company", ""))
            duration = _escape(exp.get("duration", ""))
            bullets  = exp.get("bullets", [])
            bullet_tex = "\n".join(f"  \\item {_escape(b)}" for b in bullets)
            exp_items += f"""
\\noindent\\textbf{{{title}}} \\hfill \\textcolor{{accent}}{{\\small {duration}}}\\\\
\\textit{{{company}}}
\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=2pt]
{bullet_tex}
\\end{{itemize}}
\\vspace{{3pt}}
"""
        exp_tex = f"\\section{{{exp_label}}}\n{exp_items}"

    # ─── EDUCATION ───
    edu_tex = ""
    if data.get("education"):
        edu_items = ""
        for edu in data["education"]:
            degree  = _escape(edu.get("degree", ""))
            inst    = _escape(edu.get("institution", ""))
            year    = _escape(edu.get("year", ""))
            gpa     = edu.get("gpa", "")
            gpa_str = f" \\hfill \\textcolor{{gray}}{{\\small GPA: {_escape(gpa)}}}" if gpa else ""
            edu_items += f"""
\\noindent\\textbf{{{degree}}} \\hfill \\textcolor{{accent}}{{\\small {year}}}\\\\
{inst}{gpa_str}\\\\[4pt]
"""
        edu_tex = f"\\section{{Education}}\n{edu_items}"

    # ─── SKILLS ───
    skills_tex = _skills_section(data, domain, d)

    # ─── PROJECTS ───
    proj_label = PROJECTS_LABELS.get(domain, "Projects")
    proj_tex = ""
    if data.get("projects"):
        proj_items = ""
        for proj in data["projects"]:
            pname = _escape(proj.get("name", ""))
            tech  = _escape(proj.get("tech", ""))
            desc  = _escape(proj.get("description", ""))
            metrics = _escape(proj.get("metrics", ""))
            tech_str    = f"\\\\\\textit{{{tech}}}" if tech else ""
            metrics_str = f"\n  \\item {metrics}" if metrics else ""
            proj_items += f"""
\\noindent\\textbf{{{pname}}}{tech_str}
\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=2pt]
  \\item {desc}{metrics_str}
\\end{{itemize}}
\\vspace{{3pt}}
"""
        proj_tex = f"\\section{{{proj_label}}}\n{proj_items}"

    # ─── CERTIFICATIONS ───
    cert_tex = ""
    if data.get("certifications"):
        certs = "\n".join(f"  \\item {_escape(c)}" for c in data["certifications"])
        cert_tex = f"""
\\section{{Certifications}}
\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=2pt]
{certs}
\\end{{itemize}}
"""

    # ─── ACHIEVEMENTS ───
    ach_tex = ""
    if data.get("achievements"):
        achs = "\n".join(f"  \\item {_escape(a)}" for a in data["achievements"])
        ach_tex = f"""
\\section{{Achievements \\& Awards}}
\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=2pt]
{achs}
\\end{{itemize}}
"""

    # ─── PUBLICATIONS ───
    pub_tex = ""
    if data.get("publications"):
        pubs = "\n".join(f"  \\item {_escape(p)}" for p in data["publications"])
        pub_tex = f"""
\\section{{Publications \\& Research}}
\\begin{{itemize}}[leftmargin=*, itemsep=1pt, topsep=2pt]
{pubs}
\\end{{itemize}}
"""

    # ─── SECTION ORDER ───
    fresher_order  = [summary_tex, skills_tex, proj_tex, edu_tex, exp_tex, cert_tex, ach_tex, pub_tex]
    exp_order      = [summary_tex, exp_tex, skills_tex, proj_tex, cert_tex, edu_tex, ach_tex, pub_tex]
    section_order  = fresher_order if level in ("fresher","junior") else exp_order
    sections_combined = "\n".join(s for s in section_order if s.strip())

    # Executive design uses a dark header background
    header_tex = ""
    if design == "executive":
        header_tex = f"""
\\begin{{center}}
  \\colorbox{{dark}}{{\\parbox{{\\linewidth}}{{\\centering\\vspace{{8pt}}
    {{\\Huge\\bfseries\\color{{accent}} {name}}}\\\\[4pt]
    {{\\small\\color{{white}} {contact_line}}}
  \\vspace{{8pt}}}}}}
\\end{{center}}
"""
    else:
        header_tex = f"""
\\begin{{center}}
  {{\\Huge\\bfseries\\color{{dark}} {name}}}\\\\[4pt]
  {{\\small\\color{{gray}} {contact_line}}}
\\end{{center}}
\\vspace{{2pt}}
\\noindent\\color{{accent}}\\rule{{\\linewidth}}{{1.5pt}}
\\vspace{{2pt}}
"""

    # ─── FULL LATEX DOCUMENT ───
    latex_doc = f"""\\documentclass[a4paper,10pt]{{article}}
\\usepackage[top=1.2cm,bottom=1.2cm,left=1.5cm,right=1.5cm]{{geometry}}
\\usepackage[T1]{{fontenc}}
\\usepackage[utf8]{{inputenc}}
\\usepackage{{xcolor}}
\\usepackage{{titlesec}}
\\usepackage{{enumitem}}
\\usepackage{{tabularx}}
\\usepackage{{array}}
\\usepackage{{parskip}}
\\usepackage{{hyperref}}

\\definecolor{{accent}}{{HTML}}{{{accent}}}
\\definecolor{{dark}}{{HTML}}{{{dark}}}
\\definecolor{{gray}}{{HTML}}{{{gray}}}

\\titleformat{{\\section}}{{\\large\\bfseries\\color{{accent}}}}{{}}{{0em}}{{}}[\\color{{accent}}\\titlerule]
\\titlespacing{{\\section}}{{0pt}}{{8pt}}{{5pt}}

\\hypersetup{{colorlinks=true,urlcolor=accent,linkcolor=accent}}
\\pagestyle{{empty}}
\\setlength{{\\parskip}}{{2pt}}

\\begin{{document}}

{header_tex}

{sections_combined}

\\end{{document}}
"""

    # ─── COMPILE WITH PDFLATEX ───
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_doc)

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
            capture_output=True, timeout=30
        )

        if not os.path.exists(pdf_path):
            # Return error info for debugging
            raise RuntimeError(
                f"pdflatex failed:\n{result.stdout.decode()[-500:]}\n{result.stderr.decode()[-200:]}"
            )

        with open(pdf_path, "rb") as f:
            return f.read()


# Which designs use LaTeX vs WeasyPrint
LATEX_DESIGNS_SET = {"classic", "academic", "executive"}

def should_use_latex(design):
    return design in LATEX_DESIGNS_SET