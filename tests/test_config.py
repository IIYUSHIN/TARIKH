import pytest

from app.config import Settings


def test_settings_derive_both_resource_domains_from_project_endpoint():
    s = Settings.from_env({
        "AZURE_AI_PROJECT_ENDPOINT": "https://tarikh-res.services.ai.azure.com/api/projects/tarikh-proj",
        "AZURE_AI_MODEL_DEPLOYMENT_NAME": "gpt-4.1",
    })
    assert s.services_base == "https://tarikh-res.services.ai.azure.com"
    assert s.cognitive_base == "https://tarikh-res.cognitiveservices.azure.com"
    assert s.model_deployment == "gpt-4.1"


def test_bad_mode_rejected():
    with pytest.raises(ValueError, match="TARIKH_MODE"):
        Settings.from_env({"TARIKH_MODE": "demo"})


def test_missing_endpoint_gives_empty_bases_not_a_crash():
    s = Settings.from_env({})
    assert s.services_base == "" and s.cognitive_base == ""


def test_other_two_content_understanding_deployments_default_to_their_model_names_and_can_be_overridden():
    from app.config import Settings
    assert Settings.from_env({}).cu_mini_deployment == "gpt-4.1-mini"
    assert Settings.from_env({}).cu_embedding_deployment == "text-embedding-3-large"
    s = Settings.from_env({"TARIKH_CU_MINI_DEPLOYMENT": "mini-x", "TARIKH_CU_EMBEDDING_DEPLOYMENT": "emb-x"})
    assert (s.cu_mini_deployment, s.cu_embedding_deployment) == ("mini-x", "emb-x")
