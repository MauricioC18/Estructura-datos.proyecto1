"""Ejecutor de --bench (§5.3).

Llama al run() que cada integrante expone para su modulo y muestra todas las
mediciones juntas. No usa la vista ni la red: el benchmark de precarga simula
la cripta en memoria.

Cada run() devuelve una lista de Measurement con name, seconds y detail. En
las mediciones que cuentan solicitudes en vez de medir tiempo, seconds es None.
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
    ("Inventario, historial, rastro, bitacora y ordenamientos", "benchmark.persona3_bench"),
)


def run_suite(module_name):
    return importlib.import_module(module_name).run()


def format_measurement(measurement):
    if measurement.seconds is None:
        seconds = "-"
    else:
        seconds = f"{measurement.seconds:.3e} s"

    return f"  {measurement.name:<55} {seconds:>12}  {measurement.detail}"


def main(suites=SUITES, output=print):
    output(descripcion_del_equipo())

    for title, module_name in suites:
        output("")
        output(f"== {title} ({module_name})")
        started = time.perf_counter()

        try:
            measurements = run_suite(module_name)
        except Exception as error:  # una suite rota no debe tapar las demas
            output(f"  No se pudo medir: {type(error).__name__}: {error}")
            continue

        for measurement in measurements:
            output(format_measurement(measurement))

        output(f"  ({time.perf_counter() - started:.1f} s)")


if __name__ == "__main__":
    main()
