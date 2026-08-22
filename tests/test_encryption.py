from django.test import SimpleTestCase, override_settings

from django_gc.conf import decrypt_value, encrypt_value


class EncryptionKeyTests(SimpleTestCase):
    """
    Проверить шифрование SECURE одним ключом из settings.
    """

    def test_roundtrip_with_encryption_key(self) -> None:
        """
        Зашифровать и расшифровать одним GLOBAL_CONFIG_ENCRYPTION_KEY.
        """
        encrypted = encrypt_value(text='plain-secret')

        self.assertNotEqual(encrypted, 'plain-secret')
        self.assertEqual(decrypt_value(text=encrypted), 'plain-secret')

    @override_settings(GLOBAL_CONFIG_ENCRYPTION_KEY=None)
    def test_passthrough_without_encryption_key(self) -> None:
        """
        Без ключа хранить SECURE открытым текстом.
        """
        self.assertEqual(encrypt_value(text='plain-secret'), 'plain-secret')
        self.assertEqual(decrypt_value(text='plain-secret'), 'plain-secret')

    def test_invalid_ciphertext_returns_none(self) -> None:
        """
        Невалидный шифротекст не выдавать как секрет.
        """
        self.assertIsNone(decrypt_value(text='not-a-fernet-token'))
