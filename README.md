# Sistema Web Interno de Gestión y Control de Transmetro

Proyecto académico de NexoQA para el curso Aseguramiento de la Calidad del Software,
Universidad Mariano Gálvez de Guatemala. Cliente del caso de estudio: Municipalidad
de Guatemala. No existe conexión con sistemas municipales ni datos reales.

El objetivo es administrar estructura operativa, flota, personal, recorridos,
demanda manual y alertas, con permisos y trazabilidad. Es un MVP interno para
demostración, sin pagos, GPS, sensores, servicios externos ni cálculo de ocupación real.

## Tecnologías y requisitos

Python 3.10 o superior (validado con 3.13.2), Django 5.2, Django ORM y Templates,
SQLite, Bootstrap 5.3.3 local y Git. Única dependencia directa de Python: Django.
Bootstrap se distribuye en `static/vendor/bootstrap.min.css`, con licencia MIT en
su cabecera; la interfaz no necesita CDN ni JavaScript.

## Instalación en PowerShell

Desde la raíz del proyecto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrir http://127.0.0.1:8000/. Si la política de PowerShell impide activar el entorno,
usar `.\venv\Scripts\python.exe` en lugar de `python`, sin modificar políticas del sistema.
En Linux/macOS activar con `source venv/bin/activate`.

Para una base vacía sin demo, ejecutar `python manage.py configurar_roles` y
`python manage.py createsuperuser`. El superusuario puede crear usuarios con rol
en la pantalla Usuarios. El panel `/admin/` permite consultar los modelos operativos;
las escrituras se realizan en las pantallas del sistema para conservar auditoría.

## Credenciales de demostración

| Usuario | Rol | Contraseña inicial |
| --- | --- | --- |
| admin_demo | ADMINISTRATIVO | DemoTransmetro2026! |
| supervisor_demo | OPERATIVO | DemoTransmetro2026! |
| operador_demo | OPERATIVO | DemoTransmetro2026! |

Contraseñas exclusivamente locales y demostrativas, almacenadas con hash Django.
El comando no restablece contraseñas ya cambiadas. Cada usuario puede cambiar su
clave desde la barra superior. Estas cuentas no tienen acceso al admin de Django.

Hay dos roles. Administrativo gestiona todos los módulos de negocio y usuarios.
Operativo consulta información, visualiza/descarga reportes CSV y finaliza recorridos;
no crea ni edita catálogos, demanda, personal, usuarios o alertas. La auditoría es de
solo lectura para Administrativo. Los registros mantienen sus bajas lógicas.

Al actualizar una instalación anterior ejecutar `python manage.py migrate` y
`python manage.py configurar_roles`. El segundo comando conserva usuarios y claves,
convierte ADMINISTRADOR en ADMINISTRATIVO y SUPERVISOR/OPERADOR DE ESTACIÓN en
OPERATIVO, y elimina los tres grupos anteriores. Las cuentas con ambos roles
anteriores conservan únicamente el Administrativo. La selección de rol en Usuarios
ofrece solo las dos opciones actuales.

La franja superior muestra «Sistema Municipal» y el pie «Desarrollado por nexoQA».
Los formularios, detalles y reportes indican pasajeros/personas, kilómetros y
porcentajes en los campos correspondientes. Los datos de ejemplo siguen siendo ficticios.

`seed_demo` crea 1 municipalidad, 3 líneas, 10 estaciones compartidas por 12 tramos,
10 accesos con guardia, 18 buses, 3 parqueos, 8 pilotos, 5 operadores, 10 guardias,
9 recorridos, 9 demandas y 9 alertas. Es transaccional e idempotente: una segunda
ejecución conserva los datos existentes; no es un comando de reparación ni de reinicio.

## Estructura y módulos

```text
config/        Configuración, URLs y WSGI
accounts/      Usuarios, formularios y configuración de grupos/permisos
core/          Dashboard, gestión reutilizable, auditoría, seed y pruebas
operacion/     Estructura, flota, recorridos, demanda, alertas y servicios
personal/      Pilotos, operadores, guardias y asignaciones
reportes/      Siete reportes HTML con filtros y paginación
templates/     Pantallas administrativas, autenticación y errores
static/        Estilos institucionales y Bootstrap local
docs/          Requisitos, modelo, pruebas, métricas, SQL y manuales
```

