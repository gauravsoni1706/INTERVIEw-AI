# InterviewAI - Enterprise AI Interview Agent

InterviewAI is an adaptive, enterprise-grade AI Technical Interviewer built for an Enterprise AI Engineering Cohort. Unlike generic Q&A chatbots or static questionnaires, InterviewAI conducts realistic, multi-turn technical interviews based on a candidate's actual AI Cohort learning journey (`curriculum.json` & `candidates.json`).

---

## 1. Problem & Solution

### The Problem
Traditional technical interviewing is often static, inconsistent, and disconnected from what candidates actually built during their learning journey. Generic AI chatbots fail as interviewers because they lack candidate context, repeat questions, and fail to probe with adaptive follow-ups.

### The Solution
InterviewAI acts as an autonomous AI interviewer that:
- Reads candidate cohort profiles and mission completion status dynamically.
- Strictly respects skipped topics (never asking about skipped missions as if completed).
- Adaptively adjusts difficulty based on answer quality.
- Conducts follow-up questions probing trade-offs, scalability, and error recovery.
- Maintains multi-turn conversation memory via `sessionId`.
- Enforces minimum coverage (>= 8 questions, >= 4 distinct curriculum days).
- Generates structured, evidence-based feedback reports (`summary`, `strengths`, `gaps`, `next`).

---

## 2. Architecture

```text
               +-----------------------------------+
               |           React Frontend          |
               | (Candidate Selector / Chat / Eval)|
               +-----------------+-----------------+
                                 |
                        POST /api/interview
                                 |
               +-----------------v-----------------+
               |          FastAPI Gateway          |
               +-----------------+-----------------+
                                 |
        +------------------------+------------------------+
        |                                                 |
+-------v-------+       +-------------------+     +-------v-------+
|  Candidate    |       |  Curriculum RAG   |     |  State        |
|  Context      |       |  Retriever        |     |  Machine      |
|  Builder      |       | (curriculum.json) |     | (SessionStore)|
+-------+-------+       +---------+---------+     +-------+-------+
        |                         |                       |
        +-------------------------+-----------------------+
                                  |
                      +-----------v-----------+
                      |   Interview Planner   |
                      +-----------+-----------+
                                  |
                      +-----------v-----------+
                      |   Question Generator  |
                      | (LLM / Smart Engine)  |
                      +-----------+-----------+
                                  |
                      +-----------v-----------+
                      |   Answer Evaluator &  |
                      |   Follow-up Engine    |
                      +-----------+-----------+
                                  |
                      +-----------v-----------+
                      |   Feedback Generator  |
                      +-----------------------+
```

---

## 3. Key Features

- **Candidate Personalization Engine**: Analyzes candidate background, completed missions, skipped topics, attempt counts, and experience level.
- **Skipped Topic Filtering**: Ensures candidates who skipped a mission (e.g. Day 29 Monitoring) are never asked questions assuming they completed it.
- **Adaptive Difficulty & Follow-ups**: Probes candidate choices ("Why Cosine Similarity over Euclidean?") or simplifies when answers show confusion.
- **Multi-Turn State Persistence**: Maintains complete conversation state by `sessionId`.
- **Multi-Provider LLM Abstraction**: Supports Google Gemini, OpenAI, Claude Anthropic, or an offline **Smart Fallback Engine**.
- **Evidence-Based Feedback**: Generates structured evaluation report containing `summary`, `strengths`, `gaps`, `next`, 6-axis metrics, category breakdown, and Mermaid architecture diagram.

---

## 4. API Specification

Complies strictly with `technical-spec.md`:

### Endpoint
`POST /api/interview`

### Start Interview Payload
```json
{
  "candidate": "CAND-001",
  "personality": "Senior Engineer"
}
```
**Response:**
```json
{
  "reply": "Hi Sarah. I see you've completed key missions...",
  "done": false,
  "sessionId": "session_a1b2c3d4",
  "question_count": 1,
  "covered_days": [7],
  "difficulty": "Medium"
}
```

### Next Turn Payload
```json
{
  "sessionId": "session_a1b2c3d4",
  "message": "Sentence Transformers output 384 or 768 dim embeddings..."
}
```
**Response:**
```json
{
  "reply": "Great explanation. Moving on to Day 8...",
  "done": false,
  "sessionId": "session_a1b2c3d4",
  "question_count": 2,
  "covered_days": [7, 8],
  "difficulty": "Hard"
}
```

### Final Response (Interview Complete)
```json
{
  "reply": "Interview completed.",
  "done": true,
  "sessionId": "session_a1b2c3d4",
  "feedback": {
    "summary": "Sarah Johnson demonstrated senior capability with strong performance in Day 7...",
    "strengths": ["Demonstrated clear understanding of Embeddings (Day 7).", "..."],
    "gaps": ["Demonstrated less technical depth in production latency bounds.", "..."],
    "next": ["Review Day 10 — Retrieval & Matching Engine...", "..."]
  }
}
```

---

## 5. Quick Start Guide

### Prerequisites
- Python 3.9+
- Pip & Virtualenv

### Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. **Run Automated Test Suite (10 Test Cases):**
   ```bash
   python run_tests.py
   ```

4. **Start Backend & Server:**
   ```bash
   python main.py
   ```

5. **Access Application:**
   - Web App: `http://localhost:8000`
   - REST API Docs: `http://localhost:8000/docs`

---

## 6. Project Structure

```
.
├── app/
│   ├── feedback_engine.py   # Feedback report & score generation
│   ├── interview_engine.py  # Interview state machine & follow-up engine
│   ├── llm_provider.py      # Multi-provider LLM abstraction & fallback engine
│   ├── models.py            # Pydantic data schemas & API payloads
│   └── rag_engine.py        # RAG semantic retriever over curriculum.json
├── data/
│   ├── candidates.json      # Candidate profiles & mission data
│   └── curriculum.json      # 31-Day Enterprise AI Cohort curriculum
├── static/
│   └── index.html           # Single-page React dashboard
├── tests/
│   └── test_interview.py    # Pytest API integration test suite (10 tests)
├── .env.example             # Environment variable template
├── Dockerfile               # Production container definition
├── docker-compose.yml       # Docker compose service definition
├── main.py                  # FastAPI application entrypoint
├── package.json             # NPM metadata
├── PROMPTS.md               # AI System Prompt Audit Log
├── README.md                # Project documentation
├── requirements.txt         # Python dependencies
└── run_tests.py             # Test execution runner
```
