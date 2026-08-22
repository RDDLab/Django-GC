import json
from typing import TYPE_CHECKING, Any, override

from django import forms
from django.utils.translation import gettext_lazy as _

from django_gc.enums import SettingType
from django_gc.fields import SemicolonSeparatedArrayField
from django_gc.models import GlobalConfig

if TYPE_CHECKING:
    _GlobalConfigForm = forms.ModelForm[GlobalConfig]
else:
    _GlobalConfigForm = forms.ModelForm


class GlobalConfigForm(_GlobalConfigForm):
    """
    Редактировать только значение существующего системного ключа.
    """

    key = forms.CharField(
        widget=forms.TextInput(attrs={'style': 'width: 500px;'}), required=True, label=_('Ключ'), disabled=True
    )
    value_type = forms.ChoiceField(choices=SettingType.choices(), required=True, label=_('Тип'), disabled=True)
    value = forms.CharField(widget=forms.Textarea({'cols': '80', 'rows': '10'}), required=True, label=_('Значение'))
    description = forms.CharField(
        widget=forms.TextInput(attrs={'style': 'width: 500px;'}), required=True, label=_('Описание'), disabled=True
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        obj: GlobalConfig | None = kwargs.get('instance')
        if obj is None:
            return
        value_type = SettingType(obj.value_type)
        if value_type == SettingType.BOOLEAN:
            self.fields['value'] = forms.ChoiceField(choices=(('True', 'True'), ('False', 'False')))
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
            parsed: dict[str, Any]
            try:
                loaded = json.loads(obj.value or '{}')
            except json.JSONDecodeError:
                parsed = {}
            else:
                parsed = loaded if isinstance(loaded, dict) else {}
            self.initial['value'] = json.dumps(parsed)
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

        if obj.is_read_only:
            self.fields['value'].disabled = True

        self.fields['value'].required = not obj.nullable
        self.fields['value'].label = _('Value')

    @override
    def clean(self) -> dict[str, Any]:
        """
        Проверить обязательность значения конфигурации.
        """
        cleaned_data = super().clean()
        if cleaned_data is None:
            return {}
        value: Any = cleaned_data.get('value')
        if (value is None or value == '') and not self.instance.nullable:
            self.add_error(field='value', error=_('Значение должно быть заполнено в любом случае.'))
        return cleaned_data

    def clean_value(self) -> Any:
        """
        Сериализовать типизированное значение формы к строке хранения.
        """
        value = self.cleaned_data.get('value')
        value_type = SettingType(self.instance.value_type)
        if value is None or value == '':
            return value
        if value_type == SettingType.JSON and not isinstance(value, str):
            return json.dumps(value)
        if value_type in {
            SettingType.INTEGER_MULTIPLE_CHOICES,
            SettingType.STRING_MULTIPLE_CHOICES,
            SettingType.FLOAT_MULTIPLE_CHOICES,
        } and not isinstance(value, str):
            return json.dumps(value)
        return value

    class Meta:
        model = GlobalConfig
        fields = ['key', 'value_type', 'description', 'value']
