"""
llm_service.py
--------------
Groq API wrapper for all LLM-based features in CareerShieldAI.
Handles: AI Rewrite, Bullet Improvement, Cover Letter, Email,
LinkedIn Message, LinkedIn Profile improvement, RAG Career Assistant.

WHERE TO PUT THIS FILE:
  C:\\CareerShieldAI\\backend\\app\\llm_service.py

SETUP:
  1. Create C:\\CareerShieldAI\\backend\\.env file:
       GROQ_API_KEY=gsk_your_key_here
  2. pip install groq python-dotenv
"""

import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.1-8b-instant"  # Fast model — ~500 tokens/sec   # free, fast, good quality


def _call_groq(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str:
    """
    Core Groq API call. Returns the model's response text.
    Returns an error string (never raises) so endpoints don't crash.
    """
    if not GROQ_API_KEY:
        return "ERROR: GROQ_API_KEY not set in .env file."
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"


# ============================================================
# 1. AI Resume Rewrite
# ============================================================
def ai_rewrite_resume(resume_text: str, target_role: str = "") -> dict:
    """
    Rewrites an entire resume to be more impactful — stronger action
    verbs, quantified achievements, cleaner structure.
    """
    role_hint = f" targeting the role of {target_role}" if target_role else ""
    system = (
        "You are an expert resume writer. Rewrite the given resume to be "
        "more impactful, using strong action verbs, quantified achievements, "
        "and ATS-friendly language. Keep all real information — do not invent "
        "facts. Return only the improved resume text, no commentary."
    )
    user = f"Rewrite this resume{role_hint}:\n\n{resume_text}"
    result = _call_groq(system, user, max_tokens=600)
    return {"rewritten_resume": result, "target_role": target_role}


# ============================================================
# 2. Resume Bullet Improvement
# ============================================================
def improve_bullets(bullet_points: list[str], role: str = "") -> dict:
    """
    Takes a list of resume bullet points and returns improved versions
    with stronger action verbs and quantified outcomes where possible.
    """
    bullets_text = "\n".join(f"- {b}" for b in bullet_points)
    role_hint = f" for a {role} role" if role else ""
    system = (
        "You are an expert resume coach. Improve each bullet point to start "
        "with a strong action verb and include quantified results where "
        "possible. Return ONLY the improved bullets, one per line, starting "
        "with a dash. Do not add commentary."
    )
    user = f"Improve these resume bullets{role_hint}:\n{bullets_text}"
    result = _call_groq(system, user, max_tokens=800)
    improved = [
        line.lstrip("- ").strip()
        for line in result.split("\n")
        if line.strip().startswith("-")
    ]
    return {
        "original_bullets": bullet_points,
        "improved_bullets": improved if improved else [result],
    }


# ============================================================
# 3. Cover Letter Generator
# ============================================================
def generate_cover_letter(resume_text: str, job_description: str,
                           company_name: str = "", applicant_name: str = "") -> dict:
    """
    Generates a tailored cover letter based on resume + job description.
    """
    system = (
        "You are an expert cover letter writer. Write a professional, "
        "concise cover letter (3-4 paragraphs) that highlights how the "
        "candidate's experience matches the job requirements. Sound genuine "
        "and enthusiastic. Do not use clichés like 'I am writing to apply'."
    )
    user = (
        f"Write a cover letter for {applicant_name or 'the candidate'} "
        f"applying to {company_name or 'the company'}.\n\n"
        f"RESUME:\n{resume_text[:2000]}\n\n"
        f"JOB DESCRIPTION:\n{job_description[:1500]}"
    )
    result = _call_groq(system, user, max_tokens=800)
    return {
        "cover_letter": result,
        "company_name": company_name,
        "applicant_name": applicant_name,
    }


# ============================================================
# 4. Professional Email Generator
# ============================================================
def generate_email(resume_text: str, job_description: str,
                   email_type: str = "application",
                   recipient_name: str = "", sender_name: str = "") -> dict:
    """
    Generates a professional email.
    email_type options: 'application', 'follow_up', 'networking', 'thank_you'
    """
    type_prompts = {
        "application":  "a job application email",
        "follow_up":    "a polite follow-up email after applying",
        "networking":   "a networking email to connect with a recruiter",
        "thank_you":    "a thank-you email after an interview",
    }
    email_desc = type_prompts.get(email_type, "a professional email")
    system = (
        f"You are an expert at writing professional emails. Write {email_desc}. "
        "Keep it concise (150-200 words), professional, and personalized. "
        "Include Subject line, greeting, body, and sign-off."
    )
    user = (
        f"Sender: {sender_name or 'the candidate'}\n"
        f"Recipient: {recipient_name or 'Hiring Manager'}\n\n"
        f"RESUME SUMMARY:\n{resume_text[:1000]}\n\n"
        f"JOB/CONTEXT:\n{job_description[:800]}"
    )
    result = _call_groq(system, user, max_tokens=400)
    return {"email": result, "email_type": email_type}


# ============================================================
# 5. LinkedIn Message Generator
# ============================================================
def generate_linkedin_message(resume_text: str, recipient_role: str = "",
                               purpose: str = "networking") -> dict:
    """
    Generates a short LinkedIn connection/message FROM the candidate
    TO a recruiter/hiring manager/professional.
    purpose options: 'networking', 'job_inquiry', 'mentorship'
    """
    purpose_context = {
        "networking":    "connect professionally and expand their network",
        "job_inquiry":   "inquire about job opportunities at their company",
        "mentorship":    "seek career advice or mentorship",
        "referral":      "request a referral for a job opening",
        "follow_up":     "follow up after an interview or previous conversation",
        "collaboration": "explore potential project collaboration opportunities",
    }
    goal = purpose_context.get(purpose, "connect professionally")

    system = (
        "You are an expert at LinkedIn outreach. Write a short, personalized "
        "LinkedIn message FROM a job seeker TO a recruiter or professional. "
        "The message should sound genuine and human — not salesy or template-like. "
        "Keep connection requests under 300 characters. InMail under 150 words. "
        "Write from the candidate's first-person perspective ('I', 'my', 'me')."
    )
    user = (
        f"Write a LinkedIn {purpose} message from the candidate "
        f"TO a {recipient_role or 'recruiter/hiring manager'}, "
        f"with the goal to {goal}.\n\n"
        f"Candidate's background:\n{resume_text[:800]}"
    )
    result = _call_groq(system, user, max_tokens=300)
    return {"linkedin_message": result, "purpose": purpose}


# ============================================================
# 6. LinkedIn Profile Improvement
# ============================================================
def suggest_template_with_groq(
    resume_text: str,
    job_description: str,
    detected_level: str,
    detected_domain: str,
    ats_score: float,
    breakdown: dict = None,
) -> dict:
    """
    Uses Groq to intelligently suggest the best resume template
    based on resume content, JD, level, domain, and ATS score.

    Returns:
    {
      "template_id": "skillbars",
      "template_name": "Skill Bars",
      "reasoning": "Your resume is projects-heavy...",
      "key_improvements": ["Add quantified achievements", ...],
      "confidence": "high"
    }
    """
    import json, re

    TEMPLATES_DESC = """
Available templates:
1. jakescv — Clean single column, max ATS (score 10/10), best for: all levels, software/finance/devops
2. altacv — Two column with skill tags (ATS 7/10), best for: fresher/junior/mid, aiml/data_science/product
3. moderncv — Timeline sidebar shows career growth (ATS 7/10), best for: mid/senior, software/hr/product
4. awesomecv — Bold colored sections (ATS 6/10), best for: junior/mid, marketing/design/sales
5. deedycv — Dark sidebar = authority (ATS 6/10), best for: senior/lead, software/aiml/devops
6. elegant — Formal double-rule sections (ATS 8/10), best for: mid/senior/lead, finance/hr/business_analyst
7. skillbars — Visual skill progress bars (ATS 5/10), best for: fresher/junior, aiml/data_science/design
"""

    breakdown_text = ""
    if breakdown:
        missing = breakdown.get("skills", {}).get("missing", [])
        sections = breakdown.get("structure", {}).get("missing", [])
        verbs = breakdown.get("action_verbs", {}).get("points_earned", 0)
        quant = breakdown.get("quantification", {}).get("count", 0)
        breakdown_text = f"""
ATS Breakdown:
- Missing skills: {', '.join(missing[:5]) if missing else 'none'}
- Missing sections: {', '.join(sections) if sections else 'none'}
- Action verbs score: {verbs}/10
- Quantified achievements: {quant} found
"""

    system = (
        "You are an expert resume consultant. Based on the candidate's resume, "
        "job description, career level, domain, and ATS score, suggest the single "
        "best resume template from the given list. "
        "Respond ONLY with valid JSON, no explanation outside JSON, no markdown."
    )

    user = f"""
Candidate Info:
- Detected Level: {detected_level}
- Detected Domain: {detected_domain}
- Current ATS Score: {ats_score:.0f}%
- Resume summary (first 500 chars): {resume_text[:500]}
- Job Description (first 300 chars): {job_description[:300]}
{breakdown_text}

{TEMPLATES_DESC}

Pick the single best template. Return JSON:
{{
  "template_id": "one of: jakescv/altacv/moderncv/awesomecv/deedycv/elegant/skillbars",
  "template_name": "display name",
  "reasoning": "2-3 sentences explaining why this template suits this candidate",
  "key_improvements": ["improvement 1", "improvement 2", "improvement 3"],
  "confidence": "high/medium/low"
}}
"""

    result = _call_groq(system, user, max_tokens=400)

    try:
        # Clean markdown fences
        clean = re.sub(r'```(?:json)?', '', result).strip().rstrip('`').strip()
        parsed = json.loads(clean)
        # Validate template_id
        valid_ids = ["jakescv","altacv","moderncv","awesomecv","deedycv","elegant","skillbars"]
        if parsed.get("template_id") not in valid_ids:
            parsed["template_id"] = "jakescv"
        return parsed
    except Exception:
        # Fallback to rule-based
        return {
            "template_id": "jakescv" if ats_score < 60 else "altacv",
            "template_name": "Jake's Resume" if ats_score < 60 else "AltaCV",
            "reasoning": f"Based on your {detected_level} level and {ats_score:.0f}% ATS score, this template offers the best balance.",
            "key_improvements": ["Add more quantified achievements", "Include missing sections", "Add action verbs"],
            "confidence": "medium",
        }


def improve_linkedin_profile(current_headline: str = "",
                              current_about: str = "",
                              skills: list[str] = None,
                              target_role: str = "") -> dict:
    """
    Suggests improvements for LinkedIn headline, about section, and skills.
    Returns plain text suggestions, not JSON.
    """
    skills_text = ", ".join(skills or [])
    system = (
        "You are a LinkedIn optimization expert. Given the current profile "
        "details, provide clear improvement suggestions in plain text. "
        "Structure your response with these sections:\n"
        "1) BETTER HEADLINE: (write an improved headline under 220 chars)\n"
        "2) BETTER ABOUT: (write an improved About section, 3-4 sentences)\n"
        "3) MISSING SKILLS: (list 3-5 skills they should add)\n"
        "4) QUICK TIPS: (3 specific actionable tips)\n\n"
        "Write in plain text only — no JSON, no markdown code blocks, no asterisks."
    )
    user = (
        f"Target role: {target_role or 'not specified'}\n"
        f"Current headline: {current_headline or 'not provided'}\n"
        f"Current about: {current_about[:500] if current_about else 'not provided'}\n"
        f"Current skills: {skills_text or 'not provided'}\n\n"
        "Please provide improvement suggestions."
    )
    result = _call_groq(system, user, max_tokens=800)

    # Clean response — remove JSON blocks, markdown, code fences
    import re as _re
    clean = result
    # Remove ```json ... ``` blocks
    clean = _re.sub(r'```(?:json)?(.*?)```', r'\1', clean, flags=_re.DOTALL)
    # Remove { } JSON objects if response starts with {
    if clean.strip().startswith('{'):
        # Try to extract readable text from JSON
        clean = _re.sub(r'[{}\[\]"\\]', '', clean)
        clean = _re.sub(r':\s*', ': ', clean)
    # Remove ** markdown bold
    clean = _re.sub(r'\*\*(.*?)\*\*', r'\1', clean)
    # Remove * markdown italic
    clean = _re.sub(r'\*(.*?)\*', r'\1', clean)
    # Clean up extra whitespace
    clean = _re.sub(r'\n{3,}', '\n\n', clean).strip()

    return {"improvements": clean, "target_role": target_role}



# ============================================================
# 8. Resume Builder — Raw text to structured JSON (Option B)
# ============================================================
def parse_raw_resume_to_json(raw_text: str, domain: str = "software",
                              level: str = "fresher") -> dict:
    """
    Takes raw unstructured resume text (or basic info) and converts
    it to structured JSON ready for build_resume_pdf().
    """
    system = (
        "You are a resume parsing expert. Convert the given raw resume "
        "text or basic info into a structured JSON object. "
        "Return ONLY valid JSON, no markdown, no explanation. "
        "JSON keys must be exactly: name, email, phone, location, "
        "linkedin, github, summary, experience (list of {title, company, "
        "duration, bullets[]}), education (list of {degree, institution, "
        "year, gpa}), skills (list of strings), projects (list of "
        "{name, description, tech, metrics}), certifications (list), "
        "achievements (list). Use empty string or empty list if info "
        "is not available. Do not invent information."
    )
    user = (
        f"Domain: {domain}, Level: {level}\n\n"
        f"Raw resume info:\n{raw_text}"
    )
    result = _call_groq(system, user, max_tokens=600)

    # Parse JSON safely
    import json, re
    try:
        # Strip markdown code blocks if present
        clean = re.sub(r'```(?:json)?', '', result).strip()
        return json.loads(clean)
    except Exception:
        return {"error": "Could not parse resume", "raw_llm_output": result}


# ============================================================
# 9. Resume Builder — Improve content with LLM (Option A)
# ============================================================
def improve_resume_content(data: dict, domain: str = "software",
                            level: str = "fresher") -> dict:
    """
    Takes structured resume data and improves content using Groq.
    Returns updated data dict. If Groq fails for any reason,
    returns original data unchanged — never corrupts input.
    """
    import json, re, copy

    # Always work on a deep copy — never mutate original on failure
    data = copy.deepcopy(data)

    # Improve summary first (small, reliable)
    if data.get("summary"):
        sum_system = (
            f"You are an expert resume writer for {domain} domain, {level} level. "
            "Rewrite the given summary/objective to be more compelling and impactful. "
            "Return ONLY the improved text, no quotes, no explanation, max 3 sentences."
        )
        improved_summary = _call_groq(sum_system, data["summary"], max_tokens=200)
        if improved_summary and not improved_summary.startswith("ERROR"):
            data["summary"] = improved_summary

    # Improve experience bullets (one job at a time to avoid truncation)
    for i, exp in enumerate(data.get("experience", [])):
        if not exp.get("bullets"):
            continue
        bullets_text = "\n".join(f"- {b}" for b in exp["bullets"])
        sys_prompt = (
            "You are an expert resume writer. Improve these resume bullet points: "
            "start each with a strong action verb, quantify results where possible. "
            "Return ONLY the improved bullets, one per line, starting with '-'. "
            "Keep the same number of bullets. No explanation."
        )
        result = _call_groq(sys_prompt, bullets_text, max_tokens=400)
        if result and not result.startswith("ERROR"):
            new_bullets = [
                line.lstrip("- ").strip()
                for line in result.split("\n")
                if line.strip() and line.strip().startswith("-")
            ]
            if len(new_bullets) > 0:
                data["experience"][i]["bullets"] = new_bullets

    # Improve project descriptions
    for i, proj in enumerate(data.get("projects", [])):
        if not proj.get("description"):
            continue
        sys_prompt = (
            "You are an expert resume writer. Improve this project description "
            "to be more impactful — focus on what was built, how, and the result. "
            "Return ONLY the improved description, 1-2 sentences max."
        )
        result = _call_groq(sys_prompt, proj["description"], max_tokens=150)
        if result and not result.startswith("ERROR"):
            data["projects"][i]["description"] = result

    data["_llm_improved"] = True
    return data
def career_chat(user_message: str, resume_text: str = "",
                conversation_history: list[dict] = None) -> dict:
    """
    Career guidance chatbot. Uses resume context + conversation history
    for personalized, multi-turn guidance.

    conversation_history format:
      [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    if not GROQ_API_KEY:
        return {"reply": "ERROR: GROQ_API_KEY not set.", "role": "assistant"}

    system = (
        "You are CareerShield AI's career advisor — an expert in Indian and "
        "global job markets, resume writing, interview preparation, and career "
        "growth. Give specific, actionable advice. Be warm but direct. "
        "If the user has shared their resume, use it to personalize your advice."
        + (f"\n\nUser's resume:\n{resume_text[:1500]}" if resume_text else "")
    )

    messages = [{"role": "system", "content": system}]
    if conversation_history:
        messages.extend(conversation_history[-6:])  # last 3 turns
    messages.append({"role": "user", "content": user_message})

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=600,
        )
        reply = response.choices[0].message.content.strip()
        return {"reply": reply, "role": "assistant"}
    except Exception as e:
        return {"reply": f"ERROR: {str(e)}", "role": "assistant"}