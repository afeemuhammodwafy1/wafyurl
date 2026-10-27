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
    assert any(rule.rule == "/shorten" and "POST" in rule.methods for rule in app.url_map.iter_rules())


def test_homepage_contains_shortener_and_removes_link_counter():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'id="shortener"' in page
    assert 'id="longUrl"' in page
    assert 'id="bulkToggleBtn"' in page
    assert 'links created on WafyURL' not in page
    assert 'Frequently asked' not in page


def test_legacy_shortener_get_redirects_to_home_section():
    app = create_app(TestConfig)
    response = app.test_client().get('/shorten')
    assert response.status_code == 301
    assert response.headers['Location'].endswith('/#shortener')


def test_faq_has_its_own_page_and_structured_data():
    app = create_app(TestConfig)
    response = app.test_client().get('/faq')
    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'Frequently asked' in page
    assert 'FAQPage' in page
    assert 'faq-page-item' in page
