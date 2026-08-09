from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CandidateMember(BaseModel):
    id: str
    name: str
    jobRole: str
    yearsExperience: int
    education: str
    status: str

class CandidateMission(BaseModel):
    day: int
    title: str
    passed: Optional[bool] = None
    skipped: Optional[bool] = None
    attempts: Optional[int] = 1

class CandidateSignals(BaseModel):
    commitDays: int
    missionsCompleted: int
    missionsFirstTry: int

class CandidateProfile(BaseModel):
    member: CandidateMember
    missions: List[CandidateMission]
    signals: CandidateSignals

class CurriculumDay(BaseModel):
    day: int
    title: str
    type: str
    tools: List[str]
    objectives: List[str]

class CurriculumModule(BaseModel):
    n: int
    title: str
    days: List[int]

class CurriculumData(BaseModel):
    cohort: str
    modules: List[CurriculumModule]
    days: List[CurriculumDay]

class EvaluationMetrics(BaseModel):
    technical_knowledge: float = 7.5 # 0-10
    communication: float = 8.0 # 0-10
    reasoning: float = 7.5 # 0-10
    problem_solving: float = 7.0 # 0-10
    architecture_thinking: float = 7.5 # 0-10
    confidence: float = 8.0 # 0-10

class TurnRecord(BaseModel):
    turn_index: int
    day: int
    topic_title: str
    question: str
    candidate_answer: Optional[str] = None
    evaluation_score: Optional[float] = None # 0.0 - 100.0
    evaluation_notes: Optional[str] = None
    metrics: Optional[EvaluationMetrics] = None
    is_follow_up: bool = False
    parent_turn_index: Optional[int] = None
    difficulty: str = "Medium" # Easy, Medium, Hard, Expert

class FeedbackCategoryScore(BaseModel):
    category: str
    score: float
    status: str # "EXCELLENT", "GOOD", "NEEDS_IMPROVEMENT"
    notes: str

class FeedbackReport(BaseModel):
    session_id: str
    candidate_id: str
    candidate_name: str
    job_role: str
    summary: str
    strengths: List[str]
    gaps: List[str]
    next: List[str]
    overall_score: float # 0 - 100
    technical_tier: str
    hiring_recommendation: str # Strong Hire, Hire, Lean Hire, No Hire
    interview_confidence: float # 0 - 100
    questions_answered: int
    covered_days: List[int]
    category_scores: List[FeedbackCategoryScore]
    eval_metrics: EvaluationMetrics
    areas_for_growth: List[str] # alias for gaps
    actionable_recommendations: List[str] # alias for next
    architecture_diagram: Optional[str] = None # Mermaid diagram
    duration_minutes: float = 15.5

class InterviewSessionState(BaseModel):
    session_id: str
    candidate: CandidateProfile
    personality: str = "Senior Engineer"
    difficulty: str = "Medium"
    interview_phase: str = "Phase 1 - Introduction" # Phase 1..5
    turns: List[TurnRecord] = []
    covered_days: List[int] = []
    eligible_topics: List[int] = []
    selected_topics: List[int] = []
    current_topic: Optional[str] = None
    current_day: Optional[int] = None
    question_count: int = 0
    questions_asked: int = 0
    follow_up_count: int = 0
    asked_question_hashes: List[str] = []
    current_question: Optional[str] = None
    is_complete: bool = False
    done: bool = False
    is_paused: bool = False
    feedback: Optional[FeedbackReport] = None

# API Contract Models according to technical-spec.md & REST endpoints
class UnifiedInterviewApiPayload(BaseModel):
    sessionId: Optional[str] = None
    session_id: Optional[str] = None
    candidate: Optional[Any] = None
    candidate_id: Optional[str] = None
    message: Optional[str] = None
    answer: Optional[str] = None
    personality: Optional[str] = "Senior Engineer"

class UnifiedInterviewApiResponse(BaseModel):
    reply: str
    done: bool = False
    sessionId: Optional[str] = None
    session_id: Optional[str] = None
    feedback: Optional[Dict[str, Any]] = None
    candidate: Optional[Dict[str, Any]] = None
    question_count: Optional[int] = None
    covered_days: Optional[List[int]] = None
    difficulty: Optional[str] = None

class StartInterviewRequest(BaseModel):
    candidate_id: Optional[str] = Field(None, description="ID of the candidate e.g. CAND-001")
    personality: Optional[str] = "Senior Engineer"

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Active interview session ID")
    message: str = Field(..., description="Candidate response text")

class FinishInterviewRequest(BaseModel):
    session_id: str
