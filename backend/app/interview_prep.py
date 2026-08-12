import random

# Built-in learning resources — no JSON file needed
LEARNING_RESOURCES = {
    "python":          {"youtube":"https://youtu.be/eWRfhZUzrAc", "course":"https://www.coursera.org/learn/python", "book":"Python Crash Course by Eric Matthes"},
    "machine learning":{"youtube":"https://youtu.be/aircAruvnKk", "course":"https://www.coursera.org/learn/machine-learning", "book":"Hands-On ML by Aurélien Géron"},
    "deep learning":   {"youtube":"https://youtu.be/CS4cs9xVecg", "course":"https://www.deeplearning.ai/", "book":"Deep Learning by Goodfellow"},
    "tensorflow":      {"youtube":"https://youtu.be/tPYj3fFJGjk", "course":"https://www.coursera.org/specializations/tensorflow-in-practice", "book":"Learning TensorFlow by Tom Hope"},
    "pytorch":         {"youtube":"https://youtu.be/Z_ikDlimN6A", "course":"https://pytorch.org/tutorials/", "book":"Programming PyTorch by Ian Pointer"},
    "nlp":             {"youtube":"https://youtu.be/8rXD5-xhemo", "course":"https://www.coursera.org/specializations/natural-language-processing", "book":"NLP with Python by Bird & Klein"},
    "sql":             {"youtube":"https://youtu.be/HXV3zeQKqGY", "course":"https://www.khanacademy.org/computing/computer-programming/sql", "book":"Learning SQL by Alan Beaulieu"},
    "react":           {"youtube":"https://youtu.be/bMknfKXIFA8", "course":"https://www.udemy.com/course/react-the-complete-guide-incl-redux/", "book":"Learning React by Alex Banks"},
    "nodejs":          {"youtube":"https://youtu.be/fBNz5xF-Kx4", "course":"https://www.udemy.com/course/the-complete-nodejs-developer-course-2/", "book":"Node.js Design Patterns by Casciaro"},
    "docker":          {"youtube":"https://youtu.be/fqMOX6JJhGo", "course":"https://www.udemy.com/course/docker-mastery/", "book":"Docker Deep Dive by Nigel Poulton"},
    "kubernetes":      {"youtube":"https://youtu.be/X48VuDVv0do", "course":"https://www.udemy.com/course/certified-kubernetes-administrator-with-practice-tests/", "book":"Kubernetes in Action by Luksa"},
    "aws":             {"youtube":"https://youtu.be/3hLmDS179YE", "course":"https://aws.amazon.com/training/", "book":"AWS Certified Solutions Architect Study Guide"},
    "java":            {"youtube":"https://youtu.be/eIrMbAQSU34", "course":"https://www.coursera.org/specializations/java-programming", "book":"Effective Java by Joshua Bloch"},
    "javascript":      {"youtube":"https://youtu.be/W6NZfCO5SIk", "course":"https://javascript.info/", "book":"You Don't Know JS by Kyle Simpson"},
    "data analysis":   {"youtube":"https://youtu.be/r-uOLxNrNk8", "course":"https://www.coursera.org/professional-certificates/google-data-analytics", "book":"Python for Data Analysis by Wes McKinney"},
    "fastapi":         {"youtube":"https://youtu.be/0sOvCWFmrtA", "course":"https://fastapi.tiangolo.com/tutorial/", "book":"Building Data Science Applications with FastAPI"},
    "git":             {"youtube":"https://youtu.be/RGOj5yH7evk", "course":"https://www.atlassian.com/git/tutorials", "book":"Pro Git by Scott Chacon"},
    "statistics":      {"youtube":"https://youtu.be/xxpc-HPKN28", "course":"https://www.coursera.org/learn/basic-statistics", "book":"Statistics by Freedman, Pisani & Purves"},
}

def get_resources_for_skill(skill):
    skill_lower = skill.lower().strip()
    if skill_lower in LEARNING_RESOURCES:
        return LEARNING_RESOURCES[skill_lower]
    # Generic fallback
    q = skill.replace(' ', '+')
    return {
        "youtube": f"https://www.youtube.com/results?search_query={q}+tutorial",
        "course":  f"https://www.coursera.org/search?query={q}",
        "book":    f"Search '{skill}' on Amazon Books"
    }

def generate_roadmap(current_skills, missing_skills, target_role):
    if not missing_skills:
        return ["You already have all skills needed for this role!"]
    roadmap = [f"Your goal: Become a {target_role}"]
    for i in range(0, len(missing_skills), 2):
        step_num = (i // 2) + 1
        skills_in_step = missing_skills[i:i+2]
        roadmap.append(f"Step {step_num}: Learn {' and '.join(skills_in_step)}")
        for skill in skills_in_step:
            res = get_resources_for_skill(skill)
            roadmap.append(f"  → YouTube: {res['youtube']}")
            roadmap.append(f"  → Course:  {res['course']}")
            roadmap.append(f"  → Book:    {res['book']}")
    roadmap.append("Final Step: Build 2-3 projects using all learned skills")
    roadmap.append("Apply for jobs and keep iterating!")
    return roadmap

def generate_technical_questions(target_role, skills):
    templates = [
        "Explain how you would use {} in a real project.",
        "What are the key concepts in {}?",
        "How does {} work and when would you use it?",
        "What is your experience with {}?",
        "Describe a challenge you faced while working with {}.",
    ]
    return [random.choice(templates).format(skill) for skill in skills[:8]]

def generate_hr_questions():
    return [
        "Tell me about yourself.",
        "Why do you want to work in this role?",
        "Where do you see yourself in 5 years?",
        "What is your greatest strength and weakness?",
        "Describe a situation where you worked in a team.",
        "How do you handle pressure and tight deadlines?",
        "Why should we hire you over other candidates?",
    ]

def generate_project_questions(skills):
    templates = [
        "Walk me through a project where you used {}.",
        "What was the most challenging project involving {}?",
        "How did you implement {} in one of your projects?",
    ]
    return [random.choice(templates).format(skill) for skill in skills[:5]]

def generate_interview_kit(target_role, resume_skills, missing_skills):
    return {
        "roadmap":             generate_roadmap(resume_skills, missing_skills, target_role),
        "technical_questions": generate_technical_questions(target_role, resume_skills),
        "hr_questions":        generate_hr_questions(),
        "project_questions":   generate_project_questions(resume_skills),
        "learning_resources":  {skill: get_resources_for_skill(skill) for skill in missing_skills},
    }

print("Interview prep loaded successfully.")
