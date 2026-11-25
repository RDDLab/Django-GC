from typing import Any, Literal, override

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from django_gc.models import GlobalConfig, GlobalConfigCategory
from django_gc.services import GlobalConfigInitializationService
from django_gc.utils import table_exists


class Command(BaseCommand):
    """
    Synchronize settings and categories declared by the project and its providers.

    Preserve existing values. Skip system checks for this command so the settings can be initialized before
    checks that depend on them.
    """

    help = gettext_noop('Initialize project and provider settings while preserving existing values.')
    requires_system_checks: Literal['__all__'] | list[str] | tuple[str, ...] = []

    @override
    def create_parser(self, prog_name: str, subcommand: str, **kwargs: Any) -> CommandParser:
        """
        Build Django's command parser and translate its description in the active language.

        Keep the message ID at class level so an earlier import does not fix the language of later help requests.
        """
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.description = _(self.help)
        return parser

    @override
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Verify that both tables exist and run definition initialization.

        Accept Django's standard management command arguments. Raise CommandError with the migration command
        when the schema is missing, and print a success message after initialization.
        """
        tables = [GlobalConfig._meta.db_table, GlobalConfigCategory._meta.db_table]
        if not all(table_exists(table_name=table) for table in tables):
            raise CommandError(_('GlobalConfig tables are missing. Run python manage.py migrate --skip-checks first.'))
        GlobalConfigInitializationService().initialize()
        self.stdout.write(self.style.SUCCESS(_('GlobalConfig settings initialized. Existing values were preserved.')))
