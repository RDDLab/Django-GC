from django.db import connection


def is_bool(value: object) -> bool:
    """
    Interpret a stored boolean using Django-GC's accepted truthy spellings.

    Return True for t, true, yes, y and 1, ignoring letter case. Other values return False.
    """
    return str(value).lower() in {'t', 'true', 'yes', 'y', '1'}


def table_exists(table_name: str) -> bool:
    """
    Check whether the named table is present on the active Django database connection.
    """
    return table_name in connection.introspection.table_names()
