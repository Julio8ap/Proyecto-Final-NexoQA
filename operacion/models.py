from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils import timezone
from core.models import ValidatedModel


class Catalogo(ValidatedModel):
    nombre = models.CharField(max_length=120, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Municipalidad(Catalogo):
    pass


def validar_flota(linea, buses=None, estaciones=None):
    estaciones = (
        linea.lineaestacion_set.count() if estaciones is None else estaciones
    )
    buses = linea.bus_set.count() if buses is None else buses
    if estaciones < 1 or not estaciones <= buses <= 2 * estaciones:
        raise ValidationError(
            "Una línea activa requiere entre N y 2N buses, donde N es su número de estaciones."
        )


class Linea(Catalogo):
    municipalidad = models.ForeignKey(Municipalidad, on_delete=models.PROTECT)
    activo = models.BooleanField(default=False)
    estaciones = models.ManyToManyField("Estacion", through="LineaEstacion")

    @property
    def distancia_total(self):
        return self.lineaestacion_set.aggregate(
            total=Sum("distancia_desde_anterior")
        )["total"] or Decimal("0")

    def clean(self):
        if self.activo:
            if not self.pk:
                raise ValidationError(
                    "Cree la línea inactiva y configure estaciones y buses antes de activarla."
                )
            validar_flota(self)
            if (
                not self.estaciones.filter(activo=True).count()
                == self.estaciones.count()
            ):
                raise ValidationError("Las estaciones deben estar activas.")
            accesos = Acceso.objects.filter(estacion__linea=self, activo=True)
            if not accesos.exists() or any(
                not a.tiene_guardia for a in accesos
            ):
                raise ValidationError(
                    "La línea necesita accesos activos con guardia asignado."
                )


class Estacion(Catalogo):
    municipalidad = models.ForeignKey(Municipalidad, on_delete=models.PROTECT)
    direccion = models.CharField(max_length=250, blank=True)

    def clean(self):
        if (
            self.pk
            and not self.activo
            and self.linea_set.filter(activo=True).exists()
        ):
            raise ValidationError(
                "Desactive primero las líneas que utilizan esta estación."
            )


class LineaEstacion(ValidatedModel):
    linea = models.ForeignKey(Linea, on_delete=models.PROTECT)
    estacion = models.ForeignKey(Estacion, on_delete=models.PROTECT)
    orden = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    distancia_desde_anterior = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["linea", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["linea", "orden"], name="orden_linea_unico"
            ),
            models.UniqueConstraint(
                fields=["linea", "estacion"], name="estacion_linea_unica"
            ),
            models.CheckConstraint(
                condition=Q(orden__gte=1) & Q(distancia_desde_anterior__gte=0),
                name="tramo_positivo",
            ),
        ]

    def clean(self):
        if self.linea_id and self.linea.activo:
            if self.estacion_id and not self.estacion.activo:
                raise ValidationError(
                    "Una línea activa solo admite estaciones activas."
                )
            total = (
                type(self)
                .objects.filter(linea=self.linea)
                .exclude(pk=self.pk)
                .count()
                + 1
            )
            validar_flota(self.linea, estaciones=total)
        if self.pk:
            anterior = type(self).objects.get(pk=self.pk)
            if anterior.linea_id != self.linea_id and anterior.linea.activo:
                validar_flota(
                    anterior.linea,
                    estaciones=anterior.linea.lineaestacion_set.count() - 1,
                )

    def __str__(self):
        return f"{self.linea} · {self.orden}. {self.estacion} · {self.distancia_desde_anterior} km"


class Acceso(Catalogo):
    estacion = models.ForeignKey(Estacion, on_delete=models.PROTECT)
    activo = models.BooleanField(default=False)

    @property
    def tiene_guardia(self):
        return self.asignacionguardia_set.filter(
            activo=True, guardia__activo=True
        ).exists()

    def clean(self):
        if self.activo and (not self.pk or not self.tiene_guardia):
            raise ValidationError(
                "Cree el acceso inactivo, asigne un guardia y después actívelo."
            )


