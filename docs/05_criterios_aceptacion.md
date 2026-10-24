# Criterios de aceptación

| Área | Criterio observable | Evidencia |
| --- | --- | --- |
| Login | Sin sesión se redirige al login; una clave válida permite entrar; salida POST cierra sesión | CP-01 |
| Roles | Solo dos opciones: Administrativo gestiona módulos y usuarios; Operativo consulta y no tiene creación/edición general | CP-02, 03, 20 |
| Líneas | Se prepara inactiva; activar sin estaciones/flota falla; detalle muestra suma de distancias | CP-09 |
| Estaciones | Estación puede compartirse entre líneas; no se repite dentro de la misma ni se duplica orden | Datos demo y CP-10 |
| Buses | Se rechaza capacidad cero y parqueo vacío; línea opcional; flota activa entre N y 2N | CP-06, 07, 08 |
| Parqueos | Bus conserva parqueo obligatorio y puede cambiarlo por edición; catálogos consultables | CP-04, 06 |
| Personal | Formulario piloto incluye residencia y educación; guardias/operadores administrativos; acceso activo conserva guardia | CP-04, 11, 20 |
| Recorridos | Bus coincide con línea actual al asignar; horas válidas; finalizado requiere fin; porcentaje 0–100 | CP-15, 16 |
| Baja ocupación | 24.99 % muestra espera adicional de cinco minutos y alerta; 25 % no | CP-15 |
| Demanda | Usuario autenticado se fija como responsable; no negativos ni fecha futura ni estación ajena | CP-13, 14 |
| Alta demanda | Referencia 100: demanda 149 no alerta y 150 sí; alerta no duplicada | CP-12, 17 |
| Alertas | Ambos roles atienden desde dashboard/listado/detalle; nota obligatoria; autor/fecha automáticos; historial sin sobrescribir y estado auditado; inválidos/CSRF bloqueados | CP-18 |
| Reportes | Ambos roles visualizan siete tablas y descargan CSV completo con filtros, unidades y protección de fórmulas | CP-19 |
| Finalización | Ambos roles finalizan programados/en curso con botón por fila; no se permite cierre futuro, anterior al inicio, repetido ni alterar otros campos | CP-02 |
| Identidad y unidades | Franja «Sistema Municipal», pie «Desarrollado por nexoQA»; cantidades rotuladas con personas/pasajeros, km o % | CP-04 |
| Auditoría | Creaciones/actualizaciones/cambios de estado incluyen autor, módulo, fecha y registro; fallo revierte transacción | CP-18, 20, 25 |
| Demostración | Repetir seed no duplica datos ni restablece contraseñas | CP-21 |
| Eliminar usuarios | Administrativo elimina con confirmación POST; Operativo no; cuenta propia, superusuarios técnicos y responsables de demanda protegidos; éxito auditado | CP-20 |
| Seguridad | CSRF rechaza POST sin token; texto HTML se escapa; claves son hash | CP-05, 20, 23 |

Aceptación automatizada funcional: satisfecha en la ejecución documentada.
La aceptación visual y el ensayo de respaldo corresponden a la revisión manual
de la presentación y no se consideran ejecutados por estas pruebas HTTP.
