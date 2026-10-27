"""Basic smoke tests; run with pytest after installing requirements."""
from app import create_app


class TestConfig:
    SECRET_KEY = "test-only-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PUBLIC_BASE_URL = "http://localhost"
    TESTING = True


def test_public_pages_and_security_headers():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_seo_pages_are_registered():
    app = create_app(TestConfig)
    paths = {rule.rule for rule in app.url_map.iter_rules()}
    assert "/url-shortener" in paths
    assert "/faq" in paths
    assert "/sitemap.xml" in paths
