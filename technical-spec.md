# Technical Specification - InterviewAI API

## Core Endpoint

`POST /api/interview`

## 1. Start Interview

### Request Payload
```json
{
  "candidate": "CAND-001",
  "personality": "Senior Engineer"
}
```

### Response Payload
```json
{
  "reply": "Hi Sarah. I see you've completed key missions in our enterprise AI cohort, especially around Embeddings, Vector DB and MCP. Today I'll ask you practical engineering questions about your AI Cohort journey.\n\n**Question 1 (Day 7 - Embeddings & Semantic Search):**\nHow do Sentence Transformers compare to OpenAI Embeddings in dimension size, semantic accuracy, and inference speed?",
  "done": false,
  "sessionId": "session_a1b2c3d4",
  "question_count": 1,
  "covered_days": [7],
  "difficulty": "Medium"
}
```

---

## 2. Next Turn (Interview Progression)

### Request Payload
```json
{
  "sessionId": "session_a1b2c3d4",
  "message": "Sentence Transformers output 384 or 768 dimension vectors and run locally on CPU/GPU, whereas OpenAI Embeddings return 1536 dim vectors over an API call with higher dimension size."
}
```

### Response Payload (In Progress)
```json
{
  "reply": "Great explanation. Moving on to **Day 8 (Vector DBs - ChromaDB vs Pinecone)**:\n\n**Question 2 (Day 8 | Hard):**\nUnder what production requirements would you select a local ChromaDB instance over a cloud-managed vector DB like Pinecone?",
  "done": false,
  "sessionId": "session_a1b2c3d4",
  "question_count": 2,
  "covered_days": [7, 8],
  "difficulty": "Hard"
}
```

---

## 3. Interview Completion

### Response Payload (Interview Completed)
```json
{
  "reply": "Thank you for completing the technical interview! Generating your detailed evaluation report...",
  "done": true,
  "sessionId": "session_a1b2c3d4",
  "feedback": {
    "session_id": "session_a1b2c3d4",
    "candidate_id": "CAND-001",
    "candidate_name": "Sarah Johnson",
    "job_role": "Senior AI Systems Engineer",
    "overall_score": 88.5,
    "technical_tier": "Senior AI Engineer (Staff / Principal Track)",
    "hiring_recommendation": "Strong Hire",
    "interview_confidence": 95.0,
    "questions_answered": 8,
    "covered_days": [7, 8, 10, 12, 16, 21, 23, 28],
    "eval_metrics": {
      "technical_knowledge": 8.9,
      "communication": 9.0,
      "reasoning": 8.8,
      "problem_solving": 8.7,
      "architecture_thinking": 9.1,
      "confidence": 9.2
    },
    "category_scores": [
      {
        "category": "Data Foundations & RAG",
        "score": 90.0,
        "status": "EXCELLENT",
        "notes": "Demonstrated deep architectural mastery and robust technical reasoning."
      }
    ],
    "strengths": [
      "Excellent understanding of Embeddings and Vector Search.",
      "Strong architecture thinking and systematic problem solving approach."
    ],
    "areas_for_growth": [
      "Edge-case error recovery under high concurrency load."
    ],
    "actionable_recommendations": [
      "Revise Vector Search indexing and similarity metric trade-offs.",
      "Practice implementing Model Context Protocol (MCP) servers with security guardrails."
    ],
    "architecture_diagram": "graph TD\n  A[User Query] --> B[FastAPI Gateway]\n..."
  }
}
```
