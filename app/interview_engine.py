import json
import uuid
import re
import random
from typing import Dict, List, Tuple, Optional, Any
from app.models import (
    CandidateProfile, CurriculumData, CurriculumDay,
    InterviewSessionState, TurnRecord, FeedbackReport, FeedbackCategoryScore,
    EvaluationMetrics
)
from app.rag_engine import RAGCurriculumEngine
from app.llm_provider import LLMProvider

class DataRepository:
    def __init__(self, curriculum_path: str, candidates_path: str):
        with open(curriculum_path, 'r', encoding='utf-8') as f:
            self.curriculum = CurriculumData(**json.load(f))
        
        with open(candidates_path, 'r', encoding='utf-8') as f:
            raw_cands = json.load(f)["candidates"]
            self.candidates = {c["member"]["id"]: CandidateProfile(**c) for c in raw_cands}
        
        self.rag = RAGCurriculumEngine(self.curriculum)

    def get_candidate(self, candidate_id: str) -> Optional[CandidateProfile]:
        return self.candidates.get(candidate_id)

    def get_curriculum_day(self, day_num: int) -> Optional[CurriculumDay]:
        for d in self.curriculum.days:
            if d.day == day_num:
                return d
        return None

DAY_QUESTION_BANK = {
    1: [
        "In Day 1, you set up VS Code and virtual environments. How do you configure a Python `.venv` and ensure Pylance resolves packages cleanly in an enterprise pipeline?",
        "When debugging Python microservices in VS Code, how do you set up launch configurations and handle environment variables securely?"
    ],
    2: [
        "On Day 2, you integrated local LLMs via Ollama. What are the system latency and memory trade-offs when running Ollama with Qwen2.5-Coder locally versus calling cloud API providers?",
        "How did you connect VS Code extensions (like Cline or GitHub Copilot) to local Ollama endpoints, and how do you handle local model context limits?"
    ],
    3: [
        "On Day 3, you built a FastAPI backend connected to React and local LLMs. How did you structure your API endpoints and handle CORS or asynchronous requests to prevent blocking the event loop?",
        "What state management pattern did you use in React to render streaming chatbot responses smoothly without causing unnecessary re-renders?"
    ],
    4: [
        "On Day 4, you processed structured healthcare data with Pandas & SQLite. How did you design your SQLite schema and handle query performance when joining large claims datasets?",
        "When using SQLAlchemy ORM vs raw SQL queries for chatbot data retrieval, what performance or maintainability trade-offs did you encounter?"
    ],
    5: [
        "On Day 5, you extracted unstructured data using PyPDF, python-docx, and Tesseract OCR. How did you handle noisy OCR output from scanned enrollment forms before ingestion?",
        "What cleaning and normalization pipeline did you build to strip header/footer noise from multi-page healthcare documents?"
    ],
    6: [
        "On Day 6, you built the unified knowledge base in JSONL. How did you choose chunk sizes and overlap strategies for LangChain text splitters to preserve document context?",
        "What key metadata fields (like source, plan type, or section) did you attach to each JSONL chunk, and why are they critical for downstream filtering?"
    ],
    7: [
        "On Day 7, you explored embeddings and visual PCA clusters. How do Sentence Transformers compare to OpenAI Embeddings in dimension size, semantic accuracy, and inference speed?",
        "When inspecting PCA or t-SNE embedding visualizations, how did you verify that healthcare plan concepts clustered meaningfully?"
    ],
    8: [
        "On Day 8, you evaluated ChromaDB vs Pinecone. Under what production requirements would you select a local ChromaDB instance over a cloud-managed vector DB like Pinecone?",
        "What similarity metrics (Cosine Distance, Dot Product, Euclidean Distance) did you test in vector DB indexing, and how did distance metric choice impact retrieval precision?"
    ],
    9: [
        "On Day 9, you populated ChromaDB with metadata. How do metadata filtering filters (e.g. `plan_type == 'Gold'`) optimize query execution compared to raw vector similarity search?",
        "What strategy did you use to batch index large numbers of document chunks without exceeding memory limits or database socket timeouts?"
    ],
    10: [
        "On Day 10, you shipped the hybrid Retrieval & Matching Engine. How did your query router determine whether to execute a SQL lookup, vector search, or hybrid combination?",
        "How did you deduplicate and rank merged search results coming from SQL database queries and ChromaDB vector similarity scores?"
    ],
    11: [
        "On Day 11, you built end-to-end RAG with LLM APIs. How did you construct your RAG system prompt to guarantee the LLM strictly answers from retrieved context without hallucinating?",
        "What fallback or guardrail mechanism did you put in place when vector retrieval returns zero relevant documents for a user question?"
    ],
    12: [
        "On Day 12, you worked on Prompt Engineering. How did you utilize Chain-of-Thought (CoT) and Few-Shot prompting to improve accuracy on complex healthcare policy questions?",
        "How did you systematically evaluate system prompt variations against a fixed validation question set to choose the best production prompt?"
    ],
    13: [
        "On Day 13, you implemented Function Calling and Pydantic validation. How did you define OpenAI function tool schemas, and how did Pydantic enforce strict output parsing?",
        "What happens when the LLM generates invalid JSON parameters during tool invocation, and how did your backend gracefully recover or retry?"
    ],
    14: [
        "On Day 14, you studied Fine-Tuning concepts. What specific failure cases in prompt engineering or RAG would justify fine-tuning an open model over prompt optimization?",
        "How did you structure your JSONL dataset for fine-tuning (e.g. system, user, assistant messages) to avoid overfitting or catastrophic forgetting?"
    ],
    15: [
        "On Day 15, you fine-tuned models with LoRA & QLoRA. What are the key architectural differences between standard full parameter fine-tuning and LoRA/QLoRA parameter-efficient methods?",
        "What quantitative metrics (loss curves, BLEU/ROUGE, human benchmark comparison) did you use to evaluate whether fine-tuning improved response quality?"
    ],
    16: [
        "On Day 16, you built the FastAPI `/chat` endpoint. How did you implement session-based conversation management to track user dialog state across API calls?",
        "How did you structure error handling in FastAPI when downstream vector DB queries or LLM API calls fail or time out?"
    ],
    17: [
        "On Day 17, you built the Streamlit chatbot UI. How did you handle chat session persistence, UUID tracking, and plan selection parameters in Streamlit's execution model?",
        "What frontend UX patterns did you implement to allow candidates to start new conversations or switch healthcare policy contexts?"
    ],
    18: [
        "On Day 18, you added real-time streaming with Server-Sent Events (SSE). How does `StreamingResponse` work in FastAPI, and how did you render chunked tokens dynamically in the UI?",
        "How do you handle client disconnections or interrupted streams cleanly on the server to prevent lingering LLM API socket connections?"
    ],
    19: [
        "On Day 19, you created rich outputs and document citations. How did you parse retrieved chunk metadata to render inline citations and formatted Markdown policy cards?",
        "What validation steps did you take before displaying structured JSON claims tables to ensure no unverified or corrupted data was rendered?"
    ],
    20: [
        "On Day 20, you implemented Conversation Memory & Context Management. How did you handle context window token limits (e.g. sliding window, message summarization) for long user sessions?",
        "When summarizing past dialogue to fit within token budgets, how do you preserve critical user intent and extracted metadata like plan numbers?"
    ],
    21: [
        "On Day 21, you built LangChain Agents using the ReAct pattern. How does the ReAct loop (Thought, Action, Observation) enable an agent to break down complex multi-step user queries?",
        "What techniques did you use to inspect agent reasoning traces and prevent infinite agent execution loops when tools return unexpected output?"
    ],
    22: [
        "On Day 22, you implemented Multi-Agent Orchestration with CrewAI or LangGraph. How did your supervisor/router agent delegate queries between specialized domain agents?",
        "What performance, latency, or token overhead trade-offs did you observe when moving from a single agent to a multi-agent graph architecture?"
    ],
    23: [
        "On Day 23, you built Model Context Protocol (MCP) servers. What unique architectural advantages does MCP offer over standard REST function calling for agentic tool distribution?",
        "How did you define MCP resources, prompts, and tools in your Python MCP server, and how did you test execution with MCP clients like Claude Desktop or Cline?"
    ],
    24: [
        "On Day 24, you integrated agents, MCP tools, retrieval, and memory. How did your pipeline handle retry logic, timeouts, and fallback tools when an external MCP server went down?",
        "What failure testing scenarios did you conduct to validate pipeline resilience under bad network connectivity or malformed payloads?"
    ],
    25: [
        "On Day 25, you benchmarked chatbot evaluation. How did you measure grounding, context precision, and context recall using automated evaluation frameworks?",
        "What baseline performance metrics did you establish before approving the chatbot for staging/production deployment?"
    ],
    26: [
        "On Day 26, you optimized latency and cost using tiktoken and caching. How did exact prompt template optimization and response caching impact P95 response times and API costs?",
        "What caching key design did you use (e.g. query hash + metadata filters) to avoid serving stale answers when knowledge base documents are updated?"
    ],
    27: [
        "On Day 27, you implemented Security, Privacy & Guardrails. How did you defend your agentic pipeline against prompt injection, jailbreaks, and sensitive PII disclosure?",
        "How did you sanitize user inputs and validate tool parameters in FastAPI before executing database lookup tools?"
    ],
    28: [
        "On Day 28, you deployed containerized apps using Docker & Kubernetes. How did you structure your Dockerfile multi-stage builds, and what Kubernetes health checks (liveness/readiness) did you configure?",
        "How did you manage environment variables and secrets (like vector DB keys and LLM credentials) in Kubernetes ConfigMaps and Secrets?"
    ],
    29: [
        "On Day 29, you set up Monitoring & Observability with Prometheus & Grafana. What custom telemetry metrics (e.g. token usage, tool latency, error rates) did you export for monitoring?",
        "How did structured logging help you trace a failed user transaction back through the multi-agent graph and retrieval engine?"
    ],
    30: [
        "On Day 30, you conducted Production Readiness testing. What load testing or chaos testing tools did you use to evaluate system behavior under high concurrent user loads?",
        "What operational runbooks or failover procedures did you create to maintain 99.9% uptime for the chatbot pipeline?"
    ],
    31: [
        "On Day 31, you presented your Capstone Enterprise AI system. Looking back at your full capstone architecture, what was the single most challenging engineering trade-off you faced, and how did you solve it?",
        "How does your final production architecture seamlessly integrate RAG, ReAct Agents, MCP tools, and context memory under a unified API?"
    ]
}

