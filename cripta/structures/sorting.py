"""
Algoritmos de ordenamiento del proyecto (§4.9).

Se usan en las vistas del inventario, la tabla de puntajes, los indices del
guardado y las listas auxiliares del catalogo. No se usa sorted() ni
list.sort().

Algoritmos
    insertion_sort: estable, sin memoria extra. O(n) si los datos estan casi
        ordenados y O(n^2) en el peor caso.
    merge_sort: estable, O(n log n) siempre, pero usa O(n) de memoria extra.

Seleccion automatica (sort)
    Una pasada cuenta los "descensos": posiciones donde un elemento va antes
    que su anterior. Con pocos elementos, o con pocos descensos respecto de n,
    se usa insercion; en otro caso, mezcla.

    UMBRAL_PEQUENO y PROPORCION_CASI_ORDENADO son provisionales: se calibran
    con benchmark/persona3_bench.py.

Limite conocido
    Los descensos son una aproximacion del desorden. Unos datos "rotados"
    ([5, 6, 7, 8, 9, 0, 1, 2, 3, 4]) tienen un solo descenso, pero insercion
    los ordena en O(n^2). El benchmark incluye ese caso para medirlo.

Todas las funciones devuelven una lista nueva y no modifican la entrada. La
clave de cada elemento se calcula una sola vez, para que una clave cara no se
recalcule en cada comparacion.
"""

INSERTION = "insercion"
MERGE = "mezcla"

SMALL_THRESHOLD = 16
NEARLY_SORTED_RATIO = 0.05


class ComparisonCounter:
    """Cuenta comparaciones de claves, para las mediciones."""

    def __init__(self):
        self.comparisons = 0


def _identity(value):
    return value


def _goes_after(first, second, reverse, counter):
    if counter is not None:
        counter.comparisons += 1

    return first < second if reverse else first > second


def _with_keys(data, key):
    return [(key(element), element) for element in data]


def _insertion(pairs, reverse, counter):
    for index in range(1, len(pairs)):
        current = pairs[index]
        position = index - 1

        while position >= 0 and _goes_after(pairs[position][0], current[0], reverse, counter):
            pairs[position + 1] = pairs[position]
            position -= 1

        pairs[position + 1] = current


def _merge(pairs, buffer, start, middle, end, reverse, counter):
    left = start
    right = middle
    out = start

    while left < middle and right < end:
        if _goes_after(pairs[left][0], pairs[right][0], reverse, counter):
            buffer[out] = pairs[right]
            right += 1
        else:
            buffer[out] = pairs[left]
            left += 1
        out += 1

    while left < middle:
        buffer[out] = pairs[left]
        left += 1
        out += 1

    while right < end:
        buffer[out] = pairs[right]
        right += 1
        out += 1

    for index in range(start, end):
        pairs[index] = buffer[index]


def _merge_range(pairs, buffer, start, end, reverse, counter):
    if end - start <= 1:
        return

    middle = (start + end) // 2
    _merge_range(pairs, buffer, start, middle, reverse, counter)
    _merge_range(pairs, buffer, middle, end, reverse, counter)
    _merge(pairs, buffer, start, middle, end, reverse, counter)


def _descents(pairs, reverse, counter):
    descents = 0

    for index in range(1, len(pairs)):
        if _goes_after(pairs[index - 1][0], pairs[index][0], reverse, counter):
            descents += 1

    return descents


def choose_algorithm(size, descents):
    if size <= SMALL_THRESHOLD:
        return INSERTION

    if descents <= size * NEARLY_SORTED_RATIO:
        return INSERTION

    return MERGE


def algorithm_for(data, key=_identity, reverse=False):
    """Que algoritmo escogeria sort() para estos datos."""
    pairs = _with_keys(data, key)
    return choose_algorithm(len(pairs), _descents(pairs, reverse, None))


def insertion_sort(data, key=_identity, reverse=False, counter=None):
    pairs = _with_keys(data, key)
    _insertion(pairs, reverse, counter)
    return [pair[1] for pair in pairs]


def merge_sort(data, key=_identity, reverse=False, counter=None):
    pairs = _with_keys(data, key)
    _merge_range(pairs, [None] * len(pairs), 0, len(pairs), reverse, counter)
    return [pair[1] for pair in pairs]


def sort(data, key=_identity, reverse=False, counter=None):
    """Ordena escogiendo el algoritmo segun el tamano y el desorden medidos."""
    pairs = _with_keys(data, key)

    if choose_algorithm(len(pairs), _descents(pairs, reverse, counter)) == INSERTION:
        _insertion(pairs, reverse, counter)
    else:
        _merge_range(pairs, [None] * len(pairs), 0, len(pairs), reverse, counter)

    return [pair[1] for pair in pairs]
