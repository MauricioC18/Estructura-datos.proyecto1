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
    1. Con n <= SMALL_THRESHOLD se usa insercion. El umbral sale de las
       mediciones: con datos al azar y con comparaciones costosas, insercion
       gana hasta 32 elementos y mezcla desde 64.
    2. Si no, una pasada cuenta los "descensos": posiciones donde un elemento
       va antes que su anterior. Con muchos descensos se usa mezcla.
    3. Con pocos descensos se intenta insercion, pero con un tope de
       desplazamientos: n * (bits de n), que es del orden del trabajo de
       mezcla. Si lo supera, los datos no estaban casi ordenados de verdad
       (por ejemplo, rotados: [5, 6, 7, 8, 9, 0, 1, 2, 3, 4] tiene un solo
       descenso) y se termina con mezcla sobre lo que ya quedo.

    El tope acota el peor caso a unas dos veces el costo de mezcla, en lugar
    del O(n^2) de insercion. Lo que insercion alcanzo a ordenar no se pierde:
    insercion y mezcla son estables, asi que el resultado tambien lo es.

Todas las funciones devuelven una lista nueva y no modifican la entrada. La
clave de cada elemento se calcula una sola vez, para que una clave cara no se
recalcule en cada comparacion.
"""

INSERTION = "insercion"
MERGE = "mezcla"

INSERTION_THEN_MERGE = "insercion, luego mezcla"

SMALL_THRESHOLD = 32
NEARLY_SORTED_RATIO = 0.05


class ComparisonCounter:
    """Cuenta comparaciones de claves y anota que algoritmo uso sort()."""

    def __init__(self):
        self.comparisons = 0
        self.algorithm = None


def _identity(value):
    return value


def _goes_after(first, second, reverse, counter):
    if counter is not None:
        counter.comparisons += 1

    return first < second if reverse else first > second


def _with_keys(data, key):
    return [(key(element), element) for element in data]


def _insertion(pairs, reverse, counter, max_shifts=None):
    """Insercion. Con max_shifts, se detiene al superarlo y devuelve False.

    Siempre deja cada elemento en la lista: al detenerse, la lista sigue
    siendo una permutacion de la original, con un prefijo ya ordenado.
    """
    shifts = 0

    for index in range(1, len(pairs)):
        current = pairs[index]
        position = index - 1

        while position >= 0 and _goes_after(pairs[position][0], current[0], reverse, counter):
            pairs[position + 1] = pairs[position]
            position -= 1
            shifts += 1

        pairs[position + 1] = current

        if max_shifts is not None and shifts > max_shifts:
            return False

    return True


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


def shift_budget(size):
    """Desplazamientos que se le permiten a insercion: n * (bits de n)."""
    return size * size.bit_length()


def choose_algorithm(size, descents):
    if size <= SMALL_THRESHOLD:
        return INSERTION

    if descents <= size * NEARLY_SORTED_RATIO:
        return INSERTION

    return MERGE


def algorithm_for(data, key=_identity, reverse=False):
    """Que algoritmo intentaria sort() primero con estos datos.

    Si es insercion y supera el tope, sort() termina con mezcla; para saber
    que paso de verdad, pasar un ComparisonCounter a sort().
    """
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
    size = len(pairs)

    if size <= SMALL_THRESHOLD:
        _insertion(pairs, reverse, counter)
        used = INSERTION
    elif choose_algorithm(size, _descents(pairs, reverse, counter)) == MERGE:
        _merge_range(pairs, [None] * size, 0, size, reverse, counter)
        used = MERGE
    elif _insertion(pairs, reverse, counter, shift_budget(size)):
        used = INSERTION
    else:
        _merge_range(pairs, [None] * size, 0, size, reverse, counter)
        used = INSERTION_THEN_MERGE

    if counter is not None:
        counter.algorithm = used

    return [pair[1] for pair in pairs]
