import os
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from typing import Dict, Any, Optional

from app.models import (
    StartInterviewRequest, ChatRequest, FinishInterviewRequest
)
from app.interview_engine import DataRepository, InterviewEngine
from app.feedback_engine import FeedbackEngine

app = FastAPI(
    title="InterviewAI API",
    description="Adaptive Technical Interview Engine for the 31-Day Enterprise AI Cohort",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CURRICULUM_PATH = os.path.join(BASE_DIR, "data", "curriculum.json")
CANDIDATES_PATH = os.path.join(BASE_DIR, "data", "candidates.json")

repository = DataRepository(CURRICULUM_PATH, CANDIDATES_PATH)
engine = InterviewEngine(repository)

def to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    return obj

# --- REST API Endpoints ---

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "InterviewAI Agent API", "version": "1.0.0"}

@app.get("/api/curriculum")
def get_curriculum():
    return to_dict(repository.curriculum)

@app.get("/api/candidates")
def get_candidates():
    return [to_dict(c) for c in repository.candidates.values()]

@app.get("/api/candidates/{candidate_id}")
def get_candidate(candidate_id: str):
    cand = repository.get_candidate(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate '{candidate_id}' not found.")
    return to_dict(cand)

@app.post("/api/interview")
@app.post("/api/interview/start")
@app.post("/start_interview")
@app.post("/interview/start")
@app.post("/start")
async def start_interview(request_data: Dict[str, Any] = Body(...)):
    # Support direct chat turn submission if session_id and message are present
    if ("session_id" in request_data or "sessionId" in request_data) and ("message" in request_data or "answer" in request_data):
        return await interview_chat(request_data)

    cand_raw = request_data.get("candidate") or request_data.get("candidate_id") or request_data.get("candidateId") or request_data.get("id") or "CAND-001"
    if isinstance(cand_raw, dict):
        cand_id = cand_raw.get("member", {}).get("id") or cand_raw.get("id") or "CAND-001"
    else:
        cand_id = str(cand_raw)
    personality = request_data.get("personality") or "Senior Engineer"

    try:
        session = engine.start_session(cand_id, personality=personality)
        return {
            "session_id": session.session_id,
            "sessionId": session.session_id,
            "status": "in_progress",
            "reply": session.current_question,
            "message": session.current_question,
            "candidate": to_dict(session.candidate),
            "question_count": session.question_count,
            "covered_days": session.covered_days,
            "difficulty": session.difficulty,
            "done": False
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@app.post("/api/interview/chat")
@app.post("/chat")
@app.post("/interview/chat")
async def interview_chat(request_data: Dict[str, Any] = Body(...)):
    session_id = request_data.get("session_id") or request_data.get("sessionId")
    user_msg = request_data.get("message") or request_data.get("answer") or request_data.get("response") or ""

    if not session_id:
        raise HTTPException(status_code=400, detail="Missing required field 'session_id'.")

    try:
        session = engine.process_turn(session_id, user_msg)
        
        response_payload = {
            "session_id": session.session_id,
            "sessionId": session.session_id,
            "reply": session.current_question,
            "message": session.current_question,
            "is_complete": session.is_complete,
            "done": session.is_complete,
            "question_count": session.question_count,
            "covered_days": session.covered_days,
            "difficulty": session.difficulty,
            "turn_history_length": len(session.turns)
        }

        if session.is_complete:
            if not session.feedback:
                session.feedback = FeedbackEngine.generate_report(session)
            response_payload["feedback"] = to_dict(session.feedback)

        return response_payload
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@app.post("/api/interview/hint")
@app.post("/api/interview/model_answer")
def get_interview_hint(request_data: Dict[str, Any] = Body(...)):
    session_id = request_data.get("session_id") or request_data.get("sessionId")
    if not session_id or session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Valid active session_id required.")
    try:
        return engine.generate_hint_or_model_answer(session_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@app.get("/api/interview/session/{session_id}")
@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    session = engine.sessions[session_id]
    return to_dict(session)

@app.post("/api/interview/pause")
def pause_interview(request_data: Dict[str, Any] = Body(...)):
    session_id = request_data.get("session_id") or request_data.get("sessionId")
    if session_id in engine.sessions:
        engine.sessions[session_id].is_paused = True
        return {"status": "paused", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/interview/resume")
def resume_interview(request_data: Dict[str, Any] = Body(...)):
    session_id = request_data.get("session_id") or request_data.get("sessionId")
    if session_id in engine.sessions:
        engine.sessions[session_id].is_paused = False
        return {"status": "resumed", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/interview/finish")
@app.post("/finish")
@app.post("/interview/finish")
async def finish_interview(request_data: Dict[str, Any] = Body(...)):
    session_id = request_data.get("session_id") or request_data.get("sessionId")
    if not session_id or session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Valid session_id required.")

    session = engine.sessions[session_id]
    session.is_complete = True
    if not session.feedback:
        session.feedback = FeedbackEngine.generate_report(session)

    return {
        "session_id": session.session_id,
        "sessionId": session.session_id,
        "is_complete": True,
        "done": True,
        "reply": "Interview completed. Structured feedback report generated.",
        "feedback": to_dict(session.feedback)
    }

@app.get("/api/interview/export/markdown/{session_id}", response_class=PlainTextResponse)
def export_markdown_report(session_id: str):
    if session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = engine.sessions[session_id]
    if not session.feedback:
        session.feedback = FeedbackEngine.generate_report(session)
    fb = session.feedback

    md = f"""# InterviewAI Technical Assessment Report

**Candidate Name:** {fb.candidate_name}
**Candidate ID:** {fb.candidate_id}
**Job Role:** {fb.job_role}
**Overall Score:** {fb.overall_score}/100
**Technical Tier:** {fb.technical_tier}
**Hiring Recommendation:** {fb.hiring_recommendation} (Confidence: {fb.interview_confidence}%)
**Questions Answered:** {fb.questions_answered}
**Curriculum Days Covered:** {', '.join(map(str, fb.covered_days))}

---

## Category Performance
"""
    for cat in fb.category_scores:
        md += f"### {cat.category}: {cat.score}/100 ({cat.status})\n{cat.notes}\n\n"

    md += "## Key Strengths\n"
    for s in fb.strengths:
        md += f"- {s}\n"

    md += "\n## Areas for Growth (Gaps)\n"
    for g in fb.areas_for_growth:
        md += f"- {g}\n"

    md += "\n## Actionable Next Steps\n"
    for rec in fb.actionable_recommendations:
        md += f"- {rec}\n"

    if fb.architecture_diagram:
        md += f"\n## Recommended System Architecture\n```mermaid\n{fb.architecture_diagram}\n```\n"

    return md

@app.get("/api/interview/export/json/{session_id}")
def export_json_report(session_id: str):
    if session_id not in engine.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = engine.sessions[session_id]
    if not session.feedback:
        session.feedback = FeedbackEngine.generate_report(session)
    return to_dict(session.feedback)

@app.get("/PROMPTS.md", response_class=PlainTextResponse)
@app.get("/api/prompts", response_class=PlainTextResponse)
def serve_prompts():
    prompts_file = os.path.join(BASE_DIR, "PROMPTS.md")
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "PROMPTS.md not found"

STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")
if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "<h1>InterviewAI API is running! Access /docs for REST API OpenAPI specification.</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
