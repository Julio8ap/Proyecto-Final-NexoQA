from datetime import datetime
from django import forms
from django.utils import timezone
from .models import ESTADOS_ALERTA


class AtenderAlertaForm(forms.Form):
    descripcion = forms.CharField(
        label="Gestión realizada",
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="Describa qué se hizo o qué seguimiento se realizó (máximo 2000 caracteres).",
    )
    estado = forms.ChoiceField(
        label="Estado después de la gestión", choices=ESTADOS_ALERTA
    )


class FinalizarRecorridoForm(forms.Form):
    hora_final = forms.TimeField(
        label="Hora de finalización (hora local, 24 h)",
        widget=forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
    )

    def __init__(self, *args, recorrido, **kwargs):
        self.recorrido = recorrido
        super().__init__(*args, **kwargs)
        self.fields[
            "hora_final"
        ].initial = recorrido.hora_final or timezone.localtime().time().replace(
            second=0, microsecond=0
        )

    def clean_hora_final(self):
        hora = self.cleaned_data["hora_final"]
        if hora < self.recorrido.hora_inicio:
            raise forms.ValidationError(
                "La finalización no puede ser anterior al inicio."
            )
        if datetime.combine(
            self.recorrido.fecha, hora
        ) > timezone.localtime().replace(tzinfo=None):
            raise forms.ValidationError(
                "No se puede finalizar un recorrido en una fecha u hora futura."
            )
        return hora
