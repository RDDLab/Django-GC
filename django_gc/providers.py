from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from django.contrib.admin import AdminSite
from django.http import HttpRequest, HttpResponse
from django.utils.functional import Promise

from django_gc.dto import SettingDefinition


class ConfigurationProvider(ABC):
    """
    Let a project or library own the settings in one namespace.

    Declare category codes, definitions and optional validation, access rules or a custom admin editor.
    Django-GC owns the shared catalog and persistence. A protected provider requires its trusted code to
    authorize writes.
    """

    namespace: str
    categories: Mapping[str, str | Promise]
    protected: bool = False

    @abstractmethod
    def get_definitions(self, *, category_ids: Mapping[str, int]) -> Sequence[SettingDefinition]:
        """
        Return the provider's settings using the category IDs assigned by the integrating project.

        The category_ids mapping uses the provider's declared category codes as keys.
        """
        raise NotImplementedError

    def validate(self, *, key: str, value: Any) -> Any:
        """
        Check the typed value of an owned key and return the normalized value.

        Override to enforce provider-specific rules. The default implementation accepts the input unchanged.
        """
        return value

    def initial_value(self, *, key: str, default: Any) -> Any:
        """
        Supply the first value of a newly initialized setting when no previous row is reused.

        The default implementation returns the default declared for the key.
        """
        return default

    def change_view(
        self, *, admin_site: AdminSite, request: HttpRequest, key: str
    ) -> HttpResponse | None:
        """
        Handle a setting edit in the supplied Django Admin site.

        Return a response for the requested key or None to continue with the standard editor. The caller
        provides the current HTTP request after checking admin permissions.
        """
        return None

    @classmethod
    def has_view_permission(cls, *, request: HttpRequest) -> bool:
        """
        Check the provider's additional view permission for the current admin request.

        The default permits access subject to Django Admin permissions.
        """
        return True

    @classmethod
    def has_change_permission(cls, *, request: HttpRequest) -> bool:
        """
        Check the provider's additional change permission for the current admin request.

        The default permits editing subject to Django Admin permissions and the setting's read-only policy.
        """
        return True
