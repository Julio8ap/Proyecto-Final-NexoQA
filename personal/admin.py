from django.contrib import admin
from core.admin import ConsultaAdmin
from .models import Piloto, Operador, Guardia, AsignacionGuardia

for modelo in [Piloto, Operador, Guardia, AsignacionGuardia]:
    admin.site.register(modelo, ConsultaAdmin)
