# Lista de verificación de la especificación: Terreno, costo de tránsito de las salidas

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

De los siete casos del Apéndice B bajo «Terreno y cazador», esta especificación cubre los dos que corresponden al terreno. Los otros cinco son del cazador y van en su propia especificación.

- [x] Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1 → Historia 1, escenario 5, y FR-008
- [x] Cambia la velocidad de un actor que atraviesa una salida costosa: el tiempo restante se escala según P1 §2.3 → Historia 4, escenarios 1 y 2, y FR-009

## Notas

- La fórmula del intervalo aparece en FR-004 porque es una regla del juego que fija el enunciado, no una decisión de implementación. Se redactó sin sintaxis de ningún lenguaje.
- Qué estructura de datos guarda el costo, y cómo se calculan rutas de costo mínimo con él, quedan fuera a propósito: lo primero es decisión del `plan.md` y lo segundo es de las capacidades del cazador y del viaje automático.
- Validación superada en la primera iteración, sin marcadores de aclaración pendientes.
