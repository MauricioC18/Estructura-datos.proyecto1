"""
Mediciones del mapa conocido y del viaje «ir a» (specs/005-niebla-ir-a, §5.3).

Qué se mide y contra qué
    1. Estado de una sala. La tabla de exploradas y los contadores de
       avistamiento, contra la alternativa descartada: una lista de
       exploradas recorrida en cada consulta, que para saber si una sala está
       avistada recorre además las salidas de cada explorada. FR-033.
    2. Estado recordado de una puerta. Clave entera contra clave de texto
       con los ids de las dos salas. FR-033.
    3. Explorar una sala más con un mapa conocido de tamaño k. Contadores
       incrementales contra recalcular todas las avistadas después de cada
       exploración. FR-034.
    4. Revertir una entrada con antorcha. Anotaciones inversas en el
       historial contra copiar el conocimiento antes de la acción. FR-035.
    5. Un paso de «ir a» con el mapa conocido completo, tal como lo calcula
       el viaje del programa (model/viaje.py): el primer paso de un viaje y
       el promedio por paso de un viaje entero. Se comparan con la búsqueda
       completa sin mejoras, que queda fija como referencia, y con una
       búsqueda que escoge el mínimo recorriendo una lista, sin montículo.
       El viaje va de la primera sala del esqueleto a la última; si con el
       mapa conocido no hay ruta entre ellas, va hacia la sala más lejana que
       se alcanza desde la primera, por costo mínimo, y la fila lo dice.
       FR-036.
    6. Salidas de un solo sentido (plan, alternativa 9). Tiempo y memoria de
       armar el índice de salidas entrantes, cuántas salidas entran a cada
       sala, y la búsqueda completa expandida por las salidas que entran
       contra la de hoy, por las que salen. En la cuadrícula simétrica y en
       una variante con la misma semilla donde una de cada cuatro uniones
       existe en un solo sentido. FR-036.

Criptas
    Sintéticas: cuadrículas de tres tamaños crecientes, con el costo de cada
    salida sacado de un random.Random(semilla) propio, así que son las mismas
    en cada corrida. Todas las puertas abiertas, para que el mapa conocido
    completo sea toda la cripta.
    Reales: cada cripta del paquete sin conexión, leída con la misma fuente
    sin conexión que usa el juego y reportada con el id que traen sus datos.
    Si el paquete trae la cripta de referencia, su fila es la que comprueba
    FR-036 tal como lo pide §6.1. Ningún id ni tamaño de cripta está escrito
    aquí.

Las alternativas descartadas se escriben solo en este módulo, para medirlas:
el programa no las usa.
"""
import random
import time
import tracemalloc

from adapters.fuente_offline import FuenteOffline
from benchmark.utilidades_medicion import Measurement, calentar_procesador
from model.game_state import GameState
from model import viaje
from model.room import Door, Exit, Room, RoomMap
from repository.gestor_contenido import descargar_salas_del_esqueleto
from repository.traductor import Traductor
from structures.history import History
from structures.mapa_conocido import MapaConocido
from structures.rutas_mas_baratas import RutasMasBaratas
from structures.tabla_hash import TablaHash

SEMILLA = 2026
LADOS = (10, 20, 40)
COSTO_MAXIMO = 300
CARPETA_SIN_CONEXION = "datos_offline"
# El ejecutor de --bench le pasa a run() la carpeta de --offline, si se dio.
USA_PAQUETE_SIN_CONEXION = True
REPETICIONES = 5


# ----------------------------------------------------------------------
# Criptas
# ----------------------------------------------------------------------


def cuadricula(lado, semilla=SEMILLA):
    """lado x lado salas unidas al E y al N, con costos deterministas."""
    azar = random.Random(semilla)
    room_map = RoomMap()

    for numero in range(1, lado * lado + 1):
        room_map.add(Room(numero, f"Sala {numero}"))

    for fila in range(lado):
        for columna in range(lado):
            numero = fila * lado + columna + 1

            if columna + 1 < lado:
                _unir(room_map, numero, numero + 1, "E", "O", azar)
            if fila + 1 < lado:
                _unir(room_map, numero, numero + lado, "N", "S", azar)

    return room_map


def _unir(room_map, id_a, id_b, ida, vuelta, azar):
    puerta = Door(id_a, id_b, cost=azar.randint(1, COSTO_MAXIMO))
    room_map.room(id_a).add_exit(Exit(ida, id_b, puerta))
    room_map.room(id_b).add_exit(Exit(vuelta, id_a, puerta))


