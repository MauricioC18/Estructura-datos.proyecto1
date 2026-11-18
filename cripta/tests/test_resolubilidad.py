import random
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from adapters.fuente_offline import FuenteOffline
from benchmark.bench_resolubilidad import (
    VerificacionIngenua,
    cripta_mas_grande_del_paquete,
    contar_operaciones,
    generar_cripta_encadenada,
    mapa_de,
    verificar_resolubilidad_ingenua,
)
from controller import application
from model.key_location import KeyLocation
from model.resolubilidad import (
    CODIGO_NO_RESOLUBLE,
    CODIGO_RESOLUBLE,
    CODIGO_SIN_VERIFICAR,
    MOTIVO_DEPENDE,
    MOTIVO_SIN_ACCESO,
    MOTIVO_SIN_UBICACION,
    LlaveNoObtenible,
    PuertaDeFrontera,
    VerificacionDeResolubilidad,
    verificar_resolubilidad,
)
from repository.repositorio_cripta import CriptaNoResoluble, RepositorioCripta, VersionesIncompatibles
from repository.traductor import Traductor
from tests.test_repositorio_cripta import FuenteCriptaFalsa

CARPETA_DATOS_OFFLINE = Path(__file__).resolve().parent.parent / "datos_offline"

LLAVES_DE_CRIPTA_01 = [
    {"id": "itm_llave_bronce", "sala": 3},
    {"id": "itm_llave_negra", "sala": 5},
]


def sala(id_sala, **salidas):
    return {"id": id_sala, "nombre": f"Sala {id_sala}", "salidas": salidas}


def abierta(destino):
    return {"sala": destino}


def cerrada(destino, llave=None):
    salida = {"sala": destino, "cerrada": True}
    if llave is not None:
        salida["llave"] = llave
    return salida


def verificar(salas, ubicaciones, sala_inicial=1, sala_salida=99, llave_salida="itm_llave_negra"):
    mapa = Traductor(lambda id_ficha: None).crear_mapa(salas)
    return verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, ubicaciones)


def cripta_con_bronce_y_negra():
    salas = [
        sala(1, N=abierta(2), E=abierta(4)),
        sala(2, S=abierta(1), N=cerrada(3, "itm_llave_bronce")),
        sala(3, S=abierta(2), N=cerrada(99, "itm_llave_negra")),
        sala(4, O=abierta(1)),
        sala(99, S=abierta(3)),
    ]
    ubicaciones = [KeyLocation("itm_llave_negra", 3), KeyLocation("itm_llave_bronce", 4)]
    return salas, ubicaciones


