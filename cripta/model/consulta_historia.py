"""
Consulta de un instante pasado de la partida (seccion 3.6 de la segunda parte).

Que hace
    Responde como estaba la partida en un instante anterior, sin tocar la
    partida viva.

Como lo hace: hacia adelante desde un punto de control
    1. Traduce el instante pedido a un numero de accion del jugador.
    2. Localiza la ultima copia completa tomada en o antes de ese numero, con
       la busqueda binaria de la linea.
    3. Reconstruye esa copia en OBJETOS NUEVOS, por el camino de carga que ya
       existe, que usa Game.load y no rehace el trabajo de inicio de partida.
    4. Repite a lo sumo K acciones del jugador sobre ese motor reconstruido.
    5. Devuelve el resumen como dato, no como texto.

Por que no se reconstruye hacia atras
    El historial reversible guarda cambios inversos, pero sus objetos de
    cambio guardan referencias directas a los objetos vivos. Para acotar una
    consulta a K acciones hay que partir de una copia, y una copia
    reconstruida crea objetos nuevos: los cambios inversos no se les pueden
    aplicar. El razonamiento completo esta en el plan de la capacidad.

Por que la consulta no puede alterar la partida
    Por construccion, no por cuidado: todo ocurre sobre objetos nuevos. La
    partida viva solo se lee para saber en que instante esta y para pedirle su
    linea de tiempo.

Y por que el motor reconstruido va sin bitacora y sin repositorio
    Repetir una accion no debe escribir en la bitacora de reproduccion ni
    provocar ninguna solicitud al servicio. Al no darle ninguno de los dos, no
    puede (FR-006 y el presupuesto de solicitudes).
"""
from model.game import (
    ACTION_ATTACK,
    ACTION_DROP,
    ACTION_EQUIP,
    ACTION_MOVE,
    ACTION_OPEN,
    ACTION_PICK_UP,
    ACTION_USE,
    ACTION_WAIT,
)


MAPA_CONOCIDO_NO_DISPONIBLE = "todavia no implementado"


PARTIDA_TERMINO_ANTES = (
    "La partida termino antes del instante pedido; se muestra el estado final."
)


class ConsultaRechazada(ValueError):
    """El instante o el numero de accion pedidos no se pueden consultar."""


class ResumenDeInstante:
    """Foto del estado en un instante. Es un dato: la vista decide como se ve.

    mapa_conocido viene de la capacidad de niebla de guerra, que es de otro
    integrante. Mientras no exista, se informa que el dato no esta disponible
    y el resumen se construye igual, para no bloquear esta capacidad con una
    que es de otro.
    """

    __slots__ = (
        "aviso",
        "instante",
        "acciones_del_jugador",
        "sala",
        "nombre_de_la_sala",
        "vida",
        "vida_maxima",
        "ataque",
        "defensa",
        "velocidad",
        "inventario",
        "efectos",
        "enemigos",
        "mapa_conocido",
        "resultado",
        "acciones_repetidas",
    )

    def __init__(self, **campos):
        for nombre in self.__slots__:
            setattr(self, nombre, campos.get(nombre))


def consultar_instante(juego, instante, reconstruir_copia):
    """Resumen del estado en ese instante del reloj.

    reconstruir_copia es una funcion que recibe el bloque de bytes de una
    copia y devuelve un Game nuevo. La da quien sepa deserializar, que es el
    adaptador, no el modelo (principio III).
    """
    _exigir_entero(instante, "El instante")

    if instante < 0:
        raise ConsultaRechazada(
            f"No existe el instante {instante}: el reloj empieza en 0."
        )

    if instante > juego.state.clock:
        raise ConsultaRechazada(
            f"No se puede consultar el instante {instante}: el reloj de la "
            f"partida esta en {juego.state.clock} y el futuro todavia no ocurrio."
        )

    linea = _exigir_linea(juego)
    numero = linea.accion_en_instante(instante)

    return _reconstruir(juego, linea, numero, instante, reconstruir_copia)


def consultar_accion(juego, numero_de_accion, reconstruir_copia):
    """Resumen del estado justo antes de la accion numero k del jugador."""
    _exigir_entero(numero_de_accion, "El numero de accion")

    if numero_de_accion < 0:
        raise ConsultaRechazada(
            f"No existe la accion numero {numero_de_accion}."
        )

    linea = _exigir_linea(juego)

    if numero_de_accion > linea.cantidad_de_acciones():
        raise ConsultaRechazada(
            f"No se puede consultar la accion numero {numero_de_accion}: el "
            f"jugador ha tomado {linea.cantidad_de_acciones()}."
        )

    if numero_de_accion == linea.cantidad_de_acciones():
        instante = juego.state.clock
    else:
        instante = linea.acciones()[numero_de_accion].reloj

    return _reconstruir(
        juego, linea, numero_de_accion, instante, reconstruir_copia
    )


def consultar_hasta(juego, instante, reconstruir_copia):
    """Resumen para una reproduccion sin interaccion (FR-014, FR-025).

    Se diferencia de consultar_instante en un solo punto, y es a proposito: si
    el instante pedido es POSTERIOR al final de la partida, no se rechaza. Se
    devuelve el estado final con un aviso de que la partida termino antes.

    El motivo es que reproducir una partida ya terminada no tiene futuro que
    inventar, solo un final al que llegar: pedir «hasta el instante 9999» de
    una partida que duro 3 000 es una forma normal de pedir el final. En
    partida, en cambio, el futuro de verdad no ocurrio y FR-009 lo rechaza.
    """
    _exigir_entero(instante, "El instante")

    if instante < 0:
        raise ConsultaRechazada(
            f"No existe el instante {instante}: el reloj empieza en 0."
        )

    if instante <= juego.state.clock:
        return consultar_instante(juego, instante, reconstruir_copia)

    resumen = consultar_instante(juego, juego.state.clock, reconstruir_copia)
    resumen.aviso = PARTIDA_TERMINO_ANTES

    return resumen


