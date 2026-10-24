from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .forms import FinalizarRecorridoForm
from .models import Recorrido
from .services import finalizar_recorrido


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
