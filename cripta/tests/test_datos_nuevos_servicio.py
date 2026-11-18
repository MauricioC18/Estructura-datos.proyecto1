import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from adapters.almacen_cripta import AlmacenCripta
from adapters.fuente_datos import ErrorFuenteDatos, PresupuestoAgotado, UbicacionDeLlavesNoDisponible
from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import FuenteOffline, GuardadorDatosOffline
from controller import application
from model.key_location import KeyLocation
from repository.repositorio_cripta import RepositorioCripta, VersionesIncompatibles
from repository.traductor import ErrorDatosCripta, Traductor
from tests.datos_cripta_01 import GENERALES_CRIPTA_01
from tests.test_fuente_http import EsperaFalsa, RespuestaHttpFalsa, SesionHttpFalsa
from tests.test_repositorio_cripta import FuenteCriptaFalsa

CARPETA_DATOS_OFFLINE = Path(__file__).resolve().parent.parent / "datos_offline"

LLAVES_DE_PRUEBA = [
    {"id": "itm_llave_bronce", "sala": 4},
    {"id": "itm_llave_negra", "sala": 3, "enemigo": "e-301"},
    {"id": "itm_llave_bronce", "sala": 5},
]

UBICACIONES_ESPERADAS = [
    KeyLocation("itm_llave_bronce", 4),
    KeyLocation("itm_llave_negra", 3, "e-301"),
    KeyLocation("itm_llave_bronce", 5),
]


def traductor_sin_catalogo():
    def obtener_ficha(id_ficha):
        raise AssertionError(f"No se debe pedir la ficha {id_ficha}")

    return Traductor(obtener_ficha)


def salas_existentes(*ids):
    return lambda id_sala: id_sala in ids


class FuenteConConsultaDeLlavesFallida(FuenteCriptaFalsa):

    def ubicacion_de_llaves(self, id_cripta):
        self._consumir_solicitud("obtener la ubicación de las llaves")
        raise ErrorFuenteDatos("obtener la ubicación de las llaves", "error del servidor", 500)


class FinDeLaPrueba(Exception):
    pass


class RepositorioQueAnotaElInicio:

    def __init__(self):
        self.argumentos_con_nombre = None

    def empezar_conteo_de_partida(self):
        pass

    def iniciar_partida(self, *argumentos, **argumentos_con_nombre):
        self.argumentos_con_nombre = argumentos_con_nombre
        raise VersionesIncompatibles("fin de la prueba")


class PruebasSpec004CostoEnNull(unittest.TestCase):

    def test_fr001_un_costo_en_null_vale_cien(self):
        mapa = traductor_sin_catalogo().crear_mapa([
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "costo": None}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1, "costo": None}}},
        ])

        self.assertEqual(mapa.room(1).exit_towards("N").cost, 100)
        self.assertEqual(mapa.room(2).exit_towards("S").cost, 100)

    def test_fr001_fr003_null_de_un_lado_y_costo_del_otro_usa_el_declarado(self):
        traductor = traductor_sin_catalogo()

        mapa = traductor.crear_mapa([
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "costo": None}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1, "costo": 250}}},
        ])

        self.assertEqual(mapa.room(1).exit_towards("N").cost, 250)
        self.assertEqual(mapa.room(2).exit_towards("S").cost, 250)
        self.assertEqual(traductor.avisos, [])


