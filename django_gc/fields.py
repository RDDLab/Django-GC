from typing import Any, override

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SemicolonSeparatedArrayField(forms.Field):
    """
    Edit array values in a single form field using semicolons as separators.

    Delegate conversion of each item to the supplied base field and store the normalized items as text.
    """

    default_error_messages = {'invalid': _('Enter values separated by ";".')}

    def __init__(self, base_field: forms.Field, **kwargs: Any) -> None:
        """
        Bind the supplied field to convert each array item and provide separator guidance by default.

        Forward all other keyword arguments to the underlying Django form field.
        """
        self.base_field = base_field
        kwargs.setdefault('help_text', _('Enter values separated by ";".'))
        super().__init__(**kwargs)

    @override
    def to_python(self, value: Any) -> str:
        """
        Convert the input to the semicolon-delimited format stored by the model.

        Accept a list or delimited text. Trim and discard blank segments in text input, and return an empty
        string for empty input.
        """
        if value is None or value == '':
            return ''
        if isinstance(value, list):
            return ';'.join(str(self.base_field.to_python(item)) for item in value)

        parts = [part.strip() for part in str(value).split(';') if part.strip()]
        try:
            parsed = [self.base_field.to_python(part) for part in parts]
        except Exception as exc:
            raise ValidationError(self.error_messages['invalid']) from exc
        return ';'.join(str(item) for item in parsed)
