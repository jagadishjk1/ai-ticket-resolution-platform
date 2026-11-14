"""Tests for retrieval quality and the resolution pipeline (offline, no AI)."""
import pytest

from rag_engine_tfidf import RAGEngine


@pytest.fixture(scope="module")
def engine():
    e = RAGEngine()
    assert e.is_ready()
    assert not e.has_ai_client(), "tests run without a Hugging Face token"
    return e


@pytest.mark.parametrize(
    "category, query, expected_phrase",
    [
        ("Hardware Request", "My laptop battery drains fast", "battery"),
        ("VPN Access", "VPN disconnects every few minutes when I work from home", "VPN keeps disconnecting"),
        ("Email Issues", "Outlook on my phone is not syncing new mail", "syncing"),
        ("Printer Issues", "paper stuck in printer", "paper jam"),
        ("Network Connectivity", "connected to wifi but no internet", "no internet"),
        ("System Crash", "blue screen keeps appearing", "blue screen"),
    ],
)
def test_top_match_is_relevant(engine, category, query, expected_phrase):
    results = engine.find_similar_tickets(query, category)
    assert results, f"no match for {query!r}"
    assert expected_phrase.lower() in results[0]["description"].lower()


@pytest.mark.parametrize("query", ["asdf", "hello how are you", "quantum flux capacitor on the moon"])
def test_unrelated_text_returns_no_match(engine, query):
    result = engine.suggest_resolution("Application Bug", "Low", query)
    assert result["method"] == "no-match"
    assert result["confidence"] == 0.0
    assert result["similar_tickets"] == []


def test_results_have_distinct_resolutions_and_valid_scores(engine):
    results = engine.find_similar_tickets("printer offline and cannot print", "Printer Issues")
    resolutions = [t["resolution"] for t in results]
    assert len(resolutions) == len(set(resolutions)), "same fix should not be repeated"
    assert all(0.0 <= t["similarity_score"] <= 1.0 for t in results)
    assert len(results) <= engine.top_k


def test_confidence_is_raw_similarity_of_best_match(engine):
    result = engine.suggest_resolution("Hardware Request", "Medium", "Need a second monitor for my workstation.")
    assert result["confidence"] == pytest.approx(result["similar_tickets"][0]["similarity_score"])
    assert result["confidence"] > 0.9  # exact text exists in the knowledge base


def test_retrieval_mode_response_shape(engine):
    result = engine.suggest_resolution("Password Reset", "High", "My account is locked after too many attempts")
    assert result["method"] == "retrieval"
    assert "Recommended resolution" in result["suggested_resolution"]
    assert "No similar tickets found" not in result["suggested_resolution"]
    assert set(result["timing"]) == {"search_time_ms", "generation_time_ms", "total_time_ms"}
    assert result["metadata"]["ai_generated"] is False


def test_category_breaks_ties_in_ranking(engine):
    # "login fails" appears in Password Reset tickets; the category should rank them first.
    results = engine.find_similar_tickets("login fails with an error", "Password Reset")
    assert results[0]["category"] == "Password Reset"


def test_ai_failure_falls_back_to_retrieval(engine, monkeypatch):
    class BrokenClient:
        def chat_completion(self, **kwargs):
            raise TimeoutError("model unavailable")

    monkeypatch.setattr(engine, "hf_client", BrokenClient())
    result = engine.suggest_resolution("VPN Access", "High", "Unable to connect to VPN from home network")
    assert result["method"] == "retrieval"
    assert "model unavailable" in result["metadata"]["ai_error"]


def test_ai_success_is_used_when_available(engine, monkeypatch):
    class FakeMessage:
        content = "1. Restart the VPN client.\n2. Escalate to network team if it persists."

    class FakeClient:
        def chat_completion(self, **kwargs):
            prompt = kwargs["messages"][0]["content"]
            assert "Similar resolved tickets" in prompt
            return type("R", (), {"choices": [type("C", (), {"message": FakeMessage()})()]})()

    monkeypatch.setattr(engine, "hf_client", FakeClient())
    result = engine.suggest_resolution("VPN Access", "High", "Unable to connect to VPN from home network")
    assert result["method"] == "ai-refined"
    assert result["suggested_resolution"].startswith("1. Restart the VPN client")
