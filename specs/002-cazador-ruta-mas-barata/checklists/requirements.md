# Lista de verificación de la especificación: El cazador, un enemigo que persigue por la ruta más barata

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

De los siete casos del Apéndice B bajo «Terreno y cazador», esta especificación cubre los cinco del cazador. Los otros dos son del terreno y están en `specs/001-terreno-costo-salidas`.

- [x] Un cazador no tiene ruta abierta hacia el jugador: espera con costo 100 → Historia 3, escenario 1, y FR-005
- [x] La ruta más barata del cazador cuesta más que su rango: espera con costo 100 → Historia 3, escenario 2, y FR-006
- [x] Existe una ruta de menos salas pero mayor costo y otra de más salas y menor costo: sigue la de menor costo → Historia 1, escenario 3, FR-004 y SC-001
- [x] Dos vecinas inician rutas de costo mínimo: va a la de menor identificador → Historia 2, escenario 1, FR-008 y SC-002
- [x] Una puerta de la ruta se cierra entre dos turnos: decide como si calculara desde cero → Historia 4, escenario 1, FR-011 y SC-004

## Problemas de estructuras de datos cubiertos

- [x] §5.1, el costo de la decisión depende de la región dentro del rango y no del tamaño de la cripta → FR-017 y SC-005
- [x] §5.1, decenas de cazadores a la vez: cálculo por cazador frente a cálculo compartido → SC-008
- [x] §5.1, el desempate se cumple incluso con muchas rutas de igual costo → Historia 2, escenario 3, y FR-008
- [x] §5.2, qué eventos invalidan qué información y cuánto trabajo se ahorra → FR-011 y SC-007
- [x] §5.2, medir la alternativa de recalcular siempre, con puertas que cambian mucho y poco → SC-007

## Requisitos de interfaz del enunciado cubiertos

- [x] §7.3, la vista distingue a los cazadores de los demás enemigos → Historia 6 y FR-019

## Notas

- La fórmula del intervalo no se repite aquí: ya está en FR-004 de la capacidad 001 y esta especificación solo fija cuál es el costo base de cada acción del cazador.
- «Menor identificador» se dice así, sin nombrar ningún campo ni tipo, porque el desempate es una regla del enunciado y no una decisión de implementación.
- Qué estructura calcula la ruta, si se reutiliza el montículo de la agenda de eventos y si el cálculo se comparte entre cazadores quedan fuera a propósito: son decisiones del `plan.md`. La especificación solo fija qué respuesta es la correcta y bajo qué condición se puede ahorrar trabajo (FR-011).
- Se resolvieron como supuestos documentados, en vez de marcadores de aclaración, tres puntos que el enunciado no dice de forma literal: que un rango igual al costo de la ruta sí permite perseguir (el enunciado dice «mayor que»), que un rango ausente o inválido es un error de datos de cripta (el mismo criterio que la capacidad 001 aplicó al costo) y que un rango de 0 es una ficha válida que simplemente nunca persigue.
- Validación superada en la primera iteración, sin marcadores de aclaración pendientes.
- FR-019 y la Historia 6 se agregaron después, al revisar la capacidad contra §7.3 del enunciado: la interfaz mínima exige distinguir a los cazadores y ninguna especificación lo cubría. Se agregó a esta, que es la del cazador, antes de tocar la vista.
