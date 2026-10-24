# Manual de usuario

Todos los datos son demostrativos. No se administra operación real ni se ejecutan
acciones sobre buses, accesos o molinetes. La franja superior identifica «Sistema
Municipal» y el pie indica «Desarrollado por nexoQA».

## Acceso y dashboard

Abrir http://127.0.0.1:8000/, ingresar con la cuenta asignada. Cuentas demo y clave
en README. Login incorrecto muestra error. En la barra superior puede cambiar la
contraseña usando la actual. El dashboard presenta totales de líneas, estaciones,
buses, buses ACTIVO, recorridos de hoy y alertas pendientes, atendidas y cerradas,
además de últimos cinco registros de alertas y demanda. Las alertas ofrecen Atender
o Registrar gestión y un enlace al historial completo. El menú se adapta a sus permisos.

## Catálogos, líneas y estaciones

Administrativo gestiona todos los catálogos; Operativo puede consultarlos. En cada
módulo usar Nuevo registro, completar formulario y Guardar. Editar modifica los
datos; Detalle muestra todos los campos. Buscar filtra nombre, código, apellido o
descripción según módulo. Listados con 20 registros por página. Para bajas,
desmarcar Activo; los módulos operativos no ofrecen eliminaciones físicas.

Orden de preparación recomendado:

1. Crear municipalidad, estaciones y parqueos.
2. Crear línea con Activo desmarcado.
3. En Estaciones por línea agregar estaciones, orden positivo y distancia desde la
   anterior en km. La primera distancia puede ser cero. No repetir orden ni estación
   dentro de una línea. Una estación sí se puede compartir entre líneas distintas.
4. Crear guardias activos. Crear accesos inactivos, asignar guardias en Asignaciones
   de guardias y luego activar accesos.
5. Crear buses con capacidad, estado, parqueo y línea. Si la línea tiene N estaciones,
   preparar entre N y 2N buses.
6. Editar la línea y activar. El sistema rechaza activación con preparación incompleta.

Detalle de línea muestra la distancia total. Para una reorganización que temporalmente
rompa la regla de flota, desactivar la línea, editar tramos/buses y reactivar.
Un acceso inactivo está en preparación o fuera de servicio y no necesita guardia;
un acceso activo no puede perder su último guardia activo.

## Buses y personal

En Buses registrar código único, capacidad máxima positiva, estado, parqueo
obligatorio y línea opcional. Editar para cambiar parqueo o asignación de línea.
Un bus puede estar sin línea, conservando parqueo. Las reasignaciones no pueden
dejar una línea activa bajo el mínimo ni llevar la receptora sobre el máximo.

Pilotos incluye nombres, apellidos, identificación interna, teléfono/correo,
dirección, residencia, nivel e historial educativo y activo. Operadores y guardias
incluyen solo datos administrativos básicos. «Operadores» no crea cuentas para
ingresar: las cuentas se gestionan separadamente en Usuarios por un administrador.

## Recorridos

Administrativo abre Recorridos → Nuevo registro. Seleccionar bus ACTIVO
asignado a la línea activa y piloto activo. Completar fecha, inicio, fin opcional,
ocupación estimada porcentual, estado y observaciones. FINALIZADO exige fin. No
registrar fin menor que inicio; dividir en segmentos diarios si cruza medianoche.
No se calcula ocupación automáticamente. Debajo de 25 % el detalle y el mensaje
indican «Aplicar espera adicional de 5 minutos.» y se crea alerta informativa.
25 % no genera esa alerta. Las correcciones mantienen el vínculo histórico de línea;
si la alerta ya no aplica, cualquiera de los dos roles debe atenderla/cerrarla
explícitamente registrando la gestión realizada.

Ambos roles pueden finalizar recorridos. En Recorridos, filtrar por Línea si se
desea: cada fila identifica línea, bus, fecha/inicio y estado. PROGRAMADO equivale
a pendiente de realizar; los PROGRAMADO y EN_CURSO muestran un botón Finalizar.
Pulsarlo abre una confirmación con la hora local de finalización en formato 24 h.
Confirmar guarda FINALIZADO y registra al usuario en auditoría. No se puede poner
una hora anterior al inicio ni una fecha/hora futura. Los finalizados o cancelados
no se vuelven a finalizar. Operativo no puede cambiar bus, piloto, línea ni ocupación.
Los ejemplos precargados ya están finalizados; un Administrativo puede crear uno
programado para demostrar el nuevo flujo.