class PruebasSpec004UbicacionDeLlavesEnLasFuentes(unittest.TestCase):

    def test_fr011_fr013_la_fuente_http_usa_la_ruta_de_llaves_y_cuenta_una_solicitud(self):
        sesion = SesionHttpFalsa(RespuestaHttpFalsa(200, {"llaves": LLAVES_DE_PRUEBA}))
        fuente = FuenteHttp("https://api.prueba/v1", "id", sesion, EsperaFalsa())

        respuesta = fuente.ubicacion_de_llaves("cripta-01")

        self.assertEqual(respuesta, {"llaves": LLAVES_DE_PRUEBA})
        self.assertTrue(sesion.solicitudes_recibidas[0]["url"].endswith("/criptas/cripta-01/llaves"))
        self.assertEqual(fuente.solicitudes_realizadas(), 1)
        self.assertEqual(fuente.forma_de_obtencion(), "descargada del servicio")

    def test_fr013_un_reintento_tras_429_cuenta_aparte(self):
        sesion = SesionHttpFalsa(
            RespuestaHttpFalsa(429, {"error": "demasiadas solicitudes", "reintentar_en": 1}),
            RespuestaHttpFalsa(200, {"llaves": []}),
        )
        fuente = FuenteHttp("https://api.prueba/v1", "id", sesion, EsperaFalsa())

        fuente.ubicacion_de_llaves("cripta-01")

        self.assertEqual(fuente.solicitudes_realizadas(), 2)

    def test_fr015_el_paquete_offline_la_lee_sin_contar_solicitudes(self):
        with tempfile.TemporaryDirectory() as carpeta:
            GuardadorDatosOffline(carpeta).guardar_ubicacion_de_llaves(
                "cripta-01", {"llaves": LLAVES_DE_PRUEBA})
            fuente = FuenteOffline(carpeta)

            respuesta = fuente.ubicacion_de_llaves("cripta-01")

        self.assertEqual(respuesta, {"llaves": LLAVES_DE_PRUEBA})
        self.assertEqual(fuente.solicitudes_realizadas(), 0)
        self.assertEqual(fuente.forma_de_obtencion(), "leída del paquete offline")

    def test_fr016_un_paquete_offline_sin_el_archivo_la_da_por_no_disponible(self):
        with tempfile.TemporaryDirectory() as carpeta:
            fuente = FuenteOffline(carpeta)

            with self.assertRaises(UbicacionDeLlavesNoDisponible):
                fuente.ubicacion_de_llaves("cripta-01")


