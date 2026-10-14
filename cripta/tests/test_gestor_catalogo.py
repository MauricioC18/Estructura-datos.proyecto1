"""
Pruebas de GestorCatalogo (memoria, disco y red).

Se usa una fuente simulada con las 11 fichas reales de cripta-01, que
registra cada lote pedido, y un AlmacenFichas real en una carpeta temporal.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import tempfile
import unittest
from pathlib import Path

from adapters.almacen_fichas import AlmacenFichas, ErrorAlmacenDisco
from adapters.fuente_datos import FuenteDatos, PresupuestoAgotado, validar_ids_catalogo
from structures.cache_catalogo import CacheCatalogo
from tests.datos_cripta_01 import FICHAS_CRIPTA_01, VERSION_CATALOGO_REAL
from repository.gestor_catalogo import FichaNoDisponible, GestorCatalogo

VERSION = VERSION_CATALOGO_REAL

# Los ids en el orden en que aparecen en el contenido de las salas 1 a 6.
IDS_CRIPTA_01 = [ficha["id"] for ficha in FICHAS_CRIPTA_01]


class FuenteCatalogoFalsa(FuenteDatos):
    """Sirve el catálogo desde una lista y anota cada lote pedido."""

    def __init__(self, fichas=FICHAS_CRIPTA_01, version=VERSION):
        super().__init__()
        self.fichas = list(fichas)
        self.version = version
        self.lotes_pedidos = []

    def version_catalogo(self):
        self._consumir_solicitud("obtener la versión del catálogo")
        return {"version": self.version}

    def catalogo(self, ids):
        validar_ids_catalogo(ids)  # falla si un lote supera 10 o repite ids
        self._consumir_solicitud("descargar fichas")
        self.lotes_pedidos.append(list(ids))
        return {"entidades": [ficha for ficha in self.fichas if ficha["id"] in ids]}

    # El gestor no usa estas operaciones.
    def listar_criptas(self): raise NotImplementedError
    def datos_generales(self, id_cripta): raise NotImplementedError
    def version_cripta(self, id_cripta): raise NotImplementedError
    def pagina_salas(self, id_cripta, pagina): raise NotImplementedError
    def contenido(self, id_cripta, ids_salas): raise NotImplementedError


class AlmacenQueNoPuedeGuardar(AlmacenFichas):
    """Simula un disco bloqueado (por ejemplo, por OneDrive)."""

    def guardar_fichas(self, fichas):
        raise ErrorAlmacenDisco("guardar fichas del catálogo en disco", "archivo bloqueado")


class PruebasGestorCatalogo(unittest.TestCase):

    def setUp(self):
        self._carpeta_temporal = tempfile.TemporaryDirectory()
        self.carpeta = Path(self._carpeta_temporal.name)

    def tearDown(self):
        self._carpeta_temporal.cleanup()

    def crear_gestor(self, fuente=None, capacidad=25, clase_almacen=AlmacenFichas):
        fuente = fuente if fuente is not None else FuenteCatalogoFalsa()
        gestor = GestorCatalogo(fuente, clase_almacen(self.carpeta), CacheCatalogo(capacidad))
        gestor.iniciar()
        return gestor, fuente

    # --- inicio ------------------------------------------------------

    def test_iniciar_pide_la_version_una_vez(self):
        gestor, fuente = self.crear_gestor()
        self.assertEqual(gestor.version_catalogo(), VERSION)
        self.assertEqual(fuente.solicitudes_realizadas(), 1)

    def test_hay_que_iniciar_antes_de_usar(self):
        gestor = GestorCatalogo(FuenteCatalogoFalsa(), AlmacenFichas(self.carpeta), CacheCatalogo())
        with self.assertRaises(RuntimeError):
            gestor.obtener_ficha("ent_rata_gigante")
        with self.assertRaises(RuntimeError):
            gestor.asegurar_fichas(["ent_rata_gigante"])

    # --- asegurar y obtener ------------------------------------------

    def test_asegurar_descarga_y_obtener_no_usa_la_red(self):
        gestor, fuente = self.crear_gestor()
        gestor.asegurar_fichas(["ent_rata_gigante", "trp_dardos"])
        solicitudes = fuente.solicitudes_realizadas()
        self.assertEqual(gestor.obtener_ficha("ent_rata_gigante")["nombre"], "Rata gigante")
        self.assertEqual(gestor.obtener_ficha("trp_dardos")["daño"], 4)
        self.assertEqual(fuente.solicitudes_realizadas(), solicitudes)

    def test_lo_ya_disponible_no_se_vuelve_a_pedir(self):
        gestor, fuente = self.crear_gestor()
        gestor.asegurar_fichas(["ent_rata_gigante"])
        gestor.asegurar_fichas(["ent_rata_gigante"])
        self.assertEqual(len(fuente.lotes_pedidos), 1)

    def test_ids_repetidos_en_una_misma_llamada(self):
        gestor, fuente = self.crear_gestor()
        gestor.asegurar_fichas(["trp_dardos", "trp_dardos", "trp_dardos"])
        self.assertEqual(fuente.lotes_pedidos, [["trp_dardos"]])

    def test_obtener_sin_asegurar_es_un_error(self):
        gestor, _ = self.crear_gestor()
        with self.assertRaises(FichaNoDisponible):
            gestor.obtener_ficha("ent_rata_gigante")

    def test_ids_invalidos(self):
        gestor, _ = self.crear_gestor()
        for id_invalido in ("", None, 5):
            with self.assertRaises(ValueError):
                gestor.asegurar_fichas([id_invalido])
            with self.assertRaises(ValueError):
                gestor.anotar_ids_conocidos([id_invalido])

    def test_asegurar_lista_vacia_no_pide_nada(self):
        gestor, fuente = self.crear_gestor()
        gestor.asegurar_fichas([])
        self.assertEqual(fuente.lotes_pedidos, [])

    # --- armado de lotes (D4) ----------------------------------------

    def test_relleno_con_ids_conocidos(self):
        gestor, fuente = self.crear_gestor()
        gestor.anotar_ids_conocidos(IDS_CRIPTA_01)
        gestor.asegurar_fichas(["ent_guardian_oseo"])
        primer_lote = fuente.lotes_pedidos[0]
        self.assertEqual(len(primer_lote), 10)
        self.assertEqual(primer_lote[0], "ent_guardian_oseo")  # lo necesario va primero
        self.assertNotIn("ent_guardian_oseo", primer_lote[1:])

    def test_cripta_01_completa_cabe_en_dos_lotes(self):
        """Las 11 fichas reales: 2 solicitudes de catálogo, como en el análisis
        del presupuesto (7 de 9 en un arranque en frío)."""
        gestor, fuente = self.crear_gestor()
        gestor.anotar_ids_conocidos(IDS_CRIPTA_01)
        gestor.asegurar_fichas(["itm_antorcha"])            # sala 1
        gestor.asegurar_fichas(["ent_rata_gigante", "itm_daga_oxidada", "trp_dardos"])  # sala 2
        gestor.asegurar_fichas(IDS_CRIPTA_01)               # todo lo demás
        self.assertEqual(len(fuente.lotes_pedidos), 2)
        self.assertEqual(len(fuente.lotes_pedidos[0]), 10)
        self.assertEqual(len(fuente.lotes_pedidos[1]), 1)
        for id_ficha in IDS_CRIPTA_01:
            self.assertEqual(gestor.obtener_ficha(id_ficha)["id"], id_ficha)

    def test_mas_de_diez_necesarias_se_piden_en_varios_lotes(self):
        fichas = [{"id": f"itm_{i:02d}", "clase": "arma"} for i in range(23)]
        gestor, fuente = self.crear_gestor(FuenteCatalogoFalsa(fichas))
        gestor.asegurar_fichas([ficha["id"] for ficha in fichas])
        self.assertEqual([len(lote) for lote in fuente.lotes_pedidos], [10, 10, 3])

    def test_lo_que_suelta_un_enemigo_queda_como_relleno(self):
        gestor, fuente = self.crear_gestor()
        gestor.asegurar_fichas(["ent_rata_gigante"])     # suelta itm_pocion_menor
        self.assertEqual(fuente.lotes_pedidos[0], ["ent_rata_gigante"])
        gestor.asegurar_fichas(["trp_dardos"])
        self.assertEqual(fuente.lotes_pedidos[1], ["trp_dardos", "itm_pocion_menor"])

    def test_los_lotes_son_deterministas(self):
        lotes = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as carpeta:
                fuente = FuenteCatalogoFalsa()
                gestor = GestorCatalogo(fuente, AlmacenFichas(carpeta), CacheCatalogo(3))
                gestor.iniciar()
                gestor.anotar_ids_conocidos(list(reversed(IDS_CRIPTA_01)))
                gestor.asegurar_fichas(["trp_dardos"])
                gestor.asegurar_fichas(IDS_CRIPTA_01)
                lotes.append(fuente.lotes_pedidos)
        self.assertEqual(lotes[0], lotes[1])

    # --- memoria y disco ---------------------------------------------

    def test_cache_pequena_recupera_desde_disco(self):
        gestor, fuente = self.crear_gestor(capacidad=2)
        gestor.asegurar_fichas(IDS_CRIPTA_01)
        solicitudes = fuente.solicitudes_realizadas()
        for id_ficha in IDS_CRIPTA_01:
            self.assertEqual(gestor.obtener_ficha(id_ficha)["id"], id_ficha)
        estadisticas = gestor.estadisticas()
        self.assertGreater(estadisticas.recuperaciones_desde_disco, 0)
        self.assertGreater(estadisticas.desalojos_de_memoria, 0)
        self.assertEqual(fuente.solicitudes_realizadas(), solicitudes)  # nada de red

    def test_arranque_en_caliente_no_descarga_fichas(self):
        gestor, _ = self.crear_gestor()
        gestor.asegurar_fichas(IDS_CRIPTA_01)

        otra_ejecucion, fuente = self.crear_gestor()  # misma carpeta, memoria vacía
        otra_ejecucion.asegurar_fichas(IDS_CRIPTA_01)
        self.assertEqual(fuente.lotes_pedidos, [])
        self.assertEqual(fuente.solicitudes_realizadas(), 1)  # solo la versión
        otra_ejecucion.obtener_ficha("ent_guardian_oseo")
        self.assertEqual(otra_ejecucion.estadisticas().recuperaciones_desde_disco, 1)

    def test_cambio_de_version_vuelve_a_descargar(self):
        gestor, _ = self.crear_gestor()
        gestor.asegurar_fichas(["ent_rata_gigante"])

        otra, fuente = self.crear_gestor(FuenteCatalogoFalsa(version="version-nueva"))
        otra.asegurar_fichas(["ent_rata_gigante"])
        self.assertEqual(len(fuente.lotes_pedidos), 1)
        avisos = otra.estadisticas().avisos
        self.assertTrue(any("versión del catálogo" in aviso for aviso in avisos))

    def test_reiniciar_con_otra_version_vacia_la_memoria(self):
        fuente = FuenteCatalogoFalsa()
        gestor = GestorCatalogo(fuente, AlmacenFichas(self.carpeta), CacheCatalogo())
        gestor.iniciar()
        gestor.asegurar_fichas(["ent_rata_gigante"])
        fuente.version = "version-nueva"
        gestor.iniciar()
        gestor.asegurar_fichas(["ent_rata_gigante"])
        self.assertEqual(len(fuente.lotes_pedidos), 2)

    def test_si_el_disco_falla_el_juego_sigue(self):
        gestor, fuente = self.crear_gestor(capacidad=1, clase_almacen=AlmacenQueNoPuedeGuardar)
        gestor.asegurar_fichas(["ent_rata_gigante", "trp_dardos", "itm_antorcha"])
        # Con capacidad 1, dos fichas se desalojaron de la caché y no están en disco.
        for id_ficha in ("ent_rata_gigante", "trp_dardos", "itm_antorcha"):
            self.assertEqual(gestor.obtener_ficha(id_ficha)["id"], id_ficha)
        estadisticas = gestor.estadisticas()
        self.assertEqual(estadisticas.fallos_al_guardar_en_disco, 1)
        self.assertTrue(any("solo en memoria" in aviso for aviso in estadisticas.avisos))
        self.assertEqual(len(fuente.lotes_pedidos), 1)

    # --- errores de red ----------------------------------------------

    def test_presupuesto_agotado_llega_a_quien_llama(self):
        fuente = FuenteCatalogoFalsa()
        gestor, _ = self.crear_gestor(fuente)
        fuente.establecer_presupuesto(1)  # ya se usó para la versión
        with self.assertRaises(PresupuestoAgotado):
            gestor.asegurar_fichas(["ent_rata_gigante"])

    def test_id_que_el_api_no_devuelve(self):
        gestor, _ = self.crear_gestor()
        with self.assertRaises(FichaNoDisponible) as contexto:
            gestor.asegurar_fichas(["itm_que_no_existe"])
        self.assertEqual(contexto.exception.id_ficha, "itm_que_no_existe")

    # --- estadísticas para el reporte (§5.1) --------------------------

    def test_aciertos_y_fallos_de_cache(self):
        gestor, _ = self.crear_gestor(capacidad=2)
        gestor.anotar_ids_conocidos(IDS_CRIPTA_01)
        gestor.asegurar_fichas(["ent_rata_gigante", "trp_dardos"])
        # La caché de 2 quedó con las dos últimas fichas del lote, así que la
        # rata viene del disco la primera vez y de memoria la segunda.
        gestor.obtener_ficha("ent_rata_gigante")
        gestor.obtener_ficha("ent_rata_gigante")
        estadisticas = gestor.estadisticas()
        self.assertEqual(estadisticas.fallos_de_cache(), 2)   # las 2 necesarias
        self.assertEqual(estadisticas.fichas_descargadas, 10)  # incluye el relleno
        self.assertEqual(estadisticas.lotes_de_catalogo_descargados, 1)
        self.assertEqual(estadisticas.aciertos_de_cache(), 2)
        self.assertEqual(estadisticas.version_catalogo, VERSION)


if __name__ == "__main__":
    unittest.main()
