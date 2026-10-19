import unittest

from model.enemy import Enemy
from model.item import Item
from repository.repositorio_cripta import DatosDePartida
from repository.traductor import (
    CLASE_ENEMIGO,
    CLASE_TRAMPA,
    CLASES_DE_OBJETO,
    ErrorDatosCripta,
    Traductor,
    campos_conocidos_de_la_clase,
    id_de_objeto_en_el_suelo,
    id_de_objeto_soltado,
)
from structures.tabla_hash import TablaHash
from tests.datos_cripta_01 import (
    CONTENIDO_CRIPTA_01,
    FICHAS_CRIPTA_01,
    GENERALES_CRIPTA_01,
    SALAS_CRIPTA_01,
    VERSION_CATALOGO_REAL,
)


def crear_buscador_de_fichas(fichas):
    """Función id → ficha sobre una TablaHash, como la que da el repositorio."""
    fichas_por_id = TablaHash()
    for ficha in fichas:
        fichas_por_id.insertar(ficha["id"], ficha)

    def obtener_ficha(id_tipo):
        ficha = fichas_por_id.obtener(id_tipo)
        if ficha is None:
            raise KeyError(id_tipo)
        return ficha

    return obtener_ficha


def contenido_de(id_sala):
    for entrada in CONTENIDO_CRIPTA_01:
        if entrada["sala"] == id_sala:
            return entrada
    raise ValueError(id_sala)


def nuevo_traductor(fichas=FICHAS_CRIPTA_01):
    return Traductor(crear_buscador_de_fichas(fichas))


class TestCrearJugador(unittest.TestCase):

    def test_estadisticas_de_la_cripta_y_sala_inicial(self):
        datos = DatosDePartida(GENERALES_CRIPTA_01, VERSION_CATALOGO_REAL)

        jugador = nuevo_traductor().crear_jugador(datos)

        self.assertEqual(jugador.actor_id, "jugador")
        self.assertEqual(jugador.max_health, 30)
        self.assertEqual(jugador.health, 30)
        self.assertEqual(jugador.attack, 6)
        self.assertEqual(jugador.defense, 2)
        self.assertEqual(jugador.speed, 100)
        self.assertEqual(jugador.room_id, 1)

    def test_nombre_e_id_elegidos(self):
        datos = DatosDePartida(GENERALES_CRIPTA_01, VERSION_CATALOGO_REAL)

        jugador = nuevo_traductor().crear_jugador(datos, nombre="Ana", id_jugador="p1")

        self.assertEqual((jugador.actor_id, jugador.name), ("p1", "Ana"))

    def test_estadisticas_incompletas(self):
        generales = dict(GENERALES_CRIPTA_01)
        generales["jugador"] = {"vida_max": 30, "ataque": 6, "defensa": 2}
        datos = DatosDePartida(generales, VERSION_CATALOGO_REAL)

        with self.assertRaises(ErrorDatosCripta):
            nuevo_traductor().crear_jugador(datos)

    def test_estadisticas_invalidas(self):
        generales = dict(GENERALES_CRIPTA_01)
        generales["jugador"] = {"vida_max": 0, "ataque": 6, "defensa": 2, "velocidad": 100}
        datos = DatosDePartida(generales, VERSION_CATALOGO_REAL)

        with self.assertRaises(ErrorDatosCripta):
            nuevo_traductor().crear_jugador(datos)


