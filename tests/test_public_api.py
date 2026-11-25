import os
import subprocess
import sys

import pytest

from django_gc import get_value, is_cache_ready, refresh_cache, services, set_typed_value, set_value
from django_gc.models import GlobalConfig


def test_root_api_can_be_imported_before_django_configuration() -> None:
    """
    Import the package root and its public functions before Django settings or the app registry are
    configured.
    """
    environment = os.environ.copy()
    environment.pop('DJANGO_SETTINGS_MODULE', None)
    subprocess.run(
        [
            sys.executable,
            '-c',
            'from django_gc import get_value, is_cache_ready, refresh_cache, set_typed_value, set_value; '
            'from django.apps import apps; '
            'assert not apps.ready'
        ],
        env=environment,
        check=True,
        timeout=15
    )


@pytest.mark.django_db
def test_public_api_reexports_use_same_storage_and_service() -> None:
    """
    Check that both public import paths expose the same functions and share the same typed storage behavior.
    """
    assert services.get_value is get_value
    assert services.is_cache_ready is is_cache_ready
    assert services.refresh_cache is refresh_cache
    assert services.set_typed_value is set_typed_value
    assert services.set_value is set_value

    key = 'platform.pagination_size'
    current = get_value(key, use_cache=False)
    assert isinstance(current, int)
    changed = set_typed_value(key=key, value=current + 1)
    assert isinstance(changed, GlobalConfig)
    assert get_value(key, use_cache=False) == current + 1
    set_value(key, str(current))
    assert get_value(key, use_cache=False) == current
