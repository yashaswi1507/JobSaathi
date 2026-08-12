import sys
sys.path.append(r'C:\CareerShieldAI\backend\app')

from interview_prep import generate_interview_kit
from career_recommender import recommend_careers, find_skill_gap
from resume_parser import extract_skills
import pandas as pd

# --- Load Healthcare resume ---
resume_df = pd.read_csv(r'C:\CareerShieldAI\datasets\resume_cleaned.csv')
healthcare_resume = resume_df[resume_df['Category']=='HEALTHCARE']['Resume_str'].iloc[0]
skills = extract_skills(healthcare_resume)
print("Healthcare Skills Found:", skills)

# --- Get recommendation and skill gap ---
recs = recommend_careers(skills, top_n=3)
top_role = recs[0]
gap = find_skill_gap(skills, top_role['required_skills'])

# --- Generate interview kit ---
kit = generate_interview_kit(
    target_role=top_role['job_title'],
    resume_skills=skills,
    missing_skills=gap['missing_skills']
)

print(f"\nTop 3 Recommendations:")
for i, rec in enumerate(recs, 1):
    print(f"  {i}. {rec['job_title']} ({rec['match_score']}%)")

print(f"\nSkill Gap for: {top_role['job_title']}")
print(f"  Have:    {gap['matching_skills']}")
print(f"  Missing: {gap['missing_skills']}")

print("\nCAREER ROADMAP:")
for step in kit['roadmap']:
    print(f"  {step}")

print("\nTECHNICAL QUESTIONS:")
for q in kit['technical_questions']:
    print(f"  - {q}")

print("\nPROJECT QUESTIONS:")
for q in kit['project_questions']:
    print(f"  - {q}")

print("\n" + "="*60)

# --- Test 2: Manual skill set ---
print("\nTest 2 — Manual Skill Set (Python, ML, SQL, AWS, Docker)")
manual_skills = ['python', 'machine learning', 'sql', 'aws', 'docker']

recs2 = recommend_careers(manual_skills, top_n=3)
top_role2 = recs2[0]
gap2 = find_skill_gap(manual_skills, top_role2['required_skills'])

kit2 = generate_interview_kit(
    target_role=top_role2['job_title'],
    resume_skills=manual_skills,
    missing_skills=gap2['missing_skills']
)

print(f"\nTop 3 Recommendations:")
for i, rec in enumerate(recs2, 1):
    print(f"  {i}. {rec['job_title']} ({rec['match_score']}%)")

print(f"\nSkill Gap for: {top_role2['job_title']}")
print(f"  Have:    {gap2['matching_skills']}")
print(f"  Missing: {gap2['missing_skills']}")

print("\nCAREER ROADMAP:")
for step in kit2['roadmap']:
    print(f"  {step}")

print("\nTECHNICAL QUESTIONS:")
for q in kit2['technical_questions']:
    print(f"  - {q}")

print("\nPROJECT QUESTIONS:")
for q in kit2['project_questions']:
    print(f"  - {q}")