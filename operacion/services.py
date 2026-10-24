from django.db import transaction
from core.models import auditar
from .models import Alerta, RegistroDemanda, Recorrido, GestionAlerta
from django.core.exceptions import PermissionDenied, ValidationError
from .forms import FinalizarRecorridoForm, AtenderAlertaForm


@transaction.atomic
def guardar_operacion(objeto, usuario, nuevo):
    if isinstance(objeto, RegistroDemanda) and nuevo:
        objeto.operador_responsable = usuario
    objeto.save()
    auditar(usuario, objeto, "CREAR" if nuevo else "ACTUALIZAR")
    alerta = None
    if (
        isinstance(objeto, RegistroDemanda)
        and objeto.cantidad_pasajeros * 2 >= objeto.capacidad_referencia * 3
    ):
        alerta, creada = Alerta.objects.get_or_create(
            registro_demanda=objeto,
            defaults={
                "tipo": "ALTA_DEMANDA",
                "linea": objeto.linea,
                "estacion": objeto.estacion,
                "nivel": "ALTA",
                "descripcion": f"Demanda estimada {objeto.cantidad_pasajeros}; referencia {objeto.capacidad_referencia}; umbral 150 %.",
            },
        )
        if creada:
            auditar(usuario, alerta, "CREAR")
    if isinstance(objeto, Recorrido) and objeto.ocupacion_estimada < 25:
        alerta, creada = Alerta.objects.get_or_create(
            recorrido=objeto,
            defaults={
                "tipo": "BAJA_OCUPACION",
                "linea": objeto.linea,
                "bus": objeto.bus,
                "descripcion": objeto.recomendacion,
            },
        )
        if creada:
            auditar(usuario, alerta, "CREAR")
    return alerta


@transaction.atomic
def finalizar_recorrido(pk, usuario, hora_final):
    if not usuario.has_perm("operacion.finalizar_recorrido"):
        raise PermissionDenied
    recorrido = Recorrido.objects.select_for_update().get(pk=pk)
    if not recorrido.puede_finalizar:
        raise ValidationError(
            "Solo se pueden finalizar recorridos programados o en curso."
        )
    form = FinalizarRecorridoForm(
        {"hora_final": hora_final}, recorrido=recorrido
    )
    if not form.is_valid():
        raise ValidationError(
            [error for errores in form.errors.values() for error in errores]
        )
    recorrido.hora_final = form.cleaned_data["hora_final"]
    recorrido.estado = "FINALIZADO"
    guardar_operacion(recorrido, usuario, False)
    auditar(usuario, recorrido, "CAMBIAR_ESTADO")
    return recorrido


@transaction.atomic
def atender_alerta(pk, usuario, descripcion, estado):
    if not usuario.has_perm("operacion.atender_alerta"):
        raise PermissionDenied
    form = AtenderAlertaForm({"descripcion": descripcion, "estado": estado})
    if not form.is_valid():
        raise ValidationError(
            [error for errores in form.errors.values() for error in errores]
        )
    alerta = Alerta.objects.select_for_update().get(pk=pk)
    gestion = GestionAlerta.objects.create(
        alerta=alerta,
        usuario=usuario,
        usuario_nombre=usuario.get_username(),
        estado_anterior=alerta.estado,
        estado_nuevo=form.cleaned_data["estado"],
        descripcion=form.cleaned_data["descripcion"],
    )
    anterior = alerta.estado
    alerta.estado = form.cleaned_data["estado"]
    alerta.save()
    auditar(
        usuario,
        alerta,
        "CAMBIAR_ESTADO" if anterior != alerta.estado else "ACTUALIZAR",
    )
    auditar(usuario, gestion, "CREAR")
    return gestion