class PruebasSpec004CopiaEnDisco(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.almacen = AlmacenCripta(Path(self._carpeta_temporal.name))
        self.almacen.preparar(GENERALES_CRIPTA_01)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def ruta_de_la_copia(self):
        return Path(self._carpeta_temporal.name) / "cripta-01" / "llaves.json"

    def test_fr014_la_ubicacion_guardada_se_lee_tal_cual(self):
        self.almacen.guardar_ubicacion_de_llaves("cripta-01", {"llaves": LLAVES_DE_PRUEBA})

        self.assertEqual(self.almacen.leer_ubicacion_de_llaves("cripta-01"), {"llaves": LLAVES_DE_PRUEBA})

    def test_fr021_una_copia_que_no_es_json_se_lee_como_ausente(self):
        self.ruta_de_la_copia().write_text("{", encoding="utf-8")

        self.assertIsNone(self.almacen.leer_ubicacion_de_llaves("cripta-01"))

    def test_fr021_una_copia_sin_la_lista_de_llaves_se_lee_como_ausente(self):
        self.ruta_de_la_copia().write_text(json.dumps({"otra": []}), encoding="utf-8")

        self.assertIsNone(self.almacen.leer_ubicacion_de_llaves("cripta-01"))

    def test_fr022_cambiar_la_version_de_la_cripta_borra_la_copia(self):
        self.almacen.guardar_ubicacion_de_llaves("cripta-01", {"llaves": LLAVES_DE_PRUEBA})

        self.almacen.preparar(dict(GENERALES_CRIPTA_01, version="nueva"))

        self.assertIsNone(self.almacen.leer_ubicacion_de_llaves("cripta-01"))


class PruebasSpec004TraduccionDeLaUbicacion(unittest.TestCase):

    def traducir(self, respuesta, *salas):
        return traductor_sin_catalogo().crear_ubicaciones_de_llaves(respuesta, salas_existentes(*salas))

    def test_fr012_sin_enemigo_la_llave_esta_en_el_suelo_de_la_sala(self):
        ubicacion = self.traducir({"llaves": [{"id": "itm_llave_bronce", "sala": 4}]}, 4)[0]

        self.assertEqual(ubicacion, KeyLocation("itm_llave_bronce", 4))
        self.assertFalse(ubicacion.is_dropped_by_enemy)

    def test_fr012_con_enemigo_la_suelta_esa_instancia_y_la_sala_es_donde_inicia(self):
        ubicacion = self.traducir(
            {"llaves": [{"id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203"}]}, 12)[0]

        self.assertEqual(ubicacion, KeyLocation("itm_llave_negra", 12, "e-1203"))
        self.assertTrue(ubicacion.is_dropped_by_enemy)

    def test_fr012_un_enemigo_en_null_es_una_llave_en_el_suelo(self):
        ubicacion = self.traducir({"llaves": [{"id": "itm_llave_bronce", "sala": 4, "enemigo": None}]}, 4)[0]

        self.assertFalse(ubicacion.is_dropped_by_enemy)

    def test_fr018_fr019_conserva_las_repetidas_y_el_orden(self):
        ubicaciones = self.traducir({"llaves": LLAVES_DE_PRUEBA}, 3, 4, 5)

        self.assertEqual(ubicaciones, UBICACIONES_ESPERADAS)

    def test_una_lista_vacia_es_un_dato_valido(self):
        self.assertEqual(self.traducir({"llaves": []}, 1), [])

    def test_fr017_entradas_invalidas_son_dato_invalido_de_la_cripta(self):
        respuestas_invalidas = [
            {},
            {"llaves": None},
            {"llaves": ["itm_llave_bronce"]},
            {"llaves": [{"sala": 4}]},
            {"llaves": [{"id": "", "sala": 4}]},
            {"llaves": [{"id": 7, "sala": 4}]},
            {"llaves": [{"id": "itm_llave_bronce"}]},
            {"llaves": [{"id": "itm_llave_bronce", "sala": "4"}]},
            {"llaves": [{"id": "itm_llave_bronce", "sala": True}]},
            {"llaves": [{"id": "itm_llave_bronce", "sala": 99}]},
            {"llaves": [{"id": "itm_llave_bronce", "sala": 4, "enemigo": 5}]},
        ]

        for respuesta in respuestas_invalidas:
            with self.subTest(respuesta=respuesta):
                with self.assertRaises(ErrorDatosCripta):
                    self.traducir(respuesta, 4)

    def test_fr017_el_id_de_la_llave_no_se_comprueba_contra_el_catalogo(self):
        ubicaciones = self.traducir({"llaves": [{"id": "itm_que_no_es_llave", "sala": 4}]}, 4)

        self.assertEqual(ubicaciones[0].key_id, "itm_que_no_es_llave")

    def test_fr024_los_campos_adicionales_se_ignoran_sin_aviso(self):
        traductor = traductor_sin_catalogo()

        ubicaciones = traductor.crear_ubicaciones_de_llaves(
            {"llaves": [{"id": "itm_llave_bronce", "sala": 4, "extra": "x"}]}, salas_existentes(4))

        self.assertEqual(ubicaciones, [KeyLocation("itm_llave_bronce", 4)])
        self.assertEqual(traductor.avisos, [])


class PruebasSpec004InicioDePartida(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._carpeta_temporal.name)
        self.carpeta_cache = self.carpeta / "cache_cripta"

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def iniciar(self, fuente, **argumentos_con_nombre):
        repositorio = RepositorioCripta(fuente, self.carpeta_cache)
        repositorio.empezar_conteo_de_partida()
        repositorio.iniciar_partida("cripta-01", **argumentos_con_nombre)
        return repositorio

    def paquete_offline_de_cripta_01(self, con_llaves):
        carpeta = self.carpeta / "paquete"
        shutil.copytree(CARPETA_DATOS_OFFLINE, carpeta)
        if con_llaves:
            GuardadorDatosOffline(carpeta).guardar_ubicacion_de_llaves(
                "cripta-01", {"llaves": LLAVES_DE_PRUEBA})
        return carpeta

    def linea_del_reporte(self, repositorio):
        for linea in repositorio.reporte_de_red().lineas_de_texto():
            if linea.startswith("Ubicación de llaves:"):
                return linea
        return None

    def test_fr011_se_pide_despues_del_esqueleto_y_antes_del_contenido(self):
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)

        self.iniciar(fuente)

        tipos = fuente.tipos_de_solicitud()
        self.assertEqual(tipos[:4], ["generales", "version_catalogo", "pagina", "llaves"])
        self.assertNotIn("catalogo", tipos[:4])

    def test_fr013_fr025_sin_copia_se_pide_una_vez_y_el_reporte_dice_descargada(self):
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)

        repositorio = self.iniciar(fuente)

        self.assertEqual(fuente.tipos_de_solicitud().count("llaves"), 1)
        self.assertEqual(repositorio.ubicacion_de_llaves(), UBICACIONES_ESPERADAS)
        self.assertEqual(self.linea_del_reporte(repositorio), "Ubicación de llaves: descargada del servicio")

    def test_fr014_fr025_con_copia_vigente_se_toma_del_disco(self):
        self.iniciar(FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA))
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)

        repositorio = self.iniciar(fuente)

        self.assertNotIn("llaves", fuente.tipos_de_solicitud())
        self.assertEqual(repositorio.ubicacion_de_llaves(), UBICACIONES_ESPERADAS)
        self.assertEqual(self.linea_del_reporte(repositorio), "Ubicación de llaves: recuperada de disco")

    def test_fr021_una_copia_danada_se_vuelve_a_pedir(self):
        self.iniciar(FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA))
        (self.carpeta_cache / "criptas" / "cripta-01" / "llaves.json").write_text("{", encoding="utf-8")
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)

        repositorio = self.iniciar(fuente)

        self.assertEqual(fuente.tipos_de_solicitud().count("llaves"), 1)
        self.assertEqual(repositorio.ubicacion_de_llaves(), UBICACIONES_ESPERADAS)

    def test_fr021_una_copia_con_una_sala_inexistente_se_vuelve_a_pedir(self):
        self.iniciar(FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA))
        (self.carpeta_cache / "criptas" / "cripta-01" / "llaves.json").write_text(
            json.dumps({"llaves": [{"id": "itm_llave_bronce", "sala": 99}]}), encoding="utf-8")
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)

        repositorio = self.iniciar(fuente)

        self.assertEqual(fuente.tipos_de_solicitud().count("llaves"), 1)
        self.assertEqual(repositorio.ubicacion_de_llaves(), UBICACIONES_ESPERADAS)

    def test_fr022_una_copia_de_otra_version_no_se_usa(self):
        self.iniciar(FuenteCriptaFalsa(llaves=[{"id": "itm_llave_vieja", "sala": 1}]))
        fuente = FuenteCriptaFalsa(generales=dict(GENERALES_CRIPTA_01, version="nueva"),
                                   llaves=LLAVES_DE_PRUEBA)

        repositorio = self.iniciar(fuente)

        self.assertEqual(fuente.tipos_de_solicitud().count("llaves"), 1)
        self.assertEqual(repositorio.ubicacion_de_llaves(), UBICACIONES_ESPERADAS)

    def test_fr015_fr025_en_modo_offline_se_lee_del_paquete_sin_solicitudes(self):
        fuente = FuenteOffline(self.paquete_offline_de_cripta_01(con_llaves=True))

        repositorio = self.iniciar(fuente)

        self.assertEqual(fuente.solicitudes_realizadas(), 0)
        self.assertEqual(repositorio.ubicacion_de_llaves(), UBICACIONES_ESPERADAS)
        self.assertEqual(self.linea_del_reporte(repositorio), "Ubicación de llaves: leída del paquete offline")

    def test_fr019_servicio_disco_y_paquete_offline_dan_la_misma_ubicacion(self):
        del_servicio = self.iniciar(FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)).ubicacion_de_llaves()
        del_disco = self.iniciar(FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)).ubicacion_de_llaves()
        repositorio_offline = RepositorioCripta(
            FuenteOffline(self.paquete_offline_de_cripta_01(con_llaves=True)), self.carpeta / "otra_cache")
        repositorio_offline.empezar_conteo_de_partida()
        repositorio_offline.iniciar_partida("cripta-01")

        self.assertEqual(del_servicio, del_disco)
        self.assertEqual(del_servicio, repositorio_offline.ubicacion_de_llaves())

    def test_fr016_fr025_un_paquete_sin_ubicacion_avisa_y_la_partida_sigue(self):
        repositorio = self.iniciar(FuenteOffline(self.paquete_offline_de_cripta_01(con_llaves=False)))

        self.assertIsNone(repositorio.ubicacion_de_llaves())
        self.assertEqual(self.linea_del_reporte(repositorio), "Ubicación de llaves: no disponible")
        self.assertTrue(any("ubicación de las llaves no está disponible" in aviso
                            for aviso in repositorio.reporte_de_red().avisos))
        self.assertIsNotNone(repositorio.crear_mapa())

    def test_fr016_no_disponible_se_distingue_de_una_lista_vacia(self):
        repositorio = self.iniciar(FuenteCriptaFalsa(llaves=[]))

        self.assertEqual(repositorio.ubicacion_de_llaves(), [])

    def test_fr017_una_entrada_invalida_impide_iniciar(self):
        fuente = FuenteCriptaFalsa(llaves=[{"id": "itm_llave_bronce", "sala": 99}])

        with self.assertRaises(ErrorDatosCripta):
            self.iniciar(fuente)

    def test_fr020_si_la_consulta_falla_la_partida_no_inicia(self):
        with self.assertRaises(ErrorFuenteDatos) as contexto:
            self.iniciar(FuenteConConsultaDeLlavesFallida())

        self.assertIn("ubicación de las llaves", str(contexto.exception))

    def test_fr020_sin_presupuesto_para_la_consulta_la_partida_no_inicia(self):
        fuente = FuenteCriptaFalsa(generales=dict(GENERALES_CRIPTA_01, presupuesto_solicitudes=3))

        with self.assertRaises(PresupuestoAgotado):
            self.iniciar(fuente)

        self.assertEqual(fuente.solicitudes_realizadas(), 3)

    def test_fr011_fr025_al_cargar_una_partida_guardada_no_se_obtiene(self):
        fuente = FuenteCriptaFalsa(llaves=LLAVES_DE_PRUEBA)

        repositorio = self.iniciar(fuente, obtener_ubicacion_de_llaves=False)

        self.assertNotIn("llaves", fuente.tipos_de_solicitud())
        self.assertIsNone(repositorio.ubicacion_de_llaves())
        self.assertEqual(self.linea_del_reporte(repositorio), "Ubicación de llaves: no se obtuvo en esta partida")


