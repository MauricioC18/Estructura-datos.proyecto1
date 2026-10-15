"""
Traductor: convierte los datos del API en objetos del modelo (bloque 2).

Problema que resuelve
    El API entrega JSON con nombres en español, campos que pueden faltar y
    referencias por id (§3.2, Apéndice A). El modelo trabaja con objetos:
    Player, Enemy, Room, Door, Item y Trap. Este módulo es el único lugar donde
    se conocen los nombres de los campos del API, así que si el API cambia,
    solo cambia este archivo.

Qué hace con los datos (supuestos de docs/BLOQUE_2_PARA_EL_GRUPO.md)
    - Jugador: estadísticas de los datos generales; empieza en la sala inicial.
    - Salas y puertas (S9): una sola puerta compartida por cada paso entre dos
      salas. Está cerrada si cualquiera de los dos lados la declara cerrada.
      La llave y el cierre automático se toman del lado que los declara; si
      los dos lados declaran valores distintos, gana el de la sala con menor
      id y se registra un aviso. Sin salida de vuelta, el paso es de un solo
      sentido. Una salida hacia una sala que no existe se ignora con un aviso.
    - Enemigos (S11): si la instancia no trae vida, empieza con vida_max. El
      comportamiento del API ("guardián", "errante", "rastreador") se traduce a
      las constantes de Enemy, así el modelo nunca compara contra textos del
      API. Los objetos de "suelta" se crean ya como Item, para que el motor
      solo tenga que pasarlos al suelo cuando el enemigo muere (§2.6).
      La regeneración queda en 0 (S13): el contrato del API no tiene ningún
      campo para declararla.
    - Objetos (S12): ids deterministas. En el suelo, "o-<sala>-<posición>";
      los que suelta un enemigo, "<instancia>-s<posición>".
    - Trampas: si la ficha no trae rearme, se usa el intervalo por defecto
      de §2.10 (300).

Campos que el programa no conoce
    Los esquemas del API (Swagger, /openapi.json) son cerrados: cada ficha,
    colocación y salida solo puede traer los campos que declara su esquema
    ("additionalProperties": false). Las tablas CAMPOS_* copian esos campos.
    Si algún dato trae un campo que no está en ellas, el contrato cambió: el
    campo se ignora y queda un aviso en el reporte final, una sola vez por
    campo. Así un campo nuevo (por ejemplo, uno de regeneración) nunca se
    pierde en silencio, y no hace falta adivinar su nombre.

Qué no hace
    No pide nada a la red ni al disco: recibe la función obtener_ficha del
    RepositorioCripta, que nunca usa la red. Antes de traducir el contenido de
    una sala hay que asegurar sus fichas (RepositorioCripta lo hace en
    preparar_entrada_a_sala). Tampoco activa enemigos ni aplica reglas: eso es
    del motor.

Complejidad
    crear_mapa: O(S + E) para S salas y E salidas, gracias a una TablaHash de
        salidas pendientes de emparejar.
    llenar_sala: O(enemigos + objetos + trampas + objetos soltados).
"""
from model.enemy import Enemy
from model.item import Item
from model.player import Player
from model.room import DIRECTIONS, Door, Exit, Room, RoomMap
from model.trap import DEFAULT_REARM_INTERVAL, Trap
from structures.lista_sin_repetidos import ListaSinRepetidos
from structures.tabla_hash import TablaHash

ID_DEL_JUGADOR = "jugador"
NOMBRE_DEL_JUGADOR = "Jugador"

CLASE_ENEMIGO = "enemigo"
CLASE_TRAMPA = "trampa"
CLASES_DE_OBJETO = (
    Item.WEAPON, Item.ARMOR, Item.POTION, Item.ANTIDOTE,
    Item.KEY, Item.TORCH, Item.REWIND_SCROLL,
)

