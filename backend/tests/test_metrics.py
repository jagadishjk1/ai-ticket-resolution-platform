"""Tests for the metrics tracker."""
from metrics import MetricsTracker


def test_success_rate_counts_errors():
    m = MetricsTracker()
    m.record_query("VPN Access", 10.0, 0.8)
    m.record_query("VPN Access", 20.0, 0.6)
    m.record_error("VPN Access")
    s = m.get_summary()
    assert s["total_queries"] == 3
    assert s["success_rate"] == 2 / 3
    assert s["response_times"]["avg"] == 15.0


def test_feedback_summary():
    m = MetricsTracker()
    m.record_feedback("T1", "worked", True)
    m.record_feedback("T2", "did not work", False)
    m.record_feedback("T3", "comment only")
    fb = m.get_summary()["feedback"]
    assert fb == {"total": 3, "helpful": 1, "not_helpful": 1, "helpful_rate": 0.5}


def test_realtime_stats_category_counts():
    m = MetricsTracker()
    for cat in ["A", "A", "B"]:
        m.record_query(cat, 5.0, 0.5)
    assert m.get_realtime_stats()["recent_categories"] == {"A": 2, "B": 1}