class TestCrearMapa(unittest.TestCase):

    def setUp(self):
        self.traductor = nuevo_traductor()
        self.mapa = self.traductor.crear_mapa(SALAS_CRIPTA_01)

    def test_todas_las_salas_en_orden(self):
        self.assertEqual(self.mapa.room_ids(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(self.mapa.room(4).name, "Osario profundo")
        self.assertEqual(self.traductor.avisos, [])

    def test_salidas_de_cada_sala(self):
        sala_2 = self.mapa.room(2)

        self.assertEqual([(s.direction, s.destination) for s in sala_2.exits()],
                         [("N", 3), ("S", 1), ("E", 5)])
        self.assertIsNone(sala_2.exit_towards("O"))
        self.assertEqual([(s.direction, s.destination) for s in self.mapa.room(6).exits()],
                         [("O", 4)])

    def test_puerta_abierta_compartida(self):
        ida = self.mapa.room(1).exit_towards("N").door
        vuelta = self.mapa.room(2).exit_towards("S").door

        self.assertIs(ida, vuelta)
        self.assertTrue(ida.is_open)

    def test_puerta_cerrada_compartida_con_llave_y_cierre(self):
        ida = self.mapa.room(2).exit_towards("E").door
        vuelta = self.mapa.room(5).exit_towards("O").door

        self.assertIs(ida, vuelta)
        self.assertTrue(ida.closed)
        self.assertEqual(ida.key_id, "itm_llave_bronce")
        self.assertEqual(ida.auto_close, 500)

    def test_puerta_de_la_salida(self):
        puerta = self.mapa.room(4).exit_towards("E").door

        self.assertIs(puerta, self.mapa.room(6).exit_towards("O").door)
        self.assertTrue(puerta.closed)
        self.assertEqual(puerta.key_id, "itm_llave_negra")
        self.assertIsNone(puerta.auto_close)

    def test_abrir_desde_un_lado_se_ve_del_otro(self):
        self.mapa.room(2).exit_towards("E").door.closed = False

        self.assertTrue(self.mapa.room(5).exit_towards("O").door.is_open)

    def test_hay_una_puerta_por_paso(self):
        puertas = []
        for id_sala in self.mapa.room_ids():
            for salida in self.mapa.room(id_sala).exits():
                if not any(puerta is salida.door for puerta in puertas):
                    puertas.append(salida.door)

        self.assertEqual(len(puertas), 5)

    def test_salas_sin_contenido_todavia(self):
        for id_sala in self.mapa.room_ids():
            self.assertFalse(self.mapa.room(id_sala).content_loaded)

    def test_cerrada_si_cualquier_lado_lo_dice(self):
        salas = [
            {"id": 1, "nombre": "A", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "B", "salidas": {"O": {"sala": 1, "cerrada": True, "llave": "itm_x"}}},
        ]

        mapa = nuevo_traductor().crear_mapa(salas)

        puerta = mapa.room(1).exit_towards("E").door
        self.assertTrue(puerta.closed)
        self.assertEqual(puerta.key_id, "itm_x")

    def test_llaves_distintas_gana_la_sala_de_menor_id(self):
        salas = [
            {"id": 7, "nombre": "A", "salidas": {"E": {"sala": 3, "cerrada": True, "llave": "itm_de_7"}}},
            {"id": 3, "nombre": "B", "salidas": {"O": {"sala": 7, "cerrada": True, "llave": "itm_de_3"}}},
        ]
        traductor = nuevo_traductor()

        mapa = traductor.crear_mapa(salas)

        self.assertEqual(mapa.room(7).exit_towards("E").door.key_id, "itm_de_3")
        self.assertEqual(len(traductor.avisos), 1)
        self.assertIn("3 y 7", traductor.avisos[0])

    def test_paso_de_un_solo_sentido(self):
        salas = [
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}}},
            {"id": 2, "nombre": "B", "salidas": {}},
        ]

        mapa = nuevo_traductor().crear_mapa(salas)

        self.assertEqual(mapa.room(1).exit_towards("N").destination, 2)
        self.assertEqual(mapa.room(2).exits(), [])

    def test_salida_hacia_sala_inexistente(self):
        salas = [{"id": 1, "nombre": "A", "salidas": {"N": {"sala": 99}}}]
        traductor = nuevo_traductor()

        mapa = traductor.crear_mapa(salas)

        self.assertEqual(mapa.room(1).exits(), [])
        self.assertEqual(len(traductor.avisos), 1)
        self.assertIn("99", traductor.avisos[0])

    def test_sala_sin_campo_salidas(self):
        mapa = nuevo_traductor().crear_mapa([{"id": 1, "nombre": "Sola"}])

        self.assertEqual(mapa.room(1).exits(), [])

    def test_dos_pasos_entre_las_mismas_salas(self):
        # Dos pasos distintos entre 1 y 2: cada uno empareja con su propia vuelta.
        salas = [
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}, "E": {"sala": 2, "cerrada": True}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1}, "O": {"sala": 1}}},
        ]

        mapa = nuevo_traductor().crear_mapa(salas)

        puertas_de_1 = [s.door for s in mapa.room(1).exits()]
        puertas_de_2 = [s.door for s in mapa.room(2).exits()]
        self.assertIsNot(puertas_de_1[0], puertas_de_1[1])
        for puerta in puertas_de_2:
            self.assertTrue(any(puerta is otra for otra in puertas_de_1))

    def test_datos_incompletos_del_esqueleto(self):
        casos = (
            [{"nombre": "Sin id"}],
            [{"id": 1}],
            [{"id": 1, "nombre": "A", "salidas": {"N": {"cerrada": True}}}],
            [{"id": 1, "nombre": "A"}, {"id": 1, "nombre": "Repetida"}],
        )
        for salas in casos:
            with self.subTest(salas=salas):
                with self.assertRaises(ErrorDatosCripta):
                    nuevo_traductor().crear_mapa(salas)

    def test_mapa_grande(self):
        from tests.datos_cripta_01 import salas_de_cuadricula

        mapa = nuevo_traductor().crear_mapa(salas_de_cuadricula(20, 20))

        self.assertEqual(len(mapa), 400)
        centro = mapa.room(22)
        self.assertEqual(len(centro.exits()), 4)
        self.assertIs(centro.exit_towards("E").door, mapa.room(23).exit_towards("O").door)


