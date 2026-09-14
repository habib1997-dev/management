"""Unit tests for the ``serve_frontend`` SPA helper."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from student_management.main import serve_frontend


def _make_dist(tmp_path):
    """Create a minimal fake ``dist/`` tree and return its Path."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><div id='root'></div>")
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('ok')")
    (assets / "app.css").write_text("body{}")
    return dist


def test_spa_fallback_serves_index_for_unknown_routes(tmp_path, monkeypatch):
    dist = _make_dist(tmp_path)
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    serve_frontend(app)

    client = TestClient(app)

    # Unknown non-API path → SPA fallback (index.html)
    r = client.get("/any-page")
    assert r.status_code == 200
    assert "<div id='root'>" in r.text

    # Nested SPA path works too
    r = client.get("/students/abc123")
    assert r.status_code == 200
    assert "index.html" not in r.text  # we get the HTML body, not the filename

    # /health still returns JSON (registered before the catch-all)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_spa_fallback_does_not_shadow_api_404(tmp_path, monkeypatch):
    dist = _make_dist(tmp_path)
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    serve_frontend(app)

    client = TestClient(app)

    # Unknown /api/ path → normal 404 (not SPA fallback)
    r = client.get("/api/v1/nonexistent")
    assert r.status_code == 404


def test_spa_static_assets_are_served(tmp_path, monkeypatch):
    dist = _make_dist(tmp_path)
    app = FastAPI()

    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    serve_frontend(app)

    client = TestClient(app)

    r = client.get("/assets/app.js")
    assert r.status_code == 200
    assert "console.log('ok')" in r.text

    r = client.get("/assets/app.css")
    assert r.status_code == 200


def test_spa_skips_when_dist_missing(tmp_path, monkeypatch):
    missing = tmp_path / "no_such_dir"
    app = FastAPI()

    monkeypatch.setenv("FRONTEND_DIST", str(missing))
    serve_frontend(app)

    client = TestClient(app)

    # Without SPA middleware, unknown paths return 404
    r = client.get("/anything")
    assert r.status_code == 404
