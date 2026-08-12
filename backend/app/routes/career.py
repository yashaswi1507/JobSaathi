from fastapi import APIRouter
from app.schemas import CareerRequest, InterviewRequest

router = APIRouter()

@router.post("/recommend")
def recommend(data: CareerRequest):
    from app.career_recommender import recommend_careers
    recommendations = recommend_careers(data.skills, top_n=5)
    return {"recommendations": recommendations}


@router.post("/skill-gap")
def skill_gap(data: CareerRequest):
    from app.career_recommender import recommend_careers, find_skill_gap, CAREER_DATA

    # If user provided a target_role, find that specific role's skills
    if data.target_role and data.target_role.strip():
        target_lower = data.target_role.lower().strip()

        # Find best matching role in dataset
        best_role = None
        best_score = 0
        for role in CAREER_DATA:
            title_words = set(role["job_title"].lower().split())
            query_words = set(target_lower.split())
            overlap = len(title_words & query_words)
            # Also check substring
            if target_lower in role["job_title"].lower() or role["job_title"].lower() in target_lower:
                overlap += 2
            if overlap > best_score:
                best_score = overlap
                best_role = role

        if best_role and best_score > 0:
            gap = find_skill_gap(data.skills, best_role["skills"])
            # Calculate match score
            resume_set = set(s.lower().strip() for s in data.skills)
            role_skills = set(best_role["skills"].split())
            matched = resume_set & role_skills
            match_score = round(len(matched) / max(len(role_skills), 1) * 100, 1)

            return {
                "target_role":    best_role["job_title"],
                "match_score":    match_score,
                "matched_skills": gap["matching_skills"],
                "missing_skills": gap["missing_skills"],
                "skill_gap":      gap,
                "roadmap":        _get_roadmap(best_role["skills"].split(), gap["missing_skills"]),
            }

    # Fallback — use top recommended role
    recommendations = recommend_careers(data.skills, top_n=1)
    if not recommendations:
        return {"error": "No career match found. Please provide your skills."}

    top_role = recommendations[0]
    gap = find_skill_gap(data.skills, top_role["required_skills"])

    return {
        "target_role":    top_role["job_title"],
        "match_score":    top_role["match_score"],
        "matched_skills": gap["matching_skills"],
        "missing_skills": gap["missing_skills"],
        "skill_gap":      gap,
        "roadmap":        _get_roadmap(top_role["required_skills"].split(), gap["missing_skills"]),
    }


def _get_roadmap(all_skills: list, missing_skills: list) -> list:
    """Generate simple learning roadmap for missing skills."""
    if not missing_skills:
        return ["You already have most required skills!", "Focus on building projects", "Apply for roles now!"]
    steps = []
    for i, skill in enumerate(missing_skills[:5]):
        steps.append(f"{i+1}. Learn {skill} — practice with hands-on projects")
    steps.append(f"{len(steps)+1}. Build portfolio projects using these skills")
    steps.append(f"{len(steps)+1}. Apply to entry-level positions")
    return steps


@router.post("/interview-kit")
def interview_kit(data: InterviewRequest):
    from app.interview_prep import generate_interview_kit
    kit = generate_interview_kit(
        target_role=data.target_role,
        resume_skills=data.skills,
        missing_skills=data.missing_skills
    )
    return kit
