from django.core.exceptions import ValidationError
from django.db import models
from core.models import ValidatedModel


class Persona(ValidatedModel):
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    identificacion_interna = models.CharField(max_length=30, unique=True)
    telefono = models.CharField(max_length=25, blank=True)
    correo = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return (
            f"{self.identificacion_interna} · {self.nombres} {self.apellidos}"
        )


class Piloto(Persona):
    direccion = models.CharField(max_length=250)
    residencia = models.CharField(max_length=150)
    nivel_educativo = models.CharField(max_length=100)
    historial_educativo = models.TextField(blank=True)


class Operador(Persona):
    pass


class Guardia(Persona):
    def clean(self):
        if self.pk and not self.activo:
            for asignacion in self.asignacionguardia_set.filter(activo=True):
                otros = asignacion.acceso.asignacionguardia_set.filter(
                    activo=True, guardia__activo=True
                ).exclude(guardia=self)
                if asignacion.acceso.activo and not otros.exists():
                    raise ValidationError(
                        "No puede desactivar al último guardia de un acceso activo."
                    )


class AsignacionGuardia(ValidatedModel):
    acceso = models.ForeignKey("operacion.Acceso", on_delete=models.PROTECT)
    guardia = models.ForeignKey(Guardia, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["acceso", "guardia"], name="guardia_acceso_unico"
            )
        ]

    def clean(self):
        if self.activo and self.guardia_id and not self.guardia.activo:
            raise ValidationError("El guardia debe estar activo.")
        if self.pk:
            anterior = type(self).objects.get(pk=self.pk)
            if anterior.activo and (
                not self.activo
                or self.acceso_id != anterior.acceso_id
                or self.guardia_id != anterior.guardia_id
            ):
                if (
                    anterior.acceso.activo
                    and not type(self)
                    .objects.filter(
                        acceso=anterior.acceso,
                        activo=True,
                        guardia__activo=True,
                    )
                    .exclude(pk=self.pk)
                    .exists()
                ):
                    raise ValidationError(
                        "Un acceso activo debe conservar al menos un guardia."
                    )

    def __str__(self):
        return f"{self.acceso} / {self.guardia}"
