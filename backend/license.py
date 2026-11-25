"""Provider-neutral signed offline license verification and entitlements."""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .config import Settings
from .database import connect_db

FREE_FEATURES = {
    "scan", "search", "sprint", "radar", "vault", "local_chat", "pdf_verifier",
}
PRO_FEATURES = FREE_FEATURES | {
    "obsidian_sync", "mock_exam", "solution_checker", "custom_providers",
    "agent_tools", "formula_flashcards", "exports",
}


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _mask_customer(value: str) -> str:
    if "@" in value:
        local, domain = value.split("@", 1)
        return f"{local[:1]}***@{domain}"
    return f"{value[:3]}***" if value else ""


class LicenseManager:
    def __init__(self, settings: Settings):
        self.settings = settings

    def free_status(self, code: str = "free") -> dict:
        return {
            "tier": "free", "valid": code == "free", "in_grace": False,
            "code": code, "features": sorted(FREE_FEATURES),
            "checkout_url": self.settings.checkout_url,
        }

    def verify(self, token: str | None, now: datetime | None = None) -> dict:
        if not token:
            return self.free_status()
        if not self.settings.license_public_key:
            return self.free_status("license_key_unconfigured")
        try:
            payload_part, signature_part = token.strip().split(".", 1)
            payload_bytes = _decode(payload_part)
            public_key = Ed25519PublicKey.from_public_bytes(_decode(self.settings.license_public_key))
            public_key.verify(_decode(signature_part), payload_bytes)
            payload = json.loads(payload_bytes)
            if payload.get("tier") != "pro":
                return self.free_status("license_tier_invalid")
            current = now or datetime.now(UTC)
            expires = datetime.fromisoformat(payload["expires_at"])
            in_grace = expires < current <= expires + timedelta(days=7)
            if current > expires + timedelta(days=7):
                return self.free_status("license_expired")
            return {
                "tier": "pro", "valid": True, "in_grace": in_grace,
                "code": "license_grace" if in_grace else "license_active",
                "license_id": payload.get("license_id"),
                "customer": _mask_customer(str(payload.get("customer", ""))),
                "expires_at": expires.isoformat(),
                "features": sorted(PRO_FEATURES | set(payload.get("features", []))),
                "checkout_url": self.settings.checkout_url,
            }
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, InvalidSignature):
            return self.free_status("license_invalid")

    def stored_token(self) -> str | None:
        with connect_db(self.settings) as db:
            row = db.execute("SELECT value FROM settings WHERE key='license_token'").fetchone()
        return row[0] if row else None

    def status(self) -> dict:
        return self.verify(self.stored_token())

    def activate(self, token: str) -> dict:
        status = self.verify(token)
        if status["tier"] != "pro":
            raise ValueError("License token is invalid or expired")
        with connect_db(self.settings) as db:
            db.execute("INSERT INTO settings(key,value) VALUES('license_token',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (token.strip(),))
        return status

    def deactivate(self) -> dict:
        with connect_db(self.settings) as db:
            db.execute("DELETE FROM settings WHERE key='license_token'")
        return self.free_status()

    def has(self, feature: str) -> bool:
        return feature in set(self.status()["features"])
