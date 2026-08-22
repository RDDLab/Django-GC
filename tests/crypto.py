from django_gc.conf import decrypt_value, encrypt_value


def encrypt_text(text: str) -> str:
    """
    Зашифровать секрет тем же ключом, что и пакет.
    """
    return encrypt_value(text=text)


def decrypt_text(text: str) -> str | None:
    """
    Расшифровать секрет тем же ключом, что и пакет.
    """
    return decrypt_value(text=text)