def _reconstruir(juego, linea, numero_de_accion, instante, reconstruir_copia):
    copia = linea.copia_para_accion(numero_de_accion)

    if copia is None:
        raise ConsultaRechazada(
            "La linea de tiempo no tiene ningun punto de control del que partir."
        )

    reconstruido = reconstruir_copia(copia.bloque)
    repetidas = 0
    ultima = numero_de_accion - 1

    for posicion in range(copia.acciones, numero_de_accion):
        if posicion == ultima:
            # El tope solo se pone en la ultima accion que se repite. Sin el,
            # el ciclo seguiria hasta la siguiente decision del jugador y
            # traeria eventos POSTERIORES al instante pedido.
            reconstruido.detener_eventos_en(instante)

        _repetir(reconstruido, linea.acciones()[posicion])
        repetidas += 1

    reconstruido.detener_eventos_en(None)

    return _resumir(reconstruido, instante, numero_de_accion, repetidas)



def _repetir(reconstruido, accion):
    """Vuelve a ejecutar una accion del jugador sobre el motor reconstruido."""
    nombre = accion.nombre
    argumento = accion.argumento

    if nombre == ACTION_WAIT:
        return reconstruido.wait()

    if nombre == ACTION_MOVE:
        return reconstruido.move(argumento)

    if nombre == ACTION_OPEN:
        return reconstruido.open_door(argumento)

    if nombre == ACTION_ATTACK:
        return reconstruido.attack(argumento)

    if nombre == ACTION_PICK_UP:
        return reconstruido.pick_up(argumento)

    if nombre in (ACTION_DROP, ACTION_USE, ACTION_EQUIP):
        _poner_el_cursor_en(reconstruido, argumento)

        if nombre == ACTION_DROP:
            return reconstruido.drop()

        if nombre == ACTION_USE:
            return reconstruido.use_item()

        return reconstruido.equip_item()

    raise ConsultaRechazada(
        f"La linea de tiempo tiene una accion que no se sabe repetir: {nombre!r}."
    )


def _poner_el_cursor_en(reconstruido, instance_id):
    """Deja el cursor del inventario sobre ese objeto, por su identificador.

    Soltar, usar y equipar actuan sobre el objeto que el cursor muestra, y el
    cursor lo mueven comandos que no consumen tiempo y por lo tanto no son
    acciones. Por eso la linea guarda el identificador del objeto y no su
    posicion: la posicion no se podria repetir.
    """
    inventory = reconstruido.player.inventory

    if inventory is None or instance_id is None:
        return

    inventory.go_to_start()

    for _ in range(len(inventory)):
        actual = inventory.current()

        if actual is not None and actual.instance_id == instance_id:
            return

        if not inventory.next():
            return


def _resumir(reconstruido, instante, numero_de_accion, repetidas):
    jugador = reconstruido.player
    sala = None

    if reconstruido.room_map is not None and reconstruido.room_map.contains(
        jugador.room_id
    ):
        sala = reconstruido.room_map.room(jugador.room_id)

    return ResumenDeInstante(
        instante=instante,
        acciones_del_jugador=numero_de_accion,
        sala=jugador.room_id,
        nombre_de_la_sala=None if sala is None else sala.name,
        vida=jugador.health,
        vida_maxima=jugador.max_health,
        ataque=jugador.effective_attack,
        defensa=jugador.effective_defense,
        velocidad=jugador.speed,
        inventario=_inventario_de(jugador),
        efectos=_efectos_de(reconstruido),
        enemigos=_enemigos_en_la_sala_de(reconstruido, jugador.room_id),
        mapa_conocido=_mapa_conocido_de(reconstruido),
        resultado=reconstruido.result,
        acciones_repetidas=repetidas,
    )


def _inventario_de(jugador):
    if jugador.inventory is None:
        return []

    return [(item.name, item.item_class) for item in jugador.inventory]


def _efectos_de(reconstruido):
    activos = []

    for efecto in reconstruido.effects:
        if not efecto.cancelled:
            activos.append((efecto.name, efecto.ends_at))

    return activos


def _enemigos_en_la_sala_de(reconstruido, room_id):
    encontrados = []

    for enemigo in reconstruido.enemies:
        if enemigo.room_id == room_id and enemigo.is_alive:
            encontrados.append((enemigo.actor_id, enemigo.name, enemigo.health))

    return encontrados


def _mapa_conocido_de(reconstruido):
    """Las salas que el jugador tenia exploradas en ese instante.

    Se lee por duck typing del colaborador de niebla de guerra. Una partida
    sin niebla lleva el objeto nulo del motor, que se declara no disponible, y
    el resumen lo informa asi en vez de fallar.
    """
    conocido = getattr(reconstruido, "known_map", None)

    if conocido is None or not getattr(conocido, "disponible", True):
        return MAPA_CONOCIDO_NO_DISPONIBLE

    exploradas = getattr(conocido, "salas_exploradas", None)

    if exploradas is None:
        return MAPA_CONOCIDO_NO_DISPONIBLE

    return tuple(exploradas())


def _exigir_linea(juego):
    if juego.timeline is None:
        raise ConsultaRechazada(
            "Esta partida no lleva linea de tiempo, asi que no hay historia "
            "que consultar."
        )

    return juego.timeline


def _exigir_entero(valor, que_es):
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ConsultaRechazada(f"{que_es} debe ser un numero entero: {valor!r}.")
