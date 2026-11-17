# Lista de verificación de la especificación: Niebla de guerra y viaje automático «ir a»

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
- [x] Los requisitos son verificables y no ambiguos (salvo los tres marcados)
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

- [x] `ir a` hacia una sala no explorada: se rechaza y no consume tiempo → Historia 4, escenario 1, y FR-022
- [x] El mapa recuerda abierta una puerta cerrada: al observarla se actualiza, se recalcula y, si no queda ruta, se detiene sin tiempo adicional → Historia 5, escenario 1, FR-006, FR-007, FR-026 y FR-028 (d)
- [x] `ir a` entra a una sala con enemigos dormidos: se activan y el viaje se detiene → Historia 5, escenario 2, FR-025 y FR-028 (b)
- [x] Con la antorcha encendida, entrar explora las vecinas sin activar enemigos ni trampas → Historia 3, escenarios 1 y 2, FR-009 y FR-010
- [x] Un pergamino revierte una entrada con antorcha: las salas exploradas vuelven a su estado anterior → Historia 6, escenario 1, y FR-015
- [x] Un pergamino durante un viaje: revierte solo el último paso y el viaje no continúa → Historia 5, escenario 7, y FR-032

## Problemas de estructuras de datos cubiertos (§5.3)

- [x] Consultar el estado de una sala y de una puerta es frecuente → FR-033 y SC-007
- [x] Explorar cuesta en proporción a las salas reveladas → FR-034 y SC-007
- [x] Registrar e invertir cambios es barato; se revierte y se reconstruye por instante → FR-015, FR-016 y FR-035
- [x] Justificar si «ir a» comparte implementación con el cazador → queda para el `plan.md`, anotado en Supuestos
- [x] Límite de §6.1 para un paso de «ir a» → FR-036 y SC-006

## Notas

- Primera iteración: quedan tres marcadores de aclaración, que son exactamente las tres decisiones que el grupo pidió registrar con `/speckit-clarify`: las puertas nunca observadas de una vecina explorada por la antorcha, si una puerta se observa también cuando cambia con el jugador presente, y cómo se muestra una sala avistada.
- Ningún requisito nombra estructuras de datos, clases, módulos ni algoritmos. «Menor identificador» se dice así, sin nombrar campos ni tipos, igual que en la especificación 002.
- Corrección posterior a `/speckit-analyze` (hallazgo A1): FR-028 (b) y la Historia 5 dicen ahora «enemigos vivos, activos o dormidos», con su pregunta y respuesta en la sección de aclaraciones. En la misma corrección, tres aclaraciones que habían quedado escritas por error dentro de la lista de requisitos, después de FR-029, se movieron a la sección de aclaraciones sin cambiar su texto.
- Corrección posterior (hallazgo I1 de la segunda revisión): FR-036 y SC-006 repiten ahora solo lo que dice §6.1, el límite de 5 ms sobre el mapa conocido completo de la cripta de referencia. Se quitó la regla de medir sobre la cripta publicada más grande y sobre sintéticas de al menos ese tamaño, porque el enunciado no la dice; con qué criptas se mide es decisión del plan. La aclaración original se conserva marcada como reemplazada. El supuesto sobre la cripta de referencia se actualizó: ya está publicada.
- Corrección posterior a la primera implementación: se agrega FR-038. La orden `ir a` se rechaza sin consumir tiempo cuando la partida ya terminó, igual que toda otra acción. El código ya lo hacía y ningún requisito lo decía, que es un defecto del mismo tipo que una especificación incompleta (§1 del enunciado). Va con su aclaración y su caso borde, y se numeró después del último requisito existente, sin reenumerar.
- Corrección del 2026-11-17, salidas de un solo sentido: el grupo confirmó que el servicio puede publicar salidas que solo existen en un sentido. Se agregan una aclaración (sesión 2026-11-17), un caso borde y los escenarios 7 y 8 de la Historia 4: la ruta solo atraviesa cada salida en el sentido en que existe, sigue siendo la de menor costo con el mismo desempate, y no se declara sin ruta cuando hay una salida directa recordada abierta hacia el destino. No se agrega ni se reenumera ningún requisito: FR-023 ya pide recorrer salidas y minimizar su costo, y FR-024 no cambia; los escenarios hacen verificable lo que FR-023 ya decía. Sigue sin nombrarse ninguna estructura, clase ni algoritmo.
