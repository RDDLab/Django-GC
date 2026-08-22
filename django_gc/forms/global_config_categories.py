from typing import TYPE_CHECKING

from django import forms

from django_gc.models import GlobalConfigCategory

if TYPE_CHECKING:
    _CategoryForm = forms.ModelForm[GlobalConfigCategory]
else:
    _CategoryForm = forms.ModelForm


class GlobalConfigCategoryForm(_CategoryForm):
    """
    Редактировать название категории в однострочном поле.
    """

    class Meta:
        model = GlobalConfigCategory
        fields = '__all__'
        widgets = {'name': forms.TextInput(attrs={'style': 'width: 50em;'})}
