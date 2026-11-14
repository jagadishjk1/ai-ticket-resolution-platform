"""
Metrics tracking for RAG service
"""
import threading
import time
from collections import Counter, defaultdict
from typing import Any, Dict
import statistics
class MetricsTracker:
    """Track performance and quality metrics for the RAG service"""
    def __init__(self):
        self._lock = threading.Lock()  # endpoints run in a thread pool
        self.queries = []
        self.response_times = []
        self.confidence_scores = []
        self.category_counts = defaultdict(int)
        self.error_count = 0
        self.success_count = 0
        self.feedback = []
    def record_feedback(self, ticket_id: str, feedback: str, helpful=None):
        """Store user feedback on a suggested resolution"""
        with self._lock:
            self.feedback.append(
                {
                    "ticket_id": ticket_id,
                    "feedback": feedback,
                    "helpful": helpful,
                    "timestamp": time.time(),
                }
            )
    def get_feedback_summary(self) -> Dict[str, Any]:
        rated = [f for f in self.feedback if f["helpful"] is not None]
        helpful = sum(1 for f in rated if f["helpful"])
        return {
            "total": len(self.feedback),
            "helpful": helpful,
            "not_helpful": len(rated) - helpful,
            "helpful_rate": helpful / len(rated) if rated else None,
        }
    def record_query(
        self,
        category: str,
        response_time: float,
        confidence: float,
        success: bool = True,
    ):
        """Record a query with its metrics"""
        with self._lock:
            self._record_query(category, response_time, confidence, success)

    def _record_query(self, category, response_time, confidence, success):
        self.queries.append(
            {
                "category": category,
                "response_time": response_time,
                "confidence": confidence,
                "success": success,
                "timestamp": time.time(),
            }
        )
        self.response_times.append(response_time)
        self.confidence_scores.append(confidence)
        self.category_counts[category] += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    def record_error(self, category: str = "unknown"):
        """Record a failed request"""
        with self._lock:
            self.error_count += 1
            self.category_counts[category] += 1
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        # Total requests = successful queries + failed requests
        total_queries = self.success_count + self.error_count
        if total_queries == 0:
            return {
                "total_queries": 0,
                "success_rate": 0,
                "avg_response_time": 0,
                "avg_confidence": 0,
                "category_distribution": {},
                "feedback": self.get_feedback_summary(),
            }
        return {
            "total_queries": total_queries,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (
                self.success_count / total_queries if total_queries > 0 else 0
            ),
            "response_times": {
                "avg": (
                    statistics.mean(self.response_times) if self.response_times else 0
                ),
                "min": min(self.response_times) if self.response_times else 0,
                "max": max(self.response_times) if self.response_times else 0,
                "median": (
                    statistics.median(self.response_times) if self.response_times else 0
                ),
            },
            "confidence_scores": {
                "avg": (
                    statistics.mean(self.confidence_scores)
                    if self.confidence_scores
                    else 0
                ),
                "min": min(self.confidence_scores) if self.confidence_scores else 0,
                "max": max(self.confidence_scores) if self.confidence_scores else 0,
            },
            "category_distribution": dict(self.category_counts),
            "feedback": self.get_feedback_summary(),
        }
    def get_realtime_stats(self, limit: int = 100) -> Dict[str, Any]:
        """Get real-time stats for the last N queries"""
        recent_queries = (
            self.queries[-limit:] if len(self.queries) > limit else self.queries
        )
        if not recent_queries:
            return {"recent_queries": 0, "avg_response_time": 0, "avg_confidence": 0}
        recent_response_times = [q["response_time"] for q in recent_queries]
        recent_confidences = [q["confidence"] for q in recent_queries]
        return {
            "recent_queries": len(recent_queries),
            "avg_response_time": (
                statistics.mean(recent_response_times) if recent_response_times else 0
            ),
            "avg_confidence": (
                statistics.mean(recent_confidences) if recent_confidences else 0
            ),
            "recent_categories": dict(Counter(q["category"] for q in recent_queries)),
        }
    def reset(self):
        """Reset all metrics"""
        self.queries = []
        self.response_times = []
        self.confidence_scores = []
        self.category_counts = defaultdict(int)
        self.error_count = 0
        self.success_count = 0
        self.feedback = []
# Global metrics tracker instance
metrics_tracker = MetricsTracker()
