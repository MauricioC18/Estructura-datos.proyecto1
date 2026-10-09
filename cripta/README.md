# CRIPTA

Juego de mazmorra dirigido por eventos, desarrollado como primer proyecto del curso Estructuras de Datos II, II Ciclo 2026, Universidad Nacional de Costa Rica.

El proyecto consiste en diseñar, implementar y evaluar las estructuras de datos necesarias para resolver los problemas planteados en el enunciado: selección del siguiente evento, precarga de contenido, resolución del catálogo, caché persistente, inventario, historial reversible, rastro del jugador, bitácora en pantalla, ordenamiento y guardado binario.

El enunciado oficial está en `docs/proyecto_cripta.md` y es la referencia para cualquier duda sobre las reglas del juego.

## Estado actual

El proyecto está en desarrollo. Lo implementado y probado hasta ahora es:

| Módulo | Contenido |
| --- | --- |
| `model/event.py` | Representación de un evento programado |
| `structures/event_queue.py` | Agenda de eventos, montículo binario mínimo |
| `model/game_state.py` | Reloj virtual, numeración de eventos y azar reproducible |

Todavía no existe un juego ejecutable. El punto de entrada `main.py` está vacío, y los modos sin conexión, de reproducción y de medición no están implementados.

## Requisitos

Python 3.11 o superior. El desarrollo se está realizando sobre Python 3.14.6.

Las dependencias están en `requirements.txt`. Se instalan con:

```
pip install -r requirements.txt
```

## Ejecutar las pruebas

Desde la carpeta `cripta/`:

```
python -m unittest discover -s tests -t . -v
```

En Windows también funciona `py` en lugar de `python`.

## Comandos del programa

Pendientes de implementar. Según el enunciado, la versión final debe aceptar:

| Bandera | Función |
| --- | --- |
| `--offline` | Leer las respuestas desde un paquete en disco en lugar de la red |
| `--cache-size` | Tope de fichas de catálogo en memoria, 25 por omisión |
| `--replay partida.log` | Reproducir una partida completa sin interacción del usuario |
| `--bench` | Ejecutar las mediciones de rendimiento por subsistema |

## Organización del proyecto

La estructura de carpetas, las responsabilidades de cada módulo y las interfaces acordadas están en `docs/ARQUITECTURA.md`.

Las decisiones de diseño, con sus alternativas, complejidades y evidencia, están en `docs/DECISIONES.md`.

El registro de uso de herramientas de IA está en `PROMPTS_LLM.md`.

## Archivos generados

Pendiente de definir. Aquí se indicará la ubicación de la caché persistente, los archivos de guardado binario, las bitácoras de partida y la tabla de puntajes cuando esos módulos existan.