def criptas_sin_conexion(carpeta=CARPETA_SIN_CONEXION):
    """(id, mapa de salas) de cada cripta del paquete, o una lista vacía."""
    try:
        fuente = FuenteOffline(carpeta)
        lista = fuente.listar_criptas()["criptas"]
    except Exception:  # sin paquete no hay criptas reales que medir
        return []

    criptas = []

    for cripta in lista:
        id_cripta = cripta["id"]
        generales = fuente.datos_generales(id_cripta)
        salas = descargar_salas_del_esqueleto(fuente, id_cripta, generales["paginas"])
        criptas.append((id_cripta, Traductor(lambda id_ficha: None).crear_mapa(salas)))

    return criptas


def conocimiento_completo(room_map):
    """El jugador pasó por todas las salas: todo explorado y observado."""
    mapa = MapaConocido(room_map)

    for id_sala in room_map.room_ids():
        mapa.jugador_entro(id_sala)

    return mapa


def mitad_explorada(room_map):
    mapa = MapaConocido(room_map)
    ids = room_map.room_ids()

    for id_sala in ids[: len(ids) // 2]:
        mapa.jugador_entro(id_sala)

    return mapa


def mejor_tiempo(funcion, repeticiones=REPETICIONES):
    mejor = None

    for _ in range(repeticiones):
        inicio = time.perf_counter()
        funcion()
        total = time.perf_counter() - inicio

        if mejor is None or total < mejor:
            mejor = total

    return mejor


# ----------------------------------------------------------------------
# Alternativas descartadas, solo para medirlas
# ----------------------------------------------------------------------


def estado_con_lista(room_map, exploradas, id_sala):
    """Alternativa 2 del plan: recorrer la lista en cada consulta."""
    for explorada in exploradas:
        if explorada == id_sala:
            return "explorada"

    for explorada in exploradas:
        for salida in room_map.room(explorada).exits():
            if salida.destination == id_sala:
                return "avistada"

    return "desconocida"


def avistadas_recalculadas(room_map, exploradas):
    """Alternativa 3 del plan: rehacer todas las avistadas desde cero."""
    avistadas = TablaHash()

    for explorada in exploradas:
        for salida in room_map.room(explorada).exits():
            avistadas.insertar(salida.destination, True)

    return avistadas


def clave_de_texto(puerta):
    menor = puerta.room_a if puerta.room_a < puerta.room_b else puerta.room_b
    mayor = puerta.room_b if menor == puerta.room_a else puerta.room_a
    return f"{menor}-{mayor}"


def primer_paso_sin_monticulo(vecinas, destino, desde):
    """Alternativa 5 (b): costo mínimo escogiendo el siguiente recorriendo
    la lista de pendientes, O(V^2), con el mismo desempate."""
    distancias = TablaHash()
    asentadas = TablaHash()
    distancias.insertar(destino, 0)
    pendientes = [destino]

    while pendientes:
        mejor = 0

        for indice in range(1, len(pendientes)):
            candidata = pendientes[indice]
            actual = pendientes[mejor]
            if (distancias.obtener(candidata), candidata) < (distancias.obtener(actual), actual):
                mejor = indice

        id_sala = pendientes.pop(mejor)

        if asentadas.contiene(id_sala):
            continue

        asentadas.insertar(id_sala, True)

        for vecina, costo, _ in vecinas(id_sala):
            if asentadas.contiene(vecina):
                continue

            nueva = distancias.obtener(id_sala) + costo
            conocida = distancias.obtener(vecina)

            if conocida is None or nueva < conocida:
                distancias.insertar(vecina, nueva)
                pendientes.append(vecina)

    distancia = distancias.obtener(desde)
    elegida = None

    for vecina, costo, salida in vecinas(desde):
        resto = distancias.obtener(vecina)
        if resto is not None and costo + resto == distancia:
            if elegida is None or vecina < elegida[0]:
                elegida = (vecina, salida)

    return None if elegida is None else elegida[1]


# ----------------------------------------------------------------------
# Mediciones
# ----------------------------------------------------------------------


def medir_estado_de_sala(room_map):
    mapa = mitad_explorada(room_map)
    exploradas = mapa.salas_exploradas()
    ids = room_map.room_ids()

    tabla = mejor_tiempo(lambda: [mapa.estado_de_sala(i) for i in ids]) / len(ids)
    lista = mejor_tiempo(
        lambda: [estado_con_lista(room_map, exploradas, i) for i in ids], 1
    ) / len(ids)

    return tabla, lista, len(exploradas)


def medir_puerta_recordada(room_map):
    mapa = conocimiento_completo(room_map)
    puertas = []
    for id_sala in room_map.room_ids():
        for salida in room_map.room(id_sala).exits():
            puertas.append(salida.door)

    por_texto = TablaHash()
    for puerta in puertas:
        por_texto.insertar(clave_de_texto(puerta), puerta.is_open)

    entera = mejor_tiempo(lambda: [mapa.puerta_recordada(p) for p in puertas]) / len(puertas)
    texto = mejor_tiempo(
        lambda: [por_texto.obtener(clave_de_texto(p)) for p in puertas]
    ) / len(puertas)

    return entera, texto


def medir_explorar_una_mas(room_map, muestras=20):
    """Con la mitad explorada, cuánto cuesta explorar una sala más."""
    ids = room_map.room_ids()
    mitad = len(ids) // 2
    siguientes = ids[mitad: mitad + muestras]

    def incremental():
        mapa = mitad_explorada(room_map)
        inicio = time.perf_counter()
        for id_sala in siguientes:
            mapa.jugador_entro(id_sala)
        return time.perf_counter() - inicio

    def recalculando():
        exploradas = list(ids[:mitad])
        inicio = time.perf_counter()
        for id_sala in siguientes:
            exploradas.append(id_sala)
            avistadas_recalculadas(room_map, exploradas)
        return time.perf_counter() - inicio

    mejor_incremental = min(incremental() for _ in range(REPETICIONES))
    mejor_recalculando = min(recalculando() for _ in range(REPETICIONES))

    return mejor_incremental / len(siguientes), mejor_recalculando / len(siguientes), mitad


def medir_revertir_antorcha(room_map, muestras=20):
    """Entrar con antorcha y deshacer, contra copiar y restaurar el conocimiento."""
    ids = room_map.room_ids()
    mitad = len(ids) // 2
    salas = ids[mitad: mitad + muestras]

    def con_anotaciones():
        history = History(GameState(seed=SEMILLA))
        mapa = MapaConocido(room_map, history)
        for id_sala in ids[:mitad]:
            mapa.jugador_entro(id_sala)
        inicio = time.perf_counter()
        for id_sala in salas:
            history.begin_action()
            mapa.jugador_entro(id_sala, antorcha_encendida=True)
            history.undo()
        return time.perf_counter() - inicio

    def con_copia():
        mapa = mitad_explorada(room_map)
        inicio = time.perf_counter()
        for id_sala in salas:
            copia = mapa.exportar()
            mapa.jugador_entro(id_sala, antorcha_encendida=True)
            mapa.importar(*copia)
        return time.perf_counter() - inicio

    anotaciones = min(con_anotaciones() for _ in range(REPETICIONES))
    copia = min(con_copia() for _ in range(REPETICIONES))

    return anotaciones / len(salas), copia / len(salas), mitad


def recorrido_de_prueba(room_map):
    """Destino y partida en los extremos del orden del esqueleto."""
    ids = room_map.room_ids()
    return ids[0], ids[-1]


class _JugadorDePrueba:
    def __init__(self, room_id):
        self.room_id = room_id


class _PartidaDePrueba:
    """Lo único que mira model/viaje.py para calcular un paso: la sala del jugador."""

    def __init__(self, room_id):
        self.player = _JugadorDePrueba(room_id)


def primer_paso_del_programa(mapa, destino, partida):
    """El paso que calcula el viaje del programa al empezar, sin nada guardado."""
    return viaje.siguiente_paso(_PartidaDePrueba(partida), mapa, destino)


def viaje_del_programa(mapa, destino, camino):
    """Todos los pasos de un viaje, calculados como los calcula el programa."""
    partida = _PartidaDePrueba(camino[0] if camino else destino)
    ruta = viaje.RutaDelViaje()

    for sala in camino:
        partida.player.room_id = sala
        viaje.siguiente_paso(partida, mapa, destino, ruta)


ENTRE_EXTREMOS = "entre los extremos"
HACIA_LA_MAS_LEJANA = "hacia la mas lejana"
SIN_ALCANZABLES = "sin salas alcanzables"


class RecorridoMedido:
    """Partida y destino del viaje que se mide, y por qué se escogió ese destino.

    motivo es ENTRE_EXTREMOS, HACIA_LA_MAS_LEJANA o SIN_ALCANZABLES; costo es
    el costo mínimo de la partida al destino, o None si no lo alcanza.
    """

    def __init__(self, partida, destino, motivo, costo):
        self.partida = partida
        self.destino = destino
        self.motivo = motivo
        self.costo = costo


def elegir_recorrido(mapa, room_map):
    """El viaje entre los extremos del esqueleto; si con el mapa conocido no
    hay ruta de la primera sala a la última, el viaje hacia la sala más lejana
    que sí se alcanza desde la primera, por costo mínimo.

    La búsqueda va desde la primera sala y se expande por las salidas que
    SALEN de cada sala, así que la distancia que da es la de ir de la primera
    sala a cada una, también con salidas de un solo sentido. Entre dos salas
    igual de lejanas gana la de menor id, para que la medición se repita.
    """
    partida, ultima = recorrido_de_prueba(room_map)
    desde_partida = RutasMasBaratas(mapa.vecinas_conocidas, partida)

    if ultima != partida and desde_partida.alcanza(ultima):
        return RecorridoMedido(partida, ultima, ENTRE_EXTREMOS, desde_partida.distancia_a(ultima))

    lejana = None
    costo_lejana = None

    for id_sala in room_map.room_ids():
        if id_sala == partida or not desde_partida.alcanza(id_sala):
            continue

        costo = desde_partida.distancia_a(id_sala)

        if lejana is None or costo > costo_lejana or (costo == costo_lejana and id_sala < lejana):
            lejana = id_sala
            costo_lejana = costo

    if lejana is None:
        return RecorridoMedido(partida, ultima, SIN_ALCANZABLES, None)

    return RecorridoMedido(partida, lejana, HACIA_LA_MAS_LEJANA, costo_lejana)


def medir_paso_de_ir_a(room_map, con_alternativa_lineal=True):
    """Un paso de «ir a» con el mapa conocido completo.

    primero: el primer paso de un viaje, como lo calcula el programa.
    por_paso: el promedio por paso de un viaje entero, como lo calcula el programa.
    completa: la búsqueda completa desde el destino, sin ninguna mejora,
        como referencia fija entre una mejora y otra.
    lineal: la alternativa sin montículo.
    recorrido: el RecorridoMedido, que dice hacia dónde fue el viaje.
    """
    mapa = conocimiento_completo(room_map)
    recorrido = elegir_recorrido(mapa, room_map)
    partida, destino = recorrido.partida, recorrido.destino

    camino = []
    sala = partida
    rutas = RutasMasBaratas(mapa.vecinas_conocidas, destino)
    while sala != destino:
        salida = rutas.primer_paso_desde(sala)
        if salida is None:
            break
        camino.append(sala)
        sala = salida.destination

    primero = mejor_tiempo(lambda: primer_paso_del_programa(mapa, destino, partida))
    por_paso = mejor_tiempo(lambda: viaje_del_programa(mapa, destino, camino)) / max(1, len(camino))
    completa = mejor_tiempo(
        lambda: RutasMasBaratas(mapa.vecinas_conocidas, destino).primer_paso_desde(partida)
    )
    lineal = None

    if con_alternativa_lineal:
        lineal = mejor_tiempo(
            lambda: primer_paso_sin_monticulo(mapa.vecinas_conocidas, destino, partida), 1
        )

    return primero, por_paso, completa, lineal, len(camino), recorrido


# ----------------------------------------------------------------------
# 6. Salidas de un solo sentido (plan, alternativa 9)
# ----------------------------------------------------------------------

PROPORCION_UN_SENTIDO = 0.25


def cuadricula_un_sentido(lado, semilla=SEMILLA, proporcion=PROPORCION_UN_SENTIDO):
    """La misma cuadrícula, con los mismos costos, pero una de cada cuatro
    uniones (en promedio) existe solo hacia el E o hacia el N, sin vuelta.

    Como toda unión se puede recorrer hacia el E y hacia el N, siempre hay
    ruta de la primera sala a la última, que es el recorrido de la medición 5.
    """
    azar = random.Random(semilla)
    sentido = random.Random(semilla + 1)
    room_map = RoomMap()

    for numero in range(1, lado * lado + 1):
        room_map.add(Room(numero, f"Sala {numero}"))

    for fila in range(lado):
        for columna in range(lado):
            numero = fila * lado + columna + 1

            if columna + 1 < lado:
                _unir_quizas_un_sentido(room_map, numero, numero + 1, "E", "O", azar,
                                        sentido.random() < proporcion)
            if fila + 1 < lado:
                _unir_quizas_un_sentido(room_map, numero, numero + lado, "N", "S", azar,
                                        sentido.random() < proporcion)

    return room_map


def _unir_quizas_un_sentido(room_map, id_a, id_b, ida, vuelta, azar, un_sentido):
    puerta = Door(id_a, id_b, cost=azar.randint(1, COSTO_MAXIMO))
    room_map.room(id_a).add_exit(Exit(ida, id_b, puerta))

    if not un_sentido:
        room_map.room(id_b).add_exit(Exit(vuelta, id_a, puerta))


def medir_indice_de_entrantes(room_map):
    """Tiempo y memoria de armar el índice de salidas entrantes, y cuántas
    salidas entran a cada sala: (segundos, bytes, mínimo, promedio, máximo)."""
    segundos = mejor_tiempo(lambda: MapaConocido(room_map)._armar_entrantes())

    mapa = MapaConocido(room_map)
    tracemalloc.start()
    antes = tracemalloc.get_traced_memory()[0]
    mapa._armar_entrantes()
    despues = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    cantidades = [len(mapa._entrantes.obtener(id_sala, [])) for id_sala in room_map.room_ids()]
    promedio = sum(cantidades) / len(cantidades)

    return segundos, despues - antes, min(cantidades), promedio, max(cantidades)


def medir_busqueda_con_entrantes(room_map):
    """La búsqueda completa de «ir a» desde el destino, expandida por las
    salidas que salen (como hoy) y por las que entran, con el primer paso por
    las que salen (como quedará). Sin parada anticipada en ninguna de las
    dos: la búsqueda compartida todavía no acepta la parada junto con el
    proveedor de salidas, así que esto mide el costo del proveedor y no el
    del paso final del viaje.

    Devuelve (con salientes, con entrantes, mismo primer paso).
    """
    mapa = conocimiento_completo(room_map)
    partida, destino = recorrido_de_prueba(room_map)
    mapa.entrantes_conocidas(destino)  # el índice se arma fuera de la medición

    def con_salientes():
        return RutasMasBaratas(mapa.vecinas_conocidas, destino).primer_paso_desde(partida)

    def con_entrantes():
        return RutasMasBaratas(
            mapa.entrantes_conocidas, destino, salidas_de=mapa.vecinas_conocidas
        ).primer_paso_desde(partida)

    mismo = con_salientes() is con_entrantes()

    return mejor_tiempo(con_salientes), mejor_tiempo(con_entrantes), mismo


def _us(segundos):
    return f"{segundos * 1e6:.2f} us"


def _ms(segundos):
    return f"{segundos * 1e3:.4f} ms"


def run(carpeta_sin_conexion=CARPETA_SIN_CONEXION):
    """Mediciones de este módulo, para el ejecutor de --bench."""
    calentar_procesador(0.3)
    mediciones = []
    cuadriculas = [(lado * lado, cuadricula(lado)) for lado in LADOS]

    for salas, room_map in cuadriculas:
        tabla, lista, exploradas = medir_estado_de_sala(room_map)
        mediciones.append(Measurement(
            f"1. Estado de una sala, {salas} salas", tabla,
            f"tabla {_us(tabla)} contra lista recorrida {_us(lista)} por consulta "
            f"({exploradas} exploradas)",
        ))

    for salas, room_map in cuadriculas:
        entera, texto = medir_puerta_recordada(room_map)
        mediciones.append(Measurement(
            f"2. Puerta recordada, {salas} salas", entera,
            f"clave entera {_us(entera)} contra clave de texto {_us(texto)} por consulta",
        ))

    for salas, room_map in cuadriculas:
        incremental, recalculando, conocidas = medir_explorar_una_mas(room_map)
        mediciones.append(Measurement(
            f"3. Explorar una sala mas, {salas} salas", incremental,
            f"contadores {_us(incremental)} contra recalcular avistadas "
            f"{_us(recalculando)} ({conocidas} ya exploradas)",
        ))

    for salas, room_map in cuadriculas:
        anotaciones, copia, conocidas = medir_revertir_antorcha(room_map)
        mediciones.append(Measurement(
            f"4. Entrar con antorcha y revertir, {salas} salas", anotaciones,
            f"anotaciones {_us(anotaciones)} contra copiar el conocimiento "
            f"{_us(copia)} ({conocidas} ya exploradas)",
        ))

    for salas, room_map in cuadriculas:
        primero, por_paso, completa, lineal, largo, _ = medir_paso_de_ir_a(room_map)
        mediciones.append(Measurement(
            f"5. Paso de ir a, mapa completo de {salas} salas", primero,
            f"primer paso {_ms(primero)}; por paso en un viaje de {largo} pasos "
            f"{_ms(por_paso)}; busqueda completa {_ms(completa)}; sin monticulo {_ms(lineal)}",
        ))

    for lado in LADOS:
        for nombre, room_map in (("simetrica", cuadricula(lado)),
                                 ("con un sentido", cuadricula_un_sentido(lado))):
            segundos, memoria, minimo, promedio, maximo = medir_indice_de_entrantes(room_map)
            mediciones.append(Measurement(
                f"6. Indice de entrantes, {lado * lado} salas, {nombre}", segundos,
                f"armarlo {_ms(segundos)}, {memoria / 1024:.1f} KiB; salidas que "
                f"entran por sala: min {minimo}, promedio {promedio:.2f}, max {maximo}",
            ))

    for lado in LADOS:
        for nombre, room_map in (("simetrica", cuadricula(lado)),
                                 ("con un sentido", cuadricula_un_sentido(lado))):
            salientes, entrantes, mismo = medir_busqueda_con_entrantes(room_map)
            comparacion = "mismo primer paso" if mismo else "primer paso distinto"
            mediciones.append(Measurement(
                f"6. Busqueda completa con entrantes, {lado * lado} salas, {nombre}",
                entrantes,
                f"expandir por entrantes {_ms(entrantes)} contra por salientes "
                f"{_ms(salientes)}, sin parada; {comparacion}",
            ))

    mediciones.extend(mediciones_de_criptas_reales(carpeta_sin_conexion))

    return mediciones


def mediciones_de_criptas_reales(carpeta_sin_conexion=CARPETA_SIN_CONEXION):
    """Medición 5 en cada cripta del paquete, con el id que traen sus datos."""
    mediciones = []
    reales = criptas_sin_conexion(carpeta_sin_conexion)

    if not reales:
        mediciones.append(Measurement(
            "5. Paso de ir a en criptas reales", None,
            f"no hay paquete sin conexion en {carpeta_sin_conexion}",
        ))

    for id_cripta, room_map in reales:
        primero, por_paso, completa, lineal, largo, recorrido = medir_paso_de_ir_a(room_map)
        if largo == 0:
            # Un viaje sin pasos no tiene nada que promediar.
            promedio = "por paso: el viaje no dio pasos"
        else:
            promedio = f"por paso en un viaje de {largo} pasos {_ms(por_paso)}"
        mediciones.append(Measurement(
            f"5. Paso de ir a, mapa completo de {id_cripta} ({len(room_map)} salas)", primero,
            f"{descripcion_del_recorrido(recorrido)}: primer paso {_ms(primero)}; {promedio}; "
            f"busqueda completa {_ms(completa)}; sin monticulo {_ms(lineal)}",
        ))

    return mediciones


def descripcion_del_recorrido(recorrido):
    """Hacia dónde fue el viaje medido, para la fila de una cripta real."""
    if recorrido.motivo == ENTRE_EXTREMOS:
        return (f"de la sala {recorrido.partida} a la {recorrido.destino} "
                f"(extremos, costo {recorrido.costo})")

    if recorrido.motivo == HACIA_LA_MAS_LEJANA:
        return (f"sin ruta entre los extremos; de la sala {recorrido.partida} a la "
                f"{recorrido.destino}, la mas lejana alcanzable (costo {recorrido.costo})")

    return (f"sin ruta desde la sala {recorrido.partida} a ninguna otra; "
            f"medido hacia la {recorrido.destino}")


if __name__ == "__main__":
    for medicion in run():
        print(f"{medicion.name}: {medicion.detail}")
