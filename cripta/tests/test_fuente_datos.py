"""
Pruebas del contrato FuenteDatos: validación de lotes, errores y
cuenta del presupuesto de solicitudes.

Ejecutar desde la carpeta cripta/:  python -m unittest discover -s tests -t . -v
"""
import unittest

from adapters.fuente_datos import (
    MAXIMO_POR_LOTE,
    ErrorFuenteDatos,
    FuenteDatos,
    PresupuestoAgotado,
    validar_ids_catalogo,
    validar_ids_salas,
)


class FuenteFalsa(FuenteDatos):
    """Fuente mínima para probar la cuenta: cada operación "envía" una solicitud."""

    def _solicitar(self, operacion):
        self._consumir_solicitud(operacion)
        return {}

    def listar_criptas(self):
        return self._solicitar("listar las criptas")

    def datos_generales(self, id_cripta):
        return self._solicitar(f"obtener los datos generales de {id_cripta}")

    def version_cripta(self, id_cripta):
        return self._solicitar(f"obtener la versión de {id_cripta}")

    def pagina_salas(self, id_cripta, pagina):
        return self._solicitar(f"descargar la página {pagina} de {id_cripta}")

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        return self._solicitar(f"descargar el contenido de las salas {ids_salas}")

    def catalogo(self, ids):
        validar_ids_catalogo(ids)
        return self._solicitar(f"descargar las fichas {ids}")

    def version_catalogo(self):
        return self._solicitar("obtener la versión del catálogo")


class PruebasValidacionLotes(unittest.TestCase):

    def test_lotes_validos(self):
        validar_ids_salas([1])
        validar_ids_salas(list(range(1, MAXIMO_POR_LOTE + 1)))
        validar_ids_catalogo(["ent_rata_gigante", "itm_antorcha"])

    def test_lote_vacio(self):
        with self.assertRaises(ValueError):
            validar_ids_salas([])
        with self.assertRaises(ValueError):
            validar_ids_catalogo([])

    def test_lote_mayor_al_maximo(self):
        with self.assertRaises(ValueError):
            validar_ids_salas(list(range(1, MAXIMO_POR_LOTE + 2)))

    def test_valores_repetidos(self):
        with self.assertRaises(ValueError):
            validar_ids_salas([3, 7, 3])
        with self.assertRaises(ValueError):
            validar_ids_catalogo(["itm_daga", "itm_daga"])

    def test_tipos_incorrectos(self):
        with self.assertRaises(TypeError):
            validar_ids_salas(["1"])
        with self.assertRaises(TypeError):
            validar_ids_salas([True])
        with self.assertRaises(TypeError):
            validar_ids_catalogo([5])
        with self.assertRaises(TypeError):
            validar_ids_salas((1, 2))  # debe ser una lista

    def test_id_de_catalogo_vacio(self):
        with self.assertRaises(ValueError):
            validar_ids_catalogo(["itm_antorcha", ""])


class PruebasErrores(unittest.TestCase):

    def test_mensaje_incluye_operacion_y_codigo(self):
        error = ErrorFuenteDatos("descargar la página 2 de cripta-01", "no existe", 404)
        self.assertIn("descargar la página 2 de cripta-01", str(error))
        self.assertIn("HTTP 404", str(error))

    def test_mensaje_sin_codigo_http(self):
        error = ErrorFuenteDatos("listar las criptas", "tiempo de espera agotado")
        self.assertNotIn("HTTP", str(error))

    def test_presupuesto_agotado_es_error_de_fuente(self):
        error = PresupuestoAgotado("listar las criptas", 9)
        self.assertIsInstance(error, ErrorFuenteDatos)
        self.assertEqual(error.presupuesto, 9)


class PruebasPresupuesto(unittest.TestCase):

    def test_no_se_puede_instanciar_el_contrato(self):
        with self.assertRaises(TypeError):
            FuenteDatos()

    def test_sin_presupuesto_no_hay_limite(self):
        fuente = FuenteFalsa()
        for _ in range(50):
            fuente.listar_criptas()
        self.assertEqual(fuente.solicitudes_realizadas(), 50)
        self.assertIsNone(fuente.presupuesto())
        self.assertIsNone(fuente.solicitudes_restantes())

    def test_las_solicitudes_previas_cuentan(self):
        fuente = FuenteFalsa()
        fuente.listar_criptas()
        fuente.datos_generales("cripta-01")
        fuente.establecer_presupuesto(9)
        self.assertEqual(fuente.solicitudes_restantes(), 7)

    def test_rechaza_al_agotar_el_presupuesto(self):
        fuente = FuenteFalsa()
        fuente.establecer_presupuesto(3)
        fuente.listar_criptas()
        fuente.datos_generales("cripta-01")
        fuente.version_catalogo()
        self.assertEqual(fuente.solicitudes_restantes(), 0)
        with self.assertRaises(PresupuestoAgotado):
            fuente.contenido("cripta-01", [1, 2])
        # La solicitud rechazada no se envía ni se cuenta.
        self.assertEqual(fuente.solicitudes_realizadas(), 3)

    def test_presupuesto_menor_a_lo_ya_gastado(self):
        fuente = FuenteFalsa()
        for _ in range(4):
            fuente.listar_criptas()
        fuente.establecer_presupuesto(2)
        self.assertEqual(fuente.solicitudes_restantes(), 0)
        with self.assertRaises(PresupuestoAgotado):
            fuente.version_catalogo()

    def test_presupuesto_cero(self):
        fuente = FuenteFalsa()
        fuente.establecer_presupuesto(0)
        with self.assertRaises(PresupuestoAgotado):
            fuente.listar_criptas()

    def test_presupuesto_negativo(self):
        with self.assertRaises(ValueError):
            FuenteFalsa().establecer_presupuesto(-1)

    def test_lote_invalido_no_gasta_presupuesto(self):
        fuente = FuenteFalsa()
        fuente.establecer_presupuesto(5)
        with self.assertRaises(ValueError):
            fuente.contenido("cripta-01", [1, 1])
        self.assertEqual(fuente.solicitudes_realizadas(), 0)

    def test_reiniciar_conteo_para_una_partida_nueva(self):
        fuente = FuenteFalsa()
        fuente.establecer_presupuesto(2)
        fuente.listar_criptas()
        fuente.listar_criptas()
        fuente.reiniciar_conteo()
        self.assertEqual(fuente.solicitudes_realizadas(), 0)
        self.assertIsNone(fuente.presupuesto())
        fuente.listar_criptas()  # ya no hay límite hasta conocer el nuevo presupuesto


if __name__ == "__main__":
    unittest.main()