# Comportamiento según el API (con tilde, como en su esquema) → constante del modelo.
COMPORTAMIENTOS = (
    ("guardián", Enemy.GUARDIAN),
    ("errante", Enemy.WANDERER),
    ("rastreador", Enemy.TRACKER),
)

# Campos que permite el contrato del API (esquemas del Swagger, versión 1.0.0).
# Solo sirven para avisar si llega uno nuevo; nunca deciden cómo se traduce.
CAMPOS_COMUNES_DE_OBJETO = ("id", "nombre", "clase", "peso", "valor")
CAMPOS_POR_CLASE = (
    (CLASE_ENEMIGO, ("id", "nombre", "clase", "vida_max", "ataque", "defensa",
                     "velocidad", "comportamiento", "suelta")),
    (Item.WEAPON, CAMPOS_COMUNES_DE_OBJETO + ("ataque_bonus",)),
    (Item.ARMOR, CAMPOS_COMUNES_DE_OBJETO + ("defensa_bonus",)),
    (Item.POTION, CAMPOS_COMUNES_DE_OBJETO + ("cura", "modificador_velocidad", "duracion")),
    (Item.ANTIDOTE, CAMPOS_COMUNES_DE_OBJETO),
    (Item.KEY, CAMPOS_COMUNES_DE_OBJETO + ("abre",)),
    (Item.TORCH, CAMPOS_COMUNES_DE_OBJETO + ("duracion",)),
    (Item.REWIND_SCROLL, CAMPOS_COMUNES_DE_OBJETO),
    (CLASE_TRAMPA, ("id", "nombre", "clase", "daño", "rearme")),
)
CAMPOS_DE_COLOCACION_DE_ENEMIGO = ("instancia", "tipo", "vida")
CAMPOS_DE_COLOCACION_DE_TRAMPA = ("instancia", "tipo")
CAMPOS_DE_SALIDA = ("sala", "cerrada", "llave", "cierre_automatico")


class ErrorDatosCripta(Exception):
    """Los datos del API no se pueden convertir en objetos del modelo."""


def id_de_objeto_en_el_suelo(id_sala, posicion):
    return f"o-{id_sala}-{posicion}"


def id_de_objeto_soltado(id_instancia_enemigo, posicion):
    return f"{id_instancia_enemigo}-s{posicion}"


