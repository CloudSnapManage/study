import base64
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.license import LicenseManager
from backend.main import create_app


def encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode().rstrip('=')


def license_fixture(tmp_path: Path, expires_delta: timedelta = timedelta(days=30)):
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    payload = {
        'license_id': 'lic_test_001',
        'tier': 'pro',
        'customer': 'student@example.test',
        'issued_at': datetime.now(UTC).isoformat(),
        'expires_at': (datetime.now(UTC) + expires_delta).isoformat(),
    }
    payload_bytes = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode()
    token = f'{encode(payload_bytes)}.{encode(private.sign(payload_bytes))}'
    settings = Settings(project_root=tmp_path, license_public_key=encode(public))
    return settings, token


def test_valid_signed_license_activates_pro_and_tampering_falls_back_to_free(tmp_path: Path):
    settings, token = license_fixture(tmp_path)
    manager = LicenseManager(settings)
    status = manager.verify(token)
    assert status['tier'] == 'pro'
    assert status['valid'] is True
    assert status['customer'] == 's***@example.test'
    tampered = token[:-2] + ('AA' if token[-2:] != 'AA' else 'BB')
    assert manager.verify(tampered)['tier'] == 'free'
    assert manager.verify(tampered)['valid'] is False


def test_expired_license_has_grace_then_returns_to_free(tmp_path: Path):
    settings, token = license_fixture(tmp_path, timedelta(days=-2))
    status = LicenseManager(settings).verify(token)
    assert status['tier'] == 'pro'
    assert status['in_grace'] is True
    settings, token = license_fixture(tmp_path, timedelta(days=-10))
    status = LicenseManager(settings).verify(token)
    assert status['tier'] == 'free'
    assert status['code'] == 'license_expired'


def test_license_api_activates_and_pro_routes_enforce_entitlement(tmp_path: Path):
    settings, token = license_fixture(tmp_path)
    with TestClient(create_app(settings)) as client:
        free = client.get('/api/license/status').json()
        assert free['tier'] == 'free'
        blocked = client.post('/api/mock/generate', json={'subject': 'Physics', 'count': 5})
        assert blocked.status_code == 402
        assert blocked.json()['code'] == 'pro_required'
        activated = client.post('/api/license/activate', json={'token': token}).json()
        assert activated['tier'] == 'pro'
        assert client.post('/api/mock/generate', json={'subject': 'Physics', 'count': 5}).status_code == 200