## Registrar demanda

Administrativo abre Demanda estimada → Nuevo registro. Operativo solo consulta.
Seleccionar estación y línea activa coherentes, cantidad, fecha no futura, hora y
observaciones. Guardar. El responsable es su usuario autenticado, sin campo editable.
La referencia automática es la capacidad mayor de los buses ACTIVO de la línea;
se conserva en el detalle. Si no hay bus activo, corregir primero la preparación.

Con referencia 100, registrar 149 no alerta y 150 sí. Tras guardar se muestra el
resultado y se crea alerta de alta demanda cuando corresponde. Son pasajeros
observados, no ocupación exacta ni conteos automáticos de molinetes. La demanda
guardada puede ser editada por Administrativo; la referencia y autor originales
se conservan. Las alertas previas permanecen como evidencia histórica.

## Alertas

Ambos roles pueden consultar y atender. Desde el dashboard, Alertas o su detalle,
pulsar Atender (si está pendiente) o Registrar gestión. Escribir qué se hizo y elegir
el estado resultante: Pendiente si necesita más seguimiento, Atendida si ya se
gestionó o Cerrada si se concluye. Guardar gestión registra automáticamente usuario,
fecha/hora local y transición de estado. La nota es obligatoria, hasta 2000 caracteres.

El detalle y el formulario muestran Historial de atención con todas las notas y
sus autores/fechas. Nuevas gestiones se agregan sin reemplazar las anteriores; puede
reabrir una cerrada eligiendo Pendiente y explicando por qué. El tipo, descripción
original y referencias no son editables desde esta acción. Las alertas previas
sin notas muestran un historial vacío hasta que se registre una gestión real.
La aplicación no ejecuta acciones físicas. El dashboard actualiza los contadores
de pendientes, atendidas y cerradas según el resultado guardado.

## Reportes

Ambos roles abren Reportes y eligen: estaciones, líneas, estaciones por
línea, buses por línea, recorridos, demanda o alertas. Aplicar filtros de línea,
estación, fecha y estado. Fecha aplica a recorridos, demanda y alertas; estado
ACTIVO/INACTIVO a catálogos y estados específicos a buses/recorridos/alertas.
Sin coincidencias muestra «Sin resultados». Tablas de hasta 50 filas por página;
la paginación conserva filtros. Descargar CSV genera un archivo con todas las
filas coincidentes, no solo la página visible, usando los filtros del formulario.
Los encabezados indican unidades. El archivo UTF-8 se puede abrir en una hoja
de cálculo; los textos que podrían interpretarse como fórmulas se neutralizan.
No hay PDF. La tabla de demanda muestra registros
individuales por estación, con referencia y responsable.

## Usuarios, auditoría y salida

Solo Administrativo gestiona usuarios: nombre, datos básicos, activo, clave inicial
y un rol, Administrativo u Operativo. Para dar de baja, desactivar cuenta (no puede desactivarse a sí mismo).
Usuarios existentes se editan sin mostrar contraseñas. Auditoría permite consultar
fecha, autor, módulo, acción, registro y descripción. No es editable.

Para eliminar una cuenta, Administrativo abre Usuarios → Eliminar en la fila
correspondiente → Confirmar eliminación. Cancelar vuelve al listado sin cambios.
No se puede eliminar la cuenta con la que está conectado ni un superusuario técnico.
Si la cuenta es responsable de demandas, se conserva y aparece un mensaje: use
Editar y desmarque Activo para retirarle el acceso sin perder el historial.
Una eliminación correcta se registra en auditoría; Operativo no tiene esta acción.

Salir en la barra superior cierra la sesión con POST protegido por CSRF. Accesos
no autorizados muestran 403; direcciones inexistentes, 404. Errores inesperados en
modo sin DEBUG muestran página 500 simple; contactar al administrador local.
