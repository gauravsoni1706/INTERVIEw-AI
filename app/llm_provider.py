import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("InterviewAI.LLMProvider")

class LLMProvider:
    """
    Unified LLM Provider abstraction supporting:
    - Google Gemini (via google-genai or google.generativeai)
    - OpenAI (via openai package)
    - Anthropic Claude (via anthropic package)
    - Smart Fallback Engine (for zero-dependency offline operation)
    """

    def __init__(self, provider_type: Optional[str] = None):
        self.provider_type = provider_type or os.getenv("LLM_PROVIDER", "auto").lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    def generate_interview_turn(
        self,
        personality: str,
        candidate_summary: str,
        curriculum_context: str,
        interview_history: List[Dict[str, str]],
        difficulty: str,
        current_day: int,
        topic_title: str,
        is_follow_up: bool = False
    ) -> str:
        system_prompt = self._build_system_prompt(personality)
        
        prompt = (
            f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n"
            f"--- CANDIDATE CONTEXT ---\n{candidate_summary}\n\n"
            f"--- CURRICULUM CONTEXT (RAG Grounding for Day {current_day}: {topic_title}) ---\n{curriculum_context}\n\n"
            f"--- CURRENT STATE ---\n"
            f"Difficulty Level: {difficulty}\n"
            f"Is Follow-up Question: {is_follow_up}\n\n"
            f"--- INTERVIEW HISTORY ---\n"
        )
        for turn in interview_history[-6:]:
            prompt += f"Interviewer: {turn.get('question')}\n"
            if turn.get('answer'):
                prompt += f"Candidate: {turn.get('answer')}\n"
        
        prompt += "\nNow generate the next interview prompt. Be professional, direct, and technically probing."

        # Try Live LLM call if configured
        if self.provider_type in ["gemini", "auto"] and self.gemini_api_key:
            try:
                res = self._call_gemini(prompt)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back to Smart Engine.")

        if self.provider_type in ["openai", "auto"] and self.openai_api_key:
            try:
                res = self._call_openai(prompt)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Falling back to Smart Engine.")

        if self.provider_type in ["anthropic", "claude", "auto"] and self.anthropic_api_key:
            try:
                res = self._call_anthropic(prompt)
                if res:
                    return res
            except Exception as e:
                logger.warning(f"Anthropic API call failed: {e}. Falling back to Smart Engine.")

        # Fallback to smart template generator
        return self._smart_fallback_question(
            personality=personality,
            difficulty=difficulty,
            day=current_day,
            topic=topic_title,
            is_follow_up=is_follow_up,
            history=interview_history
        )

    def _build_system_prompt(self, personality: str) -> str:
        personas = {
            "Senior Engineer": "You are a Senior AI Engineer conducting a rigorous, practical technical interview for an Enterprise AI Engineering Cohort. Focus on implementation choices, code patterns, and failure modes.",
            "Staff Engineer": "You are a Staff AI Systems Architect. Focus on system design, trade-offs, scalability, latency, cost optimization, and multi-component orchestration.",
            "Principal Engineer": "You are a Principal AI Engineer. Focus on high-level architecture, fundamental trade-offs, security, eval benchmarks, and strategic technology choices.",
            "Friendly": "You are a supportive, encouraging Senior AI Tech Lead. Provide constructive framing while maintaining high technical rigor."
        }
        base = personas.get(personality, personas["Senior Engineer"])
        return f"{base} Do NOT expose internal scoring or JSON metadata. Stay in character."

    def _call_gemini(self, prompt: str) -> Optional[str]:
        try:
            from google import genai
            client = genai.Client(api_key=self.gemini_api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except ImportError:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                res = model.generate_content(prompt)
                return res.text
            except Exception as ex:
                logger.error(f"GenerativeAI error: {ex}")
                return None

    def _call_openai(self, prompt: str) -> Optional[str]:
        import openai
        client = openai.OpenAI(api_key=self.openai_api_key)
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return res.choices[0].message.content

    def _call_anthropic(self, prompt: str) -> Optional[str]:
        import anthropic
        client = anthropic.Anthropic(api_key=self.anthropic_api_key)
        res = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        return res.content[0].text

    def _smart_fallback_question(
        self,
        personality: str,
        difficulty: str,
        day: int,
        topic: str,
        is_follow_up: bool,
        history: List[Dict[str, str]]
    ) -> str:
        # High quality context-aware fallback when offline
        if is_follow_up:
            last_turn = history[-1] if history else {}
            last_ans = last_turn.get("answer", "")
            return f"Follow-up ({difficulty}): You mentioned '{last_ans[:40]}...'. Could you explain the exact trade-offs, latency implications, or potential edge-case failures of that approach in Day {day} ({topic})?"
        
        return f"Question (Day {day} - {topic} [{difficulty}]): How did you architect your implementation for {topic}? What specific tools or design patterns ensured system reliability?"
