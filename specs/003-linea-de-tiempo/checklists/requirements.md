# Lista de verificación de la especificación: La línea de tiempo

**Propósito**: validar que la especificación esté completa y sea de calidad antes de pasar a la planificación
**Creada**: 2026-11-16
**Capacidad**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, bibliotecas, interfaces de programación)
- [x] Centrada en el valor para quien juega y en la regla del juego
- [x] Redactada para que la entienda alguien que no implementó el módulo
- [x] Todas las secciones obligatorias completas

## Completitud de los requisitos

- [x] No quedan marcadores de aclaración pendiente
- [x] Los requisitos son verificables y no ambiguos
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito son independientes de la implementación
- [x] Todos los escenarios de aceptación están definidos
- [x] Los casos borde están identificados
- [x] El alcance está delimitado
- [x] Las dependencias y los supuestos están identificados

## Preparación de la capacidad

- [x] Todos los requisitos funcionales tienen criterio de aceptación
- [x] Los escenarios de uso cubren los flujos principales
- [x] La capacidad satisface los criterios de éxito definidos
- [x] Ningún detalle de implementación se filtró a la especificación

## Casos obligatorios del Apéndice B cubiertos

Los **seis** casos del Apéndice B bajo «Línea de tiempo».

- [x] `historia <t>` con t mayor que el reloj actual: se rechaza → Historia 2, escenario 1, FR-009 y SC-004
- [x] `historia` después de usar un pergamino: no muestra las acciones revertidas → Historia 3, escenario 1, FR-011 y SC-005
- [x] Varios eventos en el mismo instante: muestra el estado después de todos ellos → Historia 1, escenarios 8 y 9, y FR-026
- [x] `historia` no consume tiempo, no se registra en `partida.log` y no toca el historial de retroceso → Historia 1, escenario 10, y FR-005 a FR-008, SC-003
- [x] `--replay --hasta t` con t posterior al final: muestra el estado final e indica que terminó antes → Historia 2, escenario 6, FR-025 y SC-011
- [x] Se carga un archivo de la primera parte: se reporta la incompatibilidad, nunca en silencio → Historia 5, escenario 3, y FR-021

**Corrección.** La primera versión de esta lista decía «los dos casos» y solo mapeaba dos. Son seis, y faltaban cuatro: dos ya estaban cubiertos por requisitos existentes y no estaban mapeados, y dos no estaban cubiertos. Uno de esos dos, el de `--hasta` más allá del final, **contradecía** a FR-009, que rechazaba cualquier instante posterior al reloj; se separó el caso en partida del caso sin interacción, con FR-025. Lo detectó Steven al revisar la especificación, y es un fallo de trazabilidad del §2.5, no un detalle.

## Problema de estructuras de datos §5.5 cubierto

- [x] Una consulta aplica o deshace cambios de a lo sumo *K* acciones → FR-016 y Historia 4, escenario 1
- [x] La memoria crece con los cambios más una copia cada *K*, nunca como acciones por tamaño del estado → FR-017, SC-007 y Historia 4, escenario 3
- [x] Ubicar la copia más cercana a un instante pedido es una búsqueda frecuente y su costo importa → FR-018 y Historia 4, escenario 4
- [x] Al usar un pergamino la línea se recorta sin recorrer toda la historia → FR-019, SC-008 y Historia 4, escenario 5
- [x] Memoria y tiempo de consulta medidos para al menos tres valores de *K*, con el valor por omisión justificado → SC-006

## Otros requisitos del enunciado cubiertos

- [x] El pergamino sigue limitado a cinco acciones y la línea no amplía ese límite (§3.6) → FR-012
- [x] La consulta no consume tiempo, no se registra como acción y no altera nada (§3.6) → FR-005 a FR-008, SC-003
- [x] Consulta sin interacción reproduciendo una bitácora hasta *t*, sin instanciar la vista (§3.6) → FR-014
- [x] Guardar y cargar conserva la línea completa; un archivo de la primera parte se detecta incompatible (§3.6) → FR-020, FR-021

## Notas

- «Copia completa del estado» es el nombre que el enunciado le da a los puntos de control, y aquí se usa en esos términos, sin decir en qué se guarda ni cómo se serializa: eso es del `plan.md`.
- No se dice si la reconstrucción va hacia adelante desde una copia, re-simulando, o hacia atrás invirtiendo cambios. El enunciado permite las dos y la elección es del `plan.md`; la especificación solo fija el resultado y el límite de *K* acciones.
- El valor por omisión de *K* no se fija aquí a propósito: el enunciado pide que se justifique con mediciones, y las mediciones son del plan.
- Se resolvió como supuesto documentado, en vez de marcador de aclaración, qué muestra el resumen en el lugar del mapa conocido mientras la niebla de guerra no exista: se informa que el dato no está disponible y el resumen se construye igual. Dejarlo como dependencia bloqueante habría detenido esta capacidad por una que es de otro integrante.
- Se resolvió también que el instante exacto del reloj actual **sí** es consultable, porque el enunciado solo prohíbe consultar un instante **posterior** al reloj.
- Validación superada en la primera iteración, sin marcadores de aclaración pendientes.
