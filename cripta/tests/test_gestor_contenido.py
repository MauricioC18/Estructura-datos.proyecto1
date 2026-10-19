"""
Pruebas de GestorContenido (precarga por BFS).

Se usa una fuente simulada que sirve el contenido real de cripta-01 (o
contenido vacío para cuadrículas sintéticas) y anota cada lote pedido.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import unittest

from adapters.fuente_datos import FuenteDatos, PresupuestoAgotado, validar_ids_salas
from structures.grafo_salas import construir_grafo_desde_esqueleto
from tests.datos_cripta_01 import CONTENIDO_CRIPTA_01, SALAS_CRIPTA_01, salas_de_cuadricula
from repository.gestor_contenido import (
    RESERVA_DE_SOLICITUDES,
    ContenidoNoDisponible,
    GestorContenido,
    descargar_salas_del_esqueleto,
    tipos_de_la_sala,
)


class FuenteContenidoFalsa(FuenteDatos):
    """Sirve contenido y esqueleto, y anota cada lote pedido."""

    def __init__(self, contenido=CONTENIDO_CRIPTA_01, salas_que_faltan=()):
        super().__init__()
        self.contenido_conocido = list(contenido)
        self.salas_que_faltan = list(salas_que_faltan)  # el "API" las omite
        self.lotes_pedidos = []
        self.paginas = []

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)  # falla si el lote supera 10 o repite salas
        self._consumir_solicitud("descargar contenido")
        self.lotes_pedidos.append(list(ids_salas))
        entradas = []
        for id_sala in ids_salas:
            if id_sala in self.salas_que_faltan:
                continue
            encontrada = None
            for entrada in self.contenido_conocido:
                if entrada["sala"] == id_sala:
                    encontrada = entrada
            entradas.append(encontrada or {"sala": id_sala, "enemigos": [], "objetos": [], "trampas": []})
        return {"contenido": entradas}

    def pagina_salas(self, id_cripta, pagina):
        self._consumir_solicitud("descargar página")
        return self.paginas[pagina - 1]

    def listar_criptas(self): raise NotImplementedError
    def datos_generales(self, id_cripta): raise NotImplementedError
    def version_cripta(self, id_cripta): raise NotImplementedError
    def catalogo(self, ids): raise NotImplementedError
    def version_catalogo(self): raise NotImplementedError


class CatalogoQueAnota:
    """Sustituye al GestorCatalogo: solo recuerda los ids anotados."""

    def __init__(self):
        self.ids_anotados = []

    def anotar_ids_conocidos(self, ids):
        self.ids_anotados.extend(ids)


def crear_gestor_cripta_01(fuente=None, catalogo=None):
    fuente = fuente if fuente is not None else FuenteContenidoFalsa()
    grafo = construir_grafo_desde_esqueleto(SALAS_CRIPTA_01)
    return GestorContenido(fuente, "cripta-01", grafo, catalogo), fuente


class PruebasCripta01(unittest.TestCase):

    def test_una_sola_solicitud_para_toda_la_cripta(self):
        gestor, fuente = crear_gestor_cripta_01()
        self.assertTrue(gestor.precargar_alrededor_de(1))
        self.assertEqual(fuente.lotes_pedidos, [[1, 2, 3, 5, 4, 6]])  # orden BFS
        for sala in (2, 3, 4, 6, 5):  # el jugador recorre la cripta
            gestor.asegurar_contenido(sala)
            self.assertFalse(gestor.precargar_alrededor_de(sala))
        self.assertEqual(len(fuente.lotes_pedidos), 1)
        self.assertEqual(gestor.estadisticas().esperas_en_la_puerta, 0)

    def test_contenido_de_sala_es_el_del_api(self):
        gestor, _ = crear_gestor_cripta_01()
        gestor.precargar_alrededor_de(1)
        sala_4 = gestor.contenido_de_sala(4)
        self.assertEqual(sala_4["enemigos"][0]["tipo"], "ent_guardian_oseo")

    def test_contenido_sin_asegurar_es_un_error(self):
        gestor, _ = crear_gestor_cripta_01()
        with self.assertRaises(ContenidoNoDisponible):
            gestor.contenido_de_sala(1)

    def test_asegurar_sin_precarga_cuenta_una_espera(self):
        gestor, fuente = crear_gestor_cripta_01()
        gestor.asegurar_contenido(4)
        self.assertEqual(fuente.lotes_pedidos[0][0], 4)  # el lote empieza por la sala pedida
        self.assertEqual(gestor.estadisticas().esperas_en_la_puerta, 1)
        gestor.asegurar_contenido(4)
        self.assertEqual(gestor.estadisticas().esperas_en_la_puerta, 1)

    def test_anota_los_tipos_en_el_catalogo(self):
        catalogo = CatalogoQueAnota()
        gestor, _ = crear_gestor_cripta_01(catalogo=catalogo)
        gestor.precargar_alrededor_de(1)
        self.assertEqual(catalogo.ids_anotados[:4],
                         ["itm_antorcha", "ent_rata_gigante", "ent_rata_gigante", "itm_daga_oxidada"])
        self.assertIn("ent_guardian_oseo", catalogo.ids_anotados)
        self.assertIn("trp_dardos", catalogo.ids_anotados)

    def test_tipos_de_la_sala_con_listas_faltantes(self):
        self.assertEqual(tipos_de_la_sala({"sala": 9}), [])
        self.assertEqual(tipos_de_la_sala({"sala": 9, "objetos": ["itm_antorcha"]}), ["itm_antorcha"])


class PruebasPersistencia(unittest.TestCase):

    def test_contenido_guardado_no_se_vuelve_a_pedir(self):
        gestor, fuente = crear_gestor_cripta_01()
        gestor.incorporar_contenido_guardado(CONTENIDO_CRIPTA_01)
        self.assertFalse(gestor.precargar_alrededor_de(1))
        gestor.asegurar_contenido(6)
        self.assertEqual(fuente.lotes_pedidos, [])
        self.assertEqual(gestor.estadisticas().salas_recuperadas_de_disco, 6)

    def test_guardado_parcial_solo_pide_lo_que_falta(self):
        gestor, fuente = crear_gestor_cripta_01()
        gestor.incorporar_contenido_guardado(CONTENIDO_CRIPTA_01[:3])  # salas 1, 2 y 3
        gestor.precargar_alrededor_de(1)  # falta nada alrededor de 1
        gestor.precargar_alrededor_de(2)  # falta la 5, vecina de 2
        self.assertEqual(fuente.lotes_pedidos, [[5, 4, 6]])

    def test_entradas_guardadas_invalidas_se_ignoran(self):
        gestor, _ = crear_gestor_cripta_01()
        gestor.incorporar_contenido_guardado([{"sin_sala": True}, {"sala": "1"}, {"sala": 99}, "texto"])
        self.assertEqual(gestor.estadisticas().salas_recuperadas_de_disco, 0)

    def test_avisa_que_guardar_con_las_entradas_nuevas(self):
        guardadas = []
        grafo = construir_grafo_desde_esqueleto(SALAS_CRIPTA_01)
        fuente = FuenteContenidoFalsa()
        gestor = GestorContenido(fuente, "cripta-01", grafo, guardar_contenido=guardadas.append)
        gestor.incorporar_contenido_guardado(CONTENIDO_CRIPTA_01[:1])  # la sala 1 ya estaba
        gestor.precargar_alrededor_de(1)
        self.assertEqual(len(guardadas), 1)
        self.assertEqual([entrada["sala"] for entrada in guardadas[0]], [2, 3, 5, 4, 6])


class PruebasCriptaGrande(unittest.TestCase):

    def setUp(self):
        self.ancho = 10
        self.grafo = construir_grafo_desde_esqueleto(salas_de_cuadricula(self.ancho, 10))
        self.fuente = FuenteContenidoFalsa(contenido=[])
        self.gestor = GestorContenido(self.fuente, "cripta-grande", self.grafo)

    def test_lotes_de_diez_sin_repetir_salas(self):
        actual = 1
        self.gestor.precargar_alrededor_de(actual)
        # Recorre la primera fila y baja por la última columna.
        camino = list(range(2, 11)) + [20, 30, 40, 50, 60, 70, 80, 90, 100]
        for sala in camino:
            self.gestor.asegurar_contenido(sala)
            self.gestor.precargar_alrededor_de(sala)
        pedidas = [sala for lote in self.fuente.lotes_pedidos for sala in lote]
        self.assertEqual(len(pedidas), len(set(pedidas)))  # ninguna sala dos veces (§4.2)
        for lote in self.fuente.lotes_pedidos:
            self.assertLessEqual(len(lote), 10)
        self.assertEqual(self.gestor.estadisticas().esperas_en_la_puerta, 0)

    def test_dentro_de_la_zona_ya_cargada_no_pide_nada(self):
        self.gestor.precargar_alrededor_de(1)
        solicitudes = len(self.fuente.lotes_pedidos)
        self.gestor.asegurar_contenido(2)
        self.gestor.precargar_alrededor_de(2)  # 2 y sus vecinas ya están
        self.assertEqual(len(self.fuente.lotes_pedidos), solicitudes)


class PruebasPresupuesto(unittest.TestCase):

    def test_con_poco_presupuesto_la_precarga_se_detiene(self):
        gestor, fuente = crear_gestor_cripta_01()
        fuente.establecer_presupuesto(RESERVA_DE_SOLICITUDES)  # quedan justo las de reserva
        self.assertFalse(gestor.precargar_alrededor_de(1))
        self.assertEqual(fuente.lotes_pedidos, [])
        self.assertEqual(gestor.estadisticas().precargas_omitidas_por_presupuesto, 1)
        # Lo estrictamente necesario sí se pide.
        gestor.asegurar_contenido(1)
        self.assertEqual(len(fuente.lotes_pedidos), 1)

    def test_presupuesto_agotado_llega_a_quien_llama(self):
        gestor, fuente = crear_gestor_cripta_01()
        fuente.establecer_presupuesto(0)
        with self.assertRaises(PresupuestoAgotado):
            gestor.asegurar_contenido(1)
        self.assertFalse(gestor.tiene_contenido(1))


class PruebasErrores(unittest.TestCase):

    def test_sala_que_el_api_no_devuelve(self):
        gestor, _ = crear_gestor_cripta_01(FuenteContenidoFalsa(salas_que_faltan=[3]))
        gestor.asegurar_contenido(1)  # la 3 venía en el lote, pero el API la omitió
        self.assertFalse(gestor.tiene_contenido(3))
        with self.assertRaises(ContenidoNoDisponible):
            gestor.asegurar_contenido(3)

    def test_sala_que_no_esta_en_el_esqueleto(self):
        gestor, _ = crear_gestor_cripta_01()
        with self.assertRaises(ValueError):
            gestor.asegurar_contenido(99)


class PruebasDescargaDelEsqueleto(unittest.TestCase):

    def test_junta_todas_las_paginas(self):
        fuente = FuenteContenidoFalsa()
        fuente.paginas = [
            {"pagina": 1, "total_paginas": 2, "salas": SALAS_CRIPTA_01[:4]},
            {"pagina": 2, "total_paginas": 2, "salas": SALAS_CRIPTA_01[4:]},
        ]
        salas = descargar_salas_del_esqueleto(fuente, "cripta-01", 2)
        self.assertEqual([sala["id"] for sala in salas], [1, 2, 3, 4, 5, 6])
        self.assertEqual(fuente.solicitudes_realizadas(), 2)


if __name__ == "__main__":
    unittest.main()