class Parqueo(Catalogo):
    direccion = models.CharField(max_length=250)


class Bus(ValidatedModel):
    codigo = models.CharField(max_length=30, unique=True)
    capacidad_maxima = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("ACTIVO", "Activo"),
            ("INACTIVO", "Inactivo"),
            ("MANTENIMIENTO", "Mantenimiento"),
        ],
        default="ACTIVO",
    )
    linea = models.ForeignKey(
        Linea, null=True, blank=True, on_delete=models.PROTECT
    )
    parqueo = models.ForeignKey(Parqueo, on_delete=models.PROTECT)

    class Meta:
        ordering = ["codigo"]
        constraints = [
            models.CheckConstraint(
                condition=Q(capacidad_maxima__gt=0), name="capacidad_positiva"
            )
        ]

    def clean(self):
        if self.linea_id:
            n = self.linea.lineaestacion_set.count()
            total = (
                type(self)
                .objects.filter(linea=self.linea)
                .exclude(pk=self.pk)
                .count()
                + 1
            )
            if total > 2 * n:
                raise ValidationError(
                    "La línea no puede superar el doble de buses que estaciones."
                )
            if self.linea.activo:
                validar_flota(self.linea, buses=total)
        if self.pk:
            anterior = type(self).objects.get(pk=self.pk)
            if (
                anterior.linea_id
                and anterior.linea_id != self.linea_id
                and anterior.linea.activo
            ):
                validar_flota(
                    anterior.linea, buses=anterior.linea.bus_set.count() - 1
                )

    def __str__(self):
        return f"{self.codigo} · {self.capacidad_maxima} pasajeros · {self.get_estado_display()}"


class Recorrido(ValidatedModel):
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT)
    linea = models.ForeignKey(Linea, on_delete=models.PROTECT)
    piloto = models.ForeignKey("personal.Piloto", on_delete=models.PROTECT)
    fecha = models.DateField(default=timezone.localdate)
    hora_inicio = models.TimeField()
    hora_final = models.TimeField(null=True, blank=True)
    ocupacion_estimada = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje estimado manualmente (0–100); no es ocupación exacta.",
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            (x, x.replace("_", " ").title())
            for x in ["PROGRAMADO", "EN_CURSO", "FINALIZADO", "CANCELADO"]
        ],
        default="PROGRAMADO",
    )
    observaciones = models.TextField(blank=True)
    capacidad_referencia = models.PositiveIntegerField(editable=False)

    class Meta:
        ordering = ["-fecha", "-hora_inicio"]
        permissions = [
            ("finalizar_recorrido", "Puede finalizar recorridos"),
            ("descargar_reportes", "Puede descargar reportes"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(ocupacion_estimada__gte=0)
                & Q(ocupacion_estimada__lte=100),
                name="ocupacion_porcentaje",
            ),
            models.CheckConstraint(
                condition=Q(hora_final__isnull=True)
                | Q(hora_final__gte=models.F("hora_inicio")),
                name="horas_recorrido",
            ),
        ]

    def clean(self):
        if (
            self.hora_final
            and self.hora_inicio
            and self.hora_final < self.hora_inicio
        ):
            raise ValidationError(
                "La hora final no puede ser anterior a la inicial; registre por día."
            )
        if self.estado == "FINALIZADO" and not self.hora_final:
            raise ValidationError(
                "Un recorrido finalizado requiere hora final."
            )
        if self.bus_id and self.linea_id and self.piloto_id:
            anterior = (
                type(self).objects.filter(pk=self.pk).first()
                if self.pk
                else None
            )
            nuevos = not anterior or (
                anterior.bus_id,
                anterior.linea_id,
                anterior.piloto_id,
            ) != (self.bus_id, self.linea_id, self.piloto_id)
            if nuevos and (
                self.bus.linea_id != self.linea_id
                or self.bus.estado != "ACTIVO"
                or not self.linea.activo
                or not self.piloto.activo
            ):
                raise ValidationError(
                    "Use un piloto activo y un bus activo asignado a la línea activa seleccionada."
                )
            if not self.capacidad_referencia:
                self.capacidad_referencia = self.bus.capacidad_maxima

    @property
    def puede_finalizar(self):
        return self.estado in ["PROGRAMADO", "EN_CURSO"]

    @property
    def recomendacion(self):
        return (
            "Aplicar espera adicional de 5 minutos."
            if self.ocupacion_estimada < 25
            else ""
        )

    def __str__(self):
        return f"{self.fecha} {self.bus.codigo} / {self.linea} / {self.get_estado_display()}"