class PruebasSpec006SiSePuedeGanar(unittest.TestCase):

    def test_fr005_una_cripta_que_se_puede_ganar_es_resoluble(self):
        salas = [sala(1, N=cerrada(99, "itm_llave_negra")), sala(99, S=abierta(1))]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 1)])

        self.assertTrue(reporte.es_resoluble)
        self.assertEqual(reporte.codigo_de_salida(), CODIGO_RESOLUBLE)

    def test_fr006_la_llave_necesaria_aparece_antes_en_el_orden(self):
        salas, ubicaciones = cripta_con_bronce_y_negra()

        reporte = verificar(salas, ubicaciones)

        self.assertTrue(reporte.es_resoluble)
        self.assertEqual([entrada.llave for entrada in reporte.orden_de_llaves],
                         ["itm_llave_bronce", "itm_llave_negra"])
        self.assertEqual([entrada.ronda for entrada in reporte.orden_de_llaves], [0, 1])
        self.assertIn("  1. itm_llave_bronce: sala 4", reporte.lineas_de_texto())
        self.assertIn("  2. itm_llave_negra: sala 3", reporte.lineas_de_texto())

    def test_fr003_apendice_b_la_llave_de_un_errante_se_ubica_en_su_sala_inicial(self):
        salas = [
            sala(1, N=abierta(2)),
            sala(2, S=abierta(1), N=cerrada(99, "itm_llave_negra")),
            sala(99, S=abierta(2)),
        ]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 2, "e-7")])

        self.assertTrue(reporte.es_resoluble)
        self.assertEqual(reporte.orden_de_llaves[0].ubicacion, KeyLocation("itm_llave_negra", 2, "e-7"))
        self.assertIn("  1. itm_llave_negra: la suelta e-7, que inicia en la sala 2", reporte.lineas_de_texto())

    def test_fr007_apendice_b_con_varios_ordenes_validos_dos_ejecuciones_dan_el_mismo(self):
        salas = [
            sala(1, N=abierta(2), E=abierta(3)),
            sala(2, S=abierta(1)),
            sala(3, O=abierta(1), N=cerrada(99, "itm_llave_negra")),
            sala(99, S=abierta(3)),
        ]
        ubicaciones = [KeyLocation("itm_llave_zeta", 2), KeyLocation("itm_llave_negra", 3),
                       KeyLocation("itm_llave_alfa", 2)]

        primera = verificar(salas, ubicaciones)
        segunda = verificar(salas, ubicaciones)

        orden = [entrada.llave for entrada in primera.orden_de_llaves]
        self.assertEqual(orden, ["itm_llave_alfa", "itm_llave_negra", "itm_llave_zeta"])
        self.assertEqual(orden, [entrada.llave for entrada in segunda.orden_de_llaves])
        self.assertEqual(primera.lineas_de_texto(), segunda.lineas_de_texto())

    def test_fr007_el_resultado_no_depende_del_orden_de_las_salas_ni_de_las_entradas(self):
        cripta = generar_cripta_encadenada(7, 12)
        esperado = verificar(cripta["salas"], cripta["ubicaciones"], cripta["sala_inicial"],
                             cripta["sala_salida"], cripta["llave_salida"]).lineas_de_texto()
        generador = random.Random(11)

        for _ in range(5):
            salas = list(cripta["salas"])
            ubicaciones = list(cripta["ubicaciones"])
            generador.shuffle(salas)
            generador.shuffle(ubicaciones)
            obtenido = verificar(salas, ubicaciones, cripta["sala_inicial"], cripta["sala_salida"],
                                 cripta["llave_salida"]).lineas_de_texto()
            self.assertEqual(obtenido, esperado)

    def test_fr004_una_salida_de_un_solo_sentido_solo_se_atraviesa_desde_su_sala(self):
        salas = [
            sala(1, N=abierta(2)),
            sala(2, N=cerrada(99, "itm_llave_negra")),
            sala(99, S=abierta(2)),
        ]

        desde_la_sala_1 = verificar(salas, [KeyLocation("itm_llave_negra", 1)], sala_inicial=1)
        desde_la_sala_2 = verificar(salas, [KeyLocation("itm_llave_negra", 1)], sala_inicial=2)

        self.assertTrue(desde_la_sala_1.es_resoluble)
        self.assertFalse(desde_la_sala_2.es_resoluble)

    def test_fr005_sin_una_puerta_que_pida_llave_salida_no_es_resoluble(self):
        salas = [sala(1, N=abierta(99)), sala(99, S=abierta(1))]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 1)])

        self.assertFalse(reporte.es_resoluble)
        self.assertTrue(reporte.falta_puerta_hacia_la_salida)
        self.assertIn("ninguna puerta que la pida lleva a la sala de salida", "\n".join(reporte.lineas_de_texto()))

    def test_fr008_si_es_resoluble_las_llaves_inalcanzables_van_como_aviso(self):
        salas, ubicaciones = cripta_con_bronce_y_negra()
        salas.append(sala(50))

        reporte = verificar(salas, ubicaciones + [KeyLocation("itm_llave_perdida", 50)])

        self.assertTrue(reporte.es_resoluble)
        lineas = reporte.lineas_de_texto()
        self.assertEqual(lineas[-2], "Aviso: estas llaves no se pueden obtener:")
        self.assertEqual(lineas[-1], "  itm_llave_perdida: está en una zona a la que no lleva ninguna salida")

    def test_fr002_el_cierre_automatico_no_bloquea_una_puerta_cuya_llave_se_tiene(self):
        salas = [
            sala(1, N=abierta(2), E={"sala": 3, "cerrada": True, "llave": "itm_llave_bronce",
                                     "cierre_automatico": 300}),
            sala(2, S=abierta(1)),
            sala(3, O=abierta(1), N=cerrada(99, "itm_llave_negra")),
            sala(99, S=abierta(3)),
        ]
        ubicaciones = [KeyLocation("itm_llave_bronce", 2), KeyLocation("itm_llave_negra", 3)]

        self.assertTrue(verificar(salas, ubicaciones).es_resoluble)

    def test_fr021_el_reporte_da_lineas_de_texto_listas_para_mostrar(self):
        salas, ubicaciones = cripta_con_bronce_y_negra()

        lineas = verificar(salas, ubicaciones).lineas_de_texto()

        self.assertTrue(all(isinstance(linea, str) for linea in lineas))
        self.assertEqual(lineas[0], "Verificación de resolubilidad: la cripta es resoluble.")

    def test_llave_salida_en_la_sala_inicial_se_obtiene_desde_el_principio(self):
        salas = [sala(1, N=cerrada(99, "itm_llave_negra")), sala(99)]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 1)])

        self.assertEqual(reporte.orden_de_llaves[0].ronda, 0)


