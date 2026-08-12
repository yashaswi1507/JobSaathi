from fastapi import APIRouter
from app.rag_system import search_knowledge_base
from app.llm_service import career_chat

router = APIRouter()

# --- RAG Career Chat endpoint ---
@router.post("/chat")
def rag_chat(data: dict):
    question = data.get("question", "")              # user question
    if not question.strip():
        return {"error": "Please provide a question"}

    # Step 1: Search knowledge base for relevant documents
    relevant_docs = search_knowledge_base(question, top_k=3)

    # Step 2: Build context from retrieved documents
    context = "\n\n".join([
        f"[{doc['title']}]\n{doc['content']}"
        for doc in relevant_docs
    ])

    # Step 3: Build prompt for Groq LLM
    prompt = f"""You are CareerShield AI, a career guidance assistant.
Use ONLY the following information to answer the question.
Do not make up information not present in the context.

CONTEXT:
{context}

QUESTION: {question}

Provide a helpful, structured answer based on the context above."""

    # Step 4: Get response from Groq
    try:
        result = career_chat(user_message=prompt)
        answer = result.get("response", result.get("message", str(result)))
    except Exception as e:
        answer = f"Could not generate response: {str(e)}"

    return {
        "question":      question,
        "answer":        answer,
        "reply":         answer,   # alias for frontend compatibility
        "sources":       [doc['title'] for doc in relevant_docs],
        "retrieved_docs": len(relevant_docs)
    }

# --- RAG Interview Questions endpoint ---
@router.post("/interview-questions")
def get_interview_questions(data: dict):
    role    = data.get("role", "")                   # target role
    company = data.get("company", "")                # company name
    topic   = data.get("topic", "")                  # DSA, ML, HR etc

    # Build search query
    query = f"{company} {role} {topic} interview questions".strip()

    # Search knowledge base
    relevant_docs = search_knowledge_base(query, top_k=3)

    # Build context
    context = "\n\n".join([
        f"[{doc['title']}]\n{doc['content']}"
        for doc in relevant_docs
    ])

    # Build prompt
    prompt = f"""You are CareerShield AI interview preparation assistant.
Based on the following information, generate 10 specific interview questions
for a {role} role {f'at {company}' if company else ''} {f'focusing on {topic}' if topic else ''}.

CONTEXT:
{context}

Generate questions in this format:
1. [Question]
2. [Question]
...

Include a mix of technical and behavioral questions."""

    try:
        result = career_chat(user_message=prompt)
        answer = result.get("response", result.get("message", str(result)))
    except Exception as e:
        answer = f"Could not generate questions: {str(e)}"

    return {
        "role":      role,
        "company":   company,
        "topic":     topic,
        "questions": answer,
        "sources":   [doc['title'] for doc in relevant_docs]
    }

# --- Search knowledge base directly ---
@router.get("/search")
def search_kb(query: str = ""):
    if not query.strip():
        return {"error": "Please provide a search query"}

    results = search_knowledge_base(query, top_k=5)
    return {
        "query":   query,
        "results": results
    }

# --- Direct Interview Questions JSON endpoint ---
@router.post("/interview-questions-json")
def get_interview_questions_json(data: dict):
    import json, re
    from app.llm_service import _call_groq

    role     = data.get("role", "Software Engineer")
    tab_type = data.get("type", "Technical")
    count    = min(data.get("count", 5), 5)

    system = "You are an interview coach. Return ONLY valid JSON arrays. No explanation, no markdown."
    user   = f"Generate {count} {tab_type} interview Q&A for {role}. Return ONLY: [{{\"q\":\"question\",\"a\":\"answer\",\"tag\":\"topic\",\"pct\":80}}]"

    def parse_json(text):
        clean = re.sub(r"```[a-z]*|```", "", text).strip()
        s, e  = clean.find("["), clean.rfind("]") + 1
        if s >= 0 and e > s:
            try:
                return json.loads(clean[s:e])
            except Exception:
                pass
        return None

    try:
        raw       = _call_groq(system, user, max_tokens=800)
        questions = parse_json(raw)
        if not questions:
            # Retry with stricter prompt
            user2     = f"JSON array only for {role} {tab_type} interview: [{{\"q\":\"q\",\"a\":\"a\",\"tag\":\"t\",\"pct\":80}}]"
            raw2      = _call_groq("Output valid JSON array only.", user2, max_tokens=600)
            questions = parse_json(raw2)
        if questions and len(questions) > 0:
            return {"success": True, "questions": questions}
        return {"success": False, "error": "No JSON found", "raw": raw[:200]}
    except Exception as ex:
        return {"success": False, "error": str(ex)}
