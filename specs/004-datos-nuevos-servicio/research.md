# Research: Datos nuevos del servicio

Decisiones de diseño de la especificación 004 (antes 001). Cada una responde a uno o más requisitos. R1 a R4 quedaron implementadas por las especificaciones 001 y 002 con las mismas decisiones, y se conservan aquí como registro de que este plan llegó a lo mismo.

## R1. Dónde vive el costo de una salida (FR-001, FR-003, FR-004, FR-005) — implementada por la especificación 001

- **Decision**: El costo se guarda en la puerta (`Door.cost`), que es un solo objeto compartido por las dos salas de un paso. La salida lo expone como `Exit.cost`, que devuelve el costo de su puerta.
- **Rationale**: El traductor ya crea una sola puerta por paso para que abrir o cerrar se vea igual desde los dos lados. Si el costo vive ahí, es imposible que los dos sentidos tengan costos distintos: la simetría la da la construcción. Toda salida tiene puerta (también las que siempre están abiertas), así que no hay caso especial. El costo queda listo al cargar el esqueleto, sin depender del contenido (FR-005).
- **Alternatives considered**:
  - Guardar el costo en cada `Exit`: habría que copiarlo a las dos salidas y cuidar que nunca se desincronicen.
  - Una tabla aparte de costos por par de salas: agrega una búsqueda por cada movimiento y por cada paso del cazador, y duplica lo que la puerta ya representa.

## R2. Cómo se combinan los costos de los dos lados (FR-003, aclaración P1 del specify) — implementada por la especificación 001

- **Decision**: Se reutiliza la regla que el traductor ya aplica a la llave y al cierre automático (`_combinar`): el valor que declara un solo lado vale para los dos; si los dos declaran valores distintos, gana el de la sala de menor id y queda un aviso. Para eso, la tabla de salidas pendientes de emparejar guarda, junto a cada puerta, el costo que declaró el primer lado, o nada si no lo declaró. Cuando llega la salida de vuelta se combinan los dos valores declarados y recién entonces se aplica el 100 por defecto.
- **Rationale**: Hay que distinguir «no declaró costo» de «declaró 100». Si el primer lado no declara y el segundo declara 250, el paso cuesta 250, y eso solo se sabe si se recuerda que el primero no declaró.
- **Alternatives considered**: Aplicar el 100 apenas se crea la puerta y comparar después: no distingue entre «no declaró» y «declaró 100», y daría un aviso falso.

## R3. Validación de enteros (FR-002, FR-007) — implementada por las especificaciones 001 y 002

- **Decision**: Un costo o un rango válido es un `int` de Python que no es `bool` y es mayor o igual que 1. Cualquier otro valor lanza `ErrorDatosCripta` con la sala y la dirección (costo) o el id de la ficha (rango), y el valor recibido.
- **Rationale**: En Python `True` es un `int`. Sin excluir `bool`, un `"costo": true` pasaría como costo 1.
- **Pendiente**: la implementación de `main` trata `"costo": null` como valor inválido. El contrato 1.1.0 declara `costo` como entero o null, así que el null debe tratarse como «no declarado» y valer 100 (FR-001). Se corrige en `_costo_de_salida`.

## R4. Cazador y rango en el enemigo (FR-006 a FR-010) — implementada por la especificación 002

- **Decision**: Se agrega `"cazador"` a la tabla de comportamientos del traductor, que lo traduce a la constante `Enemy.HUNTER`. El enemigo recibe el rango en `pursuit_range`. Solo se valida el rango cuando el comportamiento es cazador; en los demás enemigos queda en 0 y, si la ficha lo trae, se anota un aviso de que se ignora (FR-009, corregido el 2026-11-17).
- **Rationale**: El modelo nunca compara contra textos del API (es la regla de la primera parte). Validar el rango solo en el cazador cumple FR-009: en un enemigo que no es cazador el rango no tiene efecto, tampoco si viniera con un valor raro.
- **Alternatives considered**: Validar `rango` en toda ficha de enemigo: le daría efecto (un error) a un campo que la especificación dice que se ignora.

## R5. Representación de la ubicación de llaves (FR-011, FR-012, FR-018, FR-019)

