"""
Pruebas de RepositorioCripta: el bloque 2 completo, de punta a punta.

Se usa una fuente simulada que sirve cripta-01 completa y anota cada
solicitud, con las carpetas de caché en un directorio temporal. Las pruebas
más importantes verifican el presupuesto real: 7 de 9 solicitudes en un
arranque en frío y 3 en un arranque en caliente.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import tempfile
import unittest
from pathlib import Path

from adapters.fuente_datos import (
    FuenteDatos,
    PresupuestoAgotado,
    validar_ids_catalogo,
    validar_ids_salas,
)
from structures.tabla_hash import TablaHash
from tests.datos_cripta_01 import (
    CONTENIDO_CRIPTA_01,
    FICHAS_CRIPTA_01,
    GENERALES_CRIPTA_01,
    LISTA_DE_CRIPTAS,
    SALAS_CRIPTA_01,
    VERSION_CATALOGO_REAL,
)
from model.enemy import Enemy
from model.item import Item
from repository.repositorio_cripta import (
    RepositorioCripta,
    VersionesIncompatibles,
    objetos_que_sueltan,
)

# Recorrido completo de cripta-01: buscar la llave de bronce (3), abrir el
# nicho (5), volver y salir por la 6. Solo las pruebas conocen estos ids (§9).
RECORRIDO_COMPLETO = [2, 3, 2, 5, 2, 3, 4, 6]


class FuenteCriptaFalsa(FuenteDatos):
    """Sirve cripta-01 completa y anota cada solicitud por tipo."""

    def __init__(self, generales=None, version_catalogo=VERSION_CATALOGO_REAL, fichas=None):
        super().__init__()
        self.generales = dict(generales or GENERALES_CRIPTA_01)
        self.version = version_catalogo
        self.fichas = FICHAS_CRIPTA_01 if fichas is None else fichas
        self.solicitudes = []  # ("tipo", detalle)

    def listar_criptas(self):
        self._consumir_solicitud("listar las criptas")
        self.solicitudes.append(("lista", None))
        return LISTA_DE_CRIPTAS

    def datos_generales(self, id_cripta):
        self._consumir_solicitud("obtener datos generales")
        self.solicitudes.append(("generales", id_cripta))
        return dict(self.generales)

    def version_cripta(self, id_cripta):
        raise NotImplementedError

    def pagina_salas(self, id_cripta, pagina):
        self._consumir_solicitud("descargar página")
        self.solicitudes.append(("pagina", pagina))
        return {"pagina": 1, "total_paginas": 1, "salas": SALAS_CRIPTA_01}

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        self._consumir_solicitud("descargar contenido")
        self.solicitudes.append(("contenido", list(ids_salas)))
        return {"contenido": [entrada for id_sala in ids_salas
                              for entrada in CONTENIDO_CRIPTA_01 if entrada["sala"] == id_sala]}

    def catalogo(self, ids):
        validar_ids_catalogo(ids)
        self._consumir_solicitud("descargar fichas")
        self.solicitudes.append(("catalogo", list(ids)))
        return {"entidades": [ficha for ficha in self.fichas if ficha["id"] in ids]}

    def version_catalogo(self):
        self._consumir_solicitud("obtener la versión del catálogo")
        self.solicitudes.append(("version_catalogo", None))
        return {"version": self.version}

    def descripcion_del_origen(self):
        return "fuente simulada"

    def tipos_de_solicitud(self):
        return [tipo for tipo, _ in self.solicitudes]


class PruebasRepositorioCripta(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta_cache = Path(self._carpeta_temporal.name) / "cache_cripta"

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def jugar_partida(self, fuente=None, recorrido=RECORRIDO_COMPLETO, capacidad=25,
                      consultar_ids_en_uso=None, versiones_requeridas=None):
        fuente = fuente if fuente is not None else FuenteCriptaFalsa()
        repositorio = RepositorioCripta(fuente, self.carpeta_cache, capacidad, consultar_ids_en_uso)
        repositorio.empezar_conteo_de_partida()
        criptas = repositorio.listar_criptas()
        datos = repositorio.iniciar_partida(criptas[0]["id"], versiones_requeridas)
        actual = datos.sala_inicial
        for siguiente in recorrido:
            repositorio.preparar_entrada_a_sala(siguiente)
            actual = siguiente
            repositorio.despues_de_accion(actual)
        return repositorio, fuente

    # --- presupuesto real de cripta-01 -------------------------------

    def test_arranque_en_frio_usa_7_de_9_solicitudes(self):
        repositorio, fuente = self.jugar_partida()
        self.assertEqual(fuente.tipos_de_solicitud(), [
            "lista", "generales", "version_catalogo", "pagina",
            "contenido", "catalogo", "catalogo",
        ])
        self.assertEqual(fuente.solicitudes[4][1], [1, 2, 3, 5, 4, 6])  # todo el contenido en un lote
        reporte = repositorio.reporte_de_red()
        self.assertEqual(reporte.solicitudes_realizadas, 7)
        self.assertEqual(reporte.presupuesto_solicitudes, 9)
        self.assertEqual(reporte.esperas_en_la_puerta, 0)
        self.assertEqual(reporte.fichas_descargadas, 11)

    def test_arranque_en_caliente_usa_3_solicitudes(self):
        self.jugar_partida()  # primera partida: llena las copias en disco
        repositorio, fuente = self.jugar_partida()  # segunda partida, misma carpeta
        self.assertEqual(fuente.tipos_de_solicitud(), ["lista", "generales", "version_catalogo"])
        reporte = repositorio.reporte_de_red()
        self.assertEqual(reporte.solicitudes_realizadas, 3)
        self.assertEqual(reporte.salas_recuperadas_de_disco, 6)
        self.assertEqual(reporte.fallos_de_cache, 0)
        # Las fichas están en disco: pedir una que no se ha leído no usa la red.
        antes = repositorio.reporte_de_red().recuperaciones_desde_disco
        self.assertEqual(repositorio.obtener_ficha("itm_antidoto")["valor"], 12)
        self.assertEqual(repositorio.reporte_de_red().recuperaciones_desde_disco, antes + 1)
        self.assertEqual(fuente.solicitudes_realizadas(), 3)

    def test_nueva_version_de_la_cripta_vuelve_a_descargar_su_contenido(self):
        self.jugar_partida()
        fuente = FuenteCriptaFalsa(generales=dict(GENERALES_CRIPTA_01, version="nueva"))
        _, fuente = self.jugar_partida(fuente)
        # Las fichas siguen vigentes (mismo catálogo); esqueleto y contenido no.
        self.assertEqual(fuente.tipos_de_solicitud(),
                         ["lista", "generales", "version_catalogo", "pagina", "contenido"])

    def test_presupuesto_insuficiente_llega_al_controlador(self):
        fuente = FuenteCriptaFalsa(generales=dict(GENERALES_CRIPTA_01, presupuesto_solicitudes=5))
        with self.assertRaises(PresupuestoAgotado):
            self.jugar_partida(fuente)
        self.assertEqual(fuente.solicitudes_realizadas(), 5)  # nunca se pasa del presupuesto

    # --- reproducción (§4.11) ----------------------------------------

    def test_replay_con_las_mismas_versiones(self):
        versiones = (GENERALES_CRIPTA_01["version"], VERSION_CATALOGO_REAL)
        repositorio, _ = self.jugar_partida(versiones_requeridas=versiones)
        self.assertEqual(repositorio.versiones_de_la_partida(),
                         ("cripta-01", GENERALES_CRIPTA_01["version"], VERSION_CATALOGO_REAL))

    def test_replay_con_otras_versiones_se_niega(self):
        fuente = FuenteCriptaFalsa()
        with self.assertRaises(VersionesIncompatibles) as contexto:
            self.jugar_partida(fuente, versiones_requeridas=("version-vieja", VERSION_CATALOGO_REAL))
        self.assertIn("reproducción fiel", str(contexto.exception))
        # No cargó nada después de detectar la diferencia.
        self.assertEqual(fuente.tipos_de_solicitud(), ["lista", "generales", "version_catalogo"])

    # --- datos para el modelo y el controlador -----------------------

    def test_datos_de_partida_vienen_del_api(self):
        repositorio, _ = self.jugar_partida(recorrido=[])
        datos = repositorio.datos_de_partida()
        self.assertEqual((datos.sala_inicial, datos.sala_salida), (1, 6))
        self.assertEqual(datos.llave_salida, "itm_llave_negra")
        self.assertEqual(datos.inventario_max, 10)
        self.assertEqual(datos.jugador["vida_max"], 30)

    def test_accesos_a_salas_contenido_y_fichas(self):
        repositorio, _ = self.jugar_partida()
        self.assertTrue(repositorio.sala_del_esqueleto(2)["salidas"]["E"]["cerrada"])
        self.assertEqual(repositorio.vecinos_de_sala(2), [3, 1, 5])
        self.assertEqual(repositorio.ids_de_salas(), [1, 2, 3, 4, 5, 6])
        self.assertEqual(repositorio.contenido_de_sala(4)["enemigos"][0]["tipo"], "ent_guardian_oseo")
        self.assertEqual(repositorio.obtener_ficha("ent_guardian_oseo")["nombre"], "Guardián óseo")
        with self.assertRaises(ValueError):
            repositorio.sala_del_esqueleto(99)

    def test_hay_que_iniciar_la_partida(self):
        repositorio = RepositorioCripta(FuenteCriptaFalsa(), self.carpeta_cache)
        with self.assertRaises(RuntimeError):
            repositorio.preparar_entrada_a_sala(1)
        with self.assertRaises(RuntimeError):
            repositorio.versiones_de_la_partida()

    def test_usa_la_funcion_de_fichas_en_uso(self):
        llamadas = []

        def consultar_ids_en_uso():
            llamadas.append(1)
            en_uso = TablaHash()
            en_uso.insertar("ent_rata_gigante", True)
            return en_uso

        repositorio, _ = self.jugar_partida(capacidad=2, consultar_ids_en_uso=consultar_ids_en_uso)
        self.assertGreater(len(llamadas), 0)
        self.assertEqual(repositorio.obtener_ficha("ent_rata_gigante")["vida_max"], 12)

    def test_reporte_en_texto(self):
        repositorio, _ = self.jugar_partida()
        texto = "\n".join(repositorio.reporte_de_red().lineas_de_texto())
        self.assertIn("Solicitudes realizadas: 7 de 9", texto)
        self.assertIn("Aciertos de caché", texto)
        self.assertIn("Fallos de caché", texto)
        self.assertIn("fuente simulada", texto)

    def test_si_el_disco_falla_la_partida_sigue(self):
        archivo = Path(self._carpeta_temporal.name) / "no_es_carpeta"
        archivo.write_text("x", encoding="utf-8")
        self.carpeta_cache = archivo
        repositorio, fuente = self.jugar_partida()
        reporte = repositorio.reporte_de_red()
        self.assertEqual(reporte.solicitudes_realizadas, 7)
        self.assertGreater(len(reporte.avisos), 0)


class PruebasRepositorioConElModelo(unittest.TestCase):
    """El repositorio entregando objetos del modelo hechos por el Traductor,
    como los usará el controlador."""

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta_cache = Path(self._carpeta_temporal.name) / "cache_cripta"

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def jugar_con_el_modelo(self, fuente=None, recorrido=RECORRIDO_COMPLETO):
        """Recorre la cripta como lo haría el controlador: crea jugador y
        mapa, y carga cada sala antes de entrar. Devuelve también la lista
        plana de enemigos, como la que lleva Game."""
        fuente = fuente if fuente is not None else FuenteCriptaFalsa()
        repositorio = RepositorioCripta(fuente, self.carpeta_cache, 25)
        repositorio.empezar_conteo_de_partida()
        datos = repositorio.iniciar_partida(repositorio.listar_criptas()[0]["id"])
        jugador = repositorio.crear_jugador()
        mapa = repositorio.crear_mapa()
        enemigos = repositorio.cargar_contenido_de_sala(mapa.room(datos.sala_inicial))
        for siguiente in recorrido:
            enemigos.extend(repositorio.cargar_contenido_de_sala(mapa.room(siguiente)))
            jugador.room_id = siguiente
            repositorio.despues_de_accion(siguiente)
        return repositorio, fuente, jugador, mapa, enemigos

    def test_recorrido_completo_sigue_usando_7_de_9(self):
        repositorio, fuente, _, _, _ = self.jugar_con_el_modelo()

        self.assertEqual(fuente.solicitudes_realizadas(), 7)
        # La última es la poción que suelta la rata, pedida por la precarga.
        self.assertEqual(fuente.solicitudes[-1], ("catalogo", ["itm_pocion_menor"]))
        self.assertEqual(repositorio.reporte_de_red().esperas_en_la_puerta, 0)

    def test_en_caliente_sigue_usando_3(self):
        self.jugar_con_el_modelo()

        _, fuente, _, mapa, enemigos = self.jugar_con_el_modelo()

        self.assertEqual(fuente.solicitudes_realizadas(), 3)
        self.assertEqual(len(enemigos), 3)
        self.assertEqual(mapa.room(2).floor_items[0].attack_bonus, 3)

    def test_objetos_del_modelo(self):
        _, _, jugador, mapa, enemigos = self.jugar_con_el_modelo()

        self.assertEqual((jugador.room_id, jugador.max_health), (6, 30))
        self.assertEqual(len(mapa), 6)
        self.assertEqual([e.actor_id for e in enemigos], ["e-201", "e-202", "e-401"])
        self.assertEqual(enemigos[2].behavior, Enemy.GUARDIAN)
        self.assertEqual(enemigos[0].drops[0].item_class, Item.POTION)
        self.assertIs(mapa.room(2).exit_towards("E").door, mapa.room(5).exit_towards("O").door)
        for id_sala in mapa.room_ids():
            self.assertTrue(mapa.room(id_sala).content_loaded)

    def test_sala_ya_cargada_no_repite_enemigos(self):
        repositorio, _, _, mapa, _ = self.jugar_con_el_modelo()

        self.assertEqual(repositorio.cargar_contenido_de_sala(mapa.room(2)), [])
        self.assertEqual(len(mapa.room(2).floor_items), 1)

    def test_sin_presupuesto_la_sala_queda_sin_cargar(self):
        repositorio, _, _, mapa, _ = self.jugar_con_el_modelo(recorrido=[])

        def sin_presupuesto(id_sala):
            raise PresupuestoAgotado("entrar a una sala", 9)

        repositorio.preparar_entrada_a_sala = sin_presupuesto
        with self.assertRaises(PresupuestoAgotado):
            repositorio.cargar_contenido_de_sala(mapa.room(3))
        self.assertFalse(mapa.room(3).content_loaded)

    def test_lo_que_suelta_un_enemigo_queda_listo_antes_de_entrar(self):
        # La rata suelta un objeto que no aparece en ninguna sala, y solo las
        # salas 1 y 2 tienen algo: el primer lote trae todo lo de las salas,
        # y el objeto que suelta la rata se conoce cuando ya no hay más lotes.
        fichas = []
        for ficha in FICHAS_CRIPTA_01:
            if ficha["id"] == "ent_rata_gigante":
                ficha = dict(ficha, suelta=["itm_colmillo"])
            fichas.append(ficha)
        fichas.append({"id": "itm_colmillo", "nombre": "Colmillo", "clase": "arma", "peso": 1,
                       "valor": 3, "ataque_bonus": 1})

        class FuenteConDosSalasLlenas(FuenteCriptaFalsa):
            def contenido(self, id_cripta, ids_salas):
                respuesta = super().contenido(id_cripta, ids_salas)
                entradas = []
                for entrada in respuesta["contenido"]:
                    if entrada["sala"] > 2:
                        entrada = {"sala": entrada["sala"], "enemigos": [], "objetos": [], "trampas": []}
                    entradas.append(entrada)
                return {"contenido": entradas}

        def entrar_a_la_sala_2(presupuesto):
            """Inicia (sin listar criptas) y entra a la sala 2. Devuelve la
            fuente, los enemigos y la cantidad de solicitudes antes de entrar."""
            fuente = FuenteConDosSalasLlenas(
                generales=dict(GENERALES_CRIPTA_01, presupuesto_solicitudes=presupuesto), fichas=fichas)
            repositorio = RepositorioCripta(fuente, Path(self._carpeta_temporal.name) / str(presupuesto))
            repositorio.empezar_conteo_de_partida()
            repositorio.iniciar_partida("cripta-01")
            mapa = repositorio.crear_mapa()
            repositorio.cargar_contenido_de_sala(mapa.room(1))
            antes_de_entrar = fuente.solicitudes_realizadas()
            return fuente, repositorio.cargar_contenido_de_sala(mapa.room(2)), antes_de_entrar

        # Con presupuesto de sobra, la precarga lo trae antes de llegar a la puerta.
        fuente, enemigos, antes_de_entrar = entrar_a_la_sala_2(9)
        self.assertIn(("catalogo", ["itm_colmillo"]), fuente.solicitudes)
        self.assertEqual(fuente.solicitudes_realizadas(), antes_de_entrar)
        self.assertEqual(enemigos[0].drops[0].name, "Colmillo")

        # Con el presupuesto justo no hay precarga: se pide al entrar, no en combate.
        fuente, enemigos, antes_de_entrar = entrar_a_la_sala_2(6)
        self.assertEqual(antes_de_entrar, 5)
        self.assertEqual(fuente.solicitudes[-1], ("catalogo", ["itm_colmillo"]))
        self.assertEqual(enemigos[0].drops[0].instance_id, "e-201-s0")
        self.assertEqual(enemigos[0].drops[0].attack_bonus, 1)

    def test_la_precarga_no_relee_fichas_en_cada_accion(self):
        # Cada tipo de enemigo se revisa una sola vez por partida para saber
        # qué suelta: repetir acciones no infla los aciertos del reporte.
        repositorio, fuente, _, _, _ = self.jugar_con_el_modelo()
        aciertos = repositorio.reporte_de_red().aciertos_de_cache

        for _ in range(20):
            repositorio.despues_de_accion(2)
            repositorio.despues_de_accion(4)

        self.assertEqual(repositorio.reporte_de_red().aciertos_de_cache, aciertos)
        self.assertEqual(fuente.solicitudes_realizadas(), 7)

    def test_ids_en_uso_para_la_cache(self):
        repositorio, _, _, mapa, enemigos = self.jugar_con_el_modelo(recorrido=[2])
        sala = mapa.room(2)

        en_uso = repositorio.ids_en_uso(enemigos, sala.floor_items, sala.traps)

        self.assertCountEqual(en_uso.claves(),
                              ["ent_rata_gigante", "itm_pocion_menor", "itm_daga_oxidada", "trp_dardos"])

    def test_la_cache_consulta_al_modelo(self):
        # El controlador arma consultar_ids_en_uso con el repositorio y el modelo.
        estado = {}
        llamadas = []

        def consultar_ids_en_uso():
            llamadas.append(1)
            if "enemigos" not in estado:
                return TablaHash()
            return estado["repositorio"].ids_en_uso(estado["enemigos"])

        repositorio = RepositorioCripta(FuenteCriptaFalsa(), self.carpeta_cache, 2, consultar_ids_en_uso)
        estado["repositorio"] = repositorio
        repositorio.empezar_conteo_de_partida()
        repositorio.iniciar_partida("cripta-01")
        mapa = repositorio.crear_mapa()
        estado["enemigos"] = repositorio.cargar_contenido_de_sala(mapa.room(2))
        repositorio.cargar_contenido_de_sala(mapa.room(4))

        self.assertGreater(len(llamadas), 0)
        self.assertEqual(len(estado["enemigos"]), 2)

    def test_avisos_del_traductor_en_el_reporte(self):
        salas_raras = [{"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2}, "E": {"sala": 42}}},
                       {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1}}}]

        class FuenteConSalaInexistente(FuenteCriptaFalsa):
            def pagina_salas(self, id_cripta, pagina):
                super().pagina_salas(id_cripta, pagina)
                return {"pagina": 1, "total_paginas": 1, "salas": salas_raras}

        fuente = FuenteConSalaInexistente(generales=dict(GENERALES_CRIPTA_01, salas_total=2, sala_salida=2))
        repositorio = RepositorioCripta(fuente, self.carpeta_cache)
        repositorio.empezar_conteo_de_partida()
        repositorio.iniciar_partida("cripta-01")

        repositorio.crear_mapa()

        texto = "\n".join(repositorio.reporte_de_red().lineas_de_texto())
        self.assertIn("42", texto)

    def test_un_campo_nuevo_del_api_llega_al_reporte(self):
        # Si el API agregara, por ejemplo, regeneración a la rata, el juego
        # sigue y el reporte final lo dice (S13).
        fichas = []
        for ficha in FICHAS_CRIPTA_01:
            if ficha["id"] == "ent_rata_gigante":
                ficha = dict(ficha, regeneracion=2)
            fichas.append(ficha)

        repositorio, _, _, _, enemigos = self.jugar_con_el_modelo(FuenteCriptaFalsa(fichas=fichas),
                                                                   recorrido=[2])

        self.assertEqual(enemigos[0].regeneration, 0)
        texto = "\n".join(repositorio.reporte_de_red().lineas_de_texto())
        self.assertIn("Aviso: La ficha ent_rata_gigante trae el campo 'regeneracion'", texto)

    def test_hay_que_iniciar_la_partida(self):
        repositorio = RepositorioCripta(FuenteCriptaFalsa(), self.carpeta_cache)
        for operacion in (repositorio.crear_jugador, repositorio.crear_mapa, repositorio.ids_en_uso):
            with self.assertRaises(RuntimeError):
                operacion()


class PruebasObjetosQueSueltan(unittest.TestCase):

    def test_sin_repetir_y_en_orden(self):
        fichas = TablaHash()
        fichas.insertar("ent_a", {"suelta": ["itm_1", "itm_2"]})
        fichas.insertar("ent_b", {"suelta": ["itm_2", "itm_3"]})
        fichas.insertar("ent_c", {})

        self.assertEqual(objetos_que_sueltan(["ent_a", "ent_b", "ent_c"], fichas.obtener),
                         ["itm_1", "itm_2", "itm_3"])

    def test_sin_enemigos(self):
        self.assertEqual(objetos_que_sueltan([], None), [])


if __name__ == "__main__":
    unittest.main()
