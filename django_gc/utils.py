from django.db import connection


def is_bool(value: object) -> bool:
    """
    Разобрать текстовое булево значение в стиле CPA GlobalConfig.
    """
    return str(value).lower() in {'t', 'true', 'yes', 'y', '1'}


def table_exists(table_name: str) -> bool:
    """
    Проверить наличие таблицы в текущем подключении.
    """
    return table_name in connection.introspection.table_names()
