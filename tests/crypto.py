from django_gc.conf import decrypt_value, encrypt_value


def encrypt_text(text: str) -> str:
    """
    Build a stored Fernet token from a test secret using the same key derivation as Django-GC.
    """
    return encrypt_value(text=text)


def decrypt_text(text: str) -> str | None:
    """
    Decode an encrypted test value with the test key to verify what is stored.
    """
    return decrypt_value(text=text)
