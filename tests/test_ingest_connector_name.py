"""The trend ingest binds to the connector name the engine has an imported pack for."""

import pytest

import fan_manager.kg_ingest as kgi


@pytest.mark.spec("CONN-FAN-MANAGER-R005")
def test_ingest_binding_uses_the_onboarded_connector_name():
    assert kgi._BINDING.connector == "fan-manager-mcp"
    assert kgi._BINDING.stream == "fan"