- **Decision**: Cada entrada se convierte en un objeto `KeyLocation(key_id, room_id, enemy_id)`, y la ubicación de llaves de la partida es una `list` de esos objetos en el mismo orden en que llegan. No se indexa por id de llave.
- **Rationale**: La lista conserva el orden y las entradas repetidas, que es lo que piden FR-018 y FR-019. El índice que necesite la verificación de resolubilidad es una decisión de su propio plan, con sus mediciones.
- **Alternatives considered**: Una `TablaHash` por id de llave: pierde el orden y obliga a decidir aquí cómo se guardan las llaves repetidas.

## R6. Dónde se valida (FR-017, FR-019, FR-024)

- **Decision**: La respuesta JSON se guarda y se transporta tal cual, y el traductor la valida y la convierte siempre, venga del servicio, del disco o del paquete offline. La sala se comprueba contra las salas del esqueleto ya cargado. El id de la llave no se comprueba contra el catálogo (aclaración P5). Los campos adicionales se ignoran sin aviso.
- **Rationale**: Un solo camino de validación garantiza que las tres fuentes den el mismo resultado (FR-019), y el traductor ya es el único lugar que conoce los nombres de los campos del API.

## R7. Copia en disco (FR-014, FR-021, FR-022)

- **Decision**: El almacén de la cripta guarda la respuesta tal cual en `<id_cripta>/llaves.json`, con la misma escritura atómica (temporal y `os.replace`) que el resto. Un archivo que no existe, no se puede leer o no tiene la lista `llaves` se trata como ausente.
- **Rationale**: El almacén ya borra la copia entera de la cripta cuando cambia su versión. Si la ubicación de llaves vive en esa misma carpeta, se invalida con la misma regla, sin código nuevo (FR-022).

## R8. Paquete offline sin ubicación de llaves (FR-016, FR-020)

- **Decision**: La fuente offline lanza `UbicacionDeLlavesNoDisponible`, una subclase de `ErrorFuenteDatos`, cuando falta el archivo. El repositorio atrapa solo esa excepción: deja la ubicación como no disponible (`None`, distinto de una lista vacía) y agrega un aviso de datos. Cualquier otro error, como un HTTP 500, un tiempo agotado o el presupuesto agotado, se propaga y la partida no inicia, igual que con los demás datos del inicio.
- **Rationale**: Mantiene jugables los paquetes y las pruebas de la primera parte, sin inventar datos, y sin suavizar fallas reales del servicio.

## R9. Momento y flujos en que se obtiene (FR-011, aclaraciones P1 y P2)

- **Decision**: `iniciar_partida` obtiene la ubicación de llaves justo después de construir el grafo del esqueleto y antes de crear el gestor de contenido y precargar. Recibe un argumento `obtener_ubicacion_de_llaves`, verdadero por defecto, que la carga de una partida guardada pasa en falso. La reproducción lo pasa en falso cuando su log dice que la partida original empezó cargando una partida guardada. La partida nueva y `--verificar` usan el valor por defecto.
- **Rationale**: Si la verificación decide que la cripta no es resoluble, no se habrá gastado nada en contenido. `--replay` hace las mismas solicitudes que la partida original, así que los movimientos rechazados por presupuesto se reproducen igual.

## R10. Línea del reporte final (FR-025, aclaración P4)

- **Decision**: El reporte final agrega la línea `Ubicación de llaves: <origen>`, donde el origen es «descargada del servicio», «recuperada de disco», «leída del paquete offline», «no disponible» o, si la partida empezó cargando una partida guardada, «no se obtuvo en esta partida». Cada fuente sabe cómo describe lo que entrega, así que la fuente offline dice «leída del paquete offline» y la HTTP dice «descargada del servicio».
- **Rationale**: Hace visible en la partida y en las pruebas lo que exigen FR-013 y FR-014. No se mezcla con los aciertos y fallos del catálogo.

## R11. Dobles de fuente de datos en pruebas y benchmarks

- **Decision**: La operación nueva es abstracta en el contrato, como las demás. Los dobles de las pruebas que simulan el servicio la implementan consumiendo una solicitud, como el servicio real. Los dobles de los benchmarks la implementan sin consumir, para no alterar las mediciones ya publicadas. Las pruebas de la primera parte que cuentan las solicitudes exactas de un inicio de partida se ajustan sumando la consulta de llaves, que es justo el cambio que exige FR-013.
- **Rationale**: Un doble que no cuenta la consulta escondería el comportamiento que la especificación pide.