class PruebasSpec006PorQueNoSePuedeGanar(unittest.TestCase):

    def test_fr012_apendice_b_llave_salida_detras_de_la_unica_puerta_que_ella_abre(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_negra"), E=cerrada(99, "itm_llave_negra")),
            sala(2, S=abierta(1)),
            sala(99, O=abierta(1)),
        ]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 2)])

        self.assertFalse(reporte.es_resoluble)
        self.assertEqual(reporte.ciclos, [["itm_llave_negra"]])
        self.assertIn("  itm_llave_negra → itm_llave_negra (está detrás de puertas que solo ella abre)",
                      reporte.lineas_de_texto())

    def test_fr012_un_ciclo_de_dos_llaves_se_reporta_concreto(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_hierro"), E=cerrada(3, "itm_llave_negra"),
                 O=cerrada(99, "itm_llave_negra")),
            sala(2, S=abierta(1)),
            sala(3, O=abierta(1)),
            sala(99, E=abierta(1)),
        ]
        ubicaciones = [KeyLocation("itm_llave_negra", 2), KeyLocation("itm_llave_hierro", 3)]

        reporte = verificar(salas, ubicaciones)

        self.assertEqual(reporte.ciclos, [["itm_llave_hierro", "itm_llave_negra"]])
        self.assertIn("  itm_llave_hierro → itm_llave_negra → itm_llave_hierro", reporte.lineas_de_texto())

    def test_fr009_fr011_una_llave_que_piden_las_puertas_y_no_tiene_ubicacion(self):
        salas = [sala(1, N=cerrada(99, "itm_llave_negra")), sala(99)]

        reporte = verificar(salas, [])

        self.assertEqual(reporte.llaves_no_obtenibles,
                         [LlaveNoObtenible("itm_llave_negra", MOTIVO_SIN_UBICACION)])
        self.assertEqual(reporte.ubicaciones_de_la_frontera, [("itm_llave_negra", [])])
        self.assertIn("  itm_llave_negra: no tiene ubicación", reporte.lineas_de_texto())

    def test_fr010_las_puertas_de_la_frontera_salen_con_origen_direccion_destino_y_llave(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_negra"), E=abierta(3)),
            sala(2, S=abierta(1)),
            sala(3, O=abierta(1), N=cerrada(4)),
            sala(4),
        ]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 4)], sala_salida=2)

        self.assertEqual(reporte.puertas_de_la_frontera, [
            PuertaDeFrontera(1, "N", 2, "itm_llave_negra"),
            PuertaDeFrontera(3, "N", 4, None),
        ])
        lineas = reporte.lineas_de_texto()
        self.assertIn("  sala 1 (salida N) hacia la sala 2: pide itm_llave_negra", lineas)
        self.assertIn("  sala 3 (salida N) hacia la sala 4: cerrada y sin llave", lineas)

    def test_fr011_la_ubicacion_de_una_llave_de_la_frontera_dice_el_enemigo_que_la_suelta(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_hierro"), E=cerrada(99, "itm_llave_negra")),
            sala(2, S=abierta(1)),
            sala(99, O=abierta(1)),
        ]
        ubicaciones = [KeyLocation("itm_llave_hierro", 2, "e-3"), KeyLocation("itm_llave_negra", 2)]

        reporte = verificar(salas, ubicaciones)

        self.assertIn("  itm_llave_hierro: la suelta e-3, que inicia en la sala 2", reporte.lineas_de_texto())

    def test_fr009_cada_llave_no_obtenible_dice_de_cual_depende(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_hierro"), E=cerrada(99, "itm_llave_negra")),
            sala(2, S=abierta(1), N=cerrada(3, "itm_llave_plata")),
            sala(3, S=abierta(2)),
            sala(99, O=abierta(1)),
        ]
        ubicaciones = [KeyLocation("itm_llave_plata", 2), KeyLocation("itm_llave_negra", 3)]

        reporte = verificar(salas, ubicaciones)

        self.assertEqual(reporte.llaves_no_obtenibles, [
            LlaveNoObtenible("itm_llave_hierro", MOTIVO_SIN_UBICACION),
            LlaveNoObtenible("itm_llave_negra", MOTIVO_DEPENDE, "itm_llave_plata"),
            LlaveNoObtenible("itm_llave_plata", MOTIVO_DEPENDE, "itm_llave_hierro"),
        ])
        self.assertEqual(reporte.ciclos, [])

    def test_fr013_fr014_depender_de_una_llave_sin_ubicacion_no_es_un_ciclo(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_negra"), E=cerrada(2, "itm_llave_azul"),
                 O=cerrada(99, "itm_llave_negra")),
            sala(2, S=abierta(1)),
            sala(99, E=abierta(1)),
        ]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 2)])

        self.assertIn(LlaveNoObtenible("itm_llave_negra", MOTIVO_DEPENDE, "itm_llave_azul"),
                      reporte.llaves_no_obtenibles)
        self.assertEqual(reporte.ciclos, [])

    def test_fr014_entre_llaves_con_ubicacion_se_elige_la_de_menor_id(self):
        salas = [
            sala(1, N=cerrada(2, "itm_llave_zinc"), E=cerrada(2, "itm_llave_bronce"),
                 O=cerrada(99, "itm_llave_negra")),
            sala(2, S=abierta(1)),
            sala(3),
            sala(99, E=abierta(1)),
        ]
        ubicaciones = [KeyLocation("itm_llave_negra", 2), KeyLocation("itm_llave_zinc", 3),
                       KeyLocation("itm_llave_bronce", 3)]

        primera = verificar(salas, ubicaciones)
        segunda = verificar(salas, list(reversed(ubicaciones)))

        self.assertIn(LlaveNoObtenible("itm_llave_negra", MOTIVO_DEPENDE, "itm_llave_bronce"),
                      primera.llaves_no_obtenibles)
        self.assertEqual(primera.lineas_de_texto(), segunda.lineas_de_texto())

    def test_fr009_una_llave_en_una_zona_sin_salidas_que_lleguen(self):
        salas = [sala(1, N=cerrada(99, "itm_llave_negra")), sala(7), sala(99)]

        reporte = verificar(salas, [KeyLocation("itm_llave_negra", 7)])

        self.assertEqual(reporte.llaves_no_obtenibles,
                         [LlaveNoObtenible("itm_llave_negra", MOTIVO_SIN_ACCESO)])
        self.assertEqual(reporte.ciclos, [])

    def test_fr015_las_listas_salen_en_orden_determinista(self):
        cripta = generar_cripta_encadenada(3, 10)
        ubicaciones = [ubicacion for ubicacion in cripta["ubicaciones"] if ubicacion.key_id != "itm_llave_0004"]
        salas = list(cripta["salas"])
        generador = random.Random(5)

        esperado = verificar(salas, ubicaciones, cripta["sala_inicial"], cripta["sala_salida"],
                             cripta["llave_salida"]).lineas_de_texto()
        generador.shuffle(salas)
        generador.shuffle(ubicaciones)
        obtenido = verificar(salas, ubicaciones, cripta["sala_inicial"], cripta["sala_salida"],
                             cripta["llave_salida"]).lineas_de_texto()

        self.assertEqual(obtenido, esperado)
        self.assertIn("  itm_llave_0004: no tiene ubicación", obtenido)


