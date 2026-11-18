"""Ejecutor de --bench (§5.3).

Llama al run() que cada integrante expone para su modulo y muestra todas las
mediciones juntas. No usa la vista ni la red: el benchmark de precarga simula
la cripta en memoria.

Cada run() devuelve una lista de Measurement con name, seconds y detail. En
las mediciones que cuentan solicitudes en vez de medir tiempo, seconds es None.

Paquete sin conexion
    Una suite que mide criptas reales declara USA_PAQUETE_SIN_CONEXION = True
    y acepta la carpeta como primer argumento de run(). Si main.py recibe
    --offline CARPETA, esas suites miden esa carpeta; si no, cada una usa su
    carpeta por omision. Las demas suites no cambian.
"""
import importlib
import time

from benchmark.utilidades_medicion import descripcion_del_equipo


# (titulo, modulo). Para agregar un subsistema basta con sumarlo aqui.
SUITES = (
    ("Agenda de eventos y ciclo del motor", "benchmark.scheduler_bench"),
    ("Tabla hash", "benchmark.bench_tabla_hash"),
    ("Cache del catalogo", "benchmark.bench_cache_catalogo"),
    ("Recuperacion de fichas desde disco", "benchmark.bench_almacen_fichas"),
    ("Precarga de contenido", "benchmark.bench_precarga_contenido"),
    ("Frecuencia de operaciones y resolucion del catalogo (bloque 2)", "benchmark.bench_frecuencia_bloque2"),
    ("Inventario, historial, rastro, bitacora y ordenamientos", "benchmark.persona3_bench"),
    ("Bitacora de partida y reproduccion", "benchmark.replay_bench"),
    ("Guardado binario de la partida", "benchmark.bench_almacen_partida"),
    ("Persecucion del cazador", "benchmark.bench_cazador"),
    ("Mapa conocido y viaje ir a", "benchmark.bench_mapa_conocido"),
    ("Linea de tiempo", "benchmark.bench_linea_de_tiempo"),
    ("Verificacion de resolubilidad", "benchmark.bench_resolubilidad"),
)


def run_suite(module_name, carpeta_sin_conexion=None):
    module = importlib.import_module(module_name)

    if carpeta_sin_conexion is not None and getattr(module, "USA_PAQUETE_SIN_CONEXION", False):
        return module.run(carpeta_sin_conexion)

    return module.run()


def format_measurement(measurement):
    if measurement.seconds is None:
        seconds = "-"
    else:
        seconds = f"{measurement.seconds:.3e} s"

    return f"  {measurement.name:<55} {seconds:>12}  {measurement.detail}"


def main(suites=SUITES, output=print, carpeta_sin_conexion=None):
    output(descripcion_del_equipo())

    if carpeta_sin_conexion is not None:
        output(f"Paquete sin conexion: {carpeta_sin_conexion}")

    for title, module_name in suites:
        output("")
        output(f"== {title} ({module_name})")
        started = time.perf_counter()

        try:
            measurements = run_suite(module_name, carpeta_sin_conexion)
        except Exception as error:  # una suite rota no debe tapar las demas
            output(f"  No se pudo medir: {type(error).__name__}: {error}")
            continue

        for measurement in measurements:
            output(format_measurement(measurement))

        output(f"  ({time.perf_counter() - started:.1f} s)")


if __name__ == "__main__":
    main()
