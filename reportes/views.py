from datetime import date
import csv
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import HttpResponse
from core.labels import ETIQUETAS
from operacion.models import (
    Linea,
    Estacion,
    LineaEstacion,
    Bus,
    Recorrido,
    RegistroDemanda,
    Alerta,
)


@login_required
def reportes(request):
    if not request.user.has_perm("operacion.view_linea"):
        raise PermissionDenied
    tipos = {
        "estaciones": (Estacion, "Estaciones"),
        "lineas": (Linea, "Líneas"),
        "tramos": (LineaEstacion, "Líneas y estaciones"),
        "buses": (Bus, "Buses por línea"),
        "recorridos": (Recorrido, "Recorridos realizados"),
        "demanda": (RegistroDemanda, "Demanda por estación"),
        "alertas": (Alerta, "Alertas generadas"),
    }
    tipo = request.GET.get("tipo", "tramos")
    if tipo not in tipos:
        tipo = "tramos"
    modelo, titulo = tipos[tipo]
    if not request.user.has_perm(
        f"{modelo._meta.app_label}.view_{modelo._meta.model_name}"
    ):
        raise PermissionDenied
    consulta = modelo.objects.all()
    errores = []
    for filtro in ["linea", "estacion"]:
        valor = request.GET.get(filtro, "")
        if valor:
            try:
                numero = int(valor)
                if not 1 <= numero <= 2**63 - 1:
                    raise ValueError
            except ValueError:
                errores.append(f"Filtro {filtro} inválido.")
                continue
            if filtro == "linea":
                campo = (
                    "pk"
                    if modelo == Linea
                    else (
                        "lineaestacion__linea_id"
                        if modelo == Estacion
                        else "linea_id"
                    )
                )
            else:
                campo = (
                    "pk"
                    if modelo == Estacion
                    else (
                        "lineaestacion__estacion_id"
                        if modelo == Linea
                        else (
                            "linea__lineaestacion__estacion_id"
                            if modelo in [Bus, Recorrido]
                            else "estacion_id"
                        )
                    )
                )
            consulta = consulta.filter(**{campo: numero})
    fecha = request.GET.get("fecha")
    if fecha:
        try:
            date.fromisoformat(fecha)
            if modelo in [Recorrido, RegistroDemanda]:
                consulta = consulta.filter(fecha=fecha)
            elif modelo == Alerta:
                consulta = consulta.filter(fecha_hora__date=fecha)
        except ValueError:
            errores.append("Fecha inválida.")
    estado = request.GET.get("estado", "")
    nombres = {c.name for c in modelo._meta.fields}
    if estado:
        if "estado" in nombres:
            consulta = consulta.filter(estado=estado)
        elif "activo" in nombres:
            if estado in ["ACTIVO", "INACTIVO"]:
                consulta = consulta.filter(activo=estado == "ACTIVO")
    columnas = {
        "estaciones": ["nombre", "municipalidad", "activo"],
        "lineas": ["nombre", "municipalidad", "distancia_total", "activo"],
        "tramos": ["linea", "orden", "estacion", "distancia_desde_anterior"],
        "buses": ["codigo", "linea", "capacidad_maxima", "parqueo", "estado"],
        "recorridos": [
            "fecha",
            "hora_inicio",
            "hora_final",
            "bus",
            "linea",
            "piloto",
            "ocupacion_estimada",
            "estado",
        ],
        "demanda": [
            "fecha",
            "hora",
            "linea",
            "estacion",
            "cantidad_pasajeros",
            "capacidad_referencia",
            "operador_responsable",
        ],
        "alertas": [
            "fecha_hora",
            "tipo",
            "linea",
            "estacion",
            "descripcion",
            "estado",
        ],
    }[tipo]
    consulta = consulta.distinct()
    encabezados = [
        ETIQUETAS.get(c, c.replace("_", " ").title()) for c in columnas
    ]
    if request.GET.get("descargar") == "csv":
        if not request.user.has_perm("operacion.descargar_reportes"):
            raise PermissionDenied
        if errores:
            return HttpResponse(
                "; ".join(errores),
                status=400,
                content_type="text/plain; charset=utf-8",
            )
        respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
        respuesta["Content-Disposition"] = (
            f'attachment; filename="transmetro_{tipo}.csv"'
        )
        respuesta.write("\ufeff")
        salida = csv.writer(respuesta)
        salida.writerow(encabezados)
        for objeto in consulta.order_by("-pk").iterator():
            fila = []
            for campo in columnas:
                valor = str(
                    getattr(objeto, campo)
                    if getattr(objeto, campo) is not None
                    else ""
                )
                # Evita que hojas de cálculo ejecuten fórmulas de datos ingresados.
                if valor.lstrip().startswith(
                    ("=", "+", "-", "@", "\t", "\r", "\n")
                ):
                    valor = "'" + valor
                fila.append(valor)
            salida.writerow(fila)
        return respuesta
    total = consulta.count()
    pagina = Paginator(consulta.order_by("-pk"), 50).get_page(
        request.GET.get("page")
    )
    filas = [[getattr(o, c) for c in columnas] for o in pagina]
    return render(
        request,
        "reportes.html",
        {
            "titulo": titulo,
            "tipos": tipos,
            "tipo": tipo,
            "columnas": encabezados,
            "filas": filas,
            "lineas": Linea.objects.all(),
            "estaciones": Estacion.objects.all(),
            "total": total,
            "pagina": pagina,
            "errores": errores,
            "estados": [
                "ACTIVO",
                "INACTIVO",
                "MANTENIMIENTO",
                "PROGRAMADO",
                "EN_CURSO",
                "FINALIZADO",
                "CANCELADO",
                "PENDIENTE",
                "ATENDIDA",
                "CERRADA",
            ],
        },
    )
