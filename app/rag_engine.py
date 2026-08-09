import re
import math
from typing import List, Dict, Any, Optional
from app.models import CurriculumData, CurriculumDay

class RAGCurriculumEngine:
    """
    RAG Retriever over the 31-Day Enterprise AI Cohort Curriculum.
    Provides semantic keyword and vector-like similarity search over curriculum objectives,
    tools, topics, and modules.
    """

    def __init__(self, curriculum_data: CurriculumData):
        self.curriculum = curriculum_data
        self.documents: List[Dict[str, Any]] = []
        self._build_index()

    def _build_index(self):
        for day_item in self.curriculum.days:
            doc_text = (
                f"Day {day_item.day}: {day_item.title}. "
                f"Type: {day_item.type}. "
                f"Tools: {', '.join(day_item.tools)}. "
                f"Objectives: {' '.join(day_item.objectives)}"
            )
            tokens = self._tokenize(doc_text)
            self.documents.append({
                "day": day_item.day,
                "title": day_item.title,
                "type": day_item.type,
                "tools": day_item.tools,
                "objectives": day_item.objectives,
                "full_text": doc_text,
                "tokens": set(tokens)
            })

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        return [w for w in cleaned.split() if len(w) > 2]

    def search_curriculum(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves the top_k most relevant curriculum days matching a candidate query or answer.
        """
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return self.documents[:top_k]

        scored_docs = []
        for doc in self.documents:
            # Calculate Jaccard similarity & keyword overlap
            intersection = query_tokens.intersection(doc["tokens"])
            score = len(intersection) / max(len(query_tokens.union(doc["tokens"])), 1)
            
            # Boost score if query mentions day number explicitly
            day_match = re.search(r'\bday\s*(\d+)\b', query.lower())
            if day_match and int(day_match.group(1)) == doc["day"]:
                score += 2.0

            scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]

    def get_day_context(self, day_num: int) -> str:
        """
        Formats precise grounding context for a given curriculum day.
        """
        for doc in self.documents:
            if doc["day"] == day_num:
                return (
                    f"Day {doc['day']}: {doc['title']}\n"
                    f"Category: {doc['type']}\n"
                    f"Key Tools: {', '.join(doc['tools'])}\n"
                    f"Core Objectives:\n- " + "\n- ".join(doc['objectives'])
                )
        return f"Day {day_num} Curriculum Context"
