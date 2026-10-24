# Manual de instalación y respaldo

## Preparación

Requisitos: Python ≥ 3.10, pip, permisos de escritura en el proyecto, navegador y
Git opcional para versionamiento. Verificado con Python 3.13.2 y Django 5.2.18 en
Windows. SQLite viene con Python. No se requiere Node, Docker ni base externa.

En PowerShell, ubicado en la raíz:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py check
python manage.py test
python manage.py runserver
```

Alternativa sin activación: sustituir python por `.\venv\Scripts\python.exe` en los
comandos posteriores a crear el entorno. Linux/macOS: `source venv/bin/activate`.
Abrir http://127.0.0.1:8000/. Detener con Ctrl+C. No exponer runserver a Internet.

Para instalación vacía sin datos demo:

```powershell
python manage.py migrate
python manage.py configurar_roles
python manage.py createsuperuser
python manage.py runserver
```

Crear cuentas con rol desde la pantalla Usuarios al ingresar con el superusuario.
Si se modifican intencionalmente los permisos o se actualiza su definición,
`configurar_roles` vuelve a sincronizar los dos grupos. El seed también los sincroniza.
El comando no borra usuarios ni restablece sus contraseñas.

Al actualizar desde los tres roles anteriores, ejecutar `migrate` para incorporar
los permisos específicos de finalización y descarga, y después `configurar_roles`.
Este comando convierte las membresías antiguas a Administrativo/Operativo y
elimina únicamente los tres grupos de roles obsoletos, conservando cuentas y claves.

## Diagnóstico

- `No module named django`: usar Python del entorno y repetir instalación.
- Tablas inexistentes: ejecutar migrate con la misma configuración/base.
- Activación bloqueada: usar ruta al ejecutable, sin cambiar políticas globales.
- Puerto ocupado: `python manage.py runserver 8001` y abrir ese puerto.
- Sin permisos después de crear cuenta: asignar grupo correcto y volver a ingresar.
- Seed ya existente: comportamiento esperado; conserva modificaciones. No elimina
  ni repara instalaciones parciales manualmente alteradas.
- Línea/acceso no se activa: seguir preparación del manual de usuario; el error del
  formulario identifica la regla incumplida.

## Configuración

Las variables de `.env.example` se configuran en el sistema; no se leen desde un
archivo automáticamente. Modo local predeterminado DEBUG=1. Antes de un eventual
despliegue se necesita clave propia, DEBUG=0, hosts explícitos, HTTPS y servidor
WSGI con estáticos. `python manage.py collectstatic` prepara estáticos; no configura
un servidor productivo. La entrega es local académica. Ver documento 07.

## Respaldo y restauración de SQLite

1. Detener todas las instancias del servidor con Ctrl+C; no escribir durante la copia.
2. Copiar `db.sqlite3` con el servidor detenido a una carpeta de respaldo elegida.
   Ejemplo desde la raíz (no subir respaldo a repositorios públicos):

   ```powershell
   Copy-Item -LiteralPath db.sqlite3 -Destination 'D:\Respaldos\transmetro.sqlite3'
   ```

3. Guardar también la versión del código, migraciones y requirements utilizada;
   las variables secretas se conservan mediante el mecanismo seguro del operador.
4. Para restaurar, detener servidor, conservar copia de la base actual y copiar el
   respaldo a `db.sqlite3` en la raíz. Verificar que corresponde al código utilizado.
5. Ejecutar `python manage.py check`, `python manage.py migrate --check`, abrir
   sesión y verificar conteos/reportes antes de continuar. No ejecutar seed para
   «restaurar»: el seed no es una herramienta de recuperación.

La carpeta destino del ejemplo debe existir y ser accesible. Copia/restore no se
ejecutó automáticamente sobre ubicaciones externas ni se afirma haber probado
una recuperación real. Para bases en uso continuo se necesitaría una estrategia
de respaldo online con SQLite; el procedimiento simple requiere detener escritura.

## Validación de instalación

`python manage.py test` crea una base aislada y la destruye al finalizar. Deben
aprobar 25 pruebas. `python manage.py makemigrations --check --dry-run` debe informar
que no hay cambios; `python manage.py showmigrations` debe mostrar migraciones
aplicadas. Repetir seed no cambia conteos. README contiene credenciales iniciales
y limitaciones. No se requieren descargas para Bootstrap durante la ejecución.
