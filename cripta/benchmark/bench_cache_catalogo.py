"""
Benchmark de CacheCatalogo (problema 4.4).

Compara dos formas de llevar el orden de uso de un LRU:
    - CacheCatalogo: lista doblemente enlazada + TablaHash (decisión)
    - CacheLRUConListaDePython: el orden se guarda en una list de Python
      (alternativa descartada); mover una ficha al frente exige buscarla en
      la lista y desplazar elementos, O(n).

Ambas usan la TablaHash para saber si una ficha está en memoria, así que la
diferencia que se mide es solo el costo de mantener el orden de uso.

Se miden dos operaciones con la caché llena:
    - obtener una ficha que está en memoria (acierto: la mueve al frente);
    - agregar una ficha nueva (obliga a liberar la usada hace más tiempo).

Nota: la tasa de aciertos de LRU contra FIFO se medirá con la traza de
accesos de una partida real cuando exista el motor del juego.

Ejecutar desde la carpeta cripta/:  python -m benchmark.bench_cache_catalogo
"""
import random
import time

from benchmark.utilidades_medicion import (
    Measurement,
    calentar_procesador,
    descripcion_del_equipo,
    nanosegundos_por_operacion,
)
from structures.cache_catalogo import CacheCatalogo
from structures.tabla_hash import TablaHash

CAPACIDADES = (25, 100, 1000, 5000)


class CacheLRUConListaDePython:
    """Alternativa descartada: mismo comportamiento LRU, pero el orden de uso
    vive en una list de Python (la más reciente en la posición 0)."""

    def __init__(self, capacidad_maxima):
        self._capacidad_maxima = capacidad_maxima
        self._ids_en_orden_de_uso = []
        self._fichas_por_id = TablaHash()

    def obtener_ficha(self, id_ficha):
        ficha = self._fichas_por_id.obtener(id_ficha)
        if ficha is None:
            return None
        self._ids_en_orden_de_uso.remove(id_ficha)     # busca y desplaza: O(n)
        self._ids_en_orden_de_uso.insert(0, id_ficha)  # desplaza todo: O(n)
        return ficha

    def agregar_ficha(self, id_ficha, ficha):
        if self._fichas_por_id.contiene(id_ficha):
            self._ids_en_orden_de_uso.remove(id_ficha)
        self._ids_en_orden_de_uso.insert(0, id_ficha)
        self._fichas_por_id.insertar(id_ficha, ficha)
        if len(self._ids_en_orden_de_uso) > self._capacidad_maxima:
            id_mas_viejo = self._ids_en_orden_de_uso.pop()
            self._fichas_por_id.eliminar(id_mas_viejo)


ALTERNATIVAS = (
    ("Lista doble (decisión)", CacheCatalogo),
    ("list de Python", CacheLRUConListaDePython),
)


def _cache_llena(crear_cache, capacidad):
    cache = crear_cache(capacidad)
    for i in range(capacidad):
        cache.agregar_ficha(f"ficha_{i:05d}", i)
    return cache


def _medir_agregar_con_desalojo(crear_cache, capacidad, cantidad, repeticiones=5):
    """Cada repetición parte de una caché llena nueva; solo se mide el ciclo."""
    ids_nuevos = [f"nueva_{i:06d}" for i in range(cantidad)]
    mejor = None
    for _ in range(repeticiones):
        cache = _cache_llena(crear_cache, capacidad)
        inicio = time.perf_counter()
        for id_ficha in ids_nuevos:
            cache.agregar_ficha(id_ficha, id_ficha)
        total = time.perf_counter() - inicio
        if mejor is None or total < mejor:
            mejor = total
    return mejor / cantidad * 1e9


def ejecutar(capacidades=CAPACIDADES, cantidad_operaciones=20_000, semilla=2026):
    """Devuelve filas (capacidad, alternativa, ns_obtener, ns_agregar_con_desalojo)."""
    azar = random.Random(semilla)
    filas = []
    calentar_procesador()
    for capacidad in capacidades:
        consultas = [f"ficha_{azar.randrange(capacidad):05d}" for _ in range(cantidad_operaciones)]
        for nombre, crear_cache in ALTERNATIVAS:
            cache = _cache_llena(crear_cache, capacidad)
            ns_obtener = nanosegundos_por_operacion(cache.obtener_ficha, consultas)
            ns_agregar = _medir_agregar_con_desalojo(crear_cache, capacidad, cantidad_operaciones // 4)
            filas.append((capacidad, nombre, ns_obtener, ns_agregar))
    return filas


def imprimir(filas):
    print(descripcion_del_equipo())
    print()
    print("Caché llena, en nanosegundos por operación")
    encabezado = (f"{'capacidad':>9} | {'alternativa':>22} | "
                  f"{'obtener (acierto)':>17} | {'agregar con desalojo':>20}")
    print(encabezado)
    print("-" * len(encabezado))
    for capacidad, nombre, ns_obtener, ns_agregar in filas:
        print(f"{capacidad:>9} | {nombre:>22} | {ns_obtener:>17.0f} | {ns_agregar:>20.0f}")


def run():
    """Mediciones de este módulo para el ejecutor de --bench."""
    mediciones = []
    for capacidad, alternativa, ns_obtener, ns_agregar in ejecutar():
        mediciones.append(Measurement(
            f"4.4 caché LRU: {alternativa}, capacidad {capacidad}",
            ns_obtener / 1e9,
            f"tiempo por obtener con acierto; agregar con desalojo: {ns_agregar:.0f} ns",
        ))
    return mediciones


if __name__ == "__main__":
    imprimir(ejecutar())
