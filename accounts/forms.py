from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .roles import ROLES


class UsuarioCreacionForm(UserCreationForm):
    rol = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=ROLES), required=True
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "rol",
        ]

    def save(self, commit=True):
        usuario = super().save(commit)
        if commit:
            usuario.groups.set([self.cleaned_data["rol"]])
        return usuario


class UsuarioEdicionForm(forms.ModelForm):
    rol = forms.ModelChoiceField(
        queryset=Group.objects.filter(name__in=ROLES), required=True
    )

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email", "is_active", "rol"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].initial = self.instance.groups.first()

    def save(self, commit=True):
        usuario = super().save(commit)
        if commit:
            usuario.groups.set([self.cleaned_data["rol"]])
        return usuario
