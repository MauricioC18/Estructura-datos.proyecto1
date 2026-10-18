"""
Pruebas del benchmark de frecuencias del bloque 2.

Los conteos son deterministas, así que se pueden comprobar exactos: si
cambian, cambió el comportamiento del bloque 2 y hay que actualizar las
cifras del Documento de Decisiones (secciones 4.2 a 4.4).
"""
import unittest

from benchmark.bench_frecuencia_bloque2 import (
    CatalogoLotesSinRelleno,
    CatalogoUnaFichaPorSolicitud,
    FuenteCripta01,
    FuenteCriptaSintetica,
    recorrer,
    run,
)


class PruebasFrecuenciaBloque2(unittest.TestCase):

    def test_cripta_01_coincide_con_la_medicion_contra_el_api_real(self):
        resultado = recorrer(FuenteCripta01(), 20)

        # Las mismas cifras que dio el API real el 14 de octubre.
        self.assertEqual(resultado.solicitudes, 7)
        self.assertEqual(resultado.lotes_de_contenido, 1)
        self.assertEqual(resultado.lotes_de_catalogo, 2)
        self.assertEqual(resultado.fichas_descargadas, 11)
        self.assertEqual(resultado.fallos_de_cache, 2)
        self.assertEqual(resultado.aciertos_en_memoria, 16)
        self.assertEqual(resultado.esperas_en_la_puerta, 0)
        self.assertEqual((resultado.acciones, resultado.movimientos_rechazados), (20, 0))

    def test_buscar_es_mucho_mas_frecuente_que_insertar(self):
        resultado = recorrer(FuenteCriptaSintetica(8), 60)

        self.assertGreater(resultado.busquedas_en_memoria, 5 * resultado.inserciones_en_memoria)
        self.assertEqual(resultado.revisiones_de_precarga, resultado.acciones + 1)

    def test_con_cache_chica_hay_desalojos_y_lecturas_de_disco(self):
        resultado = recorrer(FuenteCripta01(), 20, capacidad=5)

        self.assertGreater(resultado.desalojos, 0)
        self.assertGreater(resultado.lecturas_de_disco, 0)
        self.assertEqual(resultado.solicitudes, 7)  # liberar memoria nunca cuesta red

    def test_sin_relleno_no_alcanza_el_presupuesto_de_cripta_01(self):
        resultado = recorrer(FuenteCripta01(), 20, clase_de_catalogo=CatalogoLotesSinRelleno)

        self.assertEqual(resultado.solicitudes, 9)
        self.assertGreater(resultado.movimientos_rechazados, 0)

    def test_una_ficha_por_solicitud_no_sale_de_la_sala_inicial(self):
        resultado = recorrer(FuenteCripta01(), 20, clase_de_catalogo=CatalogoUnaFichaPorSolicitud)

        self.assertEqual(resultado.acciones, 0)

    def test_estrategias_en_cripta_sintetica(self):
        con_relleno = recorrer(FuenteCriptaSintetica(8), 60)
        sin_relleno = recorrer(FuenteCriptaSintetica(8), 60, clase_de_catalogo=CatalogoLotesSinRelleno)
        una_por_una = recorrer(FuenteCriptaSintetica(8), 60, clase_de_catalogo=CatalogoUnaFichaPorSolicitud)

        self.assertLess(con_relleno.lotes_de_catalogo, sin_relleno.lotes_de_catalogo)
        self.assertLess(sin_relleno.lotes_de_catalogo, una_por_una.lotes_de_catalogo)
        self.assertEqual(una_por_una.lotes_de_catalogo, una_por_una.fichas_descargadas)

    def test_run_devuelve_conteos(self):
        mediciones = run()

        self.assertGreater(len(mediciones), 0)
        for medicion in mediciones:
            self.assertIsNone(medicion.seconds)


if __name__ == "__main__":
    unittest.main()
