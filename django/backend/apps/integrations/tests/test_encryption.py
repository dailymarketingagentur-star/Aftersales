import pytest

from apps.integrations.encryption import decrypt_token, encrypt_token


@pytest.mark.django_db
class TestEncryption:
    def test_roundtrip(self):
        """Encrypt then decrypt returns original plaintext."""
        original = "my-super-secret-api-token-12345"
        encrypted = encrypt_token(original)
        assert encrypted != original
        assert decrypt_token(encrypted) == original

    def test_different_plaintexts_produce_different_ciphertexts(self):
        """Different inputs produce different encrypted values."""
        a = encrypt_token("token-a")
        b = encrypt_token("token-b")
        assert a != b

    def test_empty_string(self):
        """Empty string can be encrypted and decrypted."""
        encrypted = encrypt_token("")
        assert decrypt_token(encrypted) == ""

    def test_unicode_token(self):
        """Unicode characters survive encryption roundtrip."""
        original = "toekan-mit-uemlauten-äöü"
        assert decrypt_token(encrypt_token(original)) == original
