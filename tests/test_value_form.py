from decimal import Decimal

import pytest

from django_gc.enums import SettingType
from django_gc.forms import GlobalConfigForm
from django_gc.models import GlobalConfig


@pytest.mark.parametrize(('value_type', 'stored', 'submitted', 'typed'), [
    (SettingType.INTEGER, '10', '010', 10),
    (SettingType.FLOAT, '1.5', '1.50', 1.5),
    (SettingType.DECIMAL, '1.20', '1.2', Decimal('1.2')),
])
def test_numeric_form_compares_typed_value(
    value_type: SettingType, stored: str, submitted: str, typed: int | float | Decimal
) -> None:
    """
    Verify that different strings representing the same number do not mark the form as changed.

    Confirm that submitting a different numeric value still counts as an edit.
    """
    config = GlobalConfig(key='example.number', description='Example', value_type=value_type, value=stored)
    form = GlobalConfigForm({'value': submitted}, instance=config)

    assert form.initial['value'] == typed
    assert not form.has_changed()
    edited = GlobalConfigForm({'value': '20'}, instance=config)
    assert edited.has_changed()


def test_numeric_form_displays_invalid_stored_value_for_correction() -> None:
    """
    Verify that a malformed stored integer remains visible in the form so an operator can correct it.
    """
    config = GlobalConfig(
        key='example.number', description='Example', value_type=SettingType.INTEGER, value='invalid'
    )
    form = GlobalConfigForm(instance=config)
    assert form['value'].value() == 'invalid'
