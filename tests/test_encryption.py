from django.test import SimpleTestCase, override_settings

from django_gc.conf import decrypt_value, encrypt_value


class EncryptionKeyTests(SimpleTestCase):
    """
    Verify the secure-value codec when the project configures an encryption key and when it omits one.
    """

    def test_roundtrip_with_encryption_key(self) -> None:
        """
        Round-trip a secret using GLOBAL_CONFIG_ENCRYPTION_KEY and verify that the stored token differs from
        plaintext.
        """
        encrypted = encrypt_value(text='plain-secret')

        self.assertNotEqual(encrypted, 'plain-secret')
        self.assertEqual(decrypt_value(text=encrypted), 'plain-secret')

    @override_settings(GLOBAL_CONFIG_ENCRYPTION_KEY=None)
    def test_passthrough_without_encryption_key(self) -> None:
        """
        Verify that encryption and decryption pass the text through when no key is configured.
        """
        self.assertEqual(encrypt_value(text='plain-secret'), 'plain-secret')
        self.assertEqual(decrypt_value(text='plain-secret'), 'plain-secret')

    def test_invalid_ciphertext_returns_none(self) -> None:
        """
        Check that an invalid Fernet token yields None instead of a usable cleartext value.
        """
        self.assertIsNone(decrypt_value(text='not-a-fernet-token'))
