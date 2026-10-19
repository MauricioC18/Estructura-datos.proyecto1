"""
Ejecuta todas las pruebas del proyecto y los benchmarks del bloque 2, y
guarda la salida en un archivo.

Sirve para compartir los resultados con el grupo (o adjuntarlos al
Documento de Decisiones) sin copiar la consola a mano.

Uso, desde la carpeta cripta/:
    python -m tools.ejecutar_verificaciones

Crea (o reemplaza) resultados_verificacion.txt en la carpeta cripta/.
"""
import datetime
import os
import subprocess
import sys
from pathlib import Path

from benchmark.utilidades_medicion import descripcion_del_equipo

RAIZ_DEL_PROYECTO = Path(__file__).resolve().parent.parent  # la carpeta cripta/
ARCHIVO_DE_RESULTADOS = RAIZ_DEL_PROYECTO / "resultados_verificacion.txt"

VERIFICACIONES = (
    # El mismo comando de pruebas que indica el README del proyecto.
    ("Pruebas unitarias", ["-m", "unittest", "discover", "-s", "tests", "-t", "."]),
    ("Benchmark de la tabla hash", ["-m", "benchmark.bench_tabla_hash"]),
    ("Benchmark de la caché del catálogo", ["-m", "benchmark.bench_cache_catalogo"]),
    ("Benchmark del almacén de fichas", ["-m", "benchmark.bench_almacen_fichas"]),
    ("Benchmark de la precarga de contenido", ["-m", "benchmark.bench_precarga_contenido"]),
)


def ejecutar_una_verificacion(titulo, argumentos):
    """Corre "python <argumentos>" y devuelve (código de salida, salida)."""
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")  # tildes correctas en Windows
    resultado = subprocess.run(
        [sys.executable, *argumentos],
        cwd=RAIZ_DEL_PROYECTO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=entorno,
    )
    # unittest escribe su resumen en stderr; se juntan ambas salidas.
    return resultado.returncode, resultado.stdout + resultado.stderr


def main():
    lineas = [
        "Verificación del proyecto CRIPTA",
        f"Fecha: {datetime.datetime.now():%Y-%m-%d %H:%M}",
        descripcion_del_equipo(),
        "",
    ]
    todo_correcto = True
    for titulo, argumentos in VERIFICACIONES:
        print(f"Ejecutando: {titulo} ...", flush=True)
        codigo, salida = ejecutar_una_verificacion(titulo, argumentos)
        estado = "OK" if codigo == 0 else f"FALLÓ (código {codigo})"
        if codigo != 0:
            todo_correcto = False
        lineas.append("=" * 72)
        lineas.append(f"{titulo}: {estado}")
        lineas.append(f"Comando: python {' '.join(argumentos)}")
        lineas.append("=" * 72)
        lineas.append(salida.rstrip())
        lineas.append("")

    lineas.append("Resultado general: " + ("todo correcto" if todo_correcto else "hubo fallas"))
    ARCHIVO_DE_RESULTADOS.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Listo. Resultados guardados en {ARCHIVO_DE_RESULTADOS.name}")
    if not todo_correcto:
        sys.exit(1)


if __name__ == "__main__":
    main()