Las migraciones están incluidas. Las bajas operativas son lógicas (Activo/Inactivo
o estado). Administrativo puede eliminar usuarios desde Usuarios → Eliminar →
Confirmar eliminación. No puede eliminar su propia cuenta ni superusuarios técnicos;
si la cuenta tiene demandas vinculadas, debe desactivarla para conservar el historial.
La eliminación autorizada queda auditada. Buses cambian de línea/parqueo mediante
su edición; tramos y asignaciones de guardias tienen pantallas propias. Se conserva
el historial de recorridos y la auditoría de las escrituras realizadas en la aplicación.

## Reglas relevantes

- Preparar líneas y accesos inactivos. Activar un acceso exige guardia activo;
  activar una línea exige estaciones activas, entre N y 2N buses y accesos con guardias.
- La flota máxima se valida durante la preparación; la mínima se exige al activar y
  en reasignaciones posteriores. Para reestructurar una línea, desactivarla primero.
- Todo bus requiere parqueo y capacidad positiva, con una sola línea opcional.
- La demanda usa como referencia la mayor capacidad de buses activos de la línea,
  conservada en el registro. Demanda ≥ 150 % genera alerta; sin bus de referencia
  no se admite demanda. El responsable siempre es el usuario autenticado.
- Ocupación estimada manual del recorrido entre 0 y 100 %; por debajo de 25 % genera
  alerta y muestra «Aplicar espera adicional de 5 minutos.».
- Las alertas son evidencia histórica; corregir posteriormente un recorrido no borra
  su alerta. El Administrativo puede atenderla o cerrarla.

## Finalizar recorridos y descargar reportes

En Recorridos se puede filtrar por línea. Cada fila identifica línea, bus, fecha y
estado. Los PROGRAMADO (pendientes) y EN_CURSO muestran «Finalizar» para ambos
roles. El botón abre un formulario que solicita únicamente la hora local de fin;
confirmar guarda FINALIZADO y auditoría. No permite cerrar antes del inicio, con
fecha/hora futura, ni repetir el cierre de un finalizado o cancelado. El Operativo
no puede alterar bus, línea, piloto ni ocupación mediante esta acción. La semilla
original contiene recorridos finalizados; un Administrativo puede crear programados.

Reportes → seleccionar filtros → Descargar CSV exporta todas las filas coincidentes,
incluidas las que no caben en la página HTML. Archivo UTF-8 con BOM, unidades en
encabezados y protección frente a fórmulas de hoja de cálculo. Ambos roles pueden
visualizar y descargar los siete reportes. Los filtros inválidos bloquean la descarga.

## Verificación

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py migrate
python manage.py seed_demo
```

25 pruebas Django TestCase aprobadas. Incluyen navegación con cliente HTTP Django,
operaciones POST, permisos, CSRF, filtros, reglas y restricciones SQLite.
Ver `docs/04_plan_pruebas.md` y `docs/06_metricas.md` para evidencia y cobertura.
La salida de comandos de la revisión final se conserva en `docs/11_validacion.txt`.
La verificación de los dos roles, finalización y CSV está en
`docs/12_validacion_actualizacion.txt`.

## Configuración, respaldo y limitaciones

Por defecto se ejecuta en modo demostración local con DEBUG habilitado. `.env.example`
documenta variables de entorno; no se carga automáticamente. No usar la clave de
desarrollo ni las cuentas demo para un despliegue real. Consulte `docs/07_seguridad.md`.
Para respaldar SQLite de forma consistente, detener el servidor y copiar
`db.sqlite3` a una ubicación segura. Restaurar con el servidor detenido y conservar
la misma versión del código/migraciones (más detalle en el manual de instalación).

SQLite y el servidor de desarrollo están destinados a uso académico local. No se
incluyen despliegue productivo, recuperación de claves por correo, PDF ni integraciones.
Las operaciones de ORM mediante shell, `bulk_update` o SQL directo quedan fuera
del flujo autorizado y pueden omitir servicios de negocio y auditoría; la interfaz
y los servicios validan del lado servidor. No hay control avanzado de concurrencia
para múltiples escritores simultáneos. Las alertas no representan ocupación exacta.
Las verificaciones HTTP están automatizadas; no se realizó inspección visual en navegador.

Documentación de uso: `docs/09_manual_usuario.md`. Instalación y respaldo:
`docs/10_manual_instalacion.md`.
