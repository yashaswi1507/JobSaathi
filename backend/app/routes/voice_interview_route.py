"""
voice_interview_route.py
-------------------------
Voice Interview routes — add to backend/app/routes/

Endpoints:
  POST /interview/start     — Start session, get first question
  POST /interview/evaluate  — Submit answer, get AI feedback + next question
  POST /interview/end       — End session, get full report
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import random

router = APIRouter()

# ── Question bank ────────────────────────────────────────────
HR_QUESTIONS = [
    "Tell me about yourself and your background.",
    "Why are you interested in this role?",
    "What is your greatest strength and how have you used it?",
    "What is your biggest weakness and how are you working on it?",
    "Where do you see yourself in 5 years?",
    "Why should we hire you over other candidates?",
    "Describe a situation where you worked under pressure.",
    "Tell me about a time you worked in a team and faced a conflict.",
    "What motivates you to do your best work?",
    "How do you handle failure or setbacks?",
]

TECH_TEMPLATES = [
    "Explain how {} works and when you would use it.",
    "What are the key concepts behind {}?",
    "Describe a project where you used {}. What challenges did you face?",
    "How would you optimize a system that heavily uses {}?",
    "Compare {} with an alternative approach. When would you choose each?",
    "What are common mistakes developers make when working with {}?",
    "How do you test and debug code involving {}?",
    "Walk me through your thought process for implementing {} from scratch.",
]

BEHAVIORAL_QUESTIONS = [
    "Tell me about a time you had to learn a new technology quickly.",
    "Describe a situation where you disagreed with your team. How did you handle it?",
    "Give an example of a project you are most proud of and why.",
    "Tell me about a time you failed and what you learned from it.",
    "Describe how you prioritize tasks when you have multiple deadlines.",
    "Tell me about a time you went above and beyond for a project.",
    "How do you stay updated with the latest trends in your field?",
]


def _build_question_list(role: str, skills: list, mode: str) -> list:
    """Build ordered question list based on mode."""
    questions = []

    if mode == "hr":
        questions = random.sample(HR_QUESTIONS, min(7, len(HR_QUESTIONS)))

    elif mode == "technical":
        for skill in skills[:6]:
            q = random.choice(TECH_TEMPLATES).format(skill)
            questions.append(q)
        questions += random.sample(BEHAVIORAL_QUESTIONS, 2)

    elif mode == "mixed":
        questions.append(HR_QUESTIONS[0])  # Always start with "Tell me about yourself"
        for skill in skills[:4]:
            q = random.choice(TECH_TEMPLATES).format(skill)
            questions.append(q)
        questions += random.sample(BEHAVIORAL_QUESTIONS, 2)
        questions += random.sample(HR_QUESTIONS[1:], 2)

    return questions


def _evaluate_with_groq(question: str, answer: str, role: str, q_number: int, total: int) -> dict:
    """Use Groq to evaluate the answer and return structured feedback."""
    import os, json, re
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        system = (
            "You are an expert technical interviewer evaluating a candidate's answer. "
            "Be encouraging but honest. Give specific, actionable feedback. "
            "Respond ONLY with valid JSON, no markdown, no extra text."
        )

        prompt = f"""
Interview Question ({q_number}/{total}): {question}
Target Role: {role}
Candidate's Answer: {answer}

