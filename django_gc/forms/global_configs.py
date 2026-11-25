import json
from typing import TYPE_CHECKING, Any, override

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_gc.enums import SettingType
from django_gc.exceptions import GlobalConfigValueError
from django_gc.fields import SemicolonSeparatedArrayField
from django_gc.models import GlobalConfig
from django_gc.registry import get_provider

if TYPE_CHECKING:
    _GlobalConfigForm = forms.ModelForm[GlobalConfig]
else:
    _GlobalConfigForm = forms.ModelForm


class GlobalConfigForm(_GlobalConfigForm):
    """
    Edit the value of an existing setting using a form field appropriate to its declared type.

    Display the key and metadata separately, and keep the value field disabled for read-only settings.
    """

    key = forms.CharField(
        widget=forms.TextInput(attrs={'style': 'width: 500px;'}), required=True, label=_('Key'), disabled=True
    )
    value_type = forms.ChoiceField(choices=SettingType.choices(), required=True, label=_('Type'), disabled=True)
    value = forms.CharField(widget=forms.Textarea({'cols': '80', 'rows': '10'}), required=True, label=_('Value'))
    description = forms.CharField(
        widget=forms.TextInput(attrs={'style': 'width: 500px;'}), required=True, label=_('Description'), disabled=True
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Choose the value field from the bound setting definition and prepare its initial value.

        Apply the model's nullable and read-only rules. Preserve malformed stored numeric text so it can be
        corrected.
        """
        super().__init__(*args, **kwargs)
        obj: GlobalConfig | None = kwargs.get('instance')
        if obj is None:
            return
        value_type = SettingType(obj.value_type)
        if value_type == SettingType.BOOLEAN:
            self.fields['value'] = forms.ChoiceField(choices=(('True', _('Enabled')), ('False', _('Disabled'))))
        elif value_type == SettingType.STRING:
            self.fields['value'] = forms.CharField(widget=forms.TextInput())
        elif value_type == SettingType.FLOAT:
            self.fields['value'] = forms.FloatField()
        elif value_type == SettingType.DECIMAL:
            self.fields['value'] = forms.DecimalField(max_digits=20, decimal_places=8)
        elif value_type == SettingType.INTEGER:
            self.fields['value'] = forms.IntegerField()
        elif value_type == SettingType.SECURE:
            self.fields['value'] = forms.CharField(
                widget=forms.PasswordInput(render_value=False, attrs={'style': 'width: 750px;'})
            )
        elif value_type == SettingType.DATE:
            self.fields['value'] = forms.DateField(
                widget=forms.DateInput(attrs={'type': 'date', 'style': 'width: 500px;'}),
                input_formats=('%d.%m.%Y', '%Y-%m-%d'),
            )
        elif value_type == SettingType.TIME:
            self.fields['value'] = forms.TimeField(
                widget=forms.TimeInput(attrs={'type': 'time', 'style': 'width: 500px;'}),
                input_formats=('%H:%M:%S', '%H:%M'),
            )
        elif value_type == SettingType.DATETIME:
            self.fields['value'] = forms.DateTimeField(
                widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'style': 'width: 500px;'}),
                input_formats=('%d.%m.%Y %H:%M:%S', '%d.%m.%Y %H:%M', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S'),
            )
        elif value_type == SettingType.STRING_ARRAY:
            self.fields['value'] = SemicolonSeparatedArrayField(base_field=forms.CharField())
        elif value_type == SettingType.INTEGER_ARRAY:
            self.fields['value'] = SemicolonSeparatedArrayField(base_field=forms.IntegerField())
        elif value_type == SettingType.FLOAT_ARRAY:
            self.fields['value'] = SemicolonSeparatedArrayField(base_field=forms.FloatField())
        elif value_type == SettingType.DECIMAL_ARRAY:
            self.fields['value'] = SemicolonSeparatedArrayField(
                base_field=forms.DecimalField(max_digits=20, decimal_places=8)
            )
        elif value_type in {
            SettingType.STRING_CHOICES,
            SettingType.INTEGER_CHOICES,
            SettingType.FLOAT_CHOICES,
            SettingType.DECIMAL_CHOICES,
        }:
            self.fields['value'] = forms.ChoiceField(choices=obj.choices)
        elif value_type == SettingType.JSON:
            self.fields['value'] = forms.JSONField(widget=forms.Textarea(attrs={'rows': 4}))
            self.initial['value'] = json.loads(obj.value) if obj.value else None
        elif value_type == SettingType.INTEGER_MULTIPLE_CHOICES:
            self.fields['value'] = forms.TypedMultipleChoiceField(
                choices=obj.choices, widget=forms.CheckboxSelectMultiple, coerce=int
            )
            self.initial['value'] = json.loads(obj.value or '[]')
        elif value_type == SettingType.STRING_MULTIPLE_CHOICES:
            self.fields['value'] = forms.TypedMultipleChoiceField(
                choices=obj.choices, widget=forms.CheckboxSelectMultiple, coerce=str
            )
            self.initial['value'] = json.loads(obj.value or '[]')
        elif value_type == SettingType.FLOAT_MULTIPLE_CHOICES:
            self.fields['value'] = forms.TypedMultipleChoiceField(
                choices=obj.choices, widget=forms.CheckboxSelectMultiple, coerce=float
            )
            self.initial['value'] = json.loads(obj.value or '[]')
        else:
            self.fields['value'] = forms.CharField(widget=forms.Textarea({'cols': '80', 'rows': 10}))

        value_field = self.fields['value']
        if isinstance(value_field, (forms.IntegerField, forms.FloatField, forms.DecimalField)):
            initial_value = self.initial.get('value')
            try:
                self.initial['value'] = value_field.to_python(initial_value)
            except ValidationError:
                # Keep malformed stored values visible so the operator can correct them.
                self.initial['value'] = initial_value

        if obj.is_read_only:
            value_field.disabled = True

        value_field.required = not obj.nullable and value_type != SettingType.JSON
        value_field.label = _('Value')

    @override
    def clean(self) -> dict[str, Any]:
        """
        Reject an empty value for a required setting after individual fields have been cleaned.
        """
        cleaned_data = super().clean()
        if cleaned_data is None:
            return {}
        value: Any = cleaned_data.get('value')
        if (value is None or value == '') and not self.instance.nullable:
            self.add_error(field='value', error=_('This setting requires a value.'))
        return cleaned_data

    def clean_value(self) -> Any:
        """
        Serialize structured values from JSON and multiple-choice fields for text storage.

        Validate the proposed value against the owning provider before returning it.
        """
        value = self.cleaned_data.get('value')
        value_type = SettingType(self.instance.value_type)
        if value_type in {
            SettingType.JSON,
            SettingType.INTEGER_MULTIPLE_CHOICES,
            SettingType.STRING_MULTIPLE_CHOICES,
            SettingType.FLOAT_MULTIPLE_CHOICES,
        } and value is not None and not isinstance(value, str):
            value = json.dumps(value)
        self._validate_value(value)
        return value

    def _validate_value(self, value: Any) -> None:
        """
        Parse a proposed stored value and apply ordinary provider validation using a temporary model.

        Protected providers perform validation in their own workflow. Mask details when a secure value fails
        validation.
        """
        config = self.instance
        if config.is_read_only:
            return
        provider = get_provider(key=config.key)
        if provider is None or provider.protected:
            return

        from django_gc.services import GlobalConfigService

        candidate = GlobalConfig(key=config.key, value=None if value is None else str(value),
                                 value_type=config.value_type, nullable=config.nullable)
        try:
            if config.value_type not in {SettingType.DATE, SettingType.TIME, SettingType.DATETIME}:
                value = GlobalConfigService.parse_value(config=candidate)
            provider.validate(key=config.key, value=value)
        except (GlobalConfigValueError, ValidationError, ValueError) as e:
            if config.value_type == SettingType.SECURE:
                raise ValidationError(_('Enter a valid value.')) from e
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(str(e)) from e

    def typed_value(self) -> Any:
        """
        Return the typed value from a successfully validated form without saving the row.

        Use this in a workflow that confirms or authorizes an edit before writing it.
        """
        from django_gc.services import GlobalConfigService

        if not self.is_valid():
            raise ValueError(str(_('Correct the form errors first.')))
        return GlobalConfigService.parse_value(config=self.instance)

    class Meta:
        model = GlobalConfig
        fields = ['key', 'value_type', 'description', 'value']
