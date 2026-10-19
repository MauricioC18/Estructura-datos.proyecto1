"""
Funciones de medición compartidas por los benchmarks del bloque 2.

Usar las mismas funciones en todos los benchmarks garantiza que las cifras
del Documento de Decisiones se midieron de la misma forma.

Contrato con el ejecutor de --bench
    Cada benchmark expone run(), que devuelve una lista de Measurement con
    los mismos campos que usa benchmark/scheduler_bench.py: name, seconds y
    detail. Cuando una medición no es de tiempo (por ejemplo, la precarga,
    que cuenta solicitudes), seconds es None y los números van en detail.
"""
import platform
import sys
import time
from dataclasses import dataclass

from structures.tabla_hash import TablaHash


@dataclass
class Measurement:
    name: str
    seconds: float | None
    detail: str


def calentar_procesador(segundos=1.0):
    """Mantiene el procesador ocupado un momento antes de medir.

    Muchas computadoras (sobre todo portátiles) suben la frecuencia del
    procesador después de unos instantes de trabajo. Sin este paso, la
    primera medición de la corrida puede salir más lenta de lo real.
    """
    tabla = TablaHash()
    for i in range(100):
        tabla.insertar(f"k{i}", i)
    fin = time.perf_counter() + segundos
    while time.perf_counter() < fin:
        for i in range(100):
            tabla.obtener(f"k{i}")


def nanosegundos_por_operacion(operacion, argumentos, repeticiones=5):
    """Llama operacion(argumento) para cada argumento y devuelve el tiempo
    por llamada, tomando el mejor de varias repeticiones."""
    mejor = None
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        for argumento in argumentos:
            operacion(argumento)
        total = time.perf_counter() - inicio
        if mejor is None or total < mejor:
            mejor = total
    return mejor / len(argumentos) * 1e9


def descripcion_del_equipo():
    return f"Python {sys.version.split()[0]} en {platform.system()} {platform.machine()}"
