from django.test import TestCase

from django_gc.exceptions import (
    GlobalConfigCreationForbiddenError,
    GlobalConfigDeletionForbiddenError,
    GlobalConfigNotFoundError,
)
from django_gc.models import GlobalConfig
from django_gc.services import set_value


class GlobalConfigModelTestCase(TestCase):
    """
    Проверить инварианты модели и программную запись.
    """

    def test_save_forbids_creating_a_new_key(self) -> None:
        """
        Запретить создание ключа через save().
        """
        category = GlobalConfig.objects.get(pk='platform-pagination-size').category
        config = GlobalConfig(key='new-key', value='1', category=category, value_type=4)
        with self.assertRaises(GlobalConfigCreationForbiddenError):
            config.save()

    def test_delete_is_forbidden(self) -> None:
        """
        Запретить удаление существующего ключа.
        """
        config = GlobalConfig.objects.get(pk='platform-pagination-size')
        with self.assertRaises(GlobalConfigDeletionForbiddenError):
            config.delete()

    def test_set_value_updates_existing_key(self) -> None:
        """
        Обновить существующее значение через публичный API.
        """
        config = set_value(key='platform-pagination-size', value='50')
        config.refresh_from_db()
        self.assertEqual(config.value, '50')

    def test_set_value_unknown_key_raises(self) -> None:
        """
        Не создавать отсутствующий ключ через set_value().
        """
        with self.assertRaises(GlobalConfigNotFoundError):
            set_value(key='missing-key', value='1')

    def test_meaningless_for_required_empty_value(self) -> None:
        """
        Отметить пустое обязательное значение как meaningless.
        """
        config = GlobalConfig.objects.get(pk='platform-pagination-size')
        config.value = ''
        self.assertTrue(config.meaningless)

    def test_choices_are_built_from_variables(self) -> None:
        """
        Построить пары Django choices из JSON variables.
        """
        config = GlobalConfig.objects.get(pk='theme-choice')
        self.assertEqual(set(config.choices), {('dark', 'Dark'), ('light', 'Light')})
