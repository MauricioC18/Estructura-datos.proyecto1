"""
Simula el recorrido de una partida usando solo el bloque 2 (sin motor ni interfaz).

Para qué sirve
    - Verificar contra el API real el presupuesto de solicitudes: la primera
      corrida es un arranque en frío y la segunda, con la misma carpeta de
      caché, un arranque en caliente.
    - Mostrarle al grupo cómo se usa el RepositorioCripta desde el controlador.

Cómo recorre la cripta
    No conoce ningún id de sala (§9): empieza en la sala inicial que indica
    el API y en cada paso elige al azar, con semilla fija, una salida de la
    sala actual. No aplica reglas del juego (puertas cerradas, enemigos):
    solo carga los datos que el juego necesitaría.

Uso, desde la carpeta cripta/:
    python -m tools.simular_partida_bloque2
        con el API real y la caché en la carpeta cache_cripta
    python -m tools.simular_partida_bloque2 --offline datos_offline
        con los datos guardados (no usa la red)
    python -m tools.simular_partida_bloque2 --borrar-cache
        borra la caché antes de empezar (fuerza un arranque en frío)

Otras opciones: --cripta ID, --pasos N, --semilla N, --cache-size N, --cache CARPETA
"""
import argparse
import random
import shutil
import sys
from pathlib import Path

from adapters.fuente_datos import ErrorFuenteDatos
from adapters.fuente_http import FuenteHttp
from adapters.fuente_offline import FuenteOffline
from structures.cache_catalogo import CAPACIDAD_POR_DEFECTO
from repository.gestor_contenido import tipos_de_la_sala
from repository.repositorio_cripta import RepositorioCripta

CARPETA_DE_CACHE_POR_DEFECTO = "cache_cripta"


def usar_fichas_de_la_sala(repositorio, entrada):
    """Pide las fichas de todo lo que hay en la sala, como hará el juego
    al crear sus enemigos, objetos y trampas."""
    for tipo in tipos_de_la_sala(entrada):
        repositorio.obtener_ficha(tipo)


def simular_partida(repositorio, id_cripta=None, pasos=20, semilla=2026, mostrar=print):
    """Recorre la cripta al azar y devuelve el reporte de red final."""
    repositorio.empezar_conteo_de_partida()
    criptas = repositorio.listar_criptas()
    if id_cripta is None:
        id_cripta = criptas[0]["id"]
    datos = repositorio.iniciar_partida(id_cripta)
    mostrar(f"Partida en {datos.id_cripta} (versión {datos.version_cripta}, "
            f"catálogo {datos.version_catalogo}), presupuesto {datos.presupuesto_solicitudes}")

    azar = random.Random(semilla)
    actual = datos.sala_inicial
    usar_fichas_de_la_sala(repositorio, repositorio.contenido_de_sala(actual))
    recorrido = [actual]
    for _ in range(pasos):
        vecinas = repositorio.vecinos_de_sala(actual)
        if not vecinas:
            break
        siguiente = azar.choice(vecinas)
        entrada = repositorio.preparar_entrada_a_sala(siguiente)  # antes de confirmar la entrada
        usar_fichas_de_la_sala(repositorio, entrada)
        actual = siguiente
        recorrido.append(actual)
        repositorio.despues_de_accion(actual)           # después de la acción
    mostrar("Recorrido: " + " → ".join(str(sala) for sala in recorrido))
    return repositorio.reporte_de_red()


def main():
    analizador = argparse.ArgumentParser(description="Simula una partida usando solo el bloque 2.")
    analizador.add_argument("--offline", metavar="CARPETA", help="usar datos guardados en vez del API")
    analizador.add_argument("--cache", default=CARPETA_DE_CACHE_POR_DEFECTO, help="carpeta de la caché")
    analizador.add_argument("--cache-size", type=int, default=CAPACIDAD_POR_DEFECTO)
    analizador.add_argument("--cripta", help="id de la cripta (por defecto, la primera publicada)")
    analizador.add_argument("--pasos", type=int, default=20)
    analizador.add_argument("--semilla", type=int, default=2026)
    analizador.add_argument("--borrar-cache", action="store_true", help="empezar sin caché en disco")
    argumentos = analizador.parse_args()

    if argumentos.borrar_cache and Path(argumentos.cache).exists():
        shutil.rmtree(argumentos.cache)
        print(f"Caché borrada: {argumentos.cache}")

    try:
        fuente = FuenteOffline(argumentos.offline) if argumentos.offline else FuenteHttp()
        repositorio = RepositorioCripta(fuente, argumentos.cache, argumentos.cache_size)
        reporte = simular_partida(repositorio, argumentos.cripta, argumentos.pasos, argumentos.semilla)
    except ErrorFuenteDatos as error:
        print(f"Error: {error}")
        sys.exit(1)

    print()
    for linea in reporte.lineas_de_texto():
        print(linea)


if __name__ == "__main__":
    main()
