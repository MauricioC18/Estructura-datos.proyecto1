class ReplayDivergence(Exception):
    """Una accion que en la partida original fue aceptada ahora se rechaza.

    El log solo contiene acciones aceptadas, asi que un rechazo significa que
    la reproduccion ya no es la misma partida.
    """


def replay_commands(controller, logged_commands, on_result=None):
    """Ejecuta los comandos de un log sobre el controlador, sin interaccion.

    on_result(logged_command, result) permite mostrar o registrar el avance sin
    que esta funcion dependa de la vista. Se detiene si la partida termina y
    quedan comandos, porque eso tambien es una divergencia.
    """
    for logged in logged_commands:
        if controller.is_over:
            raise ReplayDivergence(
                f"Linea {logged.line_number}: la partida ya termino y el log "
                f"todavia tiene '{logged.command.to_text()}'."
            )

        result = controller.execute(logged.command)

        if on_result is not None:
            on_result(logged, result)

        if not result.accepted:
            raise ReplayDivergence(
                f"Linea {logged.line_number}: '{logged.command.to_text()}' fue "
                f"rechazada al reproducir: {result.message}"
            )
