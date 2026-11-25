"""Filesystem and outbound-network containment helpers."""
import ipaddress
import socket
from pathlib import Path
from urllib.parse import urlparse


class PathSandboxError(ValueError):
    """Raised when a requested path escapes its configured root."""


def safe_resolve(root: Path | str, target: Path | str) -> Path:
    allowed_root = Path(root).expanduser().resolve()
    candidate = Path(target).expanduser()
    if not candidate.is_absolute():
        candidate = allowed_root / candidate
    resolved = candidate.resolve()
    if not resolved.is_relative_to(allowed_root):
        raise PathSandboxError("Path is outside the allowed root")
    return resolved


def validate_provider_url(value: str) -> str:
    """Allow HTTPS providers and deliberate loopback HTTP endpoints only."""
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Provider URL must use HTTP or HTTPS")
    if parsed.username or parsed.password:
        raise ValueError("Provider URL must not contain credentials")
    try:
        addresses = {
            ipaddress.ip_address(item[4][0])
            for item in socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        }
    except socket.gaierror as exc:
        raise ValueError("Provider hostname could not be resolved") from exc
    loopback = bool(addresses) and all(address.is_loopback for address in addresses)
    if parsed.scheme == "http" and not loopback:
        raise ValueError("Plain HTTP providers must use loopback")
    if any(address.is_private or address.is_link_local or address.is_multicast or address.is_unspecified for address in addresses) and not loopback:
        raise ValueError("Private network provider URLs are not allowed")
    return value.rstrip("/")
