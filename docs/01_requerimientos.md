# Requerimientos implementados

Caso académico: Municipalidad de Guatemala; consultora NexoQA; UMG.
Todos los datos precargados son ficticios. Alcance: sistema interno con Django,
Bootstrap y SQLite; sin pagos, GPS, IoT, mapas, aplicaciones móviles ni APIs externas.

| ID | Requerimiento | Implementación | Verificación (CP) |
| --- | --- | --- | --- |
| RF-01 | Estructura operativa | Municipalidades, líneas, estaciones, tramos ordenados, distancias y accesos | 09, 10, 20 |
| RF-02 | Buses y parqueos | Capacidad, estado, parqueo obligatorio, línea opcional; flota N–2N en líneas activas | 06, 07, 08, 09 |
| RF-03 | Personal | Pilotos con datos educativos/residencia; operadores y guardias; cobertura de accesos activos | 04, 11, 20 |
| RF-04 | Asignaciones y recorridos | Edición de bus, recorridos con piloto, fecha, horas, porcentaje y estado; historial | 15, 16, 25 |
| RF-05 | Demanda y alertas | Registro manual, referencia histórica, 150 % inclusivo, espera debajo de 25 %, gestión de alertas | 12–18, 24 |
| RF-06 | Usuarios y reportes | Login, dos roles, permisos, auditoría y siete reportes HTML/CSV filtrados | 01–05, 18–20, 25 |
| RNF-01 | Seguridad | Autenticación, CSRF, permisos servidor, hash de contraseñas, validaciones y escape | 01–05, 20, 22, 23 |
| RNF-02 | Usabilidad | Navbar, menú por permisos, dashboard, mensajes, formularios, Bootstrap responsive | 04; revisión visual pendiente del usuario |
| RNF-03 | Rendimiento | Listados de 20 y reportes de 50 filas; operación con conjunto demo | 04, 19, 21; sin carga concurrente |
| RNF-04 | Mantenibilidad | Apps separadas, formularios Django, servicios transaccionales, migraciones | check, makemigrations --check y estructura entregada |
| RNF-05 | Respaldo | Procedimiento de copia/restauración SQLite documentado | Manual 10 revisado; restauración no ejecutada |

Cada registro principal es consultable y editable según permisos; las bajas son
lógicas en los módulos operativos. Administrativo puede eliminar usuarios sin
demandas vinculadas, con confirmación; no puede eliminarse a sí mismo. La auditoría es inmutable;
Administrativo crea y edita demanda. Las alertas permiten cambio de estado.
Los porcentajes de cobertura distinguen requisitos funcionales comprobados de
aspectos no funcionales que requieren revisión visual, carga o un ensayo de respaldo.

## Roles

| Área | Administrativo | Operativo |
| --- | --- | --- |
| Dashboard y consultas operativas | Sí | Sí |
| Municipalidades, líneas, estaciones, tramos, accesos, parqueos y buses | Gestionar | Consultar |
| Personal y guardias | Gestionar | Consultar |
| Recorridos | Gestionar y finalizar | Consultar y finalizar programados/en curso |
| Demanda | Crear/editar/consultar | Consultar |
| Alertas | Consultar/atender con gestión y cambiar estado | Consultar/atender con gestión y cambiar estado |
| Usuarios | Gestionar | Sin acceso |
| Auditoría | Consultar | Sin acceso |
| Reportes HTML y descarga CSV | Sí | Sí |

La solicitud posterior del usuario sustituye los tres roles originales por estos
dos. La finalización usa un permiso específico, sin otorgar edición general de
recorridos al Operativo. Se añade descarga CSV conservando todos los filtros.
Una solicitud posterior habilita también `atender_alerta` a ambos roles, con nota
obligatoria e historial de actuaciones por alerta (usuario, fecha y estados).
Los roles se materializan como grupos con permisos Django. El superusuario es una
cuenta técnica opcional independiente de los usuarios demo. No se crean modelos
de autenticación propios. Un Operador administrativo y un User son entidades
distintas: la autoría de demanda se liga al User autenticado, como exige RF-05.
