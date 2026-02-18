"""Smoke tests for create_app()."""


def test_create_app_returns_fastapi():
    from openvibe_platform.app import create_app
    app = create_app(data_dir=":memory:")
    assert app is not None
    assert app.title == "OpenVibe Platform"


def test_app_has_api_routes():
    from openvibe_platform.app import create_app
    app = create_app(data_dir=":memory:")
    paths = {r.path for r in app.routes}
    assert "/api/v1/workspaces" in paths
    assert "/api/v1/deliverables" in paths
