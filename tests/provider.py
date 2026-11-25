from collections.abc import Mapping, Sequence
from typing import Any

from django.http import HttpResponse

from django_gc import SettingDefinition, SettingType
from django_gc.providers import ConfigurationProvider


class ExampleProvider(ConfigurationProvider):
    """
    Supply protected settings for testing provider registration, validation and the custom editor path.

    The example owns an integer limit and a JSON list of allowed origins.
    """

    namespace = 'example'
    categories = {'general': 'Example'}
    protected = True

    def get_definitions(self, *, category_ids: Mapping[str, int]) -> Sequence[SettingDefinition]:
        """
        Declare the two example keys under the category ID assigned by the test project.
        """
        return [
            SettingDefinition(key='example.limit', description='Limit', default_value=3,
                              value_type=SettingType.INTEGER, category_id=category_ids['general'],
                              previous_keys=['example.LEGACY_LIMIT']),
            SettingDefinition(key='example.origins', description='Origins', default_value=[],
                              value_type=SettingType.JSON, category_id=category_ids['general'])
        ]

    def validate(self, *, key: str, value: Any) -> Any:
        """
        Require an integer limit from 1 through 10 and a list of strings for origins.

        Return accepted values unchanged so tests can assert round-trip behavior.
        """
        if key == 'example.limit' and (isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10):
            raise ValueError('Invalid limit.')
        if key == 'example.origins' and (not isinstance(value, list)
                                         or any(not isinstance(item, str) for item in value)):
            raise ValueError('Invalid origins.')
        return value

    def initial_value(self, *, key: str, default: Any) -> Any:
        """
        Use a distinct first value for the limit so tests can distinguish provider initialization from
        defaults.
        """
        return 7 if key == 'example.limit' else default

    def change_view(self, *, admin_site: Any, request: Any, key: str) -> HttpResponse:
        """
        Return a simple response identifying the key handed to the provider's editor.
        """
        return HttpResponse(f'Owner editor: {key}')