class RegistroDemanda(ValidatedModel):
    estacion = models.ForeignKey(Estacion, on_delete=models.PROTECT)
    linea = models.ForeignKey(Linea, on_delete=models.PROTECT)
    fecha = models.DateField(default=timezone.localdate)
    hora = models.TimeField()
    cantidad_pasajeros = models.PositiveIntegerField()
    operador_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, editable=False
    )
    observaciones = models.TextField(blank=True)
    capacidad_referencia = models.PositiveIntegerField(editable=False)

    class Meta:
        ordering = ["-fecha", "-hora"]
        constraints = [
            models.CheckConstraint(
                condition=Q(cantidad_pasajeros__gte=0),
                name="demanda_no_negativa",
            )
        ]

    def clean(self):
        if self.fecha and self.fecha > timezone.localdate():
            raise ValidationError(
                "La demanda observada no puede tener fecha futura."
            )
        if self.linea_id and self.estacion_id:
            if (
                not self.linea.activo
                or not self.estacion.activo
                or not LineaEstacion.objects.filter(
                    linea=self.linea, estacion=self.estacion
                ).exists()
            ):
                raise ValidationError(
                    "Seleccione una estación de la línea activa."
                )
            if not self.capacidad_referencia:
                referencia = self.linea.bus_set.filter(
                    estado="ACTIVO"
                ).aggregate(n=models.Max("capacidad_maxima"))["n"]
                if not referencia:
                    raise ValidationError(
                        "La línea necesita un bus activo como referencia de capacidad."
                    )
                self.capacidad_referencia = referencia

    def __str__(self):
        return f"{self.fecha} · {self.estacion} · demanda estimada: {self.cantidad_pasajeros}"


class Alerta(ValidatedModel):
    tipo = models.CharField(
        max_length=25,
        choices=[
            ("ALTA_DEMANDA", "Alta demanda"),
            ("BAJA_OCUPACION", "Baja ocupación"),
        ],
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    estacion = models.ForeignKey(
        Estacion, null=True, blank=True, on_delete=models.PROTECT
    )
    linea = models.ForeignKey(Linea, on_delete=models.PROTECT)
    bus = models.ForeignKey(
        Bus, null=True, blank=True, on_delete=models.PROTECT
    )
    registro_demanda = models.OneToOneField(
        RegistroDemanda, null=True, blank=True, on_delete=models.PROTECT
    )
    recorrido = models.OneToOneField(
        Recorrido, null=True, blank=True, on_delete=models.PROTECT
    )
    descripcion = models.TextField()
    nivel = models.CharField(
        max_length=20,
        default="INFORMATIVA",
        choices=[("ALTA", "Alta"), ("INFORMATIVA", "Informativa")],
    )
    estado = models.CharField(
        max_length=15,
        choices=[(x, x.title()) for x in ["PENDIENTE", "ATENDIDA", "CERRADA"]],
        default="PENDIENTE",
    )

    class Meta:
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.get_tipo_display()} · {self.linea} · {self.get_estado_display()} · {self.descripcion}"
