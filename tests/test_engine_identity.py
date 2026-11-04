"""The trend ingest signs engine requests as the configured service identity."""

import pytest
from scion_sdk.ingest.engine import EngineSettings


@pytest.mark.spec("CONN-FAN-MANAGER-R004")
def test_trend_ingest_signs_as_the_configured_principal_and_audience(monkeypatch):
    monkeypatch.setenv("MEDULLA_ENDPOINT", "tls://engine.example:9100")
    monkeypatch.setenv("MEDULLA_AUTH_SECRET_REF", "env://ENGINE_SECRET")
    monkeypatch.setenv("MEDULLA_TENANT", "homelab")
    monkeypatch.setenv("MEDULLA_GRAPH", "__commons__")
    monkeypatch.setenv("MEDULLA_PRINCIPAL", "service:fan-manager")
    monkeypatch.setenv("MEDULLA_AUDIENCE", "agent-services")

    settings = EngineSettings.from_settings()

    assert settings is not None
    context = settings.verified_context()
    assert context["principal"] == "service:fan-manager"
    assert context["agent_id"] == "service:fan-manager"
    assert context["audience"] == "agent-services"
