# Research: Verificación de resolubilidad

Decisiones de diseño de la especificación 006. Cada una responde a uno o más requisitos.

## R1. Cómo se recorre la cripta (FR-002 a FR-005, FR-023, FR-024)

- **Decision**: Un recorrido en anchura **por rondas** desde `sala_inicial`. Una salida se atraviesa si está abierta o si su llave se obtuvo en una ronda anterior. Una salida cerrada cuya llave todavía no se tiene se anota en la **lista de espera de esa llave**. Al terminar la ronda, las llaves halladas se dan por obtenidas, en orden de id, y las salas de sus listas de espera que todavía no se visitaron forman la ronda siguiente.
- **Rationale**: Cada sala entra al recorrido una sola vez y cada salida se examina una sola vez, cuando se procesa la sala que la declara. Cada anotación en espera se libera una sola vez. El costo total es O(S + E + L) más ordenar las llaves de cada ronda, sin repetir nada por cada llave nueva.
- **Alternatives considered**:
  - **Repetir el recorrido completo cada vez que aparece una llave** (la alternativa ingenua de §5.4): O(K · (S + E)). Es la que se mide como comparación.
  - **Buscar sobre estados (sala, llaves que se tienen)**: sería exacta incluso con salidas de un solo sentido, pero el número de estados crece como 2^K.
  - **Un recorrido por llave para ver qué abre cada una**: también repite trabajo por llave y no da el orden directamente.

## R2. El orden de obtención (FR-006, FR-007, aclaración P1)

- **Decision**: Las llaves van por rondas y, dentro de cada ronda, por id, con el `merge_sort` propio del proyecto. Cada llave aparece una sola vez, en la primera ronda en que se alcanza.
- **Rationale**: El conjunto de salas de cada ronda está definido sin ambigüedad (las que se alcanzan con las llaves de rondas anteriores), así que el orden no depende de cómo se recorra ni de cómo lleguen los datos. Cada llave de la ronda r se alcanza solo con llaves de rondas anteriores, así que aparece después de todas las que necesita.

## R3. Qué ubicación se muestra en cada línea del orden (FR-006, aclaración P5)

- **Decision**: Si una llave tiene varias ubicaciones, se muestra la de la sala de menor id entre las que se alcanzan en su ronda.
- **Rationale**: La primera que encuentra el recorrido también sería determinista, pero dependería del detalle del recorrido. Con esta regla, la variante ingenua y la incremental muestran lo mismo, y FR-028 se puede comprobar línea por línea.

## R4. La explicación del bloqueo (FR-009 a FR-014, aclaraciones P2 y P3)

- **Decision**: Después de las rondas, el recorrido sigue más allá de la frontera. Saca de un **montículo binario propio** la llave pendiente de mayor prioridad: primero las que no tienen ubicación y, entre las demás, la de menor id. Abre en hipótesis sus puertas en espera, ordenadas por sala de origen y dirección, y recorre desde ahí. Cada sala que se alcanza así queda **custodiada** por la llave de la última puerta abierta en hipótesis para llegar a ella. Una llave que está en una sala custodiada **depende** de la llave que la custodia. Una llave que no tiene ninguna ubicación es «sin ubicación», y una cuya sala no se alcanza ni abriendo todo está en una «zona sin acceso».
- **Rationale**: Cada sala y cada salida se siguen examinando una sola vez en todo el recorrido, y cada llave entra al montículo una vez, así que la explicación cuesta O(S + E + K log K) más el orden de las puertas en espera. Abrir primero las llaves sin ubicación hace que, si a una sala se llega por una de esas puertas, el reporte señale esa causa de fondo y no un ciclo (FR-013).
- **Alternatives considered**:
  - **Comprobar para cada llave si su sala se alcanza abriendo todo menos sus propias puertas**: es la definición exacta de «detrás de puertas que solo ella abre», pero es un recorrido completo por llave, justo lo que §5.4 pide evitar.
  - **Abrir todas las llaves pendientes a la vez**: no deja saber qué llave custodia cada sala.

## R5. Los ciclos (FR-012, FR-025)

- **Decision**: Como cada llave bloqueada depende de a lo sumo una, las dependencias forman un grafo funcional. Se recorren en orden de id siguiendo los punteros y marcando cada llave una vez. Cuando el camino actual vuelve a una llave que ya está en él, ese tramo es un ciclo. Cada ciclo se rota para empezar en su llave de menor id, y la lista de ciclos se ordena.
- **Rationale**: O(K) en total y determinista. El ciclo que se reporta es concreto: la secuencia de llaves.

## R6. Salidas de un solo sentido (FR-004)

- **Decision**: Una salida solo se recorre desde la sala que la declara. La región alcanzable se trata como un conjunto: una llave obtenida sirve en cualquier sala de la región.
- **Rationale**: Es lo que permite el recorrido lineal.
- **Límite conocido**: con salidas de un solo sentido, el jugador podría obtener una llave en una sala desde la que no puede volver a la puerta que esa llave abre, y la verificación diría «resoluble» igual. Resolverlo exactamente exige seguir la pareja (sala, llaves que se tienen), que crece como 2^K. Las criptas publicadas a la fecha no tienen salidas de un solo sentido. Queda escrito en las suposiciones de la especificación y en la sección 5.4 de DECISIONES.

## R7. Dónde se llama y cómo se detiene el inicio (FR-001, FR-016 a FR-020, FR-022)

- **Decision**: `RepositorioCripta.iniciar_partida` verifica justo después de obtener la ubicación de llaves, con un mapa propio armado por un traductor aparte (para que sus avisos no se dupliquen en el reporte final), y guarda el reporte. Con `exigir_resolubilidad=True` y una cripta no resoluble, lanza `CriptaNoResoluble(reporte)` antes de pedir contenido o fichas. `verificar_cripta(id)` llega hasta el mismo punto y devuelve el reporte. Si no se obtuvo la ubicación de llaves (carga de partida guardada), no hay reporte; si no está disponible, el reporte dice que no se pudo verificar y no se exige nada.
- **Rationale**: El enunciado pide no gastar en una cripta que no se puede ganar, y `--verificar` no debe pedir contenido. `exigir_resolubilidad` vale falso por defecto, así que la reproducción y todos los usos de la primera parte no cambian (aclaración P4).

## R8. El reporte (FR-008 a FR-011, FR-015, FR-018, FR-021)

- **Decision**: `ReporteDeResolubilidad` es un objeto de datos con `se_pudo_verificar`, `es_resoluble`, el orden, las llaves no obtenibles con su motivo, las puertas de la frontera, sus ubicaciones y los ciclos. Expone `lineas_de_texto()` y `codigo_de_salida()` (0 resoluble, 1 no resoluble, 2 sin verificar).
- **Rationale**: La vista y las banderas solo necesitan esas dos operaciones, sin saber cómo se calculó nada.

## R9. La medición (FR-026 a FR-028)

- **Decision**: La variante ingenua es la misma clase con otra forma de recorrer: en cada ronda repite el recorrido completo desde `sala_inicial` con las llaves que ya se tienen. La explicación del bloqueo es la misma en las dos. Las criptas sintéticas son cadenas de zonas: la zona i tiene la llave i y una puerta que esa llave abre hacia la zona i+1, con costos al azar y algunas llaves en lo que suelta un enemigo, todo con `random.Random(semilla)`. Además del tiempo, cada variante cuenta las salas y salidas que examina.
- **Rationale**: En una cadena, cada llave es una ronda, así que «repetir por ronda» es exactamente «repetir por cada llave». El conteo muestra el crecimiento sin depender de la máquina, y comparar las líneas de reporte comprueba FR-028.
