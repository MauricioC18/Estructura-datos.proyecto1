"""
Benchmark de AlmacenFichas (problema 4.4, decisión D6).

Mide cuánto cuesta recuperar UNA ficha que fue liberada de memoria, con
tres formas de guardar el catálogo en disco:
    - AlmacenFichas: datos + índice ordenado con búsqueda binaria (decisión)
    - un archivo JSON por ficha (alternativa descartada): usa las carpetas
      del sistema operativo como tabla de búsqueda y crea muchos archivos
    - un solo archivo JSON con todas las fichas (alternativa descartada):
      para recuperar una ficha hay que leer y convertir el archivo completo

También mide solo la búsqueda binaria en el índice, para mostrar que no es
lo que cuesta: lo caro es ir al disco.

Nota: después de la primera lectura, el sistema operativo guarda los
archivos en su propia memoria (caché de disco), así que esto mide el disco
"caliente", que es el caso normal durante una partida.

Ejecutar desde la carpeta cripta/:  python -m benchmark.bench_almacen_fichas
"""
import json
import random
import tempfile
from pathlib import Path

from adapters.almacen_fichas import AlmacenFichas
from benchmark.utilidades_medicion import (
    Measurement,
    calentar_procesador,
    descripcion_del_equipo,
    nanosegundos_por_operacion,
)

CANTIDADES_DE_FICHAS = (25, 100, 1000)
VERSION_DE_PRUEBA = "version-bench"


def _fichas_de_prueba(cantidad):
    """Fichas con el tamaño y la forma de las reales del catálogo."""
    return [
        {"id": f"ent_tipo_{i:05d}", "nombre": f"Criatura número {i}", "clase": "enemigo",
         "vida_max": 10 + i % 20, "ataque": 5, "defensa": 1, "velocidad": 100 + i % 60,
         "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]}
        for i in range(cantidad)
    ]


def _tamano_de_carpeta(carpeta):
    archivos = 0
    total_bytes = 0
    for ruta in Path(carpeta).rglob("*"):
        if ruta.is_file():
            archivos += 1
            total_bytes += ruta.stat().st_size
    return archivos, total_bytes


def _preparar_almacen(carpeta, fichas):
    almacen = AlmacenFichas(carpeta)
    almacen.abrir(VERSION_DE_PRUEBA)
    for inicio in range(0, len(fichas), 10):
        almacen.guardar_fichas(fichas[inicio:inicio + 10])
    almacen = AlmacenFichas(carpeta)  # como en una ejecución nueva
    almacen.abrir(VERSION_DE_PRUEBA)
    return almacen.leer_ficha, almacen


def _preparar_un_json_por_ficha(carpeta, fichas):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    for ficha in fichas:
        with open(carpeta / f"{ficha['id']}.json", "w", encoding="utf-8") as archivo:
            json.dump(ficha, archivo, ensure_ascii=False)

    def leer_ficha(id_ficha):
        with open(carpeta / f"{id_ficha}.json", encoding="utf-8") as archivo:
            return json.load(archivo)
    return leer_ficha, None


def _preparar_un_solo_json(carpeta, fichas):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "catalogo.json"
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(fichas, archivo, ensure_ascii=False)

    def leer_ficha(id_ficha):
        with open(ruta, encoding="utf-8") as archivo:
            todas = json.load(archivo)  # hay que leer y convertir todo el archivo
        for ficha in todas:
            if ficha["id"] == id_ficha:
                return ficha
        return None
    return leer_ficha, None


ALTERNATIVAS = (
    ("AlmacenFichas (decisión)", _preparar_almacen),
    ("un JSON por ficha", _preparar_un_json_por_ficha),
    ("un solo JSON", _preparar_un_solo_json),
)


def ejecutar(cantidades=CANTIDADES_DE_FICHAS, cantidad_lecturas=2_000, semilla=2026):
    """Devuelve (filas, filas_indice).
    filas: (n, alternativa, microsegundos por lectura, archivos, bytes)
    filas_indice: (n, microsegundos por búsqueda binaria en el índice)"""
    azar = random.Random(semilla)
    filas = []
    filas_indice = []
    calentar_procesador()
    with tempfile.TemporaryDirectory() as carpeta_base:
        for n in cantidades:
            fichas = _fichas_de_prueba(n)
            ids_a_leer = [fichas[azar.randrange(n)]["id"] for _ in range(cantidad_lecturas)]
            for numero, (nombre, preparar) in enumerate(ALTERNATIVAS):
                carpeta = Path(carpeta_base) / f"{n}_{numero}"
                leer_ficha, almacen = preparar(carpeta, fichas)
                # Leer todo el archivo en cada consulta es lento: menos lecturas.
                lecturas = ids_a_leer if numero < 2 else ids_a_leer[: max(100, 20_000 // n)]
                microsegundos = nanosegundos_por_operacion(leer_ficha, lecturas, 3) / 1000
                archivos, total_bytes = _tamano_de_carpeta(carpeta)
                filas.append((n, nombre, microsegundos, archivos, total_bytes))
                if almacen is not None:
                    busqueda = nanosegundos_por_operacion(almacen.contiene_ficha, ids_a_leer) / 1000
                    filas_indice.append((n, busqueda))
    return filas, filas_indice


def imprimir(resultado):
    filas, filas_indice = resultado
    print(descripcion_del_equipo())
    print()
    print("Recuperar una ficha liberada de memoria")
    encabezado = (f"{'fichas':>6} | {'alternativa':>24} | {'µs por lectura':>14} | "
                  f"{'archivos':>8} | {'bytes en disco':>14}")
    print(encabezado)
    print("-" * len(encabezado))
    for n, nombre, microsegundos, archivos, total_bytes in filas:
        print(f"{n:>6} | {nombre:>24} | {microsegundos:>14.1f} | {archivos:>8} | {total_bytes:>14}")
    print()
    print("Solo la búsqueda binaria en el índice de AlmacenFichas")
    for n, microsegundos in filas_indice:
        print(f"{n:>6} fichas: {microsegundos:.2f} µs por búsqueda")


def run():
    """Mediciones de este módulo para el ejecutor de --bench."""
    filas, filas_indice = ejecutar()
    mediciones = []
    for n, alternativa, microsegundos, archivos, total_bytes in filas:
        mediciones.append(Measurement(
            f"4.4 recuperar una ficha liberada: {alternativa}, {n} fichas",
            microsegundos / 1e6,
            f"tiempo por lectura; {archivos} archivos, {total_bytes} bytes en disco",
        ))
    for n, microsegundos in filas_indice:
        mediciones.append(Measurement(
            f"4.4 búsqueda binaria en el índice de fichas, {n} fichas",
            microsegundos / 1e6,
            "solo la búsqueda, sin leer el disco",
        ))
    return mediciones


if __name__ == "__main__":
    imprimir(ejecutar())
