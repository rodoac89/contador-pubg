import os, requests

class PUBGAPI:
    def __init__(self, api_key="", platform="steam"):
        self.api_key = api_key
        self.base_url = f"https://api.pubg.com/shards/{platform}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json",
        }

    def fetch_custom_matches(self, player_name):
        """
        Obtiene las partidas personalizadas de un jugador específico.
        Args:
            player_name (str): Nombre del jugador.
        Returns:
            list: Lista de partidas personalizadas.
        """
        response = requests.get(
            f"{self.base_url}/players",
            params={"filter[playerNames]": player_name},
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        players = response.json().get("data", [])
        if not players:
            raise ValueError(f"No se encontró al jugador {player_name!r}.")

        custom_matches = []
        for player_match in players[0]["relationships"]["matches"]["data"]:
            match_id = player_match["id"]
            response = requests.get(
                f"{self.base_url}/matches/{match_id}",
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            match_json = response.json()
            if match_json["data"].get("attributes", {}).get("isCustomMatch") is True:
                custom_matches.append(match_json)
        return custom_matches

    def find_latest_custom_match(self, player_names: list[str]) -> str | None:
        """
        Devuelve el id de la partida custom más reciente que comparten los jugadores.
        None si falta algún jugador o no hay una custom en común.
        """
        names = list(dict.fromkeys(name.strip() for name in player_names if name and name.strip()))
        if not names:
            return None

        # 1. Obtiene jugadores (el filtro acepta hasta 10 nombres por request)
        players = []
        for start in range(0, len(names), 10):
            response = requests.get(
                f"{self.base_url}/players",
                params={"filter[playerNames]": ",".join(names[start:start + 10])},
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            players.extend(response.json().get("data", []))

        found = {player.get("attributes", {}).get("name", "").casefold() for player in players}
        if any(name.casefold() not in found for name in names):
            return None

        # 2. Cruza match IDs. El endpoint los entrega del más reciente al más antiguo.
        match_lists = [
            [
                match["id"]
                for match in player.get("relationships", {}).get("matches", {}).get("data", [])
            ]
            for player in players
        ]
        common_ids = set(match_lists[0])
        for match_ids in match_lists[1:]:
            common_ids.intersection_update(match_ids)
        ordered_ids = [match_id for match_id in match_lists[0] if match_id in common_ids]

        # 3. Filtra isCustomMatch == True
        # 4. Devuelve el match_id más reciente (o None si no encuentra)
        for match_id in ordered_ids:
            response = requests.get(
                f"{self.base_url}/matches/{match_id}",
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            is_custom = (
                response.json().get("data", {}).get("attributes", {}).get("isCustomMatch") is True
            )
            if is_custom:
                return match_id
        return None