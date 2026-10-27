from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_root_serves_frontend_html():
    """Verify that root / returns 200 with text/html and includes the root container."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers.get("content-type", "")
    assert '<div id="root"></div>' in res.text


def test_spa_client_side_routing_fallback():
    """Verify that client-side SPA routes (e.g. /applications) return index.html for React Router."""
    spa_routes = ["/applications", "/verification-center", "/document-review", "/reports", "/settings"]
    for route in spa_routes:
        res = client.get(route)
        assert res.status_code == 200
        assert "text/html" in res.headers.get("content-type", "")
        assert '<div id="root"></div>' in res.text


def test_api_routes_not_intercepted_by_spa_fallback():
    """Verify that unhandled API routes return 404 JSON, NOT index.html."""
    res = client.get("/api/unknown_route_xyz")
    assert res.status_code == 404
    assert "application/json" in res.headers.get("content-type", "")
    assert "API route not found" in res.json().get("detail", "")


def test_static_assets_serving():
    """Verify static assets are properly served with correct MIME types."""
    res_css = client.get("/assets/index-DFgmm7es.css")
    assert res_css.status_code == 200
    assert "text/css" in res_css.headers.get("content-type", "")

    res_js = client.get("/assets/index-CC7bS7VL.js")
    assert res_js.status_code == 200
    assert any(m in res_js.headers.get("content-type", "") for m in ["javascript", "text/plain"])


def test_api_health_and_docs_preserved():
    """Verify /api/health and /docs endpoints remain fully operational."""
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_docs = client.get("/docs")
    assert res_docs.status_code == 200
