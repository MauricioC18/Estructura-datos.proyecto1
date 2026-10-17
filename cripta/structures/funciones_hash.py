"""
Funciones hash deterministas para TablaHash.

Por qué no se usa hash() de Python
    Para textos, Python cambia el resultado de hash() en cada ejecución
    (aleatorización con PYTHONHASHSEED). La tabla seguiría funcionando, pero
    su orden interno cambiaría entre ejecuciones. Con estas funciones, la
    misma clave produce el mismo número en cualquier ejecución y computadora,
    lo que protege la reproducción de partidas (--replay).

Decisión
    hash_crc32 es la función por defecto. hash_fnv1a queda como alternativa
    descartada: es igual de determinista, pero en las mediciones del grupo
    fue unas 5 veces más lenta, porque recorre los bytes de la clave en
    Python, mientras que crc32 está escrita en C (módulo zlib de Python).
    Ver benchmark/bench_tabla_hash.py.

Claves admitidas
    int: se usa el mismo número (por ejemplo, ids de sala).
    str: se calcula sobre sus bytes UTF-8, así funcionan claves con tildes
         como "guardián".
    Cualquier otro tipo produce TypeError.
"""
import zlib

_MASCARA_64_BITS = (1 << 64) - 1
_FNV_BASE = 14695981039346656037
_FNV_PRIMO = 1099511628211


def hash_crc32(clave):
    """CRC-32: el mismo algoritmo de suma de verificación que usan ZIP y PNG."""
    if isinstance(clave, int):
        return clave
    if isinstance(clave, str):
        return zlib.crc32(clave.encode("utf-8"))
    raise TypeError(f"Tipo de clave no soportado: {type(clave).__name__}")


def hash_fnv1a(clave):
    """FNV-1a de 64 bits: por cada byte, un XOR y una multiplicación."""
    if isinstance(clave, int):
        return clave
    if isinstance(clave, str):
        resultado = _FNV_BASE
        for byte in clave.encode("utf-8"):
            resultado ^= byte
            resultado = (resultado * _FNV_PRIMO) & _MASCARA_64_BITS
        return resultado
    raise TypeError(f"Tipo de clave no soportado: {type(clave).__name__}")