class PruebasSpec006InicioDePartida(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._carpeta_temporal.name)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def repositorio(self, fuente):
        repositorio = RepositorioCripta(fuente, self.carpeta / "cache")
        repositorio.empezar_conteo_de_partida()
        return repositorio

    def test_fr016_apendice_b_sin_forzar_una_cripta_no_resoluble_no_inicia_y_trae_el_reporte(self):
        fuente = FuenteCriptaFalsa(llaves=[])
        repositorio = self.repositorio(fuente)

        with self.assertRaises(CriptaNoResoluble) as contexto:
            repositorio.iniciar_partida("cripta-01", exigir_resolubilidad=True)

        reporte = contexto.exception.reporte
        self.assertEqual(reporte.codigo_de_salida(), CODIGO_NO_RESOLUBLE)
        self.assertEqual(reporte.lineas_de_texto()[0], "Verificación de resolubilidad: la cripta no es resoluble.")
        self.assertNotIn("contenido", fuente.tipos_de_solicitud())
        self.assertNotIn("catalogo", fuente.tipos_de_solicitud())

    def test_fr016_con_forzar_la_partida_inicia_y_el_reporte_queda_disponible(self):
        repositorio = self.repositorio(FuenteCriptaFalsa(llaves=[]))

        repositorio.iniciar_partida("cripta-01", exigir_resolubilidad=False)

        self.assertFalse(repositorio.reporte_de_resolubilidad().es_resoluble)
        self.assertIsNotNone(repositorio.crear_mapa())

    def test_fr017_una_cripta_resoluble_inicia_con_su_reporte_y_su_orden(self):
        repositorio = self.repositorio(FuenteCriptaFalsa(llaves=LLAVES_DE_CRIPTA_01))

        repositorio.iniciar_partida("cripta-01", exigir_resolubilidad=True)

        reporte = repositorio.reporte_de_resolubilidad()
        self.assertTrue(reporte.es_resoluble)
        self.assertEqual(reporte.lineas_de_texto()[1:4], [
            "Orden de obtención de llaves:",
            "  1. itm_llave_bronce: sala 3",
            "  2. itm_llave_negra: sala 5",
        ])

    def test_fr018_fr001_verificar_no_pide_contenido_ni_fichas_y_da_su_codigo(self):
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_CRIPTA_01)

        reporte = self.repositorio(fuente).verificar_cripta("cripta-01")

        self.assertEqual(reporte.codigo_de_salida(), CODIGO_RESOLUBLE)
        self.assertEqual(fuente.tipos_de_solicitud(), ["generales", "version_catalogo", "pagina", "llaves"])

    def test_fr020_sin_ubicacion_de_llaves_se_informa_y_la_partida_inicia(self):
        paquete = self.carpeta / "paquete"
        shutil.copytree(CARPETA_DATOS_OFFLINE, paquete)
        repositorio = self.repositorio(FuenteOffline(paquete))

        repositorio.iniciar_partida("cripta-01", exigir_resolubilidad=True)

        reporte = repositorio.reporte_de_resolubilidad()
        self.assertFalse(reporte.se_pudo_verificar)
        self.assertEqual(reporte.codigo_de_salida(), CODIGO_SIN_VERIFICAR)
        self.assertEqual(reporte.lineas_de_texto()[0], "Verificación de resolubilidad: no se pudo verificar.")

    def test_fr019_al_cargar_una_partida_guardada_no_se_verifica(self):
        repositorio = self.repositorio(FuenteCriptaFalsa(llaves=[]))

        repositorio.iniciar_partida("cripta-01", obtener_ubicacion_de_llaves=False, exigir_resolubilidad=True)

        self.assertIsNone(repositorio.reporte_de_resolubilidad())

    def test_fr022_verificar_no_agrega_solicitudes_al_inicio(self):
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_CRIPTA_01)

        self.repositorio(fuente).iniciar_partida("cripta-01", exigir_resolubilidad=True)

        self.assertEqual(fuente.tipos_de_solicitud()[:5],
                         ["generales", "version_catalogo", "pagina", "llaves", "contenido"])
        self.assertEqual(fuente.tipos_de_solicitud().count("llaves"), 1)

    def test_fr016_la_reproduccion_nunca_exige_la_resolubilidad(self):
        llamadas = []

        class RepositorioQueAnota:
            def empezar_conteo_de_partida(self):
                pass

            def iniciar_partida(self, *argumentos, **argumentos_con_nombre):
                llamadas.append(argumentos_con_nombre)
                raise VersionesIncompatibles("fin de la prueba")

        log = SimpleNamespace(header=SimpleNamespace(
            crypt_id="cripta-01", crypt_version="v", catalog_version="c", saved_game=""))
        with mock.patch.object(application, "read_replay_log", return_value=log):
            application.replay(RepositorioQueAnota(), "partida.log", output=lambda texto: None)

        self.assertFalse(llamadas[0].get("exigir_resolubilidad", False))


