"""
Benchmark de TablaHash (problemas 4.3 y 4.4: búsquedas en la caché).

Compara el tiempo promedio por búsqueda de:
    - TablaHash con crc32 ............ decisión
    - TablaHash con FNV-1a ........... alternativa descartada (función hash)
    - lista ordenada + búsqueda binaria  alternativa descartada (estructura)
    - búsqueda lineal ................ alternativa descartada (estructura)
    - dict de Python ................. solo referencia de medición; el
                                       programa no lo usa (§7)

La búsqueda con acierto (la clave existe) y con fallo (no existe) se miden
por separado, porque la caché hace las dos cosas.

Ejecutar desde la carpeta cripta/:  python -m benchmark.bench_tabla_hash
Más adelante, --bench puede llamar a ejecutar() e imprimir().
"""
import random

from benchmark.utilidades_medicion import (
    Measurement,
    calentar_procesador,
    descripcion_del_equipo,
    nanosegundos_por_operacion,
)
from structures.funciones_hash import hash_crc32, hash_fnv1a
from structures.tabla_hash import TablaHash

ESTRUCTURAS = (
    "TablaHash crc32",
    "TablaHash FNV-1a",
    "Lista ord.+binaria",
    "Lineal",
    "dict (referencia)",
)


def _busqueda_lineal(claves, valores, clave):
    for posicion in range(len(claves)):
        if claves[posicion] == clave:
            return valores[posicion]
    return None


def _busqueda_binaria(claves_ordenadas, valores, clave):
    izquierda = 0
    derecha = len(claves_ordenadas) - 1
    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        actual = claves_ordenadas[medio]
        if actual == clave:
            return valores[medio]
        if actual < clave:
            izquierda = medio + 1
        else:
            derecha = medio - 1
    return None


def ejecutar(tamanos=(25, 100, 1000, 10000), cantidad_consultas=20_000, semilla=2026):
    """Devuelve una lista de filas (n, estructura, ns_acierto, ns_fallo)."""
    azar = random.Random(semilla)
    filas = []
    calentar_procesador()
    for n in tamanos:
        # Se generan ya en orden alfabético (números con ceros a la izquierda),
        # así la lista ordenada no necesita ordenarse.
        claves = [f"ent_tipo_{i:05d}" for i in range(n)]
        valores = list(range(n))
        # Claves ausentes intercaladas entre las existentes.
        ausentes = [f"ent_tipo_{i:05d}x" for i in range(n)]

        tabla_crc32 = TablaHash(funcion_hash=hash_crc32)
        tabla_fnv = TablaHash(funcion_hash=hash_fnv1a)
        referencia = {}  # solo para medir; no se usa en el programa (§7)
        for clave, valor in zip(claves, valores):
            tabla_crc32.insertar(clave, valor)
            tabla_fnv.insertar(clave, valor)
            referencia[clave] = valor

        aciertos = [azar.choice(claves) for _ in range(cantidad_consultas)]
        fallos = [azar.choice(ausentes) for _ in range(cantidad_consultas)]
        # La búsqueda lineal es lenta con n grande: se usan menos consultas.
        limite_lineal = max(500, min(cantidad_consultas, 2_000_000 // n))

        buscadores = (
            (tabla_crc32.obtener, 5, cantidad_consultas),
            (tabla_fnv.obtener, 5, cantidad_consultas),
            (lambda c: _busqueda_binaria(claves, valores, c), 5, cantidad_consultas),
            (lambda c: _busqueda_lineal(claves, valores, c), 3, limite_lineal),
            (referencia.get, 5, cantidad_consultas),
        )
        for nombre, (buscar, repeticiones, limite) in zip(ESTRUCTURAS, buscadores):
            ns_acierto = nanosegundos_por_operacion(buscar, aciertos[:limite], repeticiones)
            ns_fallo = nanosegundos_por_operacion(buscar, fallos[:limite], repeticiones)
            filas.append((n, nombre, ns_acierto, ns_fallo))
    return filas


def imprimir(filas):
    print(descripcion_del_equipo())
    tamanos = []
    for fila in filas:
        if fila[0] not in tamanos:
            tamanos.append(fila[0])
    for titulo, columna in (("acierto (la clave existe)", 2), ("fallo (la clave no existe)", 3)):
        print()
        print(f"Búsqueda con {titulo}, en nanosegundos por búsqueda")
        encabezado = f"{'n':>6}"
        for nombre in ESTRUCTURAS:
            encabezado += f" | {nombre:>18}"
        print(encabezado)
        print("-" * len(encabezado))
        for n in tamanos:
            linea = f"{n:>6}"
            for nombre in ESTRUCTURAS:
                for fila in filas:
                    if fila[0] == n and fila[1] == nombre:
                        linea += f" | {fila[columna]:>18.0f}"
            print(linea)


def run():
    """Mediciones de este módulo para el ejecutor de --bench."""
    mediciones = []
    for n, estructura, ns_acierto, ns_fallo in ejecutar():
        mediciones.append(Measurement(
            f"4.3/4.4 búsqueda por clave: {estructura}, {n} claves",
            ns_acierto / 1e9,
            f"tiempo por búsqueda con acierto; con fallo: {ns_fallo:.0f} ns",
        ))
    return mediciones


if __name__ == "__main__":
    imprimir(ejecutar())
