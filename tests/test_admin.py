from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from django_gc.admins import GlobalConfigAdmin, GlobalConfigCategoryAdmin
from django_gc.forms import GlobalConfigForm
from django_gc.models import GlobalConfig, GlobalConfigCategory


class GlobalConfigAdminTestCase(TestCase):
    """
    Проверить стандартный Django Admin без add/delete.
    """

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_superuser(
            username='admin', password='secret', email='admin@example.com'
        )
        self.client.force_login(self.user)

    def test_admins_are_registered_on_default_site(self) -> None:
        """
        Зарегистрировать обе модели на стандартном admin.site.
        """
        self.assertIsInstance(site._registry[GlobalConfig], GlobalConfigAdmin)
        self.assertIsInstance(site._registry[GlobalConfigCategory], GlobalConfigCategoryAdmin)

    def test_changelist_is_available(self) -> None:
        """
        Открыть список ключей в stock Admin.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'platform-pagination-size')

    def test_add_and_delete_permissions_are_denied(self) -> None:
        """
        Запретить add и delete обеих моделей.
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
        Показать страницу изменения и стандартную историю Django Admin.
        """
        url = reverse('admin:django_gc_globalconfig_change', args=['platform-pagination-size'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        history_url = reverse('admin:django_gc_globalconfig_history', args=['platform-pagination-size'])
        history_response = self.client.get(history_url)
        self.assertEqual(history_response.status_code, 200)

    def test_read_only_form_disables_value(self) -> None:
        """
        Запретить правку read-only ключа в форме.
        """
        config = GlobalConfig.objects.get(pk='read-only-flag')
        form = GlobalConfigForm(instance=config)
        self.assertTrue(form.fields['value'].disabled)

    def test_category_name_is_resolved_in_ui(self) -> None:
        """
        Показать название числовой категории из definitions.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform')

    def test_category_filter_uses_definition_names(self) -> None:
        """
        Отфильтровать ключи по числовой категории с человекочитаемым label.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url, {'category__id__exact': '2'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Auth')
        self.assertContains(response, 'secret-token')
        self.assertNotContains(response, 'platform-pagination-size')

    def test_category_search_uses_definition_code_and_name(self) -> None:
        """
        Найти ключи через code или name категории из definitions.
        """
        url = reverse('admin:django_gc_globalconfig_changelist')
        response = self.client.get(url, {'q': 'auth'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'secret-token')
        self.assertNotContains(response, 'platform-pagination-size')

    def test_category_changelist_is_matched_from_definitions(self) -> None:
        """
        Показать и искать code/name, которых нет в таблице категорий.
        """
        url = reverse('admin:django_gc_globalconfigcategory_changelist')
        response = self.client.get(url, {'q': 'platform'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Platform')
        self.assertContains(response, 'platform')
        self.assertQuerySetEqual(response.context['cl'].queryset.values_list('id', flat=True), [1])
