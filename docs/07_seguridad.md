# Seguridad y operación

- Autenticación y sesiones Django. Login obligatorio en todas las vistas de gestión,
  dashboard y reportes. El admin exige staff; cuentas demo no son staff.
- Grupos/permisos estándar. Comprobación del lado servidor en cada vista de lectura,
  creación o cambio; menú por permisos solo facilita navegación. La eliminación
  desde UI se limita a usuarios con `auth.delete_user`, exclusivo de Administrativo.
  Exige confirmación POST/CSRF, impide cuenta propia y respeta PROTECT de demanda;
  los superusuarios técnicos quedan protegidos frente al administrador funcional.
- Roles actuales: Administrativo y Operativo. Solo el primero gestiona usuarios y
  módulos de negocio; el segundo tiene permisos de lectura más `finalizar_recorrido`,
  `descargar_reportes` y `atender_alerta`. No tiene `change_recorrido`: el cierre usa una vista
  específica que solo acepta hora final y estado destino FINALIZADO, verificando
  estado previo, hora, permiso y CSRF. No se aceptan bus/línea/piloto enviados.
- La atención de alertas usa un permiso específico para ambos roles. Nota
  obligatoria, estados limitados, autor/fecha en servidor y operación atómica. Las
  gestiones anteriores no son editables; se escapan al mostrarlas. El nombre del
  autor se conserva aunque su FK quede nula tras una eliminación permitida.
- CSV usa filtros y permisos de servidor, exporta todas las coincidencias y
  neutraliza valores que una hoja de cálculo interpretaría como fórmulas.
- CSRF en todos los formularios POST. Logout por POST. Cliente estricto comprobado.
- UserCreationForm valida las contraseñas; Django guarda hashes. Cambio de clave
  requiere clave anterior. No hay restablecimiento por correo en este MVP.
- Gestión web de usuarios no expone is_staff/is_superuser ni hash de contraseña.
  Administradores funcionales no editan superusuarios técnicos. Usuarios pueden
  cambiar su clave; seed_demo nunca restablece las existentes.
- Formularios Django, full_clean en save, clean de negocio y restricciones de base.
  Consultas ORM parametrizadas; autoescape de templates. No se marca entrada como safe.
- Autor de demanda fijado en servidor; no se acepta un autor enviado por el navegador.
- Servicios con transaction.atomic agrupan operación, alerta y auditoría. Auditoría
  no editable desde UI. Admin operativo de consulta para no eludir los servicios.
- Sin archivos de usuario, integraciones externas, pagos ni datos personales reales.

## Variables

`.env.example` es una referencia; Django no carga `.env` de forma automática.
Configurar en la sesión o entorno del servicio. Ejemplo PowerShell (reemplazar valor):

```powershell
$env:DJANGO_DEBUG = '0'
$env:DJANGO_SECRET_KEY = 'introducir-un-secreto-largo-aleatorio-propio'
$env:DJANGO_ALLOWED_HOSTS = 'nombre-del-servidor-interno'
```

DEBUG por defecto es 1 exclusivamente para demostración local. Con DEBUG=0, la
clave de desarrollo provoca un error de configuración; cookies de sesión y CSRF
son Secure y necesitan HTTPS. Las páginas 403, 404 y 500 son propias. Página 500
no depende del contexto de consultas para evitar una segunda excepción.

`.gitignore` excluye entorno virtual, `.env`, base SQLite, cachés y logs. No se
incluyen secretos reales. Las claves publicadas son de demostración local.

## Límites

No es un despliegue productivo certificado. Para producción harían falta servicio
WSGI, TLS, gestión de secretos, staticfiles, política de copias, monitoreo y evaluación
de concurrencia. runserver es solo desarrollo. No hay bloqueo avanzado entre
escritores simultáneos ni registro de cada cambio efectuado por shell/SQL o admin
de auth. No habilitar escrituras directas a usuarios de operación. La auditoría
es básica, sin firma criptográfica ni diferencias de campo. No se han ejecutado
pentests ni pruebas de carga. Esos límites no agregan funciones al MVP entregado.