class PruebasSpec006CostoYMediciones(unittest.TestCase):

    def test_fr023_fr024_las_operaciones_crecen_en_proporcion_al_tamano(self):
        operaciones = []
        operaciones_ingenuas = []
        for cantidad in (25, 100):
            cripta = generar_cripta_encadenada(1, cantidad)
            mapa = mapa_de(cripta)
            operaciones.append(contar_operaciones(VerificacionDeResolubilidad, mapa, cripta)[0])
            operaciones_ingenuas.append(contar_operaciones(VerificacionIngenua, mapa, cripta)[0])

        self.assertLess(operaciones[1] / operaciones[0], 4.5)
        self.assertGreater(operaciones_ingenuas[1] / operaciones_ingenuas[0], 12)

    def test_fr026_una_cripta_de_300_salas_se_verifica_en_menos_de_200_ms(self):
        cripta = generar_cripta_encadenada(2026, 60)
        mapa = mapa_de(cripta)

        inicio = time.perf_counter()
        reporte = verificar_resolubilidad(mapa, cripta["sala_inicial"], cripta["sala_salida"],
                                          cripta["llave_salida"], cripta["ubicaciones"])
        segundos = time.perf_counter() - inicio

        self.assertEqual(len(cripta["salas"]), 301)
        self.assertTrue(reporte.es_resoluble)
        self.assertLess(segundos, 0.2)

    def test_fr026_la_cripta_mas_grande_del_paquete_se_verifica_en_menos_de_200_ms(self):
        cripta, motivo = cripta_mas_grande_del_paquete()
        if cripta is None:
            self.skipTest(motivo)
        mapa = mapa_de(cripta)

        inicio = time.perf_counter()
        reporte = verificar_resolubilidad(mapa, cripta["sala_inicial"], cripta["sala_salida"],
                                          cripta["llave_salida"], cripta["ubicaciones"])
        segundos = time.perf_counter() - inicio

        self.assertTrue(reporte.se_pudo_verificar)
        self.assertLess(segundos, 0.2)

    def test_fr025_fr028_la_ingenua_y_la_incremental_coinciden_tambien_si_no_es_resoluble(self):
        for semilla in range(12):
            cripta = generar_cripta_encadenada(semilla, 15)
            generador = random.Random(semilla)
            ubicaciones = list(cripta["ubicaciones"])
            if semilla % 3 == 1:
                ubicaciones.pop(generador.randrange(len(ubicaciones)))
            if semilla % 3 == 2:
                movida = ubicaciones.pop(generador.randrange(len(ubicaciones)))
                ubicaciones.append(KeyLocation(movida.key_id, cripta["sala_salida"] - 1))
            cripta = dict(cripta, ubicaciones=ubicaciones)
            mapa = mapa_de(cripta)
            argumentos = (mapa, cripta["sala_inicial"], cripta["sala_salida"], cripta["llave_salida"],
                          cripta["ubicaciones"])
            with self.subTest(semilla=semilla):
                self.assertEqual(verificar_resolubilidad(*argumentos).lineas_de_texto(),
                                 verificar_resolubilidad_ingenua(*argumentos).lineas_de_texto())

    def test_fr027_la_misma_semilla_genera_la_misma_cripta(self):
        self.assertEqual(generar_cripta_encadenada(9, 20), generar_cripta_encadenada(9, 20))
        self.assertNotEqual(generar_cripta_encadenada(9, 20), generar_cripta_encadenada(10, 20))


if __name__ == "__main__":
    unittest.main()
