import stat
from pathlib import Path

from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


def client(tmp_path: Path) -> TestClient:
    frontend = tmp_path / 'frontend'
    frontend.mkdir(exist_ok=True)
    (frontend / 'index.html').write_text('<title>Cognito</title>')
    return TestClient(create_app(Settings(project_root=tmp_path, frontend_dir=frontend)))


def test_security_headers_and_untrusted_hosts(tmp_path: Path):
    with client(tmp_path) as app:
        response = app.get('/api/health')
        assert response.headers['content-security-policy'].startswith("default-src 'self'")
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert response.headers['x-frame-options'] == 'DENY'
        assert response.headers['referrer-policy'] == 'no-referrer'
        rejected = app.get('/api/health', headers={'host': 'attacker.example'})
        assert rejected.status_code == 400


def test_rate_limit_returns_structured_json(tmp_path: Path):
    settings = Settings(project_root=tmp_path, frontend_dir=tmp_path / 'frontend', rate_limit_requests=2, rate_limit_window_seconds=60)
    settings.frontend_dir.mkdir()
    (settings.frontend_dir / 'index.html').write_text('<title>Cognito</title>')
    with TestClient(create_app(settings)) as app:
        assert app.get('/api/search', params={'q': 'flux'}).status_code == 200
        assert app.get('/api/search', params={'q': 'field'}).status_code == 200
        response = app.get('/api/search', params={'q': 'charge'})
        assert response.status_code == 429
        assert response.json()['code'] == 'rate_limited'
        assert 'retry-after' in response.headers


def test_oversized_inputs_are_rejected(tmp_path: Path):
    with client(tmp_path) as app:
        response = app.post('/api/chat/stream', json={'message': 'x' * 50001})
        assert response.status_code == 422
        response = app.get('/api/search', params={'q': 'x' * 501})
        assert response.status_code == 422


def test_cross_site_mutations_are_rejected(tmp_path: Path):
    with client(tmp_path) as app:
        response = app.post(
            '/api/ingest/scan',
            headers={'origin': 'https://attacker.example', 'sec-fetch-site': 'cross-site'},
        )
        assert response.status_code == 403
        assert response.json()['code'] == 'cross_site_request'


def test_configured_api_token_is_required(tmp_path: Path):
    frontend = tmp_path / 'frontend'
    frontend.mkdir()
    (frontend / 'index.html').write_text('<title>Cognito</title>')
    settings = Settings(project_root=tmp_path, frontend_dir=frontend, api_token='launch-secret')
    with TestClient(create_app(settings)) as app:
        denied = app.get('/api/search', params={'q': 'flux'})
        assert denied.status_code == 401
        assert denied.json()['code'] == 'api_token_required'
        allowed = app.get(
            '/api/search',
            params={'q': 'flux'},
            headers={'x-cognito-token': 'launch-secret'},
        )
        assert allowed.status_code == 200


def test_profile_test_rejects_private_network_ssrf(tmp_path: Path):
    with client(tmp_path) as app:
        response = app.post('/api/profiles/test', json={'base_url': 'http://169.254.169.254'})
        assert response.status_code == 422
        assert response.json()['code'] == 'invalid_request'


def test_runtime_data_permissions_are_owner_only(tmp_path: Path):
    settings = Settings(project_root=tmp_path)
    with TestClient(create_app(settings)):
        assert stat.S_IMODE(settings.data_dir.stat().st_mode) == 0o700
        assert stat.S_IMODE(settings.database_path.stat().st_mode) == 0o600
