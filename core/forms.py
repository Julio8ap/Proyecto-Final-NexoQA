from django import forms
from django.forms import modelform_factory
from accounts.forms import UsuarioCreacionForm, UsuarioEdicionForm
from .labels import ETIQUETAS


def formulario(modelo, instancia=None):
    if modelo._meta.label_lower == "auth.user":
        return UsuarioEdicionForm if instancia else UsuarioCreacionForm
    campos = ["estado"] if modelo._meta.model_name == "alerta" else "__all__"
    widgets = {}
    for campo in modelo._meta.fields:
        if campo.get_internal_type() == "DateField":
            widgets[campo.name] = forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            )
        if campo.get_internal_type() == "TimeField":
            widgets[campo.name] = forms.TimeInput(
                attrs={"type": "time"}, format="%H:%M"
            )
    excluir = ["estaciones"] if modelo._meta.model_name == "linea" else None
    return modelform_factory(
        modelo,
        fields=campos,
        exclude=excluir,
        widgets=widgets,
        labels=ETIQUETAS,
    )