class Traductor:
    """Convierte datos del API en objetos del modelo."""

    def __init__(self, obtener_ficha):
        """obtener_ficha: función id de tipo → ficha (el JSON del catálogo)."""
        self._obtener_ficha = obtener_ficha
        self._tipo_por_instancia_de_enemigo = TablaHash()
        self._fichas_revisadas = ListaSinRepetidos()
        self._campos_desconocidos_avisados = ListaSinRepetidos()
        self.avisos = []

    # ------------------------------------------------------------------
    # Jugador
    # ------------------------------------------------------------------

    def crear_jugador(self, datos_de_partida, nombre=NOMBRE_DEL_JUGADOR, id_jugador=ID_DEL_JUGADOR):
        """El jugador con las estadísticas de la cripta, en la sala inicial (§2.2, §2.4)."""
        estadisticas = datos_de_partida.jugador
        try:
            return Player(
                actor_id=id_jugador,
                name=nombre,
                max_health=estadisticas["vida_max"],
                attack=estadisticas["ataque"],
                defense=estadisticas["defensa"],
                speed=estadisticas["velocidad"],
                room_id=datos_de_partida.sala_inicial,
            )
        except (KeyError, ValueError, TypeError) as error:
            raise ErrorDatosCripta(f"Estadísticas del jugador inválidas: {error}") from error

    # ------------------------------------------------------------------
    # Salas y puertas
    # ------------------------------------------------------------------

    def crear_mapa(self, salas_del_esqueleto):
        """Todas las salas con sus salidas y puertas, sin contenido todavía."""
        mapa = RoomMap()
        for sala in salas_del_esqueleto:
            id_sala = _campo_obligatorio(sala, "id", "una sala del esqueleto")
            try:
                mapa.add(Room(id_sala, _campo_obligatorio(sala, "nombre", f"la sala {id_sala}")))
            except ValueError as error:
                raise ErrorDatosCripta(str(error)) from error

        # Salidas declaradas de una sala hacia otra que todavía esperan a su
        # salida de vuelta. Clave: "origen->destino". Valor: lista de puertas.
        pendientes = TablaHash()
        for sala in salas_del_esqueleto:
            salidas = sala.get("salidas")
            if not salidas:
                continue  # sin salidas (el campo puede faltar)
            for direccion in DIRECTIONS:
                salida = salidas.get(direccion)
                if salida is not None:
                    self._agregar_salida(mapa, pendientes, sala["id"], direccion, salida)
        return mapa

    def _agregar_salida(self, mapa, pendientes, origen, direccion, salida):
        destino = _campo_obligatorio(salida, "sala", f"la salida {direccion} de la sala {origen}")
        self._avisar_campos_desconocidos(salida, CAMPOS_DE_SALIDA, "Una salida del esqueleto")
        if not mapa.contains(destino):
            self.avisos.append(
                f"La salida {direccion} de la sala {origen} lleva a la sala {destino}, "
                f"que no existe en el esqueleto; se ignoró."
            )
            return

        cerrada = bool(salida.get("cerrada"))
        llave = salida.get("llave")
        cierre = salida.get("cierre_automatico")

        de_vuelta = pendientes.obtener(f"{destino}->{origen}")
        if de_vuelta:
            puerta = de_vuelta.pop(0)
            puerta.closed = puerta.closed or cerrada
            puerta.key_id = self._combinar(puerta.key_id, llave, origen, destino, "llave")
            puerta.auto_close = self._combinar(puerta.auto_close, cierre, origen, destino,
                                               "cierre automático")
        else:
            puerta = Door(origen, destino, closed=cerrada, key_id=llave, auto_close=cierre)
            clave = f"{origen}->{destino}"
            if not pendientes.contiene(clave):
                pendientes.insertar(clave, [])
            pendientes.obtener(clave).append(puerta)

        mapa.room(origen).add_exit(Exit(direccion, destino, puerta))

    def _combinar(self, valor_del_otro_lado, valor_de_este_lado, este_lado, otro_lado, campo):
        """Un valor declarado por un solo lado se usa tal cual. Si los dos lados
        declaran valores distintos, gana el de la sala con menor id (S9)."""
        if valor_de_este_lado is None:
            return valor_del_otro_lado
        if valor_del_otro_lado is None or valor_del_otro_lado == valor_de_este_lado:
            return valor_de_este_lado
        ganador = valor_de_este_lado if este_lado < otro_lado else valor_del_otro_lado
        self.avisos.append(
            f"La puerta entre las salas {min(este_lado, otro_lado)} y {max(este_lado, otro_lado)} "
            f"declara {campo} distinto en cada lado; se usó {ganador!r}, el de la sala de menor id."
        )
        return ganador

    # ------------------------------------------------------------------
    # Contenido de una sala
    # ------------------------------------------------------------------

    def llenar_sala(self, sala, entrada_de_contenido):
        """Pone en la sala sus objetos y trampas y devuelve sus enemigos.

        Los enemigos se devuelven dormidos (§2.4) para que el motor los agregue
        a su lista. Si el contenido de la sala ya se había cargado, no hace nada
        y devuelve una lista vacía.
        """
        if sala.content_loaded:
            return []
        if entrada_de_contenido.get("sala") != sala.room_id:
            raise ErrorDatosCripta(
                f"Se intentó llenar la sala {sala.room_id} con el contenido de la sala "
                f"{entrada_de_contenido.get('sala')}."
            )

        enemigos = []
        for colocacion in entrada_de_contenido.get("enemigos") or []:
            enemigos.append(self.crear_enemigo(colocacion, sala.room_id))

        objetos = []
        for posicion, id_tipo in enumerate(entrada_de_contenido.get("objetos") or []):
            objetos.append(self.crear_objeto(id_tipo, id_de_objeto_en_el_suelo(sala.room_id, posicion)))

        trampas = []
        for colocacion in entrada_de_contenido.get("trampas") or []:
            trampas.append(self.crear_trampa(colocacion, sala.room_id))

        # Se asigna al final: si algo falla a medio camino, la sala queda sin cargar.
        sala.floor_items = objetos
        sala.traps = trampas
        sala.content_loaded = True
        return enemigos

    def crear_enemigo(self, colocacion, id_sala):
        id_tipo = _campo_obligatorio(colocacion, "tipo", f"un enemigo de la sala {id_sala}")
        id_instancia = _campo_obligatorio(colocacion, "instancia", f"un enemigo de la sala {id_sala}")
        self._avisar_campos_desconocidos(colocacion, CAMPOS_DE_COLOCACION_DE_ENEMIGO,
                                         "Una colocación de enemigo")
        ficha = self._ficha_de_clase(id_tipo, (CLASE_ENEMIGO,))
        comportamiento = _comportamiento_del_modelo(ficha.get("comportamiento"), id_tipo)

        soltados = []
        for posicion, id_tipo_soltado in enumerate(ficha.get("suelta") or []):
            soltados.append(self.crear_objeto(id_tipo_soltado, id_de_objeto_soltado(id_instancia, posicion)))

        try:
            enemigo = Enemy(
                actor_id=id_instancia,
                name=ficha["nombre"],
                max_health=ficha["vida_max"],
                attack=ficha["ataque"],
                defense=ficha["defensa"],
                speed=ficha["velocidad"],
                room_id=id_sala,
                behavior=comportamiento,
                health=colocacion.get("vida"),
                drops=soltados,
                regeneration=0,  # el contrato del API no tiene campo de regeneración (S13)
            )
        except (KeyError, ValueError, TypeError) as error:
            raise ErrorDatosCripta(f"Datos inválidos para el enemigo {id_instancia} ({id_tipo}): {error}") from error

        self._tipo_por_instancia_de_enemigo.insertar(id_instancia, id_tipo)
        return enemigo

    def crear_objeto(self, id_tipo, id_instancia):
        ficha = self._ficha_de_clase(id_tipo, CLASES_DE_OBJETO)
        try:
            return Item(
                instance_id=id_instancia,
                type_id=id_tipo,
                name=ficha["nombre"],
                item_class=ficha["clase"],
                weight=ficha["peso"],
                value=ficha["valor"],
                attack_bonus=_entero_o_cero(ficha.get("ataque_bonus")),
                defense_bonus=_entero_o_cero(ficha.get("defensa_bonus")),
                heal=_entero_o_cero(ficha.get("cura")),
                speed_modifier=_entero_o_cero(ficha.get("modificador_velocidad")),
                duration=_entero_o_cero(ficha.get("duracion")),
                opens=ficha.get("abre"),
            )
        except KeyError as error:
            raise ErrorDatosCripta(f"A la ficha {id_tipo} le falta el campo {error}") from error

    def crear_trampa(self, colocacion, id_sala):
        id_tipo = _campo_obligatorio(colocacion, "tipo", f"una trampa de la sala {id_sala}")
        id_instancia = _campo_obligatorio(colocacion, "instancia", f"una trampa de la sala {id_sala}")
        self._avisar_campos_desconocidos(colocacion, CAMPOS_DE_COLOCACION_DE_TRAMPA,
                                         "Una colocación de trampa")
        ficha = self._ficha_de_clase(id_tipo, (CLASE_TRAMPA,))
        rearme = ficha.get("rearme")
        try:
            return Trap(
                instance_id=id_instancia,
                type_id=id_tipo,
                name=ficha["nombre"],
                damage=ficha["daño"],
                rearm_interval=DEFAULT_REARM_INTERVAL if rearme is None else rearme,
                room_id=id_sala,
            )
        except KeyError as error:
            raise ErrorDatosCripta(f"A la ficha {id_tipo} le falta el campo {error}") from error

    # ------------------------------------------------------------------
    # Fichas en uso (§4.4)
    # ------------------------------------------------------------------

    def tipo_de_enemigo(self, id_instancia):
        """El id de tipo de una instancia de enemigo creada por este traductor."""
        return self._tipo_por_instancia_de_enemigo.obtener(id_instancia)

    def ids_en_uso(self, enemigos=(), objetos=(), trampas=()):
        """TablaHash con los ids de tipo en uso, lista para la función
        consultar_ids_en_uso de la caché: enemigos vivos, objetos (del
        inventario, equipados o del suelo) y trampas de la sala actual."""
        en_uso = TablaHash()
        for enemigo in enemigos:
            if enemigo.is_alive:
                id_tipo = self.tipo_de_enemigo(enemigo.actor_id)
                if id_tipo is not None:
                    en_uso.insertar(id_tipo, True)
                for objeto in enemigo.drops:
                    en_uso.insertar(objeto.type_id, True)
        for objeto in objetos:
            en_uso.insertar(objeto.type_id, True)
        for trampa in trampas:
            en_uso.insertar(trampa.type_id, True)
        return en_uso

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _ficha_de_clase(self, id_tipo, clases_aceptadas):
        ficha = self._obtener_ficha(id_tipo)
        clase = ficha.get("clase") if isinstance(ficha, dict) else None
        if clase not in clases_aceptadas:
            raise ErrorDatosCripta(
                f"La ficha {id_tipo} es de clase {clase!r}; aquí se esperaba "
                f"{' o '.join(clases_aceptadas)}."
            )
        if self._fichas_revisadas.agregar(id_tipo):
            self._avisar_campos_desconocidos(ficha, campos_conocidos_de_la_clase(clase),
                                             f"La ficha {id_tipo}")
        return ficha

    def _avisar_campos_desconocidos(self, datos, campos_conocidos, que_dato_es):
        """Anota un aviso por cada campo que no está en campos_conocidos.

        Cada campo se avisa una sola vez por tipo de dato (por ejemplo, una vez
        para "La ficha ent_x" aunque haya cien instancias de ese enemigo). Con
        el contrato actual nunca ocurre; si ocurre, el API cambió."""
        for campo in datos:
            if campo in campos_conocidos:
                continue
            if self._campos_desconocidos_avisados.agregar(f"{que_dato_es}|{campo}"):
                self.avisos.append(
                    f"{que_dato_es} trae el campo {campo!r}, que este programa no conoce, y se "
                    f"ignoró. Puede que el API haya cambiado su contrato."
                )


def campos_conocidos_de_la_clase(clase):
    """Los campos que el contrato del API permite en una ficha de esa clase."""
    for clase_de_la_tabla, campos in CAMPOS_POR_CLASE:
        if clase_de_la_tabla == clase:
            return campos
    raise ValueError(f"Clase de ficha sin campos declarados: {clase!r}")


def _comportamiento_del_modelo(comportamiento_del_api, id_tipo):
    for texto_del_api, constante in COMPORTAMIENTOS:
        if comportamiento_del_api == texto_del_api:
            return constante
    raise ErrorDatosCripta(f"Comportamiento desconocido {comportamiento_del_api!r} en la ficha {id_tipo}.")


def _entero_o_cero(valor):
    return 0 if valor is None else valor


def _campo_obligatorio(datos, campo, descripcion):
    """El valor de un campo que el API siempre debe enviar."""
    valor = datos.get(campo) if isinstance(datos, dict) else None
    if valor is None:
        raise ErrorDatosCripta(f"Falta el campo {campo!r} en {descripcion}.")
    return valor
