from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from core.models import auditar


@login_required
@permission_required("auth.delete_user", raise_exception=True)
@require_http_methods(["GET", "POST"])
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(get_user_model(), pk=pk)
    if usuario.is_superuser and not request.user.is_superuser:
        raise PermissionDenied
    error = ""
    if usuario.pk == request.user.pk:
        error = "No puede eliminar su propia cuenta."
    if request.method == "POST" and not error:
        try:
            with transaction.atomic():
                usuario = (
                    get_user_model().objects.select_for_update().get(pk=pk)
                )
                auditar(request.user, usuario, "ELIMINAR")
                usuario.delete()
            messages.success(request, "Usuario eliminado correctamente.")
            return redirect("listado", modulo="usuarios")
        except ProtectedError:
            error = (
                "Este usuario tiene registros de demanda vinculados y no se puede "
                "eliminar para conservar el historial. Puede desactivarlo desde Editar."
            )
    return render(
        request,
        "eliminar_usuario.html",
        {
            "titulo": "Eliminar usuario",
            "usuario_objetivo": usuario,
            "error": error,
        },
    )
