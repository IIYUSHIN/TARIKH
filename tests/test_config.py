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
