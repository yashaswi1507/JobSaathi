import sys
sys.path.append(r'C:\CareerShieldAI\backend\app')

from interview_prep import generate_interview_kit
from career_recommender import recommend_careers, find_skill_gap
from resume_parser import extract_skills
import pandas as pd

# --- Load IT resume and extract skills ---
resume_df = pd.read_csv(r'C:\CareerShieldAI\datasets\resume_cleaned.csv')
it_resume = resume_df[resume_df['Category']=='INFORMATION-TECHNOLOGY']['Resume_str'].iloc[5]
skills = extract_skills(it_resume)
print("Skills found:", skills)

# --- Get top career recommendation and skill gap ---
recs = recommend_careers(skills, top_n=1)
top_role = recs[0]
gap = find_skill_gap(skills, top_role['required_skills'])

# --- Generate full interview kit ---
kit = generate_interview_kit(
    target_role=top_role['job_title'],
    resume_skills=skills,
    missing_skills=gap['missing_skills']
)

# --- Print roadmap ---
print("\nCAREER ROADMAP:")
for step in kit['roadmap']:
    print(f"  {step}")

# --- Print technical questions ---
print("\nTECHNICAL QUESTIONS:")
for q in kit['technical_questions']:
    print(f"  - {q}")

# --- Print HR questions ---
print("\nHR QUESTIONS:")
for q in kit['hr_questions']:
    print(f"  - {q}")

# --- Print project questions ---
print("\nPROJECT QUESTIONS:")
for q in kit['project_questions']:
    print(f"  - {q}")