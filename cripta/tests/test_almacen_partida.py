"""
Pruebas del guardado binario de la partida (§4.10).

Cada prueba trabaja en una carpeta temporal que se borra al terminar.

La prueba de fondo es test_la_partida_cargada_sigue_igual: la partida se
reconstruye con objetos nuevos, salidos del archivo, y despues se juegan las
mismas acciones en la original y en la cargada. Si algo no se guardo, las dos
dejan de coincidir.

Para comprobar que leer una sala no lee el archivo completo, en vez de medir
bytes se dana a proposito el bloque global o el bloque de otra sala: si leer la
sala pedida sigue funcionando, es porque esos bytes no se tocaron.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import struct
import tempfile
import unittest
from pathlib import Path

from adapters.almacen_partida import (
    FIRMA_DEL_ARCHIVO,
    VERSION_DEL_FORMATO,
    AlmacenPartida,
    ArchivoDePartidaDanado,
    PartidaIncompatible,
    construir_juego,
    construir_juego_reversible,
)
from model.enemy import Enemy
from model.game import ACTOR_ACTION, DEFEAT, Game
from model.game_state import GameState
from model.item import Item
from model.player import Player
from model.room import Door, Exit, Room, RoomMap
from model.trap import Trap
from structures.inventory import Inventory
from structures.trail import PlayerTrail


def objeto(instance_id, nombre, clase, **extra):
    return Item(
        instance_id=instance_id,
        type_id=f"itm_{nombre.lower()}",
        name=nombre,
        item_class=clase,
        weight=1,
        value=2,
        **extra,
    )


def construir_cripta(cuantas_salas=3):
    salas = [Room(numero, f"Sala {numero}") for numero in range(1, cuantas_salas + 1)]

    for sala in salas:
        sala.content_loaded = True

    for indice in range(cuantas_salas - 1):
        cerrada = indice == 1
        puerta = Door(
            indice + 1,
            indice + 2,
            closed=cerrada,
            key_id="puerta_salida" if cerrada else None,
            auto_close=400 if indice == 0 else None,
        )
        salas[indice].add_exit(Exit("N", indice + 2, puerta))
        salas[indice + 1].add_exit(Exit("S", indice + 1, puerta))

    salas[1].traps.append(Trap("t-1", "trp_dardos", "Dardos", 3, 200, 2))
    salas[0].floor_items.append(objeto("i-daga", "Daga", Item.WEAPON, attack_bonus=3))

    mapa = RoomMap()

    for sala in salas:
        mapa.add(sala)

    return mapa


def construir_partida(cuantas_salas=3, acciones=2, veneno=True):
    mapa = construir_cripta(cuantas_salas)
    jugador = Player("p-1", "Heroe", 200, 6, 2, 100, 1)
    jugador.inventory = Inventory(10)
    jugador.inventory.pick_up(
        Item(
            instance_id="i-llave",
            type_id="puerta_salida",
            name="Llave negra",
            item_class=Item.KEY,
            weight=1,
            value=2,
        )
    )
    jugador.inventory.pick_up(objeto("i-pergamino", "Pergamino", Item.REWIND_SCROLL))

    enemigos = [
        Enemy("e-1", "Rata gigante", 20, 4, 1, 150, 1, Enemy.GUARDIAN,
              drops=[objeto("i-oro", "Oro", Item.POTION, heal=5)]),
        Enemy("e-2", "Errante", 30, 5, 2, 80, 2, Enemy.WANDERER, regeneration=2),
    ]

    juego = Game(
        GameState(seed=2026),
        jugador,
        enemigos,
        room_map=mapa,
        exit_room_id=cuantas_salas,
        trail=PlayerTrail(),
    )

    if veneno:
        juego.apply_poison(juego.player, 2)

    for _ in range(acciones):
        juego.wait()

    return juego


class PruebasAlmacenPartida(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.ruta = Path(self._carpeta_temporal.name) / "guardados" / "partida.cripta"
        self.almacen = AlmacenPartida(self.ruta)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def guardar(self, juego, versiones=("cripta-01", "3", "7")):
        self.almacen.guardar(juego, versiones=versiones)

    # ------------------------------------------------------------------
    # El archivo
    # ------------------------------------------------------------------

    def test_el_archivo_empieza_con_la_firma_y_la_version(self):
        self.guardar(construir_partida())

        with open(self.ruta, "rb") as archivo:
            crudo = archivo.read(10)

        firma, version = struct.unpack("<8sH", crudo)
        self.assertEqual(firma, FIRMA_DEL_ARCHIVO)
        self.assertEqual(version, VERSION_DEL_FORMATO)

    def test_no_queda_archivo_temporal(self):
        self.guardar(construir_partida())

        sobrantes = list(self.ruta.parent.glob("*.tmp"))
        self.assertEqual(sobrantes, [])

    def test_guardar_dos_veces_deja_el_ultimo_estado(self):
        juego = construir_partida()
        self.guardar(juego)
        juego.wait()
        self.guardar(juego)

        self.assertEqual(self.almacen.cargar().clock, juego.state.clock)

    def test_existe_avisa_si_hay_algo_guardado(self):
        self.assertFalse(self.almacen.existe())

        self.guardar(construir_partida())

        self.assertTrue(self.almacen.existe())

    # ------------------------------------------------------------------
    # Estado general
    # ------------------------------------------------------------------

    def test_el_reloj_y_el_contador_de_secuencia_vuelven(self):
        juego = construir_partida()
        self.guardar(juego)

        partida = self.almacen.cargar()

        self.assertEqual(partida.clock, juego.state.clock)
        self.assertEqual(partida.sequence_counter, juego.state.sequence_counter)

    def test_los_contadores_y_el_resultado_vuelven(self):
        juego = construir_partida()
        juego.result = DEFEAT
        self.guardar(juego)

        partida = self.almacen.cargar()

        self.assertEqual(partida.player_actions, juego.player_actions)
        self.assertEqual(partida.enemies_defeated, juego.enemies_defeated)
        self.assertEqual(partida.result, DEFEAT)

    def test_las_versiones_quedan_guardadas(self):
        self.guardar(construir_partida())

        partida = self.almacen.cargar()

        self.assertEqual(partida.id_cripta, "cripta-01")
        self.assertEqual(partida.version_cripta, "3")
        self.assertEqual(partida.version_catalogo, "7")

    def test_la_sala_de_salida_vuelve(self):
        self.guardar(construir_partida(cuantas_salas=4))

        self.assertEqual(self.almacen.cargar().exit_room_id, 4)

    def test_la_antorcha_encendida_vuelve(self):
        juego = construir_partida()
        juego.torch_lit = True
        self.guardar(juego)

        self.assertTrue(self.almacen.cargar().torch_lit)

    # ------------------------------------------------------------------
    # Jugador e inventario
    # ------------------------------------------------------------------

    def test_el_jugador_vuelve_con_su_vida_y_su_sala(self):
        juego = construir_partida()
        self.guardar(juego)

        jugador = self.almacen.cargar().player

        self.assertEqual(jugador.health, juego.player.health)
        self.assertEqual(jugador.max_health, juego.player.max_health)
        self.assertEqual(jugador.room_id, juego.player.room_id)
        self.assertEqual(jugador.speed, juego.player.speed)

    def test_el_inventario_vuelve_en_el_mismo_orden(self):
        juego = construir_partida()
        self.guardar(juego)

        jugador = self.almacen.cargar().player

        self.assertEqual(
            [item.instance_id for item in jugador.inventory],
            [item.instance_id for item in juego.player.inventory],
        )
        self.assertEqual(jugador.inventory.capacity, 10)

    def test_el_cursor_del_inventario_vuelve_donde_estaba(self):
        juego = construir_partida()
        juego.player.inventory.go_to_start()
        self.guardar(juego)

        jugador = self.almacen.cargar().player

        self.assertEqual(
            jugador.inventory.current().instance_id,
            juego.player.inventory.current().instance_id,
        )

    def test_los_pergaminos_se_cuentan_igual(self):
        juego = construir_partida()
        self.guardar(juego)

        jugador = self.almacen.cargar().player

        self.assertEqual(
            jugador.inventory.scroll_count(),
            juego.player.inventory.scroll_count(),
        )

    def test_el_equipo_apunta_al_objeto_del_inventario(self):
        """No basta que vuelva el bono: tiene que ser el mismo objeto."""
        juego = construir_partida()
        juego.player.inventory.go_to_start()
        juego.pick_up(0)
        juego.equip_item()
        self.guardar(juego)

        jugador = self.almacen.cargar().player

        self.assertIsNotNone(jugador.equipped_weapon)
        self.assertEqual(jugador.equipped_weapon.instance_id, "i-daga")
        self.assertIn(jugador.equipped_weapon, list(jugador.inventory))
        self.assertEqual(jugador.effective_attack, juego.player.effective_attack)

    def test_un_jugador_sin_inventario_tambien_se_guarda(self):
        juego = construir_partida()
        juego.player.inventory = None
        self.guardar(juego)

        self.assertIsNone(self.almacen.cargar().player.inventory)

    # ------------------------------------------------------------------
    # Enemigos
    # ------------------------------------------------------------------

    def test_los_enemigos_vuelven_con_su_estado(self):
        juego = construir_partida()
        self.guardar(juego)

        enemigos = self.almacen.cargar().enemies
        por_id = sorted(enemigos, key=lambda enemigo: enemigo.actor_id)
        originales = sorted(juego.enemies, key=lambda enemigo: enemigo.actor_id)

        for cargado, original in zip(por_id, originales):
            self.assertEqual(cargado.health, original.health)
            self.assertEqual(cargado.room_id, original.room_id)
            self.assertEqual(cargado.is_active, original.is_active)
            self.assertEqual(cargado.behavior, original.behavior)
            self.assertEqual(cargado.regeneration, original.regeneration)
            self.assertEqual(
                [item.instance_id for item in cargado.drops],
                [item.instance_id for item in original.drops],
            )

    def test_un_enemigo_muerto_vuelve_muerto(self):
        juego = construir_partida()
        juego.enemies[0].health = 0
        self.guardar(juego)

        cargados = [
            enemigo for enemigo in self.almacen.cargar().enemies
            if enemigo.actor_id == "e-1"
        ]

        self.assertFalse(cargados[0].is_alive)

    def test_una_partida_sin_enemigos_se_guarda(self):
        mapa = construir_cripta()
        juego = Game(
            GameState(seed=1),
            Player("p-1", "Heroe", 50, 3, 1, 100, 1),
            None,
            room_map=mapa,
            trail=PlayerTrail(),
        )
        self.guardar(juego)

        self.assertEqual(self.almacen.cargar().enemies, [])

    # ------------------------------------------------------------------
    # Salas, puertas y trampas
    # ------------------------------------------------------------------

    def test_las_salas_vuelven_con_su_contenido(self):
        self.guardar(construir_partida())

        mapa = self.almacen.cargar().room_map

        self.assertEqual(mapa.room(1).name, "Sala 1")
        self.assertTrue(mapa.room(1).content_loaded)
        self.assertEqual(
            [item.instance_id for item in mapa.room(1).floor_items], ["i-daga"]
        )

    def test_las_puertas_vuelven_con_su_estado(self):
        self.guardar(construir_partida())

        mapa = self.almacen.cargar().room_map
        cerrada = mapa.room(2).exit_towards("N").door
        abierta = mapa.room(1).exit_towards("N").door

        self.assertTrue(cerrada.closed)
        self.assertEqual(cerrada.key_id, "puerta_salida")
        self.assertFalse(abierta.closed)
        self.assertEqual(abierta.auto_close, 400)

    def test_una_puerta_es_el_mismo_objeto_desde_sus_dos_salas(self):
        """Cada bloque guarda su copia para poder leer una sala sola; al
        cargar todo, las dos salas tienen que compartir el objeto."""
        self.guardar(construir_partida())

        mapa = self.almacen.cargar().room_map

        self.assertIs(
            mapa.room(1).exit_towards("N").door,
            mapa.room(2).exit_towards("S").door,
        )

    def test_abrir_una_puerta_cargada_la_abre_de_los_dos_lados(self):
        self.guardar(construir_partida())

        mapa = self.almacen.cargar().room_map
        mapa.room(2).exit_towards("N").door.closed = False

        self.assertTrue(mapa.room(3).exit_towards("S").door.is_open)

    def test_las_trampas_vuelven_con_su_estado(self):
        juego = construir_partida()
        juego.room_map.room(2).traps[0].armed = False
        self.guardar(juego)

        trampa = self.almacen.cargar().room_map.room(2).traps[0]

        self.assertEqual(trampa.instance_id, "t-1")
        self.assertEqual(trampa.damage, 3)
        self.assertEqual(trampa.rearm_interval, 200)
        self.assertFalse(trampa.armed)

    def test_el_rastro_vuelve(self):
        juego = construir_partida()
        self.guardar(juego)

        marcas = self.almacen.cargar().trail_marks

        self.assertEqual(
            marcas, [(1, juego.trail.time_at(1))]
        )

    # ------------------------------------------------------------------
    # La agenda
    # ------------------------------------------------------------------

    def test_la_agenda_vuelve_completa_y_en_orden(self):
        juego = construir_partida()
        self.guardar(juego)

        partida = self.almacen.cargar()
        guardados = [
            (evento.time, evento.sequence, evento.event_type)
            for evento in juego.events.active_events()
        ]
        cargados = [
            (evento.time, evento.sequence, evento.event_type)
            for evento in partida.events
        ]

        self.assertEqual(sorted(cargados), sorted(guardados))

    def test_los_eventos_vuelven_apuntando_a_los_actores_cargados(self):
        """El archivo guarda el identificador; al cargar se reapunta."""
        self.guardar(construir_partida())

        partida = self.almacen.cargar()
        conocidos = [partida.player] + list(partida.enemies)

        for evento in partida.events:
            if evento.actor is not None:
                self.assertIn(evento.actor, conocidos)

    def test_cada_actor_apunta_a_su_accion_pendiente(self):
        self.guardar(construir_partida())

        juego = construir_juego(self.almacen.cargar())

        for evento in juego.events.active_events():
            if evento.event_type == ACTOR_ACTION:
                self.assertIs(evento.actor.scheduled_event, evento)

    def test_los_efectos_se_deducen_de_la_agenda(self):
        self.guardar(construir_partida())

        juego = construir_juego(self.almacen.cargar())

        self.assertIn("veneno", [efecto.name for efecto in juego.effects])

    # ------------------------------------------------------------------
    # Leer una sala sin leer el archivo completo (§4.10)
    # ------------------------------------------------------------------

    def test_leer_una_sala_devuelve_lo_que_hay_en_ella(self):
        self.guardar(construir_partida())

        guardada = self.almacen.leer_sala(2)

        self.assertEqual(guardada.room.room_id, 2)
        self.assertEqual(len(guardada.room.traps), 1)
        self.assertEqual([e.actor_id for e in guardada.enemies], ["e-2"])

    def test_leer_una_sala_que_no_esta_devuelve_none(self):
        self.guardar(construir_partida())

        self.assertIsNone(self.almacen.leer_sala(99))

    def test_leer_una_sala_no_lee_el_bloque_global(self):
        """Se dana el bloque global a proposito: leer la sala tiene que seguir
        funcionando, y cargar todo tiene que fallar."""
        self.guardar(construir_partida())
        self._danar_el_bloque_global()

        self.assertEqual(self.almacen.leer_sala(3).room.room_id, 3)

        with self.assertRaises(Exception):
            self.almacen.cargar()

    def test_leer_una_sala_no_lee_el_bloque_de_las_otras(self):
        self.guardar(construir_partida(cuantas_salas=5))
        _, posicion_del_indice, cuantas = self.almacen.leer_encabezado()
        entradas = self.almacen._leer_indice(posicion_del_indice, cuantas)
        otra = [entrada for entrada in entradas if entrada[0] == 4][0]

        self._sobrescribir(otra[1], b"\xff" * otra[2])

        self.assertEqual(self.almacen.leer_sala(2).room.room_id, 2)

    def test_los_ids_de_sala_se_leen_solo_del_indice(self):
        self.guardar(construir_partida(cuantas_salas=5))
        self._danar_el_bloque_global()

        self.assertEqual(self.almacen.ids_de_salas(), [1, 2, 3, 4, 5])

    def test_el_indice_queda_ordenado_aunque_las_salas_no_lo_esten(self):
        mapa = RoomMap()

        for numero in (7, 2, 5, 1):
            sala = Room(numero, f"Sala {numero}")
            sala.content_loaded = True
            mapa.add(sala)

        juego = Game(
            GameState(seed=1),
            Player("p-1", "Heroe", 50, 3, 1, 100, 1),
            None,
            room_map=mapa,
            trail=PlayerTrail(),
        )
        self.guardar(juego)

        self.assertEqual(self.almacen.ids_de_salas(), [1, 2, 5, 7])

    # ------------------------------------------------------------------
    # Versiones y archivos danados
    # ------------------------------------------------------------------

    def test_otra_firma_no_se_interpreta(self):
        self.guardar(construir_partida())
        self._sobrescribir(0, b"OTROJUEG")

        with self.assertRaises(PartidaIncompatible):
            self.almacen.cargar()

    def test_otra_version_del_formato_no_se_interpreta(self):
        self.guardar(construir_partida())
        self._sobrescribir(8, struct.pack("<H", VERSION_DEL_FORMATO + 1))

        with self.assertRaises(PartidaIncompatible) as reportado:
            self.almacen.cargar()

        self.assertIn("formato", str(reportado.exception))

    def test_otra_version_de_la_cripta_se_reporta(self):
        self.guardar(construir_partida())

        with self.assertRaises(PartidaIncompatible) as reportado:
            self.almacen.cargar(versiones_vigentes=("4", "7"))

        self.assertIn("cripta", str(reportado.exception))

    def test_otra_version_del_catalogo_se_reporta(self):
        self.guardar(construir_partida())

        with self.assertRaises(PartidaIncompatible):
            self.almacen.cargar(versiones_vigentes=("3", "8"))

    def test_las_mismas_versiones_cargan_sin_problema(self):
        self.guardar(construir_partida())

        partida = self.almacen.cargar(versiones_vigentes=("3", "7"))

        self.assertEqual(partida.version_cripta, "3")

    def test_un_archivo_recortado_se_reporta(self):
        self.guardar(construir_partida())
        contenido = self.ruta.read_bytes()
        self.ruta.write_bytes(contenido[: len(contenido) // 2])

        with self.assertRaises(ArchivoDePartidaDanado):
            self.almacen.cargar()

    def test_un_encabezado_incompleto_se_reporta(self):
        self.guardar(construir_partida())
        self.ruta.write_bytes(b"CRIP")

        with self.assertRaises(ArchivoDePartidaDanado):
            self.almacen.leer_encabezado()

    # ------------------------------------------------------------------
    # La prueba de fondo
    # ------------------------------------------------------------------

    def test_la_partida_cargada_sigue_igual(self):
        """Se juegan las mismas acciones en la original y en la cargada.

        La cargada se arma con objetos nuevos, salidos del archivo. Si algo no
        se guardo, las dos dejan de coincidir.
        """
        original = construir_partida(acciones=2)
        self.guardar(original)
        cargada = construir_juego(self.almacen.cargar())

        for _ in range(6):
            cargada.wait()
            original.wait()

        self.assertEqual(cargada.state.clock, original.state.clock)
        self.assertEqual(cargada.player.health, original.player.health)
        self.assertEqual(cargada.player_actions, original.player_actions)
        self.assertEqual(cargada.result, original.result)
        self.assertEqual(
            [enemigo.health for enemigo in cargada.enemies],
            [enemigo.health for enemigo in original.enemies],
        )
        self.assertEqual(
            [enemigo.room_id for enemigo in cargada.enemies],
            [enemigo.room_id for enemigo in original.enemies],
        )
        self.assertEqual(
            list(cargada.messages)[-4:], list(original.messages)[-4:]
        )

    def test_la_partida_cargada_se_puede_ganar(self):
        original = construir_partida(acciones=1, veneno=False)
        original.player.inventory.go_to_start()
        self.guardar(original)

        cargada = construir_juego(self.almacen.cargar())
        cargada.move("N")
        cargada.open_door("N")
        cargada.move("N")

        self.assertTrue(cargada.is_over)

    def test_cargar_no_arranca_una_partida_nueva(self):
        original = construir_partida(acciones=2)
        self.guardar(original)
        cuantos = len(original.events.active_events())

        cargada = construir_juego(self.almacen.cargar())

        self.assertEqual(len(cargada.events.active_events()), cuantos)
        self.assertGreater(cargada.state.clock, 0)

    def test_una_partida_terminada_vuelve_terminada(self):
        original = construir_partida(acciones=1)
        original.result = DEFEAT
        self.guardar(original)

        cargada = construir_juego(self.almacen.cargar())

        self.assertTrue(cargada.is_over)
        self.assertFalse(cargada.wait().accepted)

    # ------------------------------------------------------------------
    # Ayudas
    # ------------------------------------------------------------------

    def _sobrescribir(self, posicion, crudo):
        contenido = bytearray(self.ruta.read_bytes())
        contenido[posicion:posicion + len(crudo)] = crudo
        self.ruta.write_bytes(bytes(contenido))

    def _danar_el_bloque_global(self):
        tamano_del_encabezado = struct.calcsize("<8sHQI")
        contenido = self.ruta.read_bytes()
        largo = struct.unpack_from("<I", contenido, tamano_del_encabezado)[0]
        empieza = tamano_del_encabezado + struct.calcsize("<I")
        self._sobrescribir(empieza, b"\xff" * largo)


class PruebasPartidaCargadaConHistorial(unittest.TestCase):
    """construir_juego_reversible: la version que usa el programa.

    El historial necesita el GameState, que se arma despues de leer el
    archivo, asi que el inventario sale de la lectura sin historial. Si se
    quedara asi, las acciones posteriores a cargar no se anotarian y un
    pergamino no las desharia, sin dar ningun error. Estas pruebas fijan que
    el retroceso funcione despues de cargar.
    """

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.ruta = Path(self._carpeta_temporal.name) / "partida.cripta"

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def cargada(self, juego):
        AlmacenPartida(self.ruta).guardar(juego, versiones=("cripta-01", "3", "7"))
        return construir_juego_reversible(AlmacenPartida(self.ruta).cargar())

    def test_recien_cargada_no_hay_nada_que_deshacer(self):
        juego = self.cargada(construir_partida())

        self.assertFalse(juego.rewind().accepted)

    def test_una_espera_posterior_se_puede_deshacer(self):
        juego = self.cargada(construir_partida())
        reloj = juego.state.clock

        juego.wait()

        self.assertGreater(juego.state.clock, reloj)
        self.assertTrue(juego.rewind().accepted)
        self.assertEqual(juego.state.clock, reloj)

    def test_recoger_despues_de_cargar_se_deshace(self):
        """La prueba del arreglo: si el inventario perdiera el historial, el
        objeto se quedaria adentro al retroceder."""
        juego = self.cargada(construir_partida())
        suelo = juego.room_map.room(1).floor_items
        cuantos = len(suelo)
        recogido = suelo[0].instance_id
        pergaminos = juego.player.inventory.scroll_count()

        self.assertTrue(juego.pick_up(0).accepted)
        self.assertIn(
            recogido, [item.instance_id for item in juego.player.inventory]
        )
        self.assertEqual(len(suelo), cuantos - 1)

        juego.rewind()

        # El objeto vuelve al suelo y sale del inventario. El pergamino usado
        # no vuelve: §2.11 lo excluye del historial reversible.
        self.assertNotIn(
            recogido, [item.instance_id for item in juego.player.inventory]
        )
        self.assertEqual(len(suelo), cuantos)
        self.assertEqual(
            juego.player.inventory.scroll_count(), pergaminos - 1
        )

    def test_el_inventario_cargado_conserva_su_orden_y_su_cursor(self):
        original = construir_partida()
        original.player.inventory.go_to_start()
        juego = self.cargada(original)

        self.assertEqual(
            [item.instance_id for item in juego.player.inventory],
            [item.instance_id for item in original.player.inventory],
        )
        self.assertEqual(
            juego.player.inventory.current().instance_id,
            original.player.inventory.current().instance_id,
        )

    def test_los_pergaminos_cargados_se_cuentan(self):
        original = construir_partida()
        juego = self.cargada(original)

        self.assertEqual(
            juego.player.inventory.scroll_count(),
            original.player.inventory.scroll_count(),
        )

    def test_la_agenda_cargada_es_reversible(self):
        juego = self.cargada(construir_partida())
        pendientes = len(juego.events.active_events())

        juego.wait()
        juego.rewind()

        self.assertEqual(len(juego.events.active_events()), pendientes)


if __name__ == "__main__":
    unittest.main()
