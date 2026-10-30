"""The trend ingest signs engine requests as the configured service identity."""

import pytest
from scion_sdk.ingest.engine import EngineSettings


@pytest.mark.spec("CONN-FAN-MANAGER-R004")
def test_trend_ingest_signs_as_the_configured_principal_and_audience(monkeypatch):
    monkeypatch.setenv("EPISTEMIC_GRAPH_ENDPOINT", "tls://engine.example:9100")
    monkeypatch.setenv("EPISTEMIC_GRAPH_AUTH_SECRET_REF", "env://ENGINE_SECRET")
    monkeypatch.setenv("EPISTEMIC_GRAPH_TENANT", "homelab")
    monkeypatch.setenv("EPISTEMIC_GRAPH_GRAPH", "__commons__")
    monkeypatch.setenv("EPISTEMIC_GRAPH_PRINCIPAL", "service:fan-manager")
    monkeypatch.setenv("EPISTEMIC_GRAPH_AUDIENCE", "agent-services")

    settings = EngineSettings.from_settings()

    assert settings is not None
    context = settings.verified_context()
    assert context["principal"] == "service:fan-manager"
    assert context["agent_id"] == "service:fan-manager"
    assert context["audience"] == "agent-services"
