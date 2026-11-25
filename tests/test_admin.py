from io import StringIO
from unittest.mock import patch

from django.contrib.admin.sites import site
from django.contrib.admin.utils import quote
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from django_gc.admins import GlobalConfigAdmin, GlobalConfigCategoryAdmin
from django_gc.dto import ProviderDefinition
from django_gc.forms import GlobalConfigForm
from django_gc.models import GlobalConfig, GlobalConfigCategory
from tests.provider import ExampleProvider


class GlobalConfigAdminTestCase(TestCase):
    """
    Verify the catalog, permissions and editing behavior in standard Django Admin.

    Exercise both the project definitions and access rules supplied by an integrating provider.
    """

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_superuser(
            username='admin', password='secret', email='admin@example.com'
        )
        self.client.force_login(self.user)

    def test_admins_are_registered_on_default_site(self) -> None:
        """
        Verify that both configuration models are registered on Django's default admin site.
        """
        self.assertIsInstance(site._registry[GlobalConfig], GlobalConfigAdmin)
        self.assertIsInstance(site._registry[GlobalConfigCategory], GlobalConfigCategoryAdmin)

    def test_changelist_is_available(self) -> None:
        """
        Open the settings list and verify that the active definition is visible in standard Django Admin.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'platform.pagination_size')
        self.assertContains(response, 'id="result_list"')
        self.assertNotContains(response, 'data-chassis-modal-url')
        change_url = reverse('admin:django_gc_globalconfig_change', args=[quote('platform.pagination_size')])
        self.assertContains(response, f'href="{change_url}"')
        edit = self.client.get(change_url, headers={'X-Chassis-Modal': '1'})
        self.assertTemplateUsed(edit, 'admin/change_form.html')
        self.assertNotIn('X-Chassis-Modal-Fragment', edit.headers)

    def test_add_and_delete_permissions_are_denied(self) -> None:
        """
        Check that settings and categories cannot be added or deleted from the admin.
        """
        config_admin = site._registry[GlobalConfig]
        category_admin = site._registry[GlobalConfigCategory]
        request = RequestFactory().get('/')
        request.user = self.user
        self.assertFalse(config_admin.has_add_permission(request))
        self.assertFalse(config_admin.has_delete_permission(request))
        self.assertFalse(category_admin.has_add_permission(request))
        self.assertFalse(category_admin.has_delete_permission(request))

    def test_change_form_shows_django_history_link(self) -> None:
        """
        Open an existing setting and check that the standard Django Admin history view remains available.
        """
        url = reverse('admin:django_gc_globalconfig_change', args=['platform.pagination_size'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        history_url = reverse('admin:django_gc_globalconfig_history', args=['platform.pagination_size'])
        history_response = self.client.get(history_url)
        self.assertEqual(history_response.status_code, 200)

    def test_read_only_form_disables_value(self) -> None:
        """
        Check that the settings form disables the value field for a read-only key.
        """
        config = GlobalConfig.objects.get(pk='platform.read_only_flag')
        form = GlobalConfigForm(instance=config)
        self.assertTrue(form.fields['value'].disabled)
        url = reverse('admin:django_gc_globalconfig_change', args=[config.pk])
        self.assertEqual(self.client.post(url, {'value': 'False'}).status_code, 403)

    def test_secret_is_masked_in_stock_list_and_read_only_form(self) -> None:
        """
        Check that a view-only operator sees the mask in both the catalog and the change page.

        Ensure neither response contains the stored secure value.
        """
        key = 'auth.secret_token'
        stored = GlobalConfig.objects.get(pk=key).value
        assert stored is not None
        reader = get_user_model().objects.create_user('reader', is_staff=True)
        reader.user_permissions.add(Permission.objects.get(codename='view_globalconfig'))
        self.client.force_login(reader)
        catalog = self.client.get(reverse('admin:django_gc_globalconfig_changelist'), {'q': key})
        editor = self.client.get(reverse('admin:django_gc_globalconfig_change', args=[key]))
        for response in [catalog, editor]:
            self.assertContains(response, '••••••••')
            self.assertNotContains(response, stored)

    @override_settings(GLOBAL_CONFIG_PROVIDERS=[ProviderDefinition(
        provider='tests.provider.ExampleProvider', category_ids={'general': 30},
    )])
    def test_stock_admin_obeys_provider_visibility_and_validation(self) -> None:
        """
        Exercise provider permissions in the catalog and direct edit links.

        Verify that an authorized operator's standard form also enforces the provider's validation rules.
        """
        call_command('initialize_global_configs', stdout=StringIO())
        catalog_url = reverse('admin:django_gc_globalconfig_changelist')
        key = 'example.limit'
        change_url = reverse('admin:django_gc_globalconfig_change', args=[key])
        with (
            patch.object(ExampleProvider, 'has_view_permission', return_value=False),
            patch.object(ExampleProvider, 'has_change_permission', return_value=False),
        ):
            response = self.client.get(catalog_url, {'q': key})
            self.assertNotContains(response, f'href="{change_url}"')
            self.assertEqual(response.context['cl'].result_count, 0)
            self.assertEqual(self.client.get(change_url).status_code, 403)
        with (
            patch.object(ExampleProvider, 'protected', False),
            patch.object(ExampleProvider, 'change_view', return_value=None),
        ):
            bad = self.client.post(change_url, {'value': '11'})
            self.assertContains(bad, 'Invalid limit.')
            self.assertEqual(GlobalConfig.objects.get(pk=key).value, '7')
            saved = self.client.post(change_url, {'value': '8'})
            self.assertEqual(saved.status_code, 302)
            self.assertEqual(GlobalConfig.objects.get(pk=key).value, '8')

    def test_category_name_is_resolved_in_ui(self) -> None:
        """
        Verify that the admin displays a name from the definitions for a stored numeric category.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform')

    def test_category_filter_uses_definition_names(self) -> None:
        """
        Check that the category filter shows the declared label and filters by its stored numeric ID.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url, {'category__id__exact': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Auth')
        self.assertContains(response, 'auth.secret_token')
        self.assertNotContains(response, 'platform.pagination_size')

    def test_category_search_uses_definition_code_and_name(self) -> None:
        """
        Search the settings list using both the declared category code and its display name.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url, {'q': 'auth'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'auth.secret_token')
        self.assertNotContains(response, 'platform.pagination_size')

    def test_category_changelist_is_matched_from_definitions(self) -> None:
        """
        Verify that category display and search use codes and names resolved from the definitions.
        """
        url = reverse('admin:django_gc_globalconfigcategory_changelist')
        response = self.client.get(url, {'q': 'platform'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform')
        self.assertContains(response, 'platform')
        self.assertQuerySetEqual(response.context['cl'].queryset.values_list('id', flat=True), [1])
