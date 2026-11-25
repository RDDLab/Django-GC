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
    Verify the model's storage invariants and the public update path for initialized settings.
    """

    def test_save_forbids_creating_a_new_key(self) -> None:
        """
        Verify that calling save directly cannot create a settings row outside explicit initialization.
        """
        category = GlobalConfig.objects.get(pk='platform.pagination_size').category
        config = GlobalConfig(key='new-key', value='1', category=category, value_type=4)
        with self.assertRaises(GlobalConfigCreationForbiddenError):
            config.save()

    def test_delete_is_forbidden(self) -> None:
        """
        Verify that the model signal rejects deleting an existing setting.
        """
        config = GlobalConfig.objects.get(pk='platform.pagination_size')
        with self.assertRaises(GlobalConfigDeletionForbiddenError):
            config.delete()

    def test_set_value_updates_existing_key(self) -> None:
        """
        Update an existing setting through the public API and verify the stored value.
        """
        config = set_value(key='platform.pagination_size', value='50')
        config.refresh_from_db()
        self.assertEqual(config.value, '50')

    def test_set_value_unknown_key_raises(self) -> None:
        """
        Expect a missing-setting error when an update targets a key that has never been initialized.
        """
        with self.assertRaises(GlobalConfigNotFoundError):
            set_value(key='missing-key', value='1')

    def test_meaningless_for_required_empty_value(self) -> None:
        """
        Check that a missing required value is reported as meaningless.
        """
        config = GlobalConfig.objects.get(pk='platform.pagination_size')
        config.value = ''
        self.assertTrue(config.meaningless)

    def test_choices_are_built_from_variables(self) -> None:
        """
        Check that stored label-to-value metadata produces Django's value-and-label pairs.
        """
        config = GlobalConfig.objects.get(pk='platform.theme')
        self.assertEqual(set(config.choices), {('dark', 'Dark'), ('light', 'Light')})
