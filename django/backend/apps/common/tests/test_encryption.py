"""Tests for the shared Fernet encryption module."""

import pytest

from apps.common.encryption import decrypt_token, encrypt_token


@pytest.mark.django_db
class TestEncryption:
    def test_roundtrip(self):
        """Encrypt then decrypt returns the original plaintext."""
        secret = "my-super-secret-api-key-123"
        ciphertext = encrypt_token(secret)
        assert ciphertext != secret
        assert decrypt_token(ciphertext) == secret

    def test_different_inputs_produce_different_ciphertexts(self):
        ct1 = encrypt_token("secret-one")
        ct2 = encrypt_token("secret-two")
        assert ct1 != ct2

    def test_backward_compatible_import(self):
        """The old import path still works via re-export."""
        from apps.integrations.encryption import decrypt_token as dec
        from apps.integrations.encryption import encrypt_token as enc

        secret = "backward-compat-test"
        assert dec(enc(secret)) == secret

    def test_cross_module_compatibility(self):
        """Tokens encrypted via old path can be decrypted via new path and vice versa."""
        from apps.integrations.encryption import encrypt_token as old_encrypt

        secret = "cross-module-test"
        ciphertext = old_encrypt(secret)
        assert decrypt_token(ciphertext) == secret
