"""
Corre todas las mediciones de la Persona 3 y guarda los resultados.

    python -m benchmark.persona3_corridas

Hace tres corridas de benchmark/persona3_bench.py y una de
benchmark/persona3_frecuencias.py, calcula la mediana de cada medicion y lo
guarda todo en docs/mediciones/persona3/, con la fecha y el equipo en el
nombre del archivo y en la primera linea. Son las cifras que van al Documento
de Decisiones (secciones 4.5 a 4.9).

Tarda unos minutos: la mayor parte es insercion con datos desordenados.
"""
import contextlib
import io
import os
import platform
from datetime import date

from benchmark import persona3_bench, persona3_frecuencias
from benchmark.utilidades_medicion import descripcion_del_equipo
from structures.sorting import sort

RUNS = 3
FOLDER = os.path.join("docs", "mediciones", "persona3")


def _median(values):
    ordered = sort(values)
    return ordered[len(ordered) // 2]


def _format(seconds):
    return "-" if seconds is None else f"{seconds:.3e} s"


def _write(path, lines):
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def main():
    os.makedirs(FOLDER, exist_ok=True)
    today = date.today().isoformat()
    machine = platform.node() or "equipo"
    header = f"{descripcion_del_equipo()}, {machine}, {today}"
    prefix = os.path.join(FOLDER, f"{today}_{machine}")

    runs = []
    for number in range(1, RUNS + 1):
        print(f"Corrida {number} de {RUNS}...")
        measurements = persona3_bench.run()
        runs.append(measurements)
        _write(
            f"{prefix}_corrida_{number}.txt",
            [header] + [f"{m.name:<45} {_format(m.seconds):>14}  {m.detail}" for m in measurements],
        )

    lines = [header, f"Mediana de {RUNS} corridas", ""]
    for index in range(len(runs[0])):
        first = runs[0][index]
        values = [run[index].seconds for run in runs]
        if values[0] is None:
            median = None
        else:
            median = _median(values)
        every = ", ".join(_format(value) for value in values)
        lines.append(f"{first.name:<45} {_format(median):>14}  [{every}]  {first.detail}")
    _write(f"{prefix}_medianas.txt", lines)

    print("Frecuencias...")
    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        persona3_frecuencias.main()
    _write(f"{prefix}_frecuencias.txt", [header, ""] + captured.getvalue().splitlines())

    print(f"Listo. Resultados en {FOLDER}{os.sep}{today}_{machine}_*.txt")


if __name__ == "__main__":
    main()
