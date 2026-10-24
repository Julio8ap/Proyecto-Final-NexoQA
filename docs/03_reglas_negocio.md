# Reglas de negocio y decisiones

1. Una línea y una estación pertenecen a una municipalidad. Una estación puede
   integrar varias líneas mediante tramos únicos y ordenados. Las distancias se
   expresan en kilómetros; la primera puede ser cero. La distancia total se calcula.
2. Un acceso pertenece a una sola estación. Se crea inactivo, se asigna al menos un
   guardia activo y se activa. No se permite retirar/desactivar/reasignar al último
   guardia de un acceso activo ni desactivar a ese guardia.
3. La línea se prepara inactiva para romper la dependencia inicial entre estaciones
   y flota. N es la cantidad de sus estaciones. Durante preparación se valida el
   máximo 2N; al activar se valida N ≤ buses ≤ 2N, con N ≥ 1, estaciones activas y
   accesos activos con guardias. La activación requiere al menos un acceso activo.
   Las reasignaciones y modificaciones de tramos conservan N–2N en líneas activas.
   La flota cuenta buses asignados, incluyendo mantenimiento; «buses activos» del
   dashboard cuenta únicamente estado ACTIVO. No se desactiva una estación usada
   por una línea activa. Para reorganizar, desactivar la línea, preparar y reactivar.
4. Bus: código único, capacidad entera positiva, parqueo obligatorio, línea opcional.
   Un FK garantiza como máximo una línea. Cambiar parqueo es editar el bus.
5. Personal usa identificación interna única por tipo; los datos de demostración
   son ficticios. Pilotos guardan todos los campos de RF-03. Operadores administrativos
   no equivalen automáticamente a cuentas de usuario.
6. Nuevos recorridos o cambios de bus/línea/piloto requieren línea y piloto activos
   y bus ACTIVO asignado a esa línea. El historial existente se puede consultar y
   corregir aunque cambie la asignación actual del bus. Hora final opcional salvo
   FINALIZADO; nunca menor que inicio. Fechas se validan como fechas Django; se
   permiten recorridos programados futuros. Se trabaja por día, sin cruce de medianoche.
7. Ocupación es un porcentaje manual entre 0 y 100, ambos incluidos. Debajo de 25
   se muestra «Aplicar espera adicional de 5 minutos.» y se crea una alerta de
   BAJA_OCUPACION con relación única al recorrido. Exactamente 25 no genera alerta.
8. Demanda: estación activa de la línea activa, cantidad entera no negativa, fecha
   no futura. Responsable fijado en servidor al User autenticado. Como no se pide
   seleccionar bus en esta pantalla, la referencia es la mayor capacidad entre
   buses ACTIVO asignados a la línea; sin referencia se rechaza. Se almacena la
   referencia en el registro. Solo Administrativo registra o edita demanda; el
   responsable original y la referencia histórica se conservan al editar.
9. Alta demanda si `cantidad * 2 >= capacidad_referencia * 3`, evitando redondeo del
   umbral de 150 %. Una demanda puede generar una sola alerta. 149/100 no alerta;
   150/100 sí alerta. Es demanda estimada, nunca ocupación exacta.
10. Alertas: PENDIENTE, ATENDIDA y CERRADA. Ambos roles registran gestiones y
    cambian estado desde Atender. Se permite cambiar entre los tres estados, incluida reapertura.
    Las alertas existentes permanecen como evidencia histórica si se corrige un recorrido;
    el usuario debe resolverlas explícitamente. No se ejecuta ninguna acción física.
11. Escritura de objeto, evaluación de alerta y auditoría se realizan en transacción.
    Acciones: CREAR, ACTUALIZAR, CAMBIAR_ESTADO. La auditoría registra quién, cuándo,
    módulo y PK, con descripción; no es un registro completo de diferencias de campos.
12. No se ofrecen borrados físicos de datos operativos. Catálogos/personal/asignaciones usan activo;
    buses y recorridos usan estado. Tramos se editan; la reestructuración se realiza
    con la línea inactiva. No hay reservas o programación avanzada de turnos.

13. Dos roles: Administrativo gestiona todos los módulos de negocio y usuarios;
    Operativo consulta, descarga reportes, finaliza recorridos y atiende alertas. No puede
    crear demanda ni editar alertas, personal, usuarios o recorridos por el formulario
    general. Auditoría conserva carácter de evidencia y es de solo lectura.
14. Finalización: botón por fila de recorrido con línea visible y filtro por línea.
    Solo PROGRAMADO (pendiente) y EN_CURSO. El usuario proporciona hora local de
    finalización, no anterior al inicio ni futura respecto a fecha/hora actual.
    Se guarda FINALIZADO, la hora y el autor de la acción en auditoría, en transacción.
    GET no modifica; POST exige CSRF. Reintentos no duplican la finalización.
15. CSV: exporta todas las filas de los filtros vigentes, con unidades en encabezados,
    UTF-8 con BOM y neutralización de textos interpretables como fórmulas. Filtros
    inválidos generan HTTP 400 en descarga. Ambos roles tienen permiso de exportación.

16. Administrativo tiene `auth.delete_user`. Usuarios ofrece Eliminar con pantalla
    de confirmación y POST protegido por CSRF. GET no elimina. La cuenta propia no
    se elimina; un Administrativo funcional no elimina superusuarios técnicos.
    La FK PROTECT de demanda impide eliminar al responsable de registros históricos:
    se muestra un mensaje con la alternativa de desactivar. Una eliminación correcta
    registra ELIMINAR en auditoría dentro de la misma transacción. Los eventos
    anteriores de auditoría se conservan (usuario SET_NULL si se elimina su cuenta).

17. Atender una alerta exige permiso `atender_alerta`, concedido a ambos roles,
    texto no vacío de hasta 2000 caracteres y estado válido. Usuario, nombre histórico
    y fecha/hora se fijan en servidor. Cada envío válido crea una GestionAlerta,
    conservando todas las anteriores, aunque no cambie el estado. Se permite reabrir
    mediante nueva nota. Gestión, estado y auditoría se guardan en una transacción.
    GET solo muestra; POST exige CSRF. No se puede editar tipo, descripción original,
    línea, bus o responsable por este formulario. La antigua edición de estado de
    Administrativo redirige al flujo con nota; no actualiza directamente. Las alertas
    anteriores conservan estado sin fabricar notas de atención previas.

Las reglas multitabla se garantizan por el flujo del sistema en uso académico con
escritores serializados. Actualizaciones masivas, SQL directo y concurrencia avanzada
no están cubiertas. Las restricciones básicas también existen en la base de datos.