class TestLlenarSala(unittest.TestCase):

    def setUp(self):
        self.traductor = nuevo_traductor()
        self.mapa = self.traductor.crear_mapa(SALAS_CRIPTA_01)

    def test_sala_con_ratas_daga_y_trampa(self):
        sala = self.mapa.room(2)

        enemigos = self.traductor.llenar_sala(sala, contenido_de(2))

        self.assertEqual([e.actor_id for e in enemigos], ["e-201", "e-202"])
        rata = enemigos[0]
        self.assertEqual(rata.name, "Rata gigante")
        self.assertEqual((rata.health, rata.max_health, rata.attack, rata.defense, rata.speed),
                         (12, 12, 5, 1, 150))
        self.assertEqual(rata.behavior, Enemy.TRACKER)
        self.assertEqual(rata.room_id, 2)
        self.assertFalse(rata.is_active)

        self.assertEqual([o.instance_id for o in sala.floor_items], ["o-2-0"])
        daga = sala.floor_items[0]
        self.assertEqual((daga.type_id, daga.item_class, daga.attack_bonus, daga.weight, daga.value),
                         ("itm_daga_oxidada", Item.WEAPON, 3, 2, 15))

        self.assertEqual(len(sala.traps), 1)
        trampa = sala.traps[0]
        self.assertEqual((trampa.instance_id, trampa.type_id, trampa.damage, trampa.rearm_interval),
                         ("t-17", "trp_dardos", 4, 300))
        self.assertEqual(trampa.room_id, 2)
        self.assertTrue(trampa.armed)
        self.assertTrue(sala.content_loaded)

    def test_objetos_que_suelta_un_enemigo(self):
        enemigos = self.traductor.llenar_sala(self.mapa.room(2), contenido_de(2))

        soltados = enemigos[1].drops
        self.assertEqual(len(soltados), 1)
        self.assertEqual(soltados[0].instance_id, "e-202-s0")
        self.assertEqual((soltados[0].type_id, soltados[0].item_class, soltados[0].heal),
                         ("itm_pocion_menor", Item.POTION, 8))

    def test_guardian_sin_vida_en_la_colocacion(self):
        enemigos = self.traductor.llenar_sala(self.mapa.room(4), contenido_de(4))

        guardian = enemigos[0]
        self.assertEqual(guardian.health, 20)
        self.assertEqual(guardian.behavior, Enemy.GUARDIAN)
        self.assertEqual(guardian.drops, [])
        self.assertEqual([o.type_id for o in self.mapa.room(4).floor_items],
                         ["itm_llave_negra", "itm_pocion_menor"])
        self.assertEqual(self.mapa.room(4).floor_items[0].opens, "puerta_salida")

    def test_ids_de_objetos_son_deterministas(self):
        otro_traductor = nuevo_traductor()
        otro_mapa = otro_traductor.crear_mapa(SALAS_CRIPTA_01)

        self.traductor.llenar_sala(self.mapa.room(5), contenido_de(5))
        otro_traductor.llenar_sala(otro_mapa.room(5), contenido_de(5))

        self.assertEqual([o.instance_id for o in self.mapa.room(5).floor_items],
                         [o.instance_id for o in otro_mapa.room(5).floor_items])
        self.assertEqual(id_de_objeto_en_el_suelo(5, 1), "o-5-1")
        self.assertEqual(id_de_objeto_soltado("e-201", 0), "e-201-s0")

    def test_todos_los_tipos_de_objeto(self):
        for id_sala in (1, 3, 5):
            self.traductor.llenar_sala(self.mapa.room(id_sala), contenido_de(id_sala))

        antorcha = self.mapa.room(1).floor_items[0]
        llave, coraza = self.mapa.room(3).floor_items
        pergamino, antidoto = self.mapa.room(5).floor_items
        self.assertEqual((antorcha.item_class, antorcha.duration), (Item.TORCH, 2000))
        self.assertEqual((llave.item_class, llave.opens), (Item.KEY, "puerta_2_7"))
        self.assertEqual((coraza.item_class, coraza.defense_bonus), (Item.ARMOR, 2))
        self.assertEqual(pergamino.item_class, Item.REWIND_SCROLL)
        self.assertEqual(antidoto.item_class, Item.ANTIDOTE)

    def test_sala_vacia(self):
        sala = self.mapa.room(6)

        enemigos = self.traductor.llenar_sala(sala, contenido_de(6))

        self.assertEqual((enemigos, sala.floor_items, sala.traps), ([], [], []))
        self.assertTrue(sala.content_loaded)

    def test_llenar_dos_veces_no_duplica(self):
        sala = self.mapa.room(2)
        self.traductor.llenar_sala(sala, contenido_de(2))

        enemigos = self.traductor.llenar_sala(sala, contenido_de(2))

        self.assertEqual(enemigos, [])
        self.assertEqual(len(sala.floor_items), 1)

    def test_contenido_de_otra_sala(self):
        with self.assertRaises(ErrorDatosCripta):
            self.traductor.llenar_sala(self.mapa.room(2), contenido_de(3))

    def test_si_falla_la_sala_queda_sin_cargar(self):
        sala = self.mapa.room(2)
        entrada = dict(contenido_de(2))
        entrada["trampas"] = [{"instancia": "t-99", "tipo": "itm_antorcha"}]

        with self.assertRaises(ErrorDatosCripta):
            self.traductor.llenar_sala(sala, entrada)

        self.assertFalse(sala.content_loaded)
        self.assertEqual(sala.floor_items, [])

    def test_trampa_sin_rearme_usa_el_valor_por_defecto(self):
        fichas = FICHAS_CRIPTA_01 + [{"id": "trp_foso", "nombre": "Foso", "clase": "trampa", "daño": 6}]
        traductor = nuevo_traductor(fichas)

        trampa = traductor.crear_trampa({"instancia": "t-1", "tipo": "trp_foso"}, 3)

        self.assertEqual(trampa.rearm_interval, 300)

    def test_comportamientos_del_api(self):
        fichas = FICHAS_CRIPTA_01 + [
            {"id": "ent_espectro", "nombre": "Espectro", "clase": "enemigo", "vida_max": 9,
             "ataque": 3, "defensa": 0, "velocidad": 80, "comportamiento": "errante"},
        ]
        traductor = nuevo_traductor(fichas)

        espectro = traductor.crear_enemigo({"instancia": "e-1", "tipo": "ent_espectro"}, 1)

        self.assertEqual(espectro.behavior, Enemy.WANDERER)

    def test_comportamiento_desconocido(self):
        fichas = [{"id": "ent_raro", "nombre": "Raro", "clase": "enemigo", "vida_max": 5,
                   "ataque": 1, "defensa": 0, "velocidad": 100, "comportamiento": "volador"}]

        with self.assertRaises(ErrorDatosCripta):
            nuevo_traductor(fichas).crear_enemigo({"instancia": "e-1", "tipo": "ent_raro"}, 1)

    def test_ficha_de_otra_clase(self):
        with self.assertRaises(ErrorDatosCripta):
            self.traductor.crear_enemigo({"instancia": "e-1", "tipo": "itm_antorcha"}, 1)
        with self.assertRaises(ErrorDatosCripta):
            self.traductor.crear_objeto("ent_rata_gigante", "o-1-0")

    def test_colocacion_incompleta(self):
        with self.assertRaises(ErrorDatosCripta):
            self.traductor.crear_enemigo({"tipo": "ent_rata_gigante"}, 2)
        with self.assertRaises(ErrorDatosCripta):
            self.traductor.crear_trampa({"instancia": "t-1"}, 2)

    def test_ficha_incompleta(self):
        fichas = [{"id": "itm_rota", "nombre": "Rota", "clase": "arma", "peso": 1}]

        with self.assertRaises(ErrorDatosCripta):
            nuevo_traductor(fichas).crear_objeto("itm_rota", "o-1-0")

    def test_el_jugador_usa_el_arma_creada(self):
        datos = DatosDePartida(GENERALES_CRIPTA_01, VERSION_CATALOGO_REAL)
        jugador = self.traductor.crear_jugador(datos)
        sala = self.mapa.room(2)
        self.traductor.llenar_sala(sala, contenido_de(2))

        jugador.equipped_weapon = sala.floor_items[0]

        self.assertEqual(jugador.effective_attack, 9)


