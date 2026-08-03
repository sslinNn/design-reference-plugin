from unittest.mock import Mock, patch

import pytest

from mcp_server import get_design_system, list_references, settings


@pytest.fixture(autouse=True)
def _api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "test-key-123")


@patch("mcp_server.requests.get")
def test_list_references_calls_backend_and_returns_json(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: [{"id": "stripe-header", "block_type": "header"}],
    )

    result = list_references(block_type="header")

    assert result == [{"id": "stripe-header", "block_type": "header"}]
    mock_get.assert_called_once_with(
        "http://localhost:8000/references",
        params={"block_type": "header"},
        headers={"X-API-Key": "test-key-123"},
        timeout=10,
    )


@patch("mcp_server.requests.get")
def test_get_design_system_groups_response(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"header": {"reference": "stripe-header", "tokens": {}, "skeleton": {}}},
    )

    result = get_design_system(["stripe-header"])

    assert "header" in result
    mock_get.assert_called_once_with(
        "http://localhost:8000/design-system",
        params={"ref_ids": "stripe-header"},
        headers={"X-API-Key": "test-key-123"},
        timeout=10,
    )


@patch("mcp_server.requests.get")
def test_get_design_system_raises_on_404(mock_get):
    mock_get.return_value = Mock(
        status_code=404,
        json=lambda: {"detail": "Unknown reference ids: ['nope']"},
    )

    with pytest.raises(ValueError, match="Unknown reference ids"):
        get_design_system(["nope"])


@patch("mcp_server.requests.get")
def test_get_design_system_raises_clear_error_on_401(mock_get):
    mock_get.return_value = Mock(status_code=401, json=lambda: {"detail": "unauthorized"})

    with pytest.raises(ValueError, match="invalid or has been revoked"):
        get_design_system(["stripe-header"])


@patch("mcp_server.requests.get")
def test_list_references_raises_clear_error_on_401(mock_get):
    mock_get.return_value = Mock(status_code=401, json=lambda: {"detail": "unauthorized"})

    with pytest.raises(ValueError, match="invalid or has been revoked"):
        list_references()


def test_list_references_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "api_key", None)

    with pytest.raises(ValueError, match="No API key set"):
        list_references()
