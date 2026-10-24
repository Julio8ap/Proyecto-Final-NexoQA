-- SQLite / Django. Consultas documentales de solo lectura.
-- Datos DEMOSTRATIVOS; no representan operación real de Transmetro.

-- 1. Estaciones por municipalidad.
SELECT e.id, e.nombre, m.nombre AS municipalidad, e.activo
FROM operacion_estacion e
JOIN operacion_municipalidad m ON m.id = e.municipalidad_id
ORDER BY e.nombre;

-- 2. Líneas con distancia total calculada en kilómetros.
SELECT l.id, l.nombre, COALESCE(SUM(t.distancia_desde_anterior), 0) AS distancia_total
FROM operacion_linea l
LEFT JOIN operacion_lineaestacion t ON t.linea_id = l.id
GROUP BY l.id, l.nombre;

-- 3. Estaciones de una línea, en orden (reemplazar 1 por el ID deseado).
SELECT l.nombre AS linea, t.orden, e.nombre AS estacion, t.distancia_desde_anterior
FROM operacion_lineaestacion t
JOIN operacion_linea l ON l.id = t.linea_id
JOIN operacion_estacion e ON e.id = t.estacion_id
WHERE l.id = 1
ORDER BY t.orden;

-- 4. Buses asignados por línea, incluyendo buses sin asignación.
SELECT b.codigo, l.nombre AS linea, b.capacidad_maxima, b.estado, p.nombre AS parqueo
FROM operacion_bus b
LEFT JOIN operacion_linea l ON l.id = b.linea_id
JOIN operacion_parqueo p ON p.id = b.parqueo_id
ORDER BY l.nombre, b.codigo;

-- 5. Recorridos realizados y piloto histórico.
SELECT r.fecha, r.hora_inicio, r.hora_final, b.codigo, l.nombre AS linea,
       p.nombres, p.apellidos, r.ocupacion_estimada, r.estado
FROM operacion_recorrido r
JOIN operacion_bus b ON b.id = r.bus_id
JOIN operacion_linea l ON l.id = r.linea_id
JOIN personal_piloto p ON p.id = r.piloto_id
WHERE r.estado = 'FINALIZADO'
ORDER BY r.fecha DESC, r.hora_inicio DESC;

-- 6. Demanda estimada por estación y día; no es ocupación exacta.
SELECT e.nombre AS estacion, d.fecha, SUM(d.cantidad_pasajeros) AS demanda_estimada
FROM operacion_registrodemanda d
JOIN operacion_estacion e ON e.id = d.estacion_id
GROUP BY e.id, e.nombre, d.fecha
ORDER BY d.fecha DESC, e.nombre;

-- 7. Alertas con ubicación y estado; las de baja ocupación pueden no tener estación.
SELECT a.fecha_hora, a.tipo, l.nombre AS linea, e.nombre AS estacion,
       a.descripcion, a.nivel, a.estado
FROM operacion_alerta a
JOIN operacion_linea l ON l.id = a.linea_id
LEFT JOIN operacion_estacion e ON e.id = a.estacion_id
ORDER BY a.fecha_hora DESC;

-- 8. Flota fuera del rango para líneas activas.
SELECT l.nombre, COUNT(DISTINCT t.estacion_id) AS estaciones,
       COUNT(DISTINCT b.id) AS buses
FROM operacion_linea l
LEFT JOIN operacion_lineaestacion t ON t.linea_id = l.id
LEFT JOIN operacion_bus b ON b.linea_id = l.id
WHERE l.activo = 1
GROUP BY l.id, l.nombre
HAVING COUNT(DISTINCT b.id) < COUNT(DISTINCT t.estacion_id)
    OR COUNT(DISTINCT b.id) > 2 * COUNT(DISTINCT t.estacion_id);
