from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .forms import FinalizarRecorridoForm, AtenderAlertaForm
from .models import Recorrido, Alerta
from .services import finalizar_recorrido, atender_alerta


@login_required
@permission_required("operacion.finalizar_recorrido", raise_exception=True)
@require_http_methods(["GET", "POST"])
def finalizar(request, pk):
    recorrido = get_object_or_404(Recorrido, pk=pk)
    form = FinalizarRecorridoForm(
        request.POST if request.method == "POST" else None,
        recorrido=recorrido,
    )
    if request.method == "POST" and form.is_valid():
        try:
            finalizar_recorrido(
                pk, request.user, form.cleaned_data["hora_final"]
            )
            messages.success(request, "Recorrido finalizado correctamente.")
            return redirect("listado", modulo="recorridos")
        except ValidationError as error:
            form.add_error(None, error)
    elif request.method == "GET" and not recorrido.puede_finalizar:
        messages.error(request, "Este recorrido ya finalizó o está cancelado.")
        return redirect("listado", modulo="recorridos")
    return render(
        request,
        "finalizar_recorrido.html",
        {
            "titulo": "Finalizar recorrido",
            "recorrido": recorrido,
            "form": form,
        },
    )


@login_required
@permission_required("operacion.atender_alerta", raise_exception=True)
@require_http_methods(["GET", "POST"])
def atender(request, pk):
    alerta = get_object_or_404(
        Alerta.objects.select_related("linea", "estacion", "bus"), pk=pk
    )
    form = AtenderAlertaForm(
        request.POST if request.method == "POST" else None,
        initial={
            "estado": (
                "ATENDIDA" if alerta.estado == "PENDIENTE" else alerta.estado
            )
        },
    )
    if request.method == "POST" and form.is_valid():
        try:
            atender_alerta(pk, request.user, **form.cleaned_data)
            messages.success(
                request,
                "Gestión registrada y estado de la alerta actualizado.",
            )
            return redirect("detalle", modulo="alertas", pk=pk)
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request,
        "atender_alerta.html",
        {
            "titulo": "Atender alerta",
            "alerta": alerta,
            "form": form,
            "gestiones": alerta.gestiones.all(),
        },
    )
