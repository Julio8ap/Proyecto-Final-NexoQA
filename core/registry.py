from django.contrib.auth.models import User
from core.models import Auditoria
from operacion.models import (
    Municipalidad,
    Linea,
    Estacion,
    LineaEstacion,
    Acceso,
    Parqueo,
    Bus,
    Recorrido,
    RegistroDemanda,
    Alerta,
)
from personal.models import Piloto, Operador, Guardia, AsignacionGuardia

MODULOS = {
    "municipalidades": (Municipalidad, "Municipalidades"),
    "lineas": (Linea, "Líneas"),
    "estaciones": (Estacion, "Estaciones"),
    "tramos": (LineaEstacion, "Estaciones por línea"),
    "accesos": (Acceso, "Accesos"),
    "parqueos": (Parqueo, "Parqueos"),
    "buses": (Bus, "Buses y asignación de línea"),
    "pilotos": (Piloto, "Pilotos"),
    "operadores": (Operador, "Operadores"),
    "guardias": (Guardia, "Guardias"),
    "asignaciones": (AsignacionGuardia, "Asignaciones de guardias"),
    "recorridos": (Recorrido, "Recorridos"),
    "demanda": (RegistroDemanda, "Demanda estimada"),
    "alertas": (Alerta, "Alertas"),
    "auditoria": (Auditoria, "Auditoría"),
    "usuarios": (User, "Usuarios"),
}


def permiso(modelo, accion):
    return f"{modelo._meta.app_label}.{accion}_{modelo._meta.model_name}"
