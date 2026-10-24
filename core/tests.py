from datetime import time, timedelta
from decimal import Decimal
from io import StringIO
from unittest.mock import patch
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from core.models import Auditoria
from core.registry import MODULOS
from operacion.models import (
    Municipalidad,
    Linea,
    Estacion,
    LineaEstacion,
    Acceso,
    Bus,
    Recorrido,
    RegistroDemanda,
    Alerta,
)
from operacion.services import guardar_operacion
from personal.models import Guardia, AsignacionGuardia, Piloto, Operador
from accounts.roles import configurar_roles, ADMINISTRATIVO, OPERATIVO
from core.forms import formulario


class TransmetroTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())
        cls.admin = User.objects.get(username="admin_demo")
        cls.supervisor = User.objects.get(username="supervisor_demo")
        cls.operador = User.objects.get(username="operador_demo")
        cls.linea = Linea.objects.first()
        cls.estacion = cls.linea.estaciones.first()
        cls.bus = cls.linea.bus_set.first()

    def demanda(self, cantidad, **cambios):
        datos = {
            "linea": self.linea,
            "estacion": self.estacion,
            "fecha": timezone.localdate(),
            "hora": time(12),
            "cantidad_pasajeros": cantidad,
        }
        datos.update(cambios)
        return RegistroDemanda(**datos)

    def recorrido(self, ocupacion=25, **cambios):
        datos = {
            "bus": self.bus,
            "linea": self.linea,
            "piloto": Piloto.objects.first(),
            "fecha": timezone.localdate(),
            "hora_inicio": time(12),
            "ocupacion_estimada": Decimal(ocupacion),
        }
        datos.update(cambios)
        return Recorrido(**datos)

    def test_01_autenticacion_y_logout(self):
        self.assertEqual(self.client.get("/").status_code, 302)
        self.assertFalse(
            self.client.login(username="admin_demo", password="incorrecta")
        )
        self.assertTrue(
            self.client.login(
                username="admin_demo", password="DemoTransmetro2026!"
            )
        )
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/logout/").status_code, 405)
        self.assertEqual(self.client.post("/logout/").status_code, 302)

    def test_02_operativo_consulta_y_finaliza(self):
        self.client.force_login(self.operador)
        for modulo in MODULOS:
            self.assertEqual(
                self.client.get(reverse("crear", args=[modulo])).status_code,
                403,
                modulo,
            )
            objeto = MODULOS[modulo][0].objects.first()
            if objeto:
                self.assertEqual(
                    self.client.post(
                        reverse("editar", args=[modulo, objeto.pk]), {}
                    ).status_code,
                    403,
                    modulo,
                )
            if modulo not in ["usuarios", "auditoria"]:
                self.assertEqual(
                    self.client.get(
                        reverse("listado", args=[modulo])
                    ).status_code,
                    200,
                    modulo,
                )
        self.assertEqual(self.client.get("/reportes/").status_code, 200)
        self.assertEqual(
            self.client.get("/gestion/usuarios/").status_code, 403
        )
        for estado in ["PROGRAMADO", "EN_CURSO"]:
            recorrido = self.recorrido(
                50,
                fecha=timezone.localdate() - timedelta(days=1),
                hora_inicio=time(8),
                estado=estado,
            )
            guardar_operacion(recorrido, self.admin, True)
            url = reverse("finalizar_recorrido", args=[recorrido.pk])
            self.assertContains(
                self.client.get(
                    "/gestion/recorridos/", {"linea": self.linea.pk}
                ),
                url,
            )
            self.assertEqual(self.client.get(url).status_code, 200)
            recorrido.refresh_from_db()
            self.assertEqual(recorrido.estado, estado)  # GET nunca modifica.
            respuesta = self.client.post(
                url,
                {
                    "hora_final": "09:00",
                    "bus": 999999,
                    "linea": 999999,
                    "ocupacion_estimada": 99,
                },
            )
            self.assertEqual(respuesta.status_code, 302)
            recorrido.refresh_from_db()
            self.assertEqual(recorrido.estado, "FINALIZADO")
            self.assertEqual(recorrido.hora_final, time(9))
            self.assertEqual(recorrido.bus, self.bus)
            self.assertEqual(recorrido.linea, self.linea)
            self.assertEqual(recorrido.ocupacion_estimada, 50)
            self.assertTrue(
                Auditoria.objects.filter(
                    usuario=self.operador,
                    accion="CAMBIAR_ESTADO",
                    registro=str(recorrido.pk),
                ).exists()
            )
            cantidad = Auditoria.objects.count()
            self.assertEqual(
                self.client.post(url, {"hora_final": "10:00"}).status_code, 200
            )
            self.assertEqual(Auditoria.objects.count(), cantidad)
            self.assertNotContains(
                self.client.get("/gestion/recorridos/"), url
            )
        for estado in ["CANCELADO", "FINALIZADO"]:
            recorrido = self.recorrido(50, estado=estado, hora_final=time(13))
            guardar_operacion(recorrido, self.admin, True)
            url = reverse("finalizar_recorrido", args=[recorrido.pk])
            self.assertEqual(
                self.client.post(url, {"hora_final": "14:00"}).status_code, 200
            )
            recorrido.refresh_from_db()
            self.assertEqual(recorrido.estado, estado)
        recorrido = self.recorrido(
            50, fecha=timezone.localdate() + timedelta(days=1)
        )
        guardar_operacion(recorrido, self.admin, True)
        url = reverse("finalizar_recorrido", args=[recorrido.pk])
        self.assertEqual(
            self.client.post(url, {"hora_final": "13:00"}).status_code, 200
        )
        recorrido.refresh_from_db()
        self.assertEqual(recorrido.estado, "PROGRAMADO")
        self.assertEqual(
            self.client.post(url, {"hora_final": "11:00"}).status_code, 200
        )
        self.client.force_login(
            User.objects.create_user("sin_rol", password="ClavePrueba!2026")
        )
        self.assertEqual(
            self.client.post(url, {"hora_final": "13:00"}).status_code, 403
        )
        self.assertEqual(
            self.client.get("/reportes/?descargar=csv").status_code, 403
        )

    def test_03_migracion_a_dos_roles(self):
        self.client.force_login(self.supervisor)
        self.assertEqual(
            self.client.get("/gestion/lineas/nuevo/").status_code, 403
        )
        self.assertEqual(
            self.client.post(
                "/gestion/municipalidades/nuevo/", {"nombre": "Intrusión"}
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get("/gestion/usuarios/").status_code, 403
        )
        legado = User.objects.create_user("legado", password="Conservar!2026")
        grupo = Group.objects.create(name="SUPERVISOR")
        legado.groups.add(grupo)
        grupo_admin = Group.objects.create(name="ADMINISTRADOR")
        self.admin.groups.set([grupo_admin])
        configurar_roles()
        configurar_roles()
        self.assertEqual(
            set(Group.objects.values_list("name", flat=True)),
            {ADMINISTRATIVO, OPERATIVO},
        )
        legado.refresh_from_db()
        self.assertTrue(legado.check_password("Conservar!2026"))
        self.assertEqual(legado.groups.get().name, OPERATIVO)
        self.assertEqual(self.admin.groups.get().name, ADMINISTRATIVO)
        from accounts.forms import UsuarioCreacionForm

        self.assertEqual(
            set(
                UsuarioCreacionForm()
                .fields["rol"]
                .queryset.values_list("name", flat=True)
            ),
            {ADMINISTRATIVO, OPERATIVO},
        )

    def test_04_navegacion_administrador(self):
        self.client.force_login(self.admin)
        for modulo, (modelo, _) in MODULOS.items():
            with self.subTest(modulo=modulo):
                self.assertEqual(
                    self.client.get(
                        reverse("listado", args=[modulo])
                    ).status_code,
                    200,
                )
                objeto = modelo.objects.first()
                if objeto:
                    respuesta = self.client.get(
                        reverse("detalle", args=[modulo, objeto.pk])
                    )
                    self.assertEqual(respuesta.status_code, 200)
                    if modulo != "auditoria":
                        self.assertNotContains(respuesta, "pbkdf2_")
                if modulo not in ["auditoria", "alertas"]:
                    self.assertEqual(
                        self.client.get(
                            reverse("crear", args=[modulo])
                        ).status_code,
                        200,
                    )

                if objeto and modulo != "auditoria":
                    self.assertEqual(
                        self.client.get(
                            reverse("editar", args=[modulo, objeto.pk])
                        ).status_code,
                        200,
                    )

        respuesta = self.client.get("/")
        self.assertContains(respuesta, "Sistema Municipal")
        self.assertContains(respuesta, "Desarrollado por nexoQA")
        self.assertNotContains(respuesta, "ENTORNO ACADÉMICO")
        self.assertEqual(
            formulario(Bus)().fields["capacidad_maxima"].label,
            "Capacidad máxima (pasajeros)",
        )
        self.assertIn(
            "(km)",
            formulario(LineaEstacion)()
            .fields["distancia_desde_anterior"]
            .label,
        )
        self.assertIn(
            "(%)", formulario(Recorrido)().fields["ocupacion_estimada"].label
        )
        self.assertIn(
            "(personas)",
            formulario(RegistroDemanda)().fields["cantidad_pasajeros"].label,
        )

    def test_05_csrf_y_metodos(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.admin)
        self.assertEqual(
            cliente.post(
                "/gestion/municipalidades/nuevo/", {"nombre": "Sin token"}
            ).status_code,
            403,
        )
        self.assertFalse(
            Municipalidad.objects.filter(nombre="Sin token").exists()
        )
        recorrido = self.recorrido(
            50,
            fecha=timezone.localdate() - timedelta(days=1),
            hora_inicio=time(8),
        )
        guardar_operacion(recorrido, self.admin, True)
        self.assertEqual(
            cliente.post(
                reverse("finalizar_recorrido", args=[recorrido.pk]),
                {"hora_final": "09:00"},
            ).status_code,
            403,
        )
        recorrido.refresh_from_db()
        self.assertEqual(recorrido.estado, "PROGRAMADO")

    def test_06_bus_capacidad_parqueo(self):
        for cambios in [{"capacidad_maxima": 0}, {"parqueo": None}]:
            bus = Bus(
                codigo="PRUEBA", capacidad_maxima=100, parqueo=self.bus.parqueo
            )
            for clave, valor in cambios.items():
                setattr(bus, clave, valor)
            with self.assertRaises(ValidationError):
                bus.save()

    def test_07_maximo_buses(self):
        for i in range(2):
            Bus.objects.create(
                codigo=f"MAX{i}",
                capacidad_maxima=100,
                parqueo=self.bus.parqueo,
                linea=self.linea,
            )
        with self.assertRaises(ValidationError):
            Bus.objects.create(
                codigo="MAX3",
                capacidad_maxima=100,
                parqueo=self.bus.parqueo,
                linea=self.linea,
            )

    def test_08_minimo_buses_y_asignacion_opcional(self):
        buses = list(self.linea.bus_set.all())
        for bus in buses[:2]:
            bus.linea = None
            bus.save()
            self.assertIsNone(Bus.objects.get(pk=bus.pk).linea)
        buses[2].linea = None
        with self.assertRaises(ValidationError):
            buses[2].save()

    def test_09_linea_activacion_y_distancia(self):
        linea = Linea.objects.create(
            nombre="Prueba", municipalidad=self.linea.municipalidad
        )
        linea.activo = True
        with self.assertRaises(ValidationError):
            linea.save()
        self.assertEqual(self.linea.distancia_total, Decimal("3.75"))

    def test_10_tramos_unicidad_orden_y_estacion(self):
        tramo = self.linea.lineaestacion_set.first()
        for orden, estacion in [
            (
                tramo.orden,
                Estacion.objects.exclude(pk=tramo.estacion_id).first(),
            ),
            (10, tramo.estacion),
            (0, tramo.estacion),
        ]:
            with self.assertRaises(ValidationError):
                LineaEstacion.objects.create(
                    linea=self.linea,
                    estacion=estacion,
                    orden=orden,
                    distancia_desde_anterior=1,
                )
        with self.assertRaises(ValidationError):
            tramo.distancia_desde_anterior = -1
            tramo.save()

    def test_11_guardias_cobertura(self):
        acceso = Acceso(
            nombre="Nuevo acceso", estacion=self.estacion, activo=True
        )
        with self.assertRaises(ValidationError):
            acceso.save()
        asignacion = AsignacionGuardia.objects.first()
        asignacion.activo = False
        with self.assertRaises(ValidationError):
            asignacion.save()
        guardia = asignacion.guardia
        guardia.activo = False
        with self.assertRaises(ValidationError):
            guardia.save()

    def test_12_demanda_umbral_inclusivo(self):
        for cantidad, alerta_esperada in [
            (149, False),
            (150, True),
            (151, True),
        ]:
            demanda = self.demanda(cantidad)
            alerta = guardar_operacion(demanda, self.operador, True)
            self.assertEqual(alerta is not None, alerta_esperada)
            self.assertEqual(demanda.capacidad_referencia, 100)
            self.assertEqual(demanda.operador_responsable, self.operador)

    def test_13_demanda_validaciones(self):
        otra = Estacion.objects.exclude(linea=self.linea).first()
        for cambios in [
            {"cantidad_pasajeros": -1},
            {"estacion": otra},
            {"fecha": timezone.localdate() + timedelta(days=1)},
        ]:
            with self.assertRaises(ValidationError):
                guardar_operacion(
                    self.demanda(100, **cambios), self.operador, True
                )

    def test_14_responsable_post_no_suplantable(self):
        self.client.force_login(self.admin)
        respuesta = self.client.post(
            "/gestion/demanda/nuevo/",
            {
                "linea": self.linea.pk,
                "estacion": self.estacion.pk,
                "fecha": timezone.localdate().isoformat(),
                "hora": "14:30",
                "cantidad_pasajeros": 150,
                "operador_responsable": self.operador.pk,
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            RegistroDemanda.objects.latest("pk").operador_responsable,
            self.admin,
        )

    def test_15_ocupacion_limites(self):
        for porcentaje in [-1, 101]:
            with self.assertRaises(ValidationError):
                guardar_operacion(
                    self.recorrido(porcentaje), self.supervisor, True
                )
        for porcentaje, esperado in [
            (0, True),
            (Decimal("24.99"), True),
            (25, False),
            (100, False),
        ]:
            recorrido = self.recorrido(porcentaje)
            alerta = guardar_operacion(recorrido, self.supervisor, True)
            self.assertEqual(alerta is not None, esperado)
            self.assertEqual(bool(recorrido.recomendacion), esperado)

    def test_16_recorrido_horas_y_asignacion(self):
        for cambios in [
            {"hora_final": time(11)},
            {"estado": "FINALIZADO"},
            {"linea": Linea.objects.exclude(pk=self.linea.pk).first()},
        ]:
            with self.assertRaises(ValidationError):
                guardar_operacion(
                    self.recorrido(**cambios), self.supervisor, True
                )

    def test_17_alertas_idempotentes_historicas(self):
        demanda = self.demanda(150)
        alerta = guardar_operacion(demanda, self.operador, True)
        guardar_operacion(demanda, self.operador, False)
        self.assertEqual(
            Alerta.objects.filter(registro_demanda=demanda).count(), 1
        )
        self.bus.capacidad_maxima = 200
        self.bus.save()
        demanda.refresh_from_db()
        self.assertEqual(demanda.capacidad_referencia, 100)
        self.assertIn("referencia 100", alerta.descripcion)

    def test_18_cambio_estado_y_auditoria(self):
        alerta = Alerta.objects.first()
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.post(
                reverse("editar", args=["alertas", alerta.pk]),
                {"estado": "ATENDIDA"},
            ).status_code,
            302,
        )
        alerta.refresh_from_db()
        self.assertEqual(alerta.estado, "ATENDIDA")
        self.assertTrue(
            Auditoria.objects.filter(
                usuario=self.admin,
                accion="CAMBIAR_ESTADO",
                registro=str(alerta.pk),
            ).exists()
        )
        self.client.force_login(self.operador)
        self.assertEqual(
            self.client.post(
                reverse("editar", args=["alertas", alerta.pk]),
                {"estado": "CERRADA"},
            ).status_code,
            403,
        )

    def test_19_reportes_y_filtros(self):
        self.client.force_login(self.supervisor)
        estacion_alerta = (
            Alerta.objects.filter(linea=self.linea, tipo="ALTA_DEMANDA")
            .first()
            .estacion
        )
        for tipo in [
            "estaciones",
            "lineas",
            "tramos",
            "buses",
            "recorridos",
            "demanda",
            "alertas",
        ]:
            with self.subTest(tipo=tipo):
                respuesta = self.client.get(
                    "/reportes/",
                    {
                        "tipo": tipo,
                        "linea": self.linea.pk,
                        "estacion": estacion_alerta.pk,
                    },
                )
                self.assertEqual(respuesta.status_code, 200)
                self.assertGreater(respuesta.context["total"], 0)
        respuesta = self.client.get(
            "/reportes/",
            {
                "tipo": "recorridos",
                "fecha": "2000-01-01",
                "estado": "FINALIZADO",
            },
        )
        self.assertEqual(respuesta.context["total"], 0)
        respuesta = self.client.get(
            "/reportes/",
            {"tipo": "demanda", "fecha": "inválida", "linea": "no-numero"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.context["errores"]), 2)
        import csv

        for tipo in [
            "estaciones",
            "lineas",
            "tramos",
            "buses",
            "recorridos",
            "demanda",
            "alertas",
        ]:
            respuesta = self.client.get(
                "/reportes/",
                {"tipo": tipo, "linea": self.linea.pk, "descargar": "csv"},
            )
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn("attachment;", respuesta["Content-Disposition"])
            self.assertIn("text/csv", respuesta["Content-Type"])
            self.assertTrue(respuesta.content.startswith(b"\xef\xbb\xbf"))
            self.assertGreater(
                len(
                    list(
                        csv.reader(
                            StringIO(respuesta.content.decode("utf-8-sig"))
                        )
                    )
                ),
                1,
            )
        respuesta = self.client.get(
            "/reportes/",
            {"tipo": "recorridos", "fecha": "2000-01-01", "descargar": "csv"},
        )
        self.assertEqual(
            len(
                list(
                    csv.reader(StringIO(respuesta.content.decode("utf-8-sig")))
                )
            ),
            1,
        )
        self.assertEqual(
            self.client.get(
                "/reportes/", {"linea": "x", "descargar": "csv"}
            ).status_code,
            400,
        )
        estacion_formula = Estacion.objects.create(
            nombre="=SUM(1,2)", municipalidad=self.linea.municipalidad
        )
        respuesta = self.client.get(
            "/reportes/", {"tipo": "estaciones", "descargar": "csv"}
        )
        self.assertIn("'=SUM(1,2)", respuesta.content.decode("utf-8-sig"))
        for indice in range(51):
            Estacion.objects.create(
                nombre=f"CSV {indice}", municipalidad=self.linea.municipalidad
            )
        respuesta = self.client.get(
            "/reportes/", {"tipo": "estaciones", "descargar": "csv"}
        )
        self.assertEqual(
            len(
                list(
                    csv.reader(StringIO(respuesta.content.decode("utf-8-sig")))
                )
            ),
            Estacion.objects.count() + 1,
        )
        lector = User.objects.create_user(
            "lector_sin_descarga", password="Clave2026!Prueba"
        )
        lector.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="operacion", codename="view_linea"
            )
        )
        self.client.force_login(lector)
        self.assertEqual(
            self.client.get("/reportes/?tipo=lineas").status_code, 200
        )
        self.assertEqual(
            self.client.get(
                "/reportes/?tipo=lineas&descargar=csv"
            ).status_code,
            403,
        )

    def test_20_crud_catalogo_personal_y_usuarios(self):
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.post(
                "/gestion/municipalidades/nuevo/",
                {"nombre": "Prueba CRUD", "activo": "on"},
            ).status_code,
            302,
        )
        obj = Municipalidad.objects.get(nombre="Prueba CRUD")
        self.assertEqual(
            self.client.post(
                reverse("editar", args=["municipalidades", obj.pk]),
                {"nombre": "Prueba editada"},
            ).status_code,
            302,
        )
        obj.refresh_from_db()
        self.assertFalse(obj.activo)
        self.assertTrue(
            Auditoria.objects.filter(
                modulo="operacion.Municipalidad",
                registro=str(obj.pk),
                accion="CREAR",
            ).exists()
        )
        self.assertEqual(
            self.client.post(
                "/gestion/guardias/nuevo/",
                {
                    "nombres": "DEMO",
                    "apellidos": "Prueba",
                    "identificacion_interna": "TEST-G",
                    "activo": "on",
                },
            ).status_code,
            302,
        )
        rol = self.operador.groups.first()
        respuesta = self.client.post(
            "/gestion/usuarios/nuevo/",
            {
                "username": "nuevo_demo",
                "rol": rol.pk,
                "is_active": "on",
                "password1": "ClaveSegura2026!",
                "password2": "ClaveSegura2026!",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        usuario = User.objects.get(username="nuevo_demo")
        self.assertTrue(usuario.check_password("ClaveSegura2026!"))
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertEqual(usuario.groups.first(), rol)

        # Flujo completo de preparación mediante los formularios públicos.
        def crear(modulo, datos, modelo):
            respuesta = self.client.post(
                reverse("crear", args=[modulo]), datos
            )
            self.assertEqual(
                respuesta.status_code,
                302,
                (
                    respuesta.context["form"].errors
                    if respuesta.status_code == 200
                    else modulo
                ),
            )
            return modelo.objects.latest("pk")

        estacion = crear(
            "estaciones",
            {
                "nombre": "Estación prueba",
                "municipalidad": obj.pk,
                "activo": "on",
            },
            Estacion,
        )
        linea = crear(
            "lineas",
            {"nombre": "Línea prueba", "municipalidad": obj.pk},
            Linea,
        )
        crear(
            "tramos",
            {
                "linea": linea.pk,
                "estacion": estacion.pk,
                "orden": 1,
                "distancia_desde_anterior": "0",
            },
            LineaEstacion,
        )
        acceso = crear(
            "accesos",
            {"nombre": "Acceso prueba", "estacion": estacion.pk},
            Acceso,
        )
        guardia = Guardia.objects.get(identificacion_interna="TEST-G")
        crear(
            "asignaciones",
            {"acceso": acceso.pk, "guardia": guardia.pk, "activo": "on"},
            AsignacionGuardia,
        )
        self.assertEqual(
            self.client.post(
                reverse("editar", args=["accesos", acceso.pk]),
                {
                    "nombre": acceso.nombre,
                    "estacion": estacion.pk,
                    "activo": "on",
                },
            ).status_code,
            302,
        )
        from operacion.models import Parqueo

        parqueo = crear(
            "parqueos",
            {
                "nombre": "Parqueo prueba",
                "direccion": "Ficticia",
                "activo": "on",
            },
            Parqueo,
        )
        bus = crear(
            "buses",
            {
                "codigo": "TEST-BUS",
                "capacidad_maxima": 100,
                "estado": "ACTIVO",
                "linea": linea.pk,
                "parqueo": parqueo.pk,
            },
            Bus,
        )
        self.assertEqual(
            self.client.post(
                reverse("editar", args=["lineas", linea.pk]),
                {
                    "nombre": linea.nombre,
                    "municipalidad": obj.pk,
                    "activo": "on",
                },
            ).status_code,
            302,
        )
        piloto = crear(
            "pilotos",
            {
                "nombres": "Piloto",
                "apellidos": "Ficticio",
                "identificacion_interna": "TEST-P",
                "direccion": "Ficticia",
                "residencia": "Ficticia",
                "nivel_educativo": "Primaria",
                "activo": "on",
            },
            Piloto,
        )
        crear(
            "operadores",
            {
                "nombres": "Operador",
                "apellidos": "Ficticio",
                "identificacion_interna": "TEST-O",
                "activo": "on",
            },
            Operador,
        )
        recorrido = crear(
            "recorridos",
            {
                "bus": bus.pk,
                "linea": linea.pk,
                "piloto": piloto.pk,
                "fecha": timezone.localdate().isoformat(),
                "hora_inicio": "08:00",
                "hora_final": "09:00",
                "ocupacion_estimada": 20,
                "estado": "FINALIZADO",
            },
            Recorrido,
        )
        self.assertTrue(
            Alerta.objects.filter(
                recorrido=recorrido, tipo="BAJA_OCUPACION"
            ).exists()
        )

        # Eliminación de usuarios: permiso específico, confirmación e historial.
        objetivo = User.objects.create_user("usuario_eliminable")
        objetivo_pk = objetivo.pk
        url = reverse("eliminar_usuario", args=[objetivo_pk])
        self.assertContains(self.client.get("/gestion/usuarios/"), url)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(User.objects.filter(pk=objetivo_pk).exists())
        self.client.force_login(self.operador)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(self.admin)
        estricto = Client(enforce_csrf_checks=True)
        estricto.force_login(self.admin)
        self.assertEqual(estricto.post(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(User.objects.filter(pk=objetivo_pk).exists())
        self.assertTrue(
            Auditoria.objects.filter(
                usuario=self.admin,
                modulo="auth.User",
                accion="ELIMINAR",
                registro=str(objetivo_pk),
            ).exists()
        )
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertContains(
            self.client.post(
                reverse("eliminar_usuario", args=[self.admin.pk])
            ),
            "No puede eliminar su propia cuenta.",
        )
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
        antes = Auditoria.objects.filter(accion="ELIMINAR").count()
        respuesta = self.client.post(
            reverse("eliminar_usuario", args=[self.operador.pk])
        )
        self.assertContains(respuesta, "registros de demanda vinculados")
        self.assertTrue(User.objects.filter(pk=self.operador.pk).exists())
        self.assertEqual(
            Auditoria.objects.filter(accion="ELIMINAR").count(), antes
        )
        tecnico = User.objects.create_superuser(
            "tecnico", password="ClaveTecnica!2026"
        )
        self.assertEqual(
            self.client.post(
                reverse("eliminar_usuario", args=[tecnico.pk])
            ).status_code,
            403,
        )

    def test_21_seed_idempotente(self):
        antes = {
            m: m.objects.count()
            for m in [Linea, Bus, RegistroDemanda, Alerta, User, Guardia]
        }
        self.operador.set_password("ClaveModificada!2026")
        self.operador.save()
        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(antes, {m: m.objects.count() for m in antes})
        self.operador.refresh_from_db()
        self.assertTrue(self.operador.check_password("ClaveModificada!2026"))

    def test_22_restricciones_base_datos(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Bus.objects.filter(pk=self.bus.pk).update(capacidad_maxima=0)
        recorrido = Recorrido.objects.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Recorrido.objects.filter(pk=recorrido.pk).update(
                ocupacion_estimada=101
            )

    @override_settings(DEBUG=False)
    def test_23_errores_y_escape(self):
        self.client.force_login(self.operador)
        self.assertContains(
            self.client.get("/gestion/usuarios/"),
            "Acceso restringido",
            status_code=403,
        )
        self.assertContains(
            self.client.get("/inexistente/"),
            "Registro no encontrado",
            status_code=404,
        )
        self.client.force_login(self.admin)
        obj = Municipalidad.objects.create(nombre="<script>alert(1)</script>")
        respuesta = self.client.get(
            reverse("detalle", args=["municipalidades", obj.pk])
        )
        self.assertContains(respuesta, "&lt;script&gt;")
        self.assertNotContains(respuesta, "<script>alert(1)</script>")
        self.client.raise_request_exception = False
        with patch(
            "core.views.Linea.objects.count",
            side_effect=RuntimeError("detalle-interno-privado"),
        ):
            respuesta = self.client.get("/")
        self.assertContains(respuesta, "No se pudo completar", status_code=500)
        self.assertNotContains(
            respuesta, "detalle-interno-privado", status_code=500
        )
        self.client.raise_request_exception = True

    def test_24_demanda_sin_referencia(self):
        Bus.objects.filter(linea=self.linea).update(estado="MANTENIMIENTO")
        with self.assertRaises(ValidationError):
            guardar_operacion(self.demanda(150), self.operador, True)

    def test_25_auditoria_atomica_y_historico(self):
        antes = Auditoria.objects.count()
        with self.assertRaises(ValidationError):
            guardar_operacion(self.recorrido(101), self.supervisor, True)
        self.assertEqual(Auditoria.objects.count(), antes)
        recorrido = self.recorrido(50)
        guardar_operacion(recorrido, self.supervisor, True)
        self.bus.linea = None
        self.bus.save()
        recorrido.observaciones = "Corrección histórica"
        guardar_operacion(recorrido, self.supervisor, False)
        recorrido.refresh_from_db()
        self.assertEqual(recorrido.linea, self.linea)
