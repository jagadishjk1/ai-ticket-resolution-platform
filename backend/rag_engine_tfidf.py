"""
RAG Engine - TF-IDF retrieval + optional LLM generation.

1. Retrieve: find past resolved tickets similar to the new one (TF-IDF + cosine).
2. Augment:  put the best matching resolutions into a prompt.
3. Generate: ask a Hugging Face LLM to write step-by-step guidance.

If no Hugging Face token is configured (or the AI call fails), the engine
falls back to the best retrieved resolution, so the app always works offline.
"""
import logging
import os
import time
from typing import Dict, List, Optional

from sklearn.metrics.pairwise import cosine_similarity

from knowledge_base import build_index, load_tickets, ticket_text
from metrics import metrics_tracker

logger = logging.getLogger(__name__)

try:
    from huggingface_hub import InferenceClient

    HUGGINGFACE_AVAILABLE = True
except ImportError:  # the app still works without it (retrieval-only mode)
    InferenceClient = None
    HUGGINGFACE_AVAILABLE = False

DEFAULT_MODEL = "Qwen/Qwen2.5-7B-Instruct"
# Ranking bonus when the stored ticket has the same category as the request.
# Used only to order results, never added to the reported similarity score.
CATEGORY_BONUS = 0.10


class RAGEngine:
    """Retrieval-Augmented Generation engine for IT ticket resolutions."""

    def __init__(self, dataset_path: Optional[str] = None):
        self.dataset_path = dataset_path
        self.tickets: Optional[List[Dict]] = None
        self.vectorizer = None
        self.tfidf_matrix = None
        self.loaded_from = None
        self.hf_client = None
        self.ai_provider = "none"

        self.top_k = int(os.getenv("TOP_K_SIMILAR", "5"))
        self.min_similarity = float(os.getenv("MIN_SIMILARITY", "0.2"))
        self.model = os.getenv("HF_MODEL", DEFAULT_MODEL)
        self.ai_timeout = float(os.getenv("AI_TIMEOUT_SECONDS", "20"))

        self._init_huggingface_client()
        self._load_knowledge_base()

    # ------------------------------------------------------------------ setup
    def _init_huggingface_client(self) -> bool:
        """Enable AI generation only when the library and an API token exist."""
        token = os.getenv("HUGGINGFACE_API_TOKEN", "").strip()
        if not HUGGINGFACE_AVAILABLE:
            logger.warning("huggingface_hub not installed - running in retrieval-only mode")
            return False
        if not token:
            logger.info("HUGGINGFACE_API_TOKEN not set - running in retrieval-only mode")
            return False
        try:
            self.hf_client = InferenceClient(model=self.model, token=token, timeout=self.ai_timeout)
            self.ai_provider = "huggingface"
            logger.info("Hugging Face AI enabled with model %s", self.model)
            return True
        except Exception as e:  # pragma: no cover - depends on network/library
            logger.error("Failed to initialise Hugging Face client: %s", e)
            self.hf_client = None
            return False

    def _load_knowledge_base(self):
        """Load the dataset and build the TF-IDF index in memory."""
        tickets, path = load_tickets(self.dataset_path)
        vectorizer, matrix = build_index(tickets)
        # Assign together so the engine is never half-loaded.
        self.tickets, self.vectorizer, self.tfidf_matrix = tickets, vectorizer, matrix
        self.loaded_from = path
        logger.info("Knowledge base ready: %d tickets, matrix %s", len(tickets), matrix.shape)

    def has_ai_client(self) -> bool:
        return self.hf_client is not None

    # -------------------------------------------------------------- retrieval
    def find_similar_tickets(self, description: str, category: str = "", k: Optional[int] = None) -> List[Dict]:
        """Return up to k similar resolved tickets, one per distinct resolution."""
        if not self.is_ready():
            raise RuntimeError("RAG engine not ready. Knowledge base not loaded.")
        k = k or self.top_k
        query_vec = self.vectorizer.transform([ticket_text(category, description)])
        scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        candidates = []
        for idx, score in enumerate(scores):
            score = float(score)
            if score < self.min_similarity:
                continue
            ticket = self.tickets[idx]
            same_category = bool(category) and ticket["category"].lower() == category.lower()
            rank = score + (CATEGORY_BONUS if same_category else 0.0)
            candidates.append((rank, score, idx))
        candidates.sort(reverse=True)

        results, seen_resolutions = [], set()
        for _, score, idx in candidates:
            ticket = self.tickets[idx]
            key = ticket["resolution"].lower()
            if key in seen_resolutions:  # same fix already shown - keep results varied
                continue
            seen_resolutions.add(key)
            results.append({**ticket, "similarity_score": round(score, 4)})
            if len(results) >= k:
                break
        return results

    # ------------------------------------------------------------- generation
    def _call_ai(self, prompt: str, max_tokens: int) -> str:
        response = self.hf_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ValueError("Empty response from AI model")
        return text

    @staticmethod
    def _build_rag_prompt(category: str, priority: str, description: str, similar: List[Dict]) -> str:
        references = "\n".join(
            f"{i}. ({t['similarity_score']:.0%} match) Issue: {t['description']} -> Resolution: {t['resolution']}"
            for i, t in enumerate(similar[:3], 1)
        )
        return f"""You are a professional IT support specialist.
Write a resolution for the new ticket below, using the resolutions of similar past tickets as reference.

New ticket:
- Category: {category}
- Priority: {priority}
- Issue: {description}

Similar resolved tickets:
{references}

Instructions:
- Give 4 to 7 numbered, specific, actionable steps.
- Follow the approach of the most relevant past resolution.
- End with one line saying when to escalate.
- Plain text only, no preamble."""

    @staticmethod
    def _build_fallback_prompt(category: str, priority: str, description: str) -> str:
        return f"""You are a professional IT support specialist.
No similar past ticket exists for this issue. Write general troubleshooting guidance.

Ticket:
- Category: {category}
- Priority: {priority}
- Issue: {description}

Instructions:
- Give 4 to 7 numbered, specific, actionable steps.
- End with one line saying when to escalate.
- Plain text only, no preamble."""

    @staticmethod
    def _template_resolution(similar: List[Dict]) -> str:
        best = similar[0]
        lines = [
            f"Recommended resolution (from ticket {best['ticket_id']}, {best['similarity_score']:.0%} match):",
            best["resolution"],
        ]
        others = similar[1:3]
        if others:
            lines += ["", "Other resolutions that worked for similar tickets:"]
            lines += [f"- {t['resolution']} ({t['ticket_id']}, {t['similarity_score']:.0%} match)" for t in others]
        lines += ["", "If the issue persists after these steps, escalate to Level 2 support."]
        return "\n".join(lines)

    @staticmethod
    def _no_match_resolution(category: str, priority: str) -> str:
        return (
            "No similar resolved tickets were found in the knowledge base.\n\n"
            "Suggested next steps:\n"
            "1. Restart the affected application or device and note any error message.\n"
            "2. Check network connectivity and whether other users are affected.\n"
            "3. Take screenshots of the error and note when the issue started.\n"
            f"4. Assign the ticket to the {category} support queue (priority: {priority}) for manual review.\n\n"
            "Tip: configure a Hugging Face API token to get AI-generated guidance for new issue types."
        )

    def suggest_resolution(self, category: str, priority: str, description: str) -> Dict:
        """Full RAG pipeline: retrieve similar tickets, then generate a resolution."""
        total_start = time.perf_counter()
        similar = self.find_similar_tickets(description, category)
        search_ms = (time.perf_counter() - total_start) * 1000

        gen_start = time.perf_counter()
        ai_error = None
        if similar:
            confidence = similar[0]["similarity_score"]
            if self.has_ai_client():
                try:
                    resolution = self._call_ai(self._build_rag_prompt(category, priority, description, similar), 450)
                    method, model = "ai-refined", self.model
                except Exception as e:
                    logger.error("AI generation failed, using retrieved resolution: %s", e)
                    ai_error = str(e)
                    resolution, method, model = self._template_resolution(similar), "retrieval", "template"
            else:
                resolution, method, model = self._template_resolution(similar), "retrieval", "template"
        else:
            confidence = 0.0
            resolution, method, model = self._no_match_resolution(category, priority), "no-match", "none"
            if self.has_ai_client():
                try:
                    resolution = self._call_ai(self._build_fallback_prompt(category, priority, description), 600)
                    method, model = "ai-fallback", self.model
                except Exception as e:
                    logger.error("AI fallback failed: %s", e)
                    ai_error = str(e)
        generation_ms = (time.perf_counter() - gen_start) * 1000
        total_ms = (time.perf_counter() - total_start) * 1000

        metrics_tracker.record_query(category=category, response_time=total_ms, confidence=confidence, success=True)
        logger.info(
            "Resolution: method=%s confidence=%.2f matches=%d search=%.1fms generation=%.1fms",
            method, confidence, len(similar), search_ms, generation_ms,
        )

        metadata = {
            "model": model,
            "ai_provider": self.ai_provider if method.startswith("ai") else "none",
            "num_similar_tickets": len(similar),
            "ai_generated": method.startswith("ai"),
            "knowledge_base_size": len(self.tickets),
        }
        if ai_error:
            metadata["ai_error"] = ai_error

        return {
            "suggested_resolution": resolution,
            "confidence": round(float(confidence), 4),
            "similar_tickets": [
                {
                    "ticket_id": t["ticket_id"],
                    "category": t["category"],
                    "description": t["description"][:200],
                    "resolution": t["resolution"][:300],
                    "priority": t["priority"],
                    "similarity_score": t["similarity_score"],
                }
                for t in similar
            ],
            "method": method,
            "timing": {
                "search_time_ms": round(search_ms, 2),
                "generation_time_ms": round(generation_ms, 2),
                "total_time_ms": round(total_ms, 2),
            },
            "metadata": metadata,
        }

    # ------------------------------------------------------------------ info
    def is_ready(self) -> bool:
        return self.tickets is not None and self.vectorizer is not None and self.tfidf_matrix is not None

    def get_knowledge_base_size(self) -> int:
        return len(self.tickets) if self.tickets else 0

    def get_top_categories(self, limit: int = 10) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for t in self.tickets or []:
            counts[t["category"]] = counts.get(t["category"], 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:limit])

    def get_categories(self) -> List[str]:
        return sorted({t["category"] for t in self.tickets or []})

    def reload_knowledge_base(self):
        """Re-read the dataset (e.g. after it was edited). Keeps the old index if loading fails."""
        logger.info("Reloading knowledge base...")
        self._load_knowledge_base()
