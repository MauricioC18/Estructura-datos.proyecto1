"""
Benchmark de la precarga de contenido (problema 4.2).

Compara, en el MISMO recorrido del jugador, tres estrategias:
    - BFS (decisión): pide las 10 salas sin contenido más cercanas cuando a
      la sala actual o a una vecina directa le falta contenido.
    - Solo vecinos directos (alternativa descartada): pide la sala actual y
      sus vecinas directas (a lo sumo 5 salas por solicitud).
    - Sin precarga (referencia): pide cada sala justo al intentar entrar.

No mide tiempo sino lo que importa en este problema:
    - solicitudes de contenido: gastan presupuesto (§5.1);
    - esperas en la puerta: veces que el jugador tuvo que esperar ~400 ms
      al cruzar una puerta porque el contenido no estaba listo (§4.2).

Los recorridos usan una semilla fija, así que los resultados son exactos y
se repiten igual en cualquier computadora.

Ejecutar desde la carpeta cripta/:  python -m benchmark.bench_precarga_contenido
"""
import random

from adapters.fuente_datos import MAXIMO_POR_LOTE, FuenteDatos, validar_ids_salas
from benchmark.utilidades_medicion import Measurement
from structures.grafo_salas import construir_grafo_desde_esqueleto
from structures.tabla_hash import TablaHash
from tests.datos_cripta_01 import SALAS_CRIPTA_01, salas_de_cuadricula
from repository.gestor_contenido import GestorContenido

PASOS_DEL_RECORRIDO_ALEATORIO = 300
SEMILLA = 2026


class FuenteDeContenidoSimulada(FuenteDatos):
    """Responde contenido vacío para cualquier sala y cuenta las solicitudes."""

    def contenido(self, id_cripta, ids_salas):
        validar_ids_salas(ids_salas)
        self._consumir_solicitud("descargar contenido")
        return {"contenido": [{"sala": id_sala} for id_sala in ids_salas]}

    def listar_criptas(self): raise NotImplementedError
    def datos_generales(self, id_cripta): raise NotImplementedError
    def version_cripta(self, id_cripta): raise NotImplementedError
    def pagina_salas(self, id_cripta, pagina): raise NotImplementedError
    def catalogo(self, ids): raise NotImplementedError
    def version_catalogo(self): raise NotImplementedError


class PrecargaSoloVecinosDirectos(GestorContenido):
    """Alternativa descartada: la sala actual y sus vecinas directas."""

    def _elegir_salas_para_lote(self, origen):
        lote = []
        for sala in [origen] + self._grafo.vecinos(origen):
            if (self._grafo.contiene_sala(sala) and not self.tiene_contenido(sala)
                    and sala not in lote):
                lote.append(sala)
        return lote[:MAXIMO_POR_LOTE]


class SinPrecarga(GestorContenido):
    """Referencia: cada sala se pide justo al intentar entrar."""

    def precargar_alrededor_de(self, sala_actual):
        return False

    def _elegir_salas_para_lote(self, origen):
        return [origen]


ESTRATEGIAS = (
    ("BFS (decisión)", GestorContenido),
    ("solo vecinos directos", PrecargaSoloVecinosDirectos),
    ("sin precarga", SinPrecarga),
)


def simular_recorrido(clase_gestor, salas, sala_inicial, camino=None,
                      pasos=PASOS_DEL_RECORRIDO_ALEATORIO, semilla=SEMILLA):
    """Simula un jugador que recorre la cripta. Si no se da un camino, en
    cada paso elige al azar (con semilla fija) una salida de la sala actual.
    Devuelve (solicitudes, salas descargadas, esperas en la puerta, salas visitadas)."""
    grafo = construir_grafo_desde_esqueleto(salas)
    gestor = clase_gestor(FuenteDeContenidoSimulada(), "simulada", grafo)
    azar = random.Random(semilla)
    visitadas = TablaHash()

    # §2.4: el contenido de la sala inicial debe estar antes de la primera acción.
    gestor.precargar_alrededor_de(sala_inicial)
    gestor.asegurar_contenido(sala_inicial)
    actual = sala_inicial
    visitadas.insertar(actual, True)

    siguientes = camino if camino is not None else [None] * pasos
    for siguiente in siguientes:
        if siguiente is None:
            siguiente = azar.choice(grafo.vecinos(actual))
        gestor.asegurar_contenido(siguiente)  # antes de confirmar la entrada
        actual = siguiente
        visitadas.insertar(actual, True)
        gestor.precargar_alrededor_de(actual)  # después de la acción

    estadisticas = gestor.estadisticas()
    return (estadisticas.lotes_de_contenido, estadisticas.salas_descargadas,
            estadisticas.esperas_en_la_puerta, visitadas.tamano())


def escenarios():
    # En cripta-01: buscar la llave de bronce (sala 3), abrir el nicho (sala 5)
    # y luego ir a la salida (sala 6).
    yield ("cripta-01 real (6 salas), recorrido completo",
           SALAS_CRIPTA_01, 1, [2, 3, 2, 5, 2, 3, 4, 6])
    for lado in (10, 20, 30):
        yield (f"cuadrícula {lado}x{lado} ({lado * lado} salas), "
               f"{PASOS_DEL_RECORRIDO_ALEATORIO} pasos al azar",
               salas_de_cuadricula(lado, lado), (lado // 2) * lado + lado // 2 + 1, None)


def ejecutar():
    """Devuelve filas (escenario, estrategia, solicitudes, salas, esperas, visitadas)."""
    filas = []
    for nombre, salas, sala_inicial, camino in escenarios():
        for nombre_estrategia, clase in ESTRATEGIAS:
            resultado = simular_recorrido(clase, salas, sala_inicial, camino)
            filas.append((nombre, nombre_estrategia) + resultado)
    return filas


def imprimir(filas):
    print("Precarga de contenido: solicitudes y esperas en el mismo recorrido")
    escenario_actual = None
    for escenario, estrategia, solicitudes, salas, esperas, visitadas in filas:
        if escenario != escenario_actual:
            escenario_actual = escenario
            print()
            print(escenario)
            encabezado = (f"  {'estrategia':>22} | {'solicitudes':>11} | "
                          f"{'salas descargadas':>17} | {'esperas en la puerta':>20}")
            print(encabezado)
            print("  " + "-" * (len(encabezado) - 2))
        print(f"  {estrategia:>22} | {solicitudes:>11} | {salas:>17} | {esperas:>20}")
        if estrategia == ESTRATEGIAS[-1][0]:
            print(f"  (salas distintas visitadas: {visitadas})")


def run():
    """Mediciones de este módulo para el ejecutor de --bench. No son de
    tiempo: seconds es None y los conteos van en detail."""
    mediciones = []
    for escenario, estrategia, solicitudes, salas, esperas, visitadas in ejecutar():
        mediciones.append(Measurement(
            f"4.2 precarga: {estrategia}, {escenario}",
            None,
            f"{solicitudes} solicitudes, {salas} salas descargadas, "
            f"{esperas} esperas en la puerta, {visitadas} salas visitadas",
        ))
    return mediciones


if __name__ == "__main__":
    imprimir(ejecutar())
