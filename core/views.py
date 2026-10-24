from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import formulario
from .registry import MODULOS, permiso
from .models import auditar
from .labels import ETIQUETAS
from operacion.models import (
    Linea,
    Estacion,
    Bus,
    Recorrido,
    RegistroDemanda,
    Alerta,
)
from operacion.services import guardar_operacion


@login_required
def dashboard(request):
    resumen = [
        ("Líneas", Linea.objects.count()),
        ("Estaciones", Estacion.objects.count()),
        ("Buses", Bus.objects.count()),
        ("Buses activos", Bus.objects.filter(estado="ACTIVO").count()),
        (
            "Recorridos del día",
            Recorrido.objects.filter(fecha=timezone.localdate()).count(),
        ),
        (
            "Alertas pendientes",
            Alerta.objects.filter(estado="PENDIENTE").count(),
        ),
        (
            "Alertas atendidas",
            Alerta.objects.filter(estado="ATENDIDA").count(),
        ),
        ("Alertas cerradas", Alerta.objects.filter(estado="CERRADA").count()),
    ]
    return render(
        request,
        "dashboard.html",
        {
            "resumen": resumen,
            "alertas": Alerta.objects.select_related("linea")[:5],
            "demanda": RegistroDemanda.objects.select_related("estacion")[:5],
        },
    )


def obtener_modulo(request, modulo, accion):
    if modulo not in MODULOS:
        raise Http404
    modelo, titulo = MODULOS[modulo]
    if not request.user.has_perm(permiso(modelo, accion)):
        raise PermissionDenied
    return modelo, titulo


@login_required
def listado(request, modulo):
    modelo, titulo = obtener_modulo(request, modulo, "view")
    objetos = modelo.objects.all().order_by("-pk")
    if modulo == "recorridos":
        objetos = objetos.select_related("linea", "bus")
        if request.GET.get("linea"):
            try:
                numero = int(request.GET["linea"])
                if not 1 <= numero <= 2**63 - 1:
                    raise ValueError
                objetos = objetos.filter(linea_id=numero)
            except ValueError:
                objetos = objetos.none()
    q = request.GET.get("q", "").strip()
    if q:
        nombres = {c.name for c in modelo._meta.fields}
        campo = next(
            (
                c
                for c in [
                    "nombre",
                    "codigo",
                    "apellidos",
                    "username",
                    "descripcion",
                ]
                if c in nombres
            ),
            None,
        )
        if campo:
            objetos = objetos.filter(**{f"{campo}__icontains": q})
    return render(
        request,
        "listado.html",
        {
            "titulo": titulo,
            "modulo": modulo,
            "lineas": Linea.objects.all() if modulo == "recorridos" else [],
            "pagina": Paginator(objetos, 20).get_page(request.GET.get("page")),
            "puede_crear": modulo not in ["alertas", "auditoria"]
            and request.user.has_perm(permiso(modelo, "add")),
            "puede_editar": modulo not in ["auditoria", "alertas"]
            and request.user.has_perm(permiso(modelo, "change")),
        },
    )


@login_required
def detalle(request, modulo, pk):
    modelo, titulo = obtener_modulo(request, modulo, "view")
    objeto = get_object_or_404(modelo, pk=pk)
    campos = []
    for campo in modelo._meta.fields:
        if campo.name in [
            "password",
            "last_login",
            "is_superuser",
            "is_staff",
        ]:
            continue
        valor = getattr(objeto, campo.name)
        mostrar = getattr(objeto, f"get_{campo.name}_display", None)
        campos.append(
            (
                ETIQUETAS.get(campo.name, campo.verbose_name),
                mostrar() if mostrar else valor,
            )
        )
    return render(
        request,
        "detalle.html",
        {
            "titulo": titulo,
            "modulo": modulo,
            "objeto": objeto,
            "campos": campos,
            "gestiones": (
                objeto.gestiones.all() if modulo == "alertas" else None
            ),
            "recomendacion": getattr(objeto, "recomendacion", ""),
            "distancia": (
                objeto.distancia_total if isinstance(objeto, Linea) else None
            ),
        },
    )


@login_required
def editar(request, modulo, pk=None):
    modelo, titulo = obtener_modulo(request, modulo, "change" if pk else "add")
    if modulo == "auditoria" or (modulo == "alertas" and pk is None):
        raise PermissionDenied
    objeto = get_object_or_404(modelo, pk=pk) if pk else None
    if modulo == "alertas":
        return redirect("atender_alerta", pk=pk)
    if (
        modulo == "usuarios"
        and objeto
        and objeto.is_superuser
        and not request.user.is_superuser
    ):
        raise PermissionDenied
    clase = formulario(modelo, objeto)
    form = clase(request.POST or None, instance=objeto)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                if modulo == "usuarios":
                    if (
                        objeto
                        and objeto.pk == request.user.pk
                        and not form.cleaned_data["is_active"]
                    ):
                        raise ValidationError(
                            "No puede desactivar su propia cuenta."
                        )
                    guardado = form.save()
                    auditar(
                        request.user, guardado, "ACTUALIZAR" if pk else "CREAR"
                    )
                    alerta = None
                else:
                    guardado = form.save(commit=False)
                    alerta = guardar_operacion(
                        guardado, request.user, pk is None
                    )
                    form.save_m2m()
            messages.success(request, "Registro guardado correctamente.")
            if alerta:
                messages.warning(request, alerta.descripcion)
            return redirect("detalle", modulo=modulo, pk=guardado.pk)
        except (ValidationError, IntegrityError) as error:
            form.add_error(
                None,
                (
                    "; ".join(error.messages)
                    if isinstance(error, ValidationError)
                    else "Conflicto de integridad. Revise los datos e intente nuevamente."
                ),
            )
    return render(
        request,
        "formulario.html",
        {"form": form, "titulo": titulo, "modulo": modulo},
    )
