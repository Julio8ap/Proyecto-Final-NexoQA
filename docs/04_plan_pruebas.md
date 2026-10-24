# Plan de pruebas y resultados

Ejecución real: 23 de octubre de 2026, Python 3.13.2, Django 5.2.18, SQLite de
pruebas en memoria. Comando: `python manage.py test --verbosity 2` con el entorno
virtual del proyecto. Tras corregir una expectativa del filtro de alertas se repitió
la suite completa: 25 casos aprobados, cero fallos. Se amplió CP-20 con la creación
por POST de toda la estructura, bus, personal y recorrido. Esto detectó un campo
M:N obligatorio improcedente en el formulario de línea; se excluyó ese campo para
gestionar estaciones exclusivamente en tramos y se repitieron las 25 pruebas con éxito.

Cada CP corresponde a `core.tests.TransmetroTests.test_NN_*`. Precondición común:
base de pruebas aislada y `seed_demo` ejecutado mediante setUpTestData. Las pruebas
se revierten entre casos y no alteran la base de demostración.

| ID | Requerimiento | Caso | Precondición | Pasos | Resultado esperado | Resultado obtenido | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CP-01 | RF-06/RNF-01 | Login y logout | Usuarios demo | GET inicio; login inválido/válido; GET/POST logout | Redirección sin sesión; clave válida abre dashboard; logout solo POST | Coincide | APROBADO |
| CP-02 | RF-04/06 | Operativo y finalización | Sesión Operativo | Intentar crear/editar; consultar; finalizar programado/en curso; repetir, cerrar cancelado/futuro; inyectar otros campos | Escrituras generales 403; consulta y cierre auditado permitidos; sin alterar otros campos; cierres inválidos rechazados | Coincide | APROBADO |
| CP-03 | RF-06 | Migración a dos roles | Cuentas y grupos anteriores | Sincronizar roles dos veces; comprobar cuentas, claves y selector | Dos opciones, membresías convertidas, claves conservadas, sin permiso de creación para Operativo | Coincide | APROBADO |
| CP-04 | RF-01 a RF-06/RNF-02/03 | Navegación | Sesión administrador | GET todos los listados, detalles y formularios autorizados | HTTP 200 y no exponer hash | Coincide | APROBADO |
| CP-05 | RNF-01 | CSRF | Cliente con CSRF estricto | POST catálogo sin token | 403 y sin creación | Coincide | APROBADO |
| CP-06 | RF-02 | Capacidad/parqueo | Bus de referencia | Guardar capacidad cero y sin parqueo | ValidationError | Coincide | APROBADO |
| CP-07 | RF-02 | Máximo flota | Línea con N=4, 6 buses | Agregar buses hasta 8; intentar noveno | Hasta 8 permitido; noveno rechazado | Coincide | APROBADO |
| CP-08 | RF-02 | Mínimo y línea opcional | Línea activa con 6 buses | Retirar 2 buses; intentar retirar tercero | 4 permitido; 3 rechazado; bus conserva parqueo | Coincide | APROBADO |
| CP-09 | RF-01/02 | Activación/distancia | Línea demo y línea nueva vacía | Activar vacía; consultar distancia demo | Rechazo y suma 3.75 km | Coincide | APROBADO |
| CP-10 | RF-01 | Tramos | Tramo existente | Duplicar orden/estación; orden cero; distancia negativa | Rechazo de todos | Coincide | APROBADO |
| CP-11 | RF-03 | Guardias | Acceso con único guardia | Crear acceso activo sin guardia; quitar/desactivar último | Rechazo de todos | Coincide | APROBADO |
| CP-12 | RF-05 | Alta demanda | Referencia 100 | Registrar 149, 150 y 151 | Solo 150 y 151 alertan; autor y referencia correctos | Coincide | APROBADO |
| CP-13 | RF-05 | Datos inválidos | Línea y estación | Negativo; estación ajena; fecha futura | Rechazo de todos | Coincide | APROBADO |
| CP-14 | RF-05/RNF-01 | Responsable automático | Sesión Administrativo | POST demanda intentando otro usuario | Responsable es usuario Administrativo autenticado | Coincide | APROBADO |
| CP-15 | RF-04/05 | Ocupación | Bus y piloto activos | -1, 101, 0, 24.99, 25, 100 % | Rechaza extremos inválidos; alerta solo debajo de 25 | Coincide | APROBADO |
| CP-16 | RF-04 | Horas y asignación | Recorrido nuevo | Fin antes de inicio; finalizado sin fin; línea ajena | Rechazo de todos | Coincide | APROBADO |
| CP-17 | RF-05 | Alerta única/histórica | Demanda 150/100 | Guardar dos veces; cambiar capacidad bus | Una alerta; referencia sigue en 100 | Coincide | APROBADO |
| CP-18 | RF-05/06/RNF-01 | Atención e historial | Alerta pendiente y ambos roles | Operativo atiende con nota; Administrativo cierra; reabrir; GET; nota vacía/larga; estado inválido; CSRF; usuario sin permiso; inyección autor; forzar fallo auditoría | Gestiones y autores históricos conservados, contadores actualizados, texto escapado, inválidos rechazados, transacción revertida si falla auditoría | Coincide | APROBADO |
| CP-19 | RF-06/RNF-01/03 | Reportes HTML y CSV | Sesión Operativo; estación con alerta | Abrir/exportar siete reportes; filtros válidos/inválidos; texto con fórmula | HTML/CSV correctos, unidades, BOM UTF-8, todas las filas, fórmula neutralizada; descarga inválida 400 | Coincide | APROBADO |
| CP-20 | RF-01/02/03/04/06 | CRUD y usuarios | Sesión Administrativo | Crear/editar registros y usuarios; confirmar eliminación; intentar como Operativo, sin CSRF, cuenta propia, superusuario o usuario con demanda | Persistencia y auditoría; eliminación solo autorizada por POST; GET no elimina; casos protegidos conservados y sin auditoría falsa de éxito | Coincide | APROBADO |
| CP-21 | Datos demo | Idempotencia | Demo cargada y clave cambiada | Repetir seed_demo | Mismos conteos; conserva clave cambiada | Coincide | APROBADO |
| CP-22 | RF-02/04/RNF-01 | Integridad SQLite | Bus y recorrido | SQL ORM update capacidad 0/ocupación 101 | IntegrityError incluso omitiendo save | Coincide | APROBADO |
| CP-23 | RNF-01 | Errores y escape | DEBUG=False | URL 403/404; nombre con script | Páginas propias; script escapado | Coincide | APROBADO |
| CP-24 | RF-05 | Sin capacidad referencia | Buses de línea en mantenimiento | Registrar demanda | ValidationError | Coincide | APROBADO |
| CP-25 | RF-04/06 | Atomicidad e historial | Conteo auditoría; bus con flota suficiente | Fallar recorrido; crear válido; reasignar bus; corregir observación | Sin auditoría de fallo; recorrido conserva línea | Coincide | APROBADO |

## Pruebas manuales recomendadas para la presentación

No se registran como ejecutadas: revisión visual en escritorio/móvil, navegación
con teclado, ensayo de copia/restauración y exposición oral con dos roles. Pasos:
ingresar como Administrativo, registrar demanda 150/100, atender alerta y crear un
recorrido programado de fecha/hora no futura; ingresar como Operativo, finalizarlo
y descargar reporte por fecha. Confirmar visualmente
mensajes, legibilidad y comportamiento responsive. No hay afirmaciones de pruebas
de carga, pentest ni compatibilidad entre navegadores.
