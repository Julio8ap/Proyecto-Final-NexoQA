from datetime import time
from decimal import Decimal
from django.contrib.auth.models import User, Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from accounts.roles import (
    configurar_roles,
    ADMINISTRATIVO,
    OPERATIVO,
)
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
)
from operacion.services import guardar_operacion
from personal.models import Piloto, Operador, Guardia, AsignacionGuardia


class Command(BaseCommand):
    help = "Carga datos ficticios DEMO una sola vez. No borra ni restablece información existente."

    @transaction.atomic
    def handle(self, *args, **options):
        configurar_roles()
        usuarios = {}
        for nombre, rol in [
            ("admin_demo", ADMINISTRATIVO),
            ("supervisor_demo", OPERATIVO),
            ("operador_demo", OPERATIVO),
        ]:
            usuario, nuevo = User.objects.get_or_create(username=nombre)
            if nuevo:
                usuario.set_password("DemoTransmetro2026!")
                usuario.first_name = "DEMOSTRATIVO"
                usuario.save()
                usuario.groups.add(Group.objects.get(name=rol))
            usuarios[nombre] = usuario
        if Municipalidad.objects.filter(
            nombre="DEMO Municipalidad ficticia"
        ).exists():
            self.stdout.write(
                "Datos DEMO ya existentes: se conservan sin duplicar ni restablecer claves."
            )
            return
        if Linea.objects.filter(nombre__startswith="DEMO").exists():
            raise CommandError(
                "Hay datos DEMO parciales. Revise antes de volver a cargar."
            )
        municipio = Municipalidad.objects.create(
            nombre="DEMO Municipalidad ficticia"
        )
        parqueos = [
            Parqueo.objects.create(
                nombre=f"DEMO Parqueo {i}", direccion=f"Dirección ficticia {i}"
            )
            for i in range(1, 4)
        ]
        pilotos = [
            Piloto.objects.create(
                nombres=f"Piloto DEMO {i}",
                apellidos="Ficticio",
                identificacion_interna=f"DEMO-P{i}",
                direccion="Dirección ficticia",
                residencia="Residencia demostrativa",
                nivel_educativo="Diversificado",
                historial_educativo="Historial ficticio para demostración",
                correo=f"piloto{i}@example.invalid",
            )
            for i in range(1, 9)
        ]
        for i in range(1, 6):
            Operador.objects.create(
                nombres=f"Operador DEMO {i}",
                apellidos="Ficticio",
                identificacion_interna=f"DEMO-O{i}",
            )
        guardias = [
            Guardia.objects.create(
                nombres=f"Guardia DEMO {i}",
                apellidos="Ficticio",
                identificacion_interna=f"DEMO-G{i}",
            )
            for i in range(1, 11)
        ]
        estaciones = []
        for i in range(1, 11):
            estacion = Estacion.objects.create(
                nombre=f"DEMO Estación {i:02}",
                municipalidad=municipio,
                direccion="Ubicación ficticia",
            )
            estaciones.append(estacion)
            acceso = Acceso.objects.create(
                nombre=f"DEMO Acceso {i:02}", estacion=estacion
            )
            AsignacionGuardia.objects.create(
                acceso=acceso, guardia=guardias[i - 1]
            )
            acceso.activo = True
            acceso.save()
        for i, indices in enumerate(
            [[0, 1, 2, 3], [3, 4, 5, 6], [6, 7, 8, 9]], 1
        ):
            linea = Linea.objects.create(
                nombre=f"DEMO Línea {i}", municipalidad=municipio
            )
            for orden, indice in enumerate(indices, 1):
                LineaEstacion.objects.create(
                    linea=linea,
                    estacion=estaciones[indice],
                    orden=orden,
                    distancia_desde_anterior=(
                        Decimal("0") if orden == 1 else Decimal("1.25")
                    ),
                )
            buses = [
                Bus.objects.create(
                    codigo=f"DEMO-B{i}{j:02}",
                    capacidad_maxima=100,
                    linea=linea,
                    parqueo=parqueos[i - 1],
                )
                for j in range(1, 7)
            ]
            linea.activo = True
            linea.save()
            for j in range(3):
                recorrido = Recorrido(
                    bus=buses[j],
                    linea=linea,
                    piloto=pilotos[(i + j) % 8],
                    fecha=timezone.localdate(),
                    hora_inicio=time(8 + j),
                    hora_final=time(9 + j),
                    ocupacion_estimada=[20, 25, 70][j],
                    estado="FINALIZADO",
                    observaciones="DEMOSTRATIVO",
                )
                guardar_operacion(recorrido, usuarios["supervisor_demo"], True)
                demanda = RegistroDemanda(
                    estacion=estaciones[indices[j]],
                    linea=linea,
                    fecha=timezone.localdate(),
                    hora=time(8 + j),
                    cantidad_pasajeros=[149, 150, 180][j],
                    observaciones="DEMOSTRATIVO",
                )
                guardar_operacion(demanda, usuarios["operador_demo"], True)
        self.stdout.write(
            self.style.SUCCESS(
                "DEMO: 3 líneas, 10 estaciones, 18 buses, 3 parqueos, 8 pilotos, 5 operadores, 10 guardias, 9 recorridos, 9 demandas y 9 alertas."
            )
        )
