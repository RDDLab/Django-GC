from django_gc.dto import CategoryDefinition, SettingDefinition
from django_gc.enums import SettingType

TEST_CATEGORIES = [
    CategoryDefinition(id=1, code='platform', name='Platform'),
    CategoryDefinition(id=2, code='auth', name='Auth'),
]

TEST_DEFINITIONS = [
    SettingDefinition(
        key='platform-pagination-size',
        description='Default pagination size',
        default_value=25,
        value_type=SettingType.INTEGER,
        category_id=1,
    ),
    SettingDefinition(
        key='maintenance-enabled',
        description='Maintenance mode',
        default_value=False,
        value_type=SettingType.BOOLEAN,
        category_id=1,
    ),
    SettingDefinition(
        key='secret-token',
        description='Secure token',
        default_value='secret',
        value_type=SettingType.SECURE,
        category_id=2,
    ),
    SettingDefinition(
        key='optional-note',
        description='Optional note',
        default_value=None,
        value_type=SettingType.STRING,
        category_id=1,
        nullable=True,
    ),
    SettingDefinition(
        key='read-only-flag',
        description='Read-only flag',
        default_value=True,
        value_type=SettingType.BOOLEAN,
        category_id=1,
        is_read_only=True,
    ),
    SettingDefinition(
        key='theme-choice',
        description='Theme',
        default_value='dark',
        value_type=SettingType.STRING_CHOICES,
        category_id=1,
        variables={'Dark': 'dark', 'Light': 'light'},
        is_always_update=True,
    ),
]