Evaluate this answer and respond with JSON:
{{
  "score": <integer 1-10>,
  "rating": "<Poor|Fair|Good|Excellent>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "improvements": ["<improvement 1>", "<improvement 2>"],
  "ideal_answer_hint": "<brief hint about what a great answer includes>",
  "follow_up": "<one natural follow-up question the interviewer might ask>"
}}
"""
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.4,
        )
        raw = response.choices[0].message.content.strip()
        clean = re.sub(r'```(?:json)?', '', raw).strip().rstrip('`').strip()
        return json.loads(clean)

    except Exception as e:
        # Fallback evaluation
        words = len(answer.split())
        score = min(10, max(3, words // 10))
        return {
            "score": score,
            "rating": "Good" if score >= 6 else "Fair",
            "strengths": ["You attempted to answer the question"],
            "improvements": ["Add more specific examples", "Quantify your achievements"],
            "ideal_answer_hint": "Use the STAR method: Situation, Task, Action, Result",
            "follow_up": "Can you elaborate on that with a specific example?",
        }


# ── Pydantic Models ──────────────────────────────────────────
class StartRequest(BaseModel):
    role: str
    skills: Optional[List[str]] = []
    mode: Optional[str] = "mixed"  # hr | technical | mixed


class EvaluateRequest(BaseModel):
    role: str
    question: str
    answer: str
    question_number: int
    total_questions: int
    all_questions: List[str]
    scores_so_far: Optional[List[int]] = []


class EndRequest(BaseModel):
    role: str
    mode: str
    questions: List[str]
    answers: List[str]
    scores: List[int]
    feedbacks: List[dict]


# ── Routes ───────────────────────────────────────────────────
@router.post("/start")
def start_interview(req: StartRequest):
    """
    Start a new interview session.
    Returns: first question + full question list
    """
    questions = _build_question_list(req.role, req.skills, req.mode)
    if not questions:
        questions = HR_QUESTIONS[:5]

    return {
        "session_started": True,
        "total_questions": len(questions),
        "current_question_number": 1,
        "current_question": questions[0],
        "all_questions": questions,
        "mode": req.mode,
        "role": req.role,
        "message": f"Interview started for {req.role}. {len(questions)} questions prepared.",
    }


@router.post("/evaluate")
def evaluate_answer(req: EvaluateRequest):
    """
    Evaluate user's answer to current question.
    Returns: feedback + next question (if any)
    """
    if not req.answer or len(req.answer.strip()) < 5:
        return {
            "error": "Answer too short",
            "feedback": {
                "score": 0,
                "rating": "No Answer",
                "strengths": [],
                "improvements": ["Please provide a detailed answer"],
                "ideal_answer_hint": "Try to speak for at least 30 seconds",
                "follow_up": req.question,
            },
            "is_last": False,
            "next_question": req.question,
            "next_question_number": req.question_number,
        }

    feedback = _evaluate_with_groq(
        question=req.question,
        answer=req.answer,
        role=req.role,
        q_number=req.question_number,
        total=req.total_questions,
    )

    is_last = req.question_number >= req.total_questions
    next_q  = None
    next_num = req.question_number + 1

    if not is_last and req.all_questions:
        idx = req.question_number  # 0-indexed next
        next_q = req.all_questions[idx] if idx < len(req.all_questions) else None

    scores = req.scores_so_far + [feedback["score"]]
    avg = sum(scores) / len(scores) if scores else 0

    return {
        "feedback": feedback,
        "is_last": is_last,
        "next_question": next_q,
        "next_question_number": next_num if not is_last else None,
        "progress": {
            "completed": req.question_number,
            "total": req.total_questions,
            "average_score_so_far": round(avg, 1),
            "percentage": round((req.question_number / req.total_questions) * 100),
        }
    }


@router.post("/end")
def end_interview(req: EndRequest):
    """
    End interview session and return full report.
    """
    scores = req.scores or []
    avg = sum(scores) / len(scores) if scores else 0

    # Grade
    if avg >= 8.5:   grade, emoji = "Outstanding", "🏆"
    elif avg >= 7.0: grade, emoji = "Excellent",   "⭐"
    elif avg >= 5.5: grade, emoji = "Good",        "👍"
    elif avg >= 4.0: grade, emoji = "Fair",        "📈"
    else:            grade, emoji = "Needs Work",  "💪"

    # Best and worst answers
    if scores:
        best_idx  = scores.index(max(scores))
        worst_idx = scores.index(min(scores))
    else:
        best_idx = worst_idx = 0

    # Overall tips
    all_improvements = []
    for fb in req.feedbacks:
        all_improvements.extend(fb.get("improvements", []))
    unique_tips = list(dict.fromkeys(all_improvements))[:5]

    return {
        "report": {
            "role": req.role,
            "mode": req.mode,
            "total_questions": len(req.questions),
            "answered": len(req.answers),
            "average_score": round(avg, 1),
            "grade": grade,
            "emoji": emoji,
            "scores": scores,
            "best_answer": {
                "question": req.questions[best_idx] if req.questions else "",
                "score": scores[best_idx] if scores else 0,
            },
            "needs_work": {
                "question": req.questions[worst_idx] if req.questions else "",
                "score": scores[worst_idx] if scores else 0,
            },
            "top_improvements": unique_tips,
            "recommendation": (
                "You are interview-ready! Apply confidently." if avg >= 7
                else "Practice more mock interviews and focus on STAR method answers." if avg >= 5
                else "Review fundamentals and practice answering out loud daily."
            ),
            "detailed_feedback": [
                {
                    "question_number": i + 1,
                    "question": req.questions[i] if i < len(req.questions) else "",
                    "answer": req.answers[i] if i < len(req.answers) else "",
                    "score": scores[i] if i < len(scores) else 0,
                    "feedback": req.feedbacks[i] if i < len(req.feedbacks) else {},
                }
                for i in range(len(req.questions))
            ],
        }
    }