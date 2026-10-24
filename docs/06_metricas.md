# Métricas de calidad

Resultados observados el 23/10/2026 tras ejecutar la suite, sin anticipar resultados.

Actualización Sistema Municipal: se mantiene la suite en 25 casos, ampliando CP-02
con finalización restringida, CP-03 con migración a dos roles, CP-04 con identidad y
unidades, CP-05 con CSRF de finalización y CP-19 con CSV completo (>50 filas), filtros,
permisos y neutralización de fórmulas. Última ejecución: 25 aprobados, cero fallos,
11.295 segundos. Evidencia en `12_validacion_actualizacion.txt`. Las descripciones
vigentes de los casos están en el plan de pruebas actualizado.

Actualización posterior de atención de alertas: CP-18 verifica ambos roles, texto
obligatorio, autor automático, historial, cambio/reapertura, CSRF, escape de contenido
y rollback transaccional. Ejecución actual: 25/25 aprobadas, cero fallos, 8.174 s.
Migración 0004 aplicada y sin cambios de modelos pendientes. Evidencia completa
en `13_validacion_atencion_alertas.txt`; las cifras anteriores corresponden a sus
respectivas revisiones y no sustituyen esta ejecución más reciente.

| Métrica | Fórmula/dato | Resultado | Meta |
| --- | --- | --- | --- |
| Pruebas aprobadas | 25 aprobadas / 25 ejecutadas × 100 | 100 % | ≥ 95 % |
| Defectos críticos abiertos conocidos | Incidencias críticas detectadas y no resueltas en suite/check | 0 | 0 |
| Cobertura de requerimientos funcionales | 6 RF verificados / 6 RF definidos × 100 | 100 % | 100 % |
| Casos por RF | Ver distribución inferior | Todos ≥ 1 | ≥ 1 |

| Requerimiento | CP relacionados | Cantidad |
| --- | --- | --- |
| RF-01 | 04, 09, 10, 20 | 4 |
| RF-02 | 06, 07, 08, 09, 20, 22 | 6 |
| RF-03 | 04, 11, 20 | 3 |
| RF-04 | 15, 16, 20, 22, 25 | 5 |
| RF-05 | 12, 13, 14, 15, 17, 18, 24 | 7 |
| RF-06 | 01, 02, 03, 04, 18, 19, 20, 25 | 8 |

La cobertura es trazabilidad funcional por requisito, no cobertura de líneas de
código ni comprobación exhaustiva de todos los caminos posibles. Para los cinco
RNF se proporciona evidencia y limitaciones en `01_requerimientos.md`; no se
declara un 100 % de validación visual, rendimiento bajo carga o recuperación de
respaldo. La ausencia de defectos conocidos no implica ausencia absoluta de defectos.

Incidencia durante pruebas: CP-19 inicialmente exigía una alerta en una estación
con demanda 149/100. Se corrigió el dato seleccionado en la prueba para usar una
estación con alerta existente. La suite completa se volvió a ejecutar satisfactoriamente.
No se omitieron pruebas para obtener el resultado final.

Al ampliar CP-20 para recorrer la preparación por formularios se encontró un
defecto real: el ModelForm de Linea incluía el M:N estaciones como obligatorio,
impidiendo crear una línea nueva. Se excluyó el campo del formulario; las estaciones
se gestionan mediante LineaEstacion. Suite repetida: 25/25 aprobadas. Defecto cerrado.
