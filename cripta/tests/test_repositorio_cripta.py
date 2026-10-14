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
from repository.repositorio_cripta import RepositorioCripta, VersionesIncompatibles

# Recorrido completo de cripta-01: buscar la llave de bronce (3), abrir el
# nicho (5), volver y salir por la 6. Solo las pruebas conocen estos ids (§9).
RECORRIDO_COMPLETO = [2, 3, 2, 5, 2, 3, 4, 6]


class FuenteCriptaFalsa(FuenteDatos):
    """Sirve cripta-01 completa y anota cada solicitud por tipo."""

    def __init__(self, generales=None, version_catalogo=VERSION_CATALOGO_REAL):
        super().__init__()
        self.generales = dict(generales or GENERALES_CRIPTA_01)
        self.version = version_catalogo
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
        return {"entidades": [ficha for ficha in FICHAS_CRIPTA_01 if ficha["id"] in ids]}

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
        # Las fichas están en disco: pedir una no usa la red.
        self.assertEqual(repositorio.obtener_ficha("ent_guardian_oseo")["vida_max"], 20)
        self.assertEqual(repositorio.reporte_de_red().recuperaciones_desde_disco, 1)
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


if __name__ == "__main__":
    unittest.main()