class PruebasSpec004CargaYReproduccion(unittest.TestCase):

    def test_fr011_la_carga_de_una_partida_guardada_no_pide_la_ubicacion(self):
        repositorio = RepositorioQueAnotaElInicio()
        partida = SimpleNamespace(id_cripta="cripta-01")

        with mock.patch.object(application, "cargar_partida", return_value=partida):
            with self.assertRaises(VersionesIncompatibles):
                application.load_saved_game(repositorio, None, "partida.bin")

        self.assertEqual(repositorio.argumentos_con_nombre, {"obtener_ubicacion_de_llaves": False})

    def test_fr011_la_reproduccion_de_una_partida_nueva_pide_la_ubicacion(self):
        repositorio = RepositorioQueAnotaElInicio()
        log = SimpleNamespace(header=SimpleNamespace(
            crypt_id="cripta-01", crypt_version="v", catalog_version="c", saved_game=""))

        with mock.patch.object(application, "read_replay_log", return_value=log):
            application.replay(repositorio, "partida.log", output=lambda texto: None)

        self.assertEqual(repositorio.argumentos_con_nombre, {"obtener_ubicacion_de_llaves": True})

    def test_fr011_la_reproduccion_de_una_partida_cargada_no_pide_la_ubicacion(self):
        repositorio = RepositorioQueAnotaElInicio()
        log = SimpleNamespace(header=SimpleNamespace(
            crypt_id="cripta-01", crypt_version="v", catalog_version="c", saved_game="partida.bin"))

        with mock.patch.object(application, "read_replay_log", return_value=log):
            application.replay(repositorio, "partida.log", output=lambda texto: None)

        self.assertEqual(repositorio.argumentos_con_nombre, {"obtener_ubicacion_de_llaves": False})


class PruebasSpec004VersionesYAvisos(unittest.TestCase):

    def test_fr023_costo_no_produce_aviso_de_campo_desconocido(self):
        traductor = traductor_sin_catalogo()

        traductor.crear_mapa([
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "costo": 120}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1, "costo": 120}}},
        ])

        self.assertEqual(traductor.avisos, [])

    def test_fr024_un_campo_inventado_en_una_salida_avisa_una_sola_vez(self):
        traductor = traductor_sin_catalogo()

        traductor.crear_mapa([
            {"id": 1, "nombre": "A", "salidas": {"N": {"sala": 2, "inventado": 1}}},
            {"id": 2, "nombre": "B", "salidas": {"S": {"sala": 1, "inventado": 1}}},
        ])

        avisos_del_campo = [aviso for aviso in traductor.avisos if "inventado" in aviso]
        self.assertEqual(len(avisos_del_campo), 1)


if __name__ == "__main__":
    unittest.main()
