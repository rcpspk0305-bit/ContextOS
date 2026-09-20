import pytest
from fastapi.testclient import TestClient
from contextos.api.app import app
from contextos.analytics.pricing import get_model_pricing, calculate_token_costs, DEFAULT_PRICING
from contextos.analytics.engine import analytics_engine
from contextos.storage.db import db
from contextos.models.analytics import TokenRecord

client = TestClient(app)

def test_pricing_model_lookups():
    # Anthropic
    assert get_model_pricing("claude-3-5-sonnet") == (3.0, 15.0)
    assert get_model_pricing("claude-3-haiku") == (0.25, 1.25)
    assert get_model_pricing("claude-3-opus") == (15.0, 75.0)

    # OpenAI
    assert get_model_pricing("gpt-4o") == (2.5, 10.0)
    assert get_model_pricing("gpt-4o-mini") == (0.15, 0.6)
    assert get_model_pricing("o1") == (15.0, 60.0)

    # Google
    assert get_model_pricing("gemini-1.5-pro") == (1.25, 5.0)
    assert get_model_pricing("gemini-1.5-flash") == (0.075, 0.3)

    # Local / Free
    assert get_model_pricing("llama3") == (0.0, 0.0)
    assert get_model_pricing("deepseek-coder") == (0.0, 0.0)

    # Unknown fallback
    assert get_model_pricing("unknown-model-xyz") == DEFAULT_PRICING

def test_calculate_token_costs():
    # gpt-4o: $2.50/M input, $10.00/M output
    # candidate=100_000 -> 100_000 * $2.50/1M = $0.25
    # output=10_000 -> 10_000 * $10.00/1M = $0.10
    # cost_without = $0.25 + $0.10 = $0.35
    # selected=10_000 -> 10_000 * $2.50/1M = $0.025
    # cost_with = $0.025 + $0.10 = $0.125
    # cost_saved = $0.35 - $0.125 = $0.225
    cost_without, cost_with, cost_saved = calculate_token_costs(
        model="gpt-4o",
        candidate_tokens=100_000,
        selected_tokens=10_000,
        output_tokens=10_000,
        cache_hit_tokens=0,
    )
    assert round(cost_without, 4) == 0.35
    assert round(cost_with, 4) == 0.125
    assert round(cost_saved, 4) == 0.225

    # Test with cache hits
    # selected=10_000 with 4_000 cache hits
    # uncached=6_000 -> 6_000 * $2.50/1M = $0.015
    # cached=4_000 -> 4_000 * $1.25/1M = $0.005
    # output=10_000 -> $0.10
    # cost_with = $0.015 + $0.005 + $0.10 = $0.12
    _, cost_with_cache, cost_saved_cache = calculate_token_costs(
        model="gpt-4o",
        candidate_tokens=100_000,
        selected_tokens=10_000,
        output_tokens=10_000,
        cache_hit_tokens=4_000,
    )
    assert round(cost_with_cache, 4) == 0.12
    assert round(cost_saved_cache, 4) == 0.23

def test_record_token_event_and_persistence():
    record = analytics_engine.record_event(
        project_id="test_project",
        session_id="test_sess_01",
        agent_id="agent_reviewer_01",
        task_id="Review pull request",
        provider="Anthropic",
        model="claude-3-5-sonnet",
        candidate_tokens=50_000,
        selected_tokens=8_000,
        output_tokens=1_200,
        cache_hit_tokens=2_000,
        estimated=False,  # Explicitly provider-reported
        metadata={"commit": "abc1234"},
    )

    assert record.tokens_avoided == 42_000
    assert record.bytes_avoided == 42_000 * 4
    assert record.estimated is False
    assert record.cost_saved_usd > 0

    # Retrieve from DB
    records = db.list_token_records(project_id="test_project", session_id="test_sess_01")
    assert any(r.id == record.id for r in records)
    matched = next(r for r in records if r.id == record.id)
    assert matched.estimated is False
    assert matched.tokens_avoided == 42_000

def test_analytics_summary_and_breakdowns():
    summary = analytics_engine.get_summary(project_id="test_project")
    assert summary.total_events >= 1
    assert summary.total_candidate_tokens >= 50_000
    assert summary.total_selected_tokens >= 8_000
    assert summary.total_tokens_avoided >= 42_000
    assert summary.overall_reduction_ratio > 0.0
    assert summary.cost_saved_usd > 0.0

    # Breakdown by provider
    providers = analytics_engine.get_breakdown(dimension="provider", project_id="test_project")
    assert len(providers) > 0
    assert any(p.key == "Anthropic" for p in providers)

    # Breakdown by model
    models = analytics_engine.get_breakdown(dimension="model", project_id="test_project")
    assert any("claude" in m.key.lower() for m in models)

    # Comparison series
    comp = analytics_engine.get_comparison(project_id="test_project", limit=5)
    assert len(comp.data_points) >= 1
    assert comp.cumulative_tokens_avoided >= 42_000

def test_analytics_api_endpoints():
    # 1. Summary
    res = client.get("/api/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_candidate_tokens" in data
    assert "total_selected_tokens" in data
    assert "total_tokens_avoided" in data
    assert "overall_reduction_ratio" in data
    assert "cost_saved_usd" in data
    assert "bytes_not_transmitted" in data

    # 2. Breakdown
    res_b = client.get("/api/analytics/breakdown?by=provider")
    assert res_b.status_code == 200
    b_data = res_b.json()
    assert isinstance(b_data, list)

    res_m = client.get("/api/analytics/breakdown?by=model")
    assert res_m.status_code == 200
    assert isinstance(res_m.json(), list)

    # 3. Invalid breakdown
    res_err = client.get("/api/analytics/breakdown?by=invalid_dim")
    assert res_err.status_code == 422

    # 4. Comparison
    res_c = client.get("/api/analytics/comparison?limit=10")
    assert res_c.status_code == 200
    c_data = res_c.json()
    assert "data_points" in c_data
    assert "cumulative_tokens_avoided" in c_data

    # 5. Record Token Event
    payload = {
        "project_id": "api_test_project",
        "session_id": "api_session",
        "agent_id": "agent_api_01",
        "task_id": "Unit test generation",
        "provider": "Google",
        "model": "gemini-1.5-pro",
        "candidate_tokens": 80_000,
        "selected_tokens": 12_000,
        "output_tokens": 2_500,
        "cache_hit_tokens": 0,
        "estimated": True,
        "metadata": {"test": True},
    }
    res_post = client.post("/api/analytics/record", json=payload)
    assert res_post.status_code == 200
    rec_data = res_post.json()
    assert rec_data["tokens_avoided"] == 68_000
    assert rec_data["bytes_avoided"] == 68_000 * 4
    assert rec_data["cost_saved_usd"] > 0
    assert rec_data["estimated"] is True