class TestCamposQueElProgramaNoConoce(unittest.TestCase):
    """El contrato del API no tiene campo de regeneración (S13). Si algún día
    llega un campo nuevo, se ignora pero queda un aviso para el reporte."""

    HIDRA = {"id": "ent_hidra", "nombre": "Hidra", "clase": "enemigo", "vida_max": 40,
             "ataque": 6, "defensa": 2, "velocidad": 100, "comportamiento": "guardián",
             "regeneracion": 3}

    def test_los_datos_reales_no_generan_avisos(self):
        traductor = nuevo_traductor()
        mapa = traductor.crear_mapa(SALAS_CRIPTA_01)
        for id_sala in mapa.room_ids():
            traductor.llenar_sala(mapa.room(id_sala), contenido_de(id_sala))

        self.assertEqual(traductor.avisos, [])

    def test_la_regeneracion_queda_en_cero(self):
        rata = nuevo_traductor().crear_enemigo({"instancia": "e-1", "tipo": "ent_rata_gigante"}, 2)

        self.assertEqual(rata.regeneration, 0)

    def test_campo_nuevo_en_una_ficha_avisa_una_sola_vez(self):
        traductor = nuevo_traductor(FICHAS_CRIPTA_01 + [self.HIDRA])

        primera = traductor.crear_enemigo({"instancia": "e-1", "tipo": "ent_hidra"}, 1)
        traductor.crear_enemigo({"instancia": "e-2", "tipo": "ent_hidra"}, 1)

        self.assertEqual(primera.regeneration, 0)
        self.assertEqual(len(traductor.avisos), 1)
        self.assertIn("ent_hidra", traductor.avisos[0])
        self.assertIn("'regeneracion'", traductor.avisos[0])

    def test_campo_nuevo_en_colocaciones_y_salidas(self):
        traductor = nuevo_traductor()
        salas = [{"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "secreta": True}}},
                 {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1, "secreta": True}}}]

        traductor.crear_mapa(salas)
        for instancia in ("e-1", "e-2"):
            traductor.crear_enemigo({"instancia": instancia, "tipo": "ent_rata_gigante",
                                     "regeneracion": 1}, 1)
        traductor.crear_trampa({"instancia": "t-1", "tipo": "trp_dardos", "oculta": True}, 1)

        self.assertEqual(len(traductor.avisos), 3)
        texto = " ".join(traductor.avisos)
        for campo in ("'secreta'", "'regeneracion'", "'oculta'"):
            self.assertIn(campo, texto)

    def test_hay_campos_declarados_para_todas_las_clases(self):
        for clase in CLASES_DE_OBJETO + (CLASE_ENEMIGO, CLASE_TRAMPA):
            self.assertIn("id", campos_conocidos_de_la_clase(clase))
        with self.assertRaises(ValueError):
            campos_conocidos_de_la_clase("dragon")

    def test_campos_opcionales_del_contrato_no_avisan(self):
        fichas = [{"id": "itm_pocion_rapida", "nombre": "Poción rápida", "clase": "pocion",
                   "peso": 1, "valor": 30, "modificador_velocidad": 50, "duracion": 300},
                  {"id": "trp_foso", "nombre": "Foso", "clase": "trampa", "daño": 6, "rearme": 500}]
        traductor = nuevo_traductor(fichas)

        traductor.crear_objeto("itm_pocion_rapida", "o-1-0")
        traductor.crear_trampa({"instancia": "t-1", "tipo": "trp_foso"}, 1)

        self.assertEqual(traductor.avisos, [])


