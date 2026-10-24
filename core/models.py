from django.conf import settings
from django.db import models


class ValidatedModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Auditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    fecha = models.DateTimeField(auto_now_add=True)
    modulo = models.CharField(max_length=80)
    accion = models.CharField(max_length=30)
    registro = models.CharField(max_length=100)
    descripcion = models.TextField()

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha:%d/%m/%Y} {self.accion}: {self.descripcion}"


def auditar(usuario, objeto, accion):
    Auditoria.objects.create(
        usuario=usuario,
        modulo=objeto._meta.label,
        accion=accion,
        registro=str(objeto.pk),
        descripcion=str(objeto),
    )
