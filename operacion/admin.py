from django.contrib import admin
from core.admin import ConsultaAdmin
from .models import (
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
    GestionAlerta,
)

for modelo in [
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
    GestionAlerta,
]:
    admin.site.register(modelo, ConsultaAdmin)