class TestIdsEnUso(unittest.TestCase):

    def setUp(self):
        self.traductor = nuevo_traductor()
        self.mapa = self.traductor.crear_mapa(SALAS_CRIPTA_01)
        self.ratas = self.traductor.llenar_sala(self.mapa.room(2), contenido_de(2))
        self.sala = self.mapa.room(2)

    def test_tipo_de_cada_instancia(self):
        self.assertEqual(self.traductor.tipo_de_enemigo("e-201"), "ent_rata_gigante")
        self.assertIsNone(self.traductor.tipo_de_enemigo("e-999"))

    def test_enemigos_objetos_y_trampas(self):
        en_uso = self.traductor.ids_en_uso(self.ratas, self.sala.floor_items, self.sala.traps)

        self.assertCountEqual(en_uso.claves(),
                              ["ent_rata_gigante", "itm_daga_oxidada", "itm_pocion_menor", "trp_dardos"])

    def test_enemigos_muertos_no_cuentan(self):
        for rata in self.ratas:
            rata.take_damage(100)

        en_uso = self.traductor.ids_en_uso(self.ratas)

        self.assertTrue(en_uso.esta_vacia())

    def test_sin_nada_en_uso(self):
        self.assertTrue(self.traductor.ids_en_uso().esta_vacia())


if __name__ == "__main__":
    unittest.main()
