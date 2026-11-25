from pathlib import Path

import pytest
from django.template.loader import get_template
from django.utils.translation import override

import django_gc
from django_gc.enums import SettingType
from django_gc.exceptions import GlobalConfigNotFoundError
from django_gc.models import GlobalConfig

METADATA_TEMPLATE = 'admin/django_gc/configuration_metadata.html'


def test_metadata_loads_from_standalone_template() -> None:
    """
    Resolve the metadata template using Django's normal app template loader.

    Assert that the packaged Django-GC template is the rendered source.
    """
    expected = Path(django_gc.__file__).parent / 'templates' / METADATA_TEMPLATE
    assert Path(get_template(METADATA_TEMPLATE).origin.name) == expected


@pytest.mark.parametrize(('language', 'can_change', 'editing_label'), [
    ('en', True, 'Allowed'),
    ('en', False, 'View only'),
    ('ru', True, 'Разрешено'),
    ('ru', False, 'Только просмотр'),
])
def test_standalone_metadata_uses_django_markup(language: str, can_change: bool, editing_label: str) -> None:
    """
    Render the stock metadata template for each supported locale and edit permission state.

    Check that the labels change with the locale, the description is escaped and the setting value is
    omitted.
    """
    record = {
        'key': 'app.example_setting',
        'get_value_type_display': 'String',
        'description': 'A & B <Settings>',
        'value': 'not part of metadata',
    }
    with override(language):
        markup = get_template(METADATA_TEMPLATE).render({
            'configuration_record': record,
            'configuration_can_change': can_change,
        })
    assert 'gc-configuration-metadata' in markup
    assert 'app.example_setting' in markup
    assert 'A &amp; B &lt;Settings&gt;' in markup
    assert f'>{editing_label}<' in markup
    assert record['value'] not in markup


@pytest.mark.parametrize(('language', 'catalog_label', 'type_label', 'error_message'), [
    ('en', 'Global settings', 'Date and time', 'GlobalConfig setting app.missing was not found.'),
    ('ru', 'Глобальные настройки', 'Дата и время', 'Настройка GlobalConfig app.missing не найдена.'),
])
def test_library_messages_follow_the_active_language(
    language: str, catalog_label: str, type_label: str, error_message: str
) -> None:
    """
    Resolve lazy model and enum labels and interpolate the setting key in a translated error.

    Exercise the packaged message catalog under a language override without writing any settings.
    """
    with override(language):
        assert str(GlobalConfig._meta.verbose_name_plural) == catalog_label
        assert str(SettingType.DATETIME.label()) == type_label
        assert str(GlobalConfigNotFoundError(key='app.missing')) == error_message
