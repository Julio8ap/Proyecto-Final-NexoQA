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
]:
    admin.site.register(modelo, ConsultaAdmin)
