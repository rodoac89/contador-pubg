class MatchPersistenceError(Exception):
    """No se pudieron guardar las partidas obtenidas del gateway."""

    status_code = 500
    default_detail = "No se pudieron guardar las partidas."

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class MatchFetchError(MatchPersistenceError):
    status_code = 502


class MatchPlayerNotFoundError(MatchPersistenceError):
    status_code = 404
    default_detail = "No se encontró al jugador en PUBG."