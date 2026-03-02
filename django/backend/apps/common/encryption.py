"""Fernet-based encryption for sensitive credentials.

Uses Django's SECRET_KEY to derive a stable Fernet key via PBKDF2.
This ensures tokens survive container restarts without extra config.

Shared by apps/integrations (Jira tokens) and apps/emails (SMTP/SendGrid keys).
"""

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _derive_key() -> bytes:
    """Derive a Fernet-compatible key from Django's SECRET_KEY."""
    key_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        settings.SECRET_KEY.encode(),
        # Keep original salt for backward compatibility with existing encrypted tokens.
        b"jira-token-encryption",
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_token(plaintext: str) -> str:
    """Encrypt a plaintext token. Returns a base64-encoded Fernet ciphertext."""
    f = Fernet(_derive_key())
    return f.encrypt(plaintext.encode()).decode()


def decrypt_token(ciphertext: str) -> str:
    """Decrypt a Fernet ciphertext back to plaintext."""
    f = Fernet(_derive_key())
    return f.decrypt(ciphertext.encode()).decode()
