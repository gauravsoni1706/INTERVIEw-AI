from typing import List, Dict, Any
from app.models import (
    InterviewSessionState, FeedbackReport, FeedbackCategoryScore, EvaluationMetrics
)

class FeedbackEngine:
    @staticmethod
    def generate_report(session: InterviewSessionState) -> FeedbackReport:
        turns = session.turns
        scores = [t.evaluation_score for t in turns if t.evaluation_score is not None]
        avg_score = sum(scores) / max(len(scores), 1) if scores else 75.0

        # Incorporate candidate profile signals
        cand_signals = session.candidate.signals
        signal_bonus = 0.0
        if cand_signals.missionsFirstTry > 20:
            signal_bonus += 5.0
        if cand_signals.commitDays >= 28:
            signal_bonus += 3.0

        final_overall_score = round(min(100.0, max(40.0, avg_score + signal_bonus)), 1)

        # Technical Tier & Hiring Recommendation
        if final_overall_score >= 88:
            tier = "Senior AI Engineer (Staff / Principal Track)"
            hiring_rec = "Strong Hire"
            confidence_level = 95.0
        elif final_overall_score >= 78:
            tier = "Mid-Senior AI Engineer"
            hiring_rec = "Hire"
            confidence_level = 88.0
        elif final_overall_score >= 65:
            tier = "Associate AI Systems Engineer"
            hiring_rec = "Lean Hire"
            confidence_level = 75.0
        else:
            tier = "Junior AI Developer (Needs Foundational Practice)"
            hiring_rec = "No Hire"
            confidence_level = 60.0

        # Category mapping across 31 curriculum days
        categories_map = {
            "Data Foundations & RAG": [4, 5, 6, 7, 8, 9, 10, 11],
            "Prompt Engineering & Tool Calling": [12, 13, 14, 15],
            "Backend Systems & Context Memory": [3, 16, 17, 18, 19, 20],
            "Agentic AI & Model Context Protocol": [21, 22, 23, 24],
            "Security, Eval & Production Ops": [25, 26, 27, 28, 29, 30, 31]
        }

        category_scores: List[FeedbackCategoryScore] = []
        for cat_name, days in categories_map.items():
            cat_turns = [t for t in turns if t.day in days and t.evaluation_score is not None]
            if cat_turns:
                cat_avg = sum(t.evaluation_score for t in cat_turns) / len(cat_turns)
            else:
                cat_avg = final_overall_score * 0.95

            cat_avg = round(cat_avg, 1)
            if cat_avg >= 82:
                status = "EXCELLENT"
                note = "Demonstrated deep architectural mastery and robust technical reasoning."
            elif cat_avg >= 68:
                status = "GOOD"
                note = "Solid operational understanding with clear practical implementation knowledge."
            else:
                status = "NEEDS_IMPROVEMENT"
                note = "Basic grasp present, but requires deeper practice on edge cases and system bounds."

            category_scores.append(FeedbackCategoryScore(
                category=cat_name,
                score=cat_avg,
                status=status,
                notes=note
            ))

        # 6-Axis Evaluation Metrics Aggregation
        turn_metrics = [t.metrics for t in turns if t.metrics is not None]
        if turn_metrics:
            avg_tk = round(sum(m.technical_knowledge for m in turn_metrics) / len(turn_metrics), 1)
            avg_comm = round(sum(m.communication for m in turn_metrics) / len(turn_metrics), 1)
            avg_reas = round(sum(m.reasoning for m in turn_metrics) / len(turn_metrics), 1)
            avg_prob = round(sum(m.problem_solving for m in turn_metrics) / len(turn_metrics), 1)
            avg_arch = round(sum(m.architecture_thinking for m in turn_metrics) / len(turn_metrics), 1)
            avg_conf = round(sum(m.confidence for m in turn_metrics) / len(turn_metrics), 1)
        else:
            s_scaled = round(final_overall_score / 10.0, 1)
            avg_tk = s_scaled
            avg_comm = min(10.0, round(s_scaled + 0.5, 1))
            avg_reas = s_scaled
            avg_prob = s_scaled
            avg_arch = s_scaled
            avg_conf = min(10.0, round(s_scaled + 0.3, 1))

        eval_metrics = EvaluationMetrics(
            technical_knowledge=avg_tk,
            communication=avg_comm,
            reasoning=avg_reas,
            problem_solving=avg_prob,
            architecture_thinking=avg_arch,
            confidence=avg_conf
        )

        # Strengths
        strengths = []
        high_turns = [t for t in turns if (t.evaluation_score or 0) >= 75]
        low_turns = [t for t in turns if (t.evaluation_score or 0) < 75]

        if high_turns:
            for ht in high_turns[:3]:
                strengths.append(f"Demonstrated clear understanding of {ht.topic_title} (Day {ht.day}).")
        else:
            strengths.append(f"Solid effort across {len(set(session.covered_days))} curriculum days evaluated during the interview.")

        if cand_signals.commitDays >= 25:
            strengths.append(f"Demonstrated strong commitment with {cand_signals.commitDays} active commit days and {cand_signals.missionsCompleted} completed missions.")

        strengths.append("Structured technical reasoning and systematic problem-solving approach.")

        # Gaps / Areas for Growth (based on actual answer performance)
        gaps = []
        if low_turns:
            for lt in low_turns[:3]:
                gaps.append(f"Demonstrated less technical depth in {lt.topic_title} (Day {lt.day}), requiring deeper trade-off and failure mode analysis.")
        else:
            gaps.append("Could provide deeper details on production latency bounds and high concurrency error recovery.")

        # Next Steps (mapped back to actual curriculum.json days)
        next_steps = []
        if low_turns:
            for lt in low_turns[:2]:
                next_steps.append(f"Review Day {lt.day} — {lt.topic_title}, focusing on system design trade-offs and edge-case handling.")
        
        # Add default recommendations mapped to real curriculum days if needed
        default_recs = [
            "Review Day 10 — The Retrieval & Matching Engine, focusing on hybrid retrieval and result deduplication.",
            "Review Day 23 — Model Context Protocol (MCP), focusing on tool schema definitions and security boundaries.",
            "Review Day 28 — Docker & Kubernetes Deployment, focusing on containerization, ConfigMaps, and health probes."
        ]
        for rec in default_recs:
            if len(next_steps) < 3 and rec not in next_steps:
                next_steps.append(rec)

        # Concise Overall Summary
        high_topics_str = ", ".join([f"Day {t.day} ({t.topic_title})" for t in high_turns[:2]]) if high_turns else "foundational AI concepts"
        low_topics_str = ", ".join([f"Day {t.day}" for t in low_turns[:2]]) if low_turns else "production optimization"
        
        summary = (
            f"{session.candidate.member.name} demonstrated {tier.lower()} capability with strong performance in {high_topics_str}. "
            f"Showed less demonstrated depth in {low_topics_str}."
        )

        # Generate Mermaid Architecture Diagram for feedback report
        mermaid_diagram = (
            "graph TD\n"
            "    A[User Query] --> B[FastAPI Gateway]\n"
            "    B --> C{Query Router}\n"
            "    C -->|Vector Similarity| D[ChromaDB / Pinecone]\n"
            "    C -->|Structured SQL| E[SQLite Claims DB]\n"
            "    D --> F[RAG Context Formatter]\n"
            "    E --> F\n"
            "    F --> G[LangChain / ReAct Agent]\n"
            "    G --> H[MCP Tool Execution]\n"
            "    H --> I[LLM Response Generation]\n"
        )

        return FeedbackReport(
            session_id=session.session_id,
            candidate_id=session.candidate.member.id,
            candidate_name=session.candidate.member.name,
            job_role=session.candidate.member.jobRole,
            summary=summary,
            strengths=strengths,
            gaps=gaps,
            next=next_steps,
            overall_score=final_overall_score,
            technical_tier=tier,
            hiring_recommendation=hiring_rec,
            interview_confidence=confidence_level,
            questions_answered=len(turns),
            covered_days=list(set(session.covered_days)),
            category_scores=category_scores,
            eval_metrics=eval_metrics,
            areas_for_growth=gaps,
            actionable_recommendations=next_steps,
            architecture_diagram=mermaid_diagram,
            duration_minutes=round(len(turns) * 2.5, 1)
        )