CURRICULUM_KEYWORDS = {
    1: ["venv", "virtualenv", "pylance", "vscode", "interpreter", "debug", "pip"],
    2: ["ollama", "qwen", "copilot", "cline", "local", "context", "quantization", "gguf"],
    3: ["fastapi", "react", "vite", "cors", "async", "await", "endpoint", "useState", "useEffect"],
    4: ["pandas", "sqlite", "sql", "sqlalchemy", "query", "schema", "join", "index"],
    5: ["pdfplumber", "pypdf", "ocr", "tesseract", "beautifulsoup", "scrape", "clean", "text"],
    6: ["chunk", "splitter", "langchain", "metadata", "jsonl", "knowledge base", "overlap"],
    7: ["embedding", "sentence transformers", "vector", "pca", "cluster", "dimension", "cosine"],
    8: ["chroma", "pinecone", "vector db", "similarity", "distance", "metric", "index"],
    9: ["chromadb", "metadata", "filter", "semantic", "batch", "upsert", "index"],
    10: ["hybrid", "router", "deduplicate", "rank", "retrieval", "matching", "rerank"],
    11: ["rag", "llm", "openai", "sdk", "prompt", "context", "grounded", "hallucination"],
    12: ["zero-shot", "few-shot", "chain-of-thought", "cot", "prompt", "system prompt", "eval"],
    13: ["function calling", "tools", "pydantic", "schema", "validation", "structured output"],
    14: ["fine-tuning", "lora", "qlora", "dataset", "overfitting", "training", "jsonl"],
    15: ["peft", "transformers", "bitsandbytes", "weights", "rank", "adapter", "loss"],
    16: ["fastapi", "chat", "session", "api", "middleware", "timeout", "exception"],
    17: ["streamlit", "ui", "state", "session_state", "widget", "history", "uuid"],
    18: ["streaming", "sse", "server-sent events", "streamingresponse", "chunk", "async"],
    19: ["citation", "cards", "markdown", "rich output", "pydantic", "table", "formatter"],
    20: ["memory", "token", "sliding window", "summarization", "context management", "history"],
    21: ["langchain", "agent", "react", "thought", "action", "observation", "tools"],
    22: ["crewai", "langgraph", "multi-agent", "router", "orchestration", "graph", "state"],
    23: ["mcp", "model context protocol", "server", "client", "claude desktop", "cline", "tools"],
    24: ["integration", "retry", "fallback", "resilience", "pipeline", "error handling"],
    25: ["eval", "grounding", "precision", "recall", "benchmark", "dataset", "testing"],
    26: ["tiktoken", "token", "cache", "latency", "cost", "optimization", "p95"],
    27: ["security", "guardrails", "pii", "injection", "jailbreak", "sanitization"],
    28: ["docker", "kubernetes", "k8s", "container", "helm", "liveness", "readiness", "secrets"],
    29: ["prometheus", "grafana", "logging", "telemetry", "metrics", "observability", "trace"],
    30: ["load test", "production", "readiness", "failover", "runbook", "concurrency"],
    31: ["capstone", "architecture", "trade-off", "rag", "agents", "mcp", "enterprise"]
}

