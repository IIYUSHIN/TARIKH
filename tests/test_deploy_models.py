from tools.deploy_models import plan_deployments, WANTED

LISTED = [
    {"name": "gpt-4.1", "format": "OpenAI", "version": "2025-04-14", "skus": [{"name": "Standard", "capacity": {"default": 30}}, {"name": "GlobalStandard", "capacity": {"default": 1000}}]},
    {"name": "gpt-4.1", "format": "OpenAI", "version": "2024-01-01", "skus": [{"name": "GlobalStandard", "capacity": {"default": 10}}]},
    {"name": "gpt-4.1-mini", "format": "OpenAI", "version": "2025-04-14", "skus": [{"name": "GlobalStandard", "capacity": {"default": 20}}]},
    {"name": "text-embedding-3-large", "format": "OpenAI", "version": "1", "skus": [{"name": "GlobalStandard", "capacity": {"default": 120}}]},
    {"name": "gpt-4o", "format": "OpenAI", "version": "2024-11-20", "skus": [{"name": "GlobalStandard", "capacity": {"default": 50}}]},
]


def test_plan_picks_newest_version_and_global_standard_with_modest_capacity():
    plan = {p["deployment"]: p for p in plan_deployments(LISTED)}
    assert set(plan) == set(WANTED) == {"gpt-4.1", "gpt-4.1-mini", "text-embedding-3-large"}
    assert plan["gpt-4.1"]["version"] == "2025-04-14" and plan["gpt-4.1"]["sku"] == "GlobalStandard"
    assert plan["gpt-4.1"]["capacity"] == 50      # capped so a student quota is not exhausted by one model
    assert plan["gpt-4.1-mini"]["capacity"] == 20  # never above the model's own default


def test_plan_names_a_missing_model_instead_of_skipping_it():
    import pytest
    with pytest.raises(LookupError, match="gpt-4.1-mini"):
        plan_deployments([m for m in LISTED if m["name"] != "gpt-4.1-mini"])
