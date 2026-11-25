from io import StringIO

import pytest
from django.core.management import call_command
from django.test import TransactionTestCase


@pytest.fixture(autouse=True)
def initialize_test_global_config(request: pytest.FixtureRequest) -> None:
    """
    Initialize declared settings for tests that request database access.

    Keep seed data independent of migrations so tests can exercise explicit initialization.
    """
    uses_database = request.node.get_closest_marker('django_db') is not None
    uses_database = uses_database or bool({'db', 'transactional_db'}.intersection(request.fixturenames))
    if request.cls is not None and issubclass(request.cls, TransactionTestCase):
        uses_database = True
    if not uses_database:
        return
    request.getfixturevalue('db')
    call_command('initialize_global_configs', stdout=StringIO())