DAY_MODEL_ANSWERS = {
    1: "To configure a clean Python `.venv` in VS Code, execute `python -m venv .venv`, select `.venv/bin/python` as your active interpreter, and configure Pylance in `.vscode/settings.json`. Set up `.vscode/launch.json` for debugging with `envFile` loading.",
    2: "Running Ollama locally with `qwen2.5-coder` provides zero-latency offline inference and data privacy. Connect VS Code extensions (Cline or Copilot) to `http://localhost:11434`. Quantize to Q4_K_M to fit within memory budgets.",
    3: "Structure FastAPI with async endpoints (`async def chat(...)`) to avoid blocking the event loop. In React, use `useEffect` and custom hooks with fetch stream readers to render tokens incrementally without re-rendering the whole component.",
    4: "Design SQLite schema with indexes on foreign keys (`claim_id`, `patient_id`). Use Pandas `to_sql(if_exists='append', chunksize=1000)` for batch loading and SQLAlchemy for ORM query isolation.",
    5: "Use `pdfplumber` for text extraction from digital PDFs. For scanned forms, run Tesseract OCR after pre-processing (grayscale, thresholding). Strip recurring headers/footers using regex patterns.",
    6: "Use LangChain `RecursiveCharacterTextSplitter` with `chunk_size=500` and `chunk_overlap=50`. Attach JSON metadata (`source`, `plan_type`, `section`) to preserve document context.",
    7: "Sentence Transformers (e.g. `all-MiniLM-L6-v2`) output 384-dim dense vectors locally. OpenAI `text-embedding-3-small` outputs 1536-dim vectors. PCA/t-SNE reduces vector dimensions for visual cluster analysis.",
    8: "Select ChromaDB for zero-cost embedded vector search. Select Pinecone for managed cloud scaling. Cosine similarity evaluates dot product normalized by magnitudes: `cos(theta) = A . B / (||A|| * ||B||)`.",
    9: "ChromaDB metadata filters (`where={'plan_type': 'Gold'}`) pre-filter search candidates before vector distance computation, significantly improving query speed.",
    10: "Build a query router: if structured filters exist, execute SQL on SQLite; otherwise execute vector search in ChromaDB. Merge and deduplicate results using Reciprocal Rank Fusion (RRF).",
    11: "Construct a grounded RAG prompt: 'Answer strictly using ONLY the provided context below. If context is insufficient, state: Information unavailable.' Add fallback thresholds for low similarity scores.",
    12: "Use Chain-of-Thought (CoT) prompting ('Let's think step by step: 1. Identify plan 2. Check limits 3. Compute co-pay') and Few-Shot examples to stabilize complex reasoning.",
    13: "Define tool schemas using Pydantic BaseModels (`class CoverageRequest(BaseModel): plan_id: str`). Handle LLM tool parameter parsing errors using try/except validation recovery.",
    14: "Fine-tuning is ideal when prompt engineering fails to produce consistent formatting or domain jargon. Prepare JSONL dataset pairs with clear system, user, and assistant roles.",
    15: "LoRA injects trainable rank decomposition matrices while freezing base model weights. QLoRA quantizes base weights to 4-bit (NF4). Evaluate using validation loss and ROUGE/BLEU scores.",
    16: "Manage session dialog state using session IDs stored in FastAPI memory or SQLite. Wrap LLM calls in `asyncio.wait_for(timeout=10.0)` for resilient error recovery.",
    17: "Manage dialog state in Streamlit with `st.session_state.messages = []`. Provide sidebar widgets for healthcare plan selection and handle full execution reruns cleanly.",
    18: "Use FastAPI `StreamingResponse(event_generator(), media_type='text/event-stream')`. On frontend, consume stream chunks asynchronously via `reader.read()`.",
    19: "Parse retrieved chunk metadata (`source_doc`, `page_number`) to render inline citations `[Doc 4, p. 12]`. Validate structured tables with Pydantic before rendering Markdown.",
    20: "Manage token context window limits using a sliding message window (last N turns) combined with background LLM conversation summarization.",
    21: "ReAct loop alternates between Thought (reasoning), Action (tool selection), and Observation (tool output). Prevent infinite loops by setting `max_iterations=5`.",
    22: "Use a Supervisor Router Agent (LangGraph/CrewAI) to classify incoming queries and delegate tasks to specialized sub-agents (Retrieval, Claims, Policy).",
    23: "Model Context Protocol (MCP) standardizes tool discovery via JSON-RPC. Build an MCP Server with `FastMCP` exposing `@mcp.tool()` handlers for Claude Desktop or Cline.",
    24: "Build pipeline resilience with exponential backoff retries, tool execution timeouts, and circuit-breaker fallback tools when external servers are unreachable.",
    25: "Benchmark chatbot responses using evaluation metrics (Ragas/TruLens) for Groundedness, Answer Relevance, Context Precision, and Context Recall.",
    26: "Audit prompt token counts with `tiktoken`. Implement response caching (`redis.setex(query_hash, 3600, response)`) for frequent queries to lower latency to <50ms.",
    27: "Defend against prompt injection using input sanitization, regex guardrails, and secondary evaluation models. Sanitize PII before context ingestion.",
    28: "Structure Dockerfile multi-stage builds (`FROM python:3.11-slim AS builder`). Deploy to Kubernetes with Deployment, ConfigMaps, and readiness probes on `/health`.",
    29: "Export custom Prometheus metrics (`http_requests_total`, `llm_latency_seconds`). Structure logs in JSON format with `session_id` and `trace_id` for Grafana dashboarding.",
    30: "Conduct load testing with Locust or k6 simulating concurrent user bursts. Verify system stays operational under 100+ req/sec.",
    31: "The capstone integrates RAG vector search, query routing, ReAct agents, MCP tools, context memory, and Kubernetes deployment under a unified API."
}


class InterviewEngine:
    def __init__(self, repository: DataRepository):
        self.repo = repository
        self.sessions: Dict[str, InterviewSessionState] = {}
        self.llm = LLMProvider()

    def generate_hint_or_model_answer(self, session_id: str) -> Dict[str, Any]:
        if session_id not in self.sessions:
            raise ValueError(f"Session '{session_id}' not found.")
        session = self.sessions[session_id]
        current_day = session.current_day or 7
        day_info = self.repo.get_curriculum_day(current_day)
        topic_title = day_info.title if day_info else f"Day {current_day}"
        model_ans = DAY_MODEL_ANSWERS.get(current_day, f"For Day {current_day} ({topic_title}), focus on key objectives, trade-offs, and error recovery strategies.")

        hint_text = (
            f"💡 **Interviewer Assistance & Reference Guide (Day {current_day} — {topic_title}):**\n\n"
            f"**Key Engineering Objectives:**\n"
            + "\n".join([f"- {obj}" for obj in (day_info.objectives if day_info else [])]) + "\n\n"
            f"**Recommended Tools:** {', '.join(day_info.tools if day_info else [])}\n\n"
            f"**Sample Model Answer / Technical Explanation:**\n{model_ans}"
        )

        return {
            "session_id": session_id,
            "day": current_day,
            "topic": topic_title,
            "model_answer": model_ans,
            "hint": hint_text
        }

    def _adapt_question_to_role(self, personality: str, day: int, topic: str, raw_question: str) -> str:
        """
        Adapts question wording and analytical focus specifically to the selected interviewer persona.
        """
        if personality == "Staff Engineer":
            return (
                f"[Staff Architect Perspective - Scale & Trade-offs]\n"
                f"Looking at Day {day} ({topic}): From a system architecture standpoint, how does your design for {topic} "
                f"handle scalability, P95 latency bounds, and component isolation? Specifically: {raw_question}"
            )
        elif personality == "Principal Engineer":
            return (
                f"[Principal Engineer Perspective - Strategy & System Bounds]\n"
                f"Evaluating Day {day} ({topic}): What core fundamental trade-offs guided your technology selection here? "
                f"Why did you choose this pattern over alternatives, and how did you guarantee zero regressions? Specifically: {raw_question}"
            )
        elif personality == "Friendly":
            return (
                f"[Tech Lead - Supportive Review]\n"
                f"Welcome! I'd love to hear about your hands-on experience with Day {day} ({topic}). "
                f"What was the most interesting engineering challenge you solved? Specifically: {raw_question}"
            )
        else: # Senior Engineer
            return (
                f"[Senior Engineer Perspective - Code Depth & Execution]\n"
                f"Focusing on Day {day} ({topic}): Let's walk through your concrete implementation choices, code patterns, and edge-case exception handling. {raw_question}"
            )

    def start_session(self, candidate_id: str, personality: str = "Senior Engineer") -> InterviewSessionState:
        candidate = self.repo.get_candidate(candidate_id)
        if not candidate:
            raise ValueError(f"Candidate with ID '{candidate_id}' not found.")

        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        target_day = self._select_next_day(candidate, covered_days=[])
        day_info = self.repo.get_curriculum_day(target_day)
        
        q_options = DAY_QUESTION_BANK.get(target_day, [
            f"Let me start by asking about Day {target_day}: {day_info.title if day_info else ''}. What major engineering trade-offs did you make?"
        ])
        raw_question = q_options[0]

        # Adapt question wording explicitly to the selected personality
        topic_title = day_info.title if day_info else 'Core Topic'
        question = self._adapt_question_to_role(personality, target_day, topic_title, raw_question)

        completed_missions = [m.title for m in candidate.missions if m.passed][:3]
        completed_str = ", ".join(completed_missions) if completed_missions else "RAG, Vector Search, and Prompt Engineering"

        # Persona welcome
        persona_greetings = {
            "Senior Engineer": "As a Senior Engineer, I'll be focusing on code depth, implementation choices, and error handling.",
            "Staff Engineer": "As a Staff Architect, I'll be focusing on system design, component scalability, and P95 latency trade-offs.",
            "Principal Engineer": "As a Principal Engineer, I'll be evaluating strategic technology choices, system bounds, and eval benchmarks.",
            "Friendly": "I'm excited to hear all about your journey and explore your hands-on AI projects with you!"
        }
        greeting = persona_greetings.get(personality, persona_greetings["Senior Engineer"])

        welcome_msg = (
            f"Hi {candidate.member.name.split()[0]}.\n\n"
            f"I'm conducting your technical interview today as a **{personality}**. {greeting}\n\n"
            f"I see you've completed key missions in our cohort, especially around {completed_str}.\n\n"
            f"**Question 1 (Day {target_day} - {topic_title}):**\n"
            f"{question}"
        )

        session = InterviewSessionState(
            session_id=session_id,
            candidate=candidate,
            personality=personality,
            difficulty="Medium",
            interview_phase="Phase 1 — Introduction",
            turns=[
                TurnRecord(
                    turn_index=1,
                    day=target_day,
                    topic_title=topic_title,
                    question=question,
                    is_follow_up=False,
                    difficulty="Medium"
                )
            ],
            covered_days=[target_day],
            eligible_topics=[m.day for m in candidate.missions if not m.skipped],
            selected_topics=[target_day],
            current_topic=topic_title,
            current_day=target_day,
            question_count=1,
            questions_asked=1,
            current_question=welcome_msg,
            is_complete=False,
            done=False
        )
        
        self.sessions[session_id] = session
        return session

    def process_turn(self, session_id: str, candidate_answer: str) -> InterviewSessionState:
        if session_id not in self.sessions:
            raise ValueError(f"Session '{session_id}' not found.")

        session = self.sessions[session_id]
        if session.is_complete or session.done:
            session.is_complete = True
            session.done = True
            return session

        last_turn = session.turns[-1]
        last_turn.candidate_answer = candidate_answer.strip()

        eval_score, eval_notes, metrics = self._evaluate_answer(last_turn.day, candidate_answer)
        last_turn.evaluation_score = eval_score
        last_turn.evaluation_notes = eval_notes
        last_turn.metrics = metrics

        if eval_score >= 85.0:
            session.difficulty = self._escalate_difficulty(session.difficulty)
        elif eval_score < 55.0:
            session.difficulty = self._deescalate_difficulty(session.difficulty)

        needs_follow_up = (
            (eval_score < 60.0 or len(candidate_answer.split()) < 15 or self._detect_keyword_triggers(candidate_answer))
            and not last_turn.is_follow_up
        )
        
        if len(session.turns) >= 8 and len(set(session.covered_days)) >= 4 and not needs_follow_up:
            session.is_complete = True
            session.done = True
            session.interview_phase = "Phase 5 — Final Assessment"
            session.current_question = "Thank you for completing the technical interview! Generating your detailed evaluation report..."
            return session

        if needs_follow_up:
            day_info = self.repo.get_curriculum_day(last_turn.day)
            topic_t = day_info.title if day_info else f"Day {last_turn.day}"
            follow_up_raw = self._generate_follow_up(last_turn.day, candidate_answer, session.difficulty)
            follow_up_q = self._adapt_question_to_role(session.personality, last_turn.day, topic_t, follow_up_raw)
            
            next_turn_idx = len(session.turns) + 1
            new_turn = TurnRecord(
                turn_index=next_turn_idx,
                day=last_turn.day,
                topic_title=topic_t,
                question=follow_up_q,
                is_follow_up=True,
                parent_turn_index=last_turn.turn_index,
                difficulty=session.difficulty
            )
            session.turns.append(new_turn)
            session.question_count = len(session.turns)
            session.questions_asked = len(session.turns)
            session.follow_up_count += 1
            session.interview_phase = self._determine_phase(len(session.turns), False)
            session.current_question = f"**Follow-up Question (Day {last_turn.day} | {session.personality} | {session.difficulty}):**\n{follow_up_q}"
            return session

        next_day = self._select_next_day(session.candidate, session.covered_days)
        if next_day not in session.covered_days:
            session.covered_days.append(next_day)

        day_info = self.repo.get_curriculum_day(next_day)
        topic_t = day_info.title if day_info else f"Day {next_day}"
        q_options = DAY_QUESTION_BANK.get(next_day, [
            f"Regarding Day {next_day}: {topic_t}, how did you approach the engineering objectives?"
        ])
        
        q_idx = 1 if len(q_options) > 1 and any(t.day == next_day for t in session.turns) else 0
        raw_question = q_options[q_idx]
        new_question = self._adapt_question_to_role(session.personality, next_day, topic_t, raw_question)

        next_turn_idx = len(session.turns) + 1
        new_turn = TurnRecord(
            turn_index=next_turn_idx,
            day=next_day,
            topic_title=topic_t,
            question=new_question,
            is_follow_up=False,
            difficulty=session.difficulty
        )
        session.turns.append(new_turn)
        session.question_count = len(session.turns)
        session.questions_asked = len(session.turns)
        session.current_day = next_day
        session.current_topic = topic_t
        session.interview_phase = self._determine_phase(len(session.turns), False)
        session.current_question = (
            f"Great response. Moving on to **Day {next_day} ({topic_t})**:\n\n"
            f"**Question {next_turn_idx} ({session.personality} | {session.difficulty}):**\n{new_question}"
        )
        return session

    def _determine_phase(self, turn_count: int, is_complete: bool) -> str:
        if is_complete:
            return "Phase 5 — Final Assessment"
        if turn_count <= 1:
            return "Phase 1 — Introduction"
        elif turn_count <= 3:
            return "Phase 2 — Core Technical Understanding"
        elif turn_count <= 5:
            return "Phase 3 — Engineering Depth"
        else:
            return "Phase 4 — Scenario / Architecture Questions"

    def _select_next_day(self, candidate: CandidateProfile, covered_days: List[int]) -> int:
        # Candidate eligible days MUST preserve the exact order in candidate.missions and exclude skipped missions
        candidate_eligible = [m.day for m in candidate.missions if not m.skipped]
        if not candidate_eligible:
            candidate_eligible = [d.day for d in self.repo.curriculum.days]

        uncovered = [d for d in candidate_eligible if d not in covered_days]
        if uncovered:
            return uncovered[0]

        # Fallback to any curriculum day that is NOT skipped
        skipped_days = set(m.day for m in candidate.missions if m.skipped)
        all_uncovered = [d.day for d in self.repo.curriculum.days if d.day not in skipped_days and d.day not in covered_days]
        if all_uncovered:
            return all_uncovered[0]

        return covered_days[-1] if covered_days else 1

    def _detect_keyword_triggers(self, answer: str) -> bool:
        triggers = ["cosine", "euclidean", "pinecone", "chroma", "langgraph", "crewai", "don't know", "dont know", "not sure"]
        ans_lower = answer.lower()
        return any(t in ans_lower for t in triggers)

    def _generate_follow_up(self, day: int, previous_answer: str, difficulty: str) -> str:
        ans_lower = previous_answer.lower()
        
        if "don't know" in ans_lower or "dont know" in ans_lower or "not sure" in ans_lower or len(previous_answer.split()) < 5:
            if day in [7, 8]:
                return "Let me simplify. Can you explain what embeddings are first, and why we turn text into vectors?"
            elif day in [21, 22, 23]:
                return "Let's step back to basics. What is the fundamental purpose of an AI Agent using tools?"
            else:
                return f"Let's simplify. Can you give a high-level overview of your approach to Day {day}?"

        if "cosine" in ans_lower:
            return "Why cosine similarity instead of Euclidean distance or dot product for high-dimensional embeddings?"
        
        if "pinecone" in ans_lower:
            return "Why choose Pinecone over an embedded vector database like ChromaDB or Qdrant for this workload?"
            
        if "langgraph" in ans_lower or "crewai" in ans_lower:
            return "What advantages does LangGraph provide over CrewAI or a custom state machine for multi-agent graph routing?"

        day_info = self.repo.get_curriculum_day(day)
        topic_title = day_info.title if day_info else f"Day {day}"

        follow_ups = {
            7: "Could you elaborate on how vector dimensions and distance metrics affect your semantic search latency and retrieval accuracy?",
            8: "Specifically, how did you configure your vector store index to handle metadata filtering while avoiding memory bottlenecking?",
            10: "Can you walk me through the exact logic your query router uses to decide when to bypass vector search and rely strictly on SQL queries?",
            12: "How did you structure your system prompt instructions to handle ambiguous user queries without generating ungrounded responses?",
            13: "What specific Pydantic error validation or fallback handling did you implement when the LLM returned malformed tool arguments?",
            16: "How did your FastAPI backend handle connection timeouts or rate limits when invoking external LLM APIs under heavy traffic?",
            21: "How did you debug the agent's ReAct loop when it entered infinite tool invocation loops or received unexpected observation formats?",
            22: "What state synchronization mechanism did you use between supervisor agents and worker sub-agents in your multi-agent architecture?",
            23: "How did you define security boundaries and tool schemas in your MCP server to prevent unauthorized command execution?",
            28: "How did you manage zero-downtime rolling updates and environment secret injection in your Kubernetes deployment manifest?"
        }

        return follow_ups.get(
            day,
            f"Could you dive deeper into the specific architectural trade-offs and error recovery strategies you used for {topic_title}?"
        )

    def _escalate_difficulty(self, current: str) -> str:
        levels = ["Easy", "Medium", "Hard", "Expert"]
        idx = levels.index(current) if current in levels else 1
        return levels[min(idx + 1, len(levels) - 1)]

    def _deescalate_difficulty(self, current: str) -> str:
        levels = ["Easy", "Medium", "Hard", "Expert"]
        idx = levels.index(current) if current in levels else 1
        return levels[max(idx - 1, 0)]

    def _evaluate_answer(self, day: int, answer: str) -> Tuple[float, str, EvaluationMetrics]:
        ans_lower = answer.lower()
        words = answer.split()
        word_count = len(words)
        
        if word_count < 10:
            metrics = EvaluationMetrics(
                technical_knowledge=4.0, communication=3.5, reasoning=4.0,
                problem_solving=3.5, architecture_thinking=3.0, confidence=4.0
            )
            return 35.0, "Answer is extremely short and lacks technical detail or explanation.", metrics

        keywords = CURRICULUM_KEYWORDS.get(day, ["system", "code", "architecture", "data"])
        matched_kw = [kw for kw in keywords if kw in ans_lower]

        base_score = 60.0
        if word_count > 50:
            base_score += 15.0
        elif word_count > 25:
            base_score += 10.0

        if len(matched_kw) >= 3:
            base_score += 25.0
        elif len(matched_kw) >= 1:
            base_score += 15.0

        reasoning_terms = ["because", "trade-off", "tradeoff", "latency", "scale", "performance", "handle", "error", "fallback", "config"]
        matched_reasoning = [rt for rt in reasoning_terms if rt in ans_lower]
        if matched_reasoning:
            base_score += 10.0

        final_score = min(100.0, max(20.0, base_score))

        tech_k = min(10.0, round(final_score / 10.0, 1))
        comm = min(10.0, round(min(100.0, word_count * 1.5 + 40.0) / 10.0, 1))
        reas = min(10.0, round((final_score + (10.0 if matched_reasoning else 0.0)) / 10.0, 1))
        prob_solv = min(10.0, round((tech_k * 0.5 + reas * 0.5), 1))
        arch = min(10.0, round((tech_k * 0.6 + comm * 0.4), 1))
        conf = min(10.0, round(min(10.0, tech_k + 1.0), 1))

        metrics = EvaluationMetrics(
            technical_knowledge=tech_k,
            communication=comm,
            reasoning=reas,
            problem_solving=prob_solv,
            architecture_thinking=arch,
            confidence=conf
        )

        notes = (
            f"Demonstrated good domain concepts ({', '.join(matched_kw[:3]) if matched_kw else 'general concept'}). "
            f"Technical depth: {'High' if final_score >= 80 else 'Moderate' if final_score >= 60 else 'Needs elaboration'}."
        )
        return final_score, notes, metrics
