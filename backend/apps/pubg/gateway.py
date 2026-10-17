import os
from functools import wraps
from .api import PUBGAPI

def get_pubg_api_key():
    """
    Obtiene la clave de API de PUBG desde la variable de entorno.
    Lanza un error si no está configurada.
    """
    API_KEY = os.environ.get("PUBG_API_KEY", default=None)
    
    if not API_KEY:
        raise RuntimeError("Configura la variable de entorno PUBG_API_KEY.")
    return API_KEY

_api = None


def pubg_api(func):
    """Entrega a la función la instancia de PUBGAPI que habla con la API."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(_pubg_api(), *args, **kwargs)

    return wrapper


def _pubg_api():
    global _api
    if _api is None:
        _api = PUBGAPI(api_key=get_pubg_api_key())
    return _api

# mapName de la API → nombre que muestra el juego.
# Baltic_Main es el Erangel actual; Erangel_Main es el mapa original.
MAP_NAMES = {
    "Baltic_Main": "Erangel",
    "Erangel_Main": "Erangel",
    "Desert_Main": "Miramar",
    "Savage_Main": "Sanhok",
    "DihorOtok_Main": "Vikendi",
    "Summerland_Main": "Karakin",
    "Chimera_Main": "Paramo",
    "Tiger_Main": "Taego",
    "Kiki_Main": "Deston",
    "Neon_Main": "Rondo",
    "Heaven_Main": "Haven",
    "Range_Main": "Camp Jackal",
}

# deathType de la API: alive, byplayer, byzone, suicide, logout.
# byzone cubre zona azul y zona roja.
DEATH_REASONS = {
    "alive": "vivo",
    "byplayer": "otro jugador",
    "byzone": "zona",
    "suicide": "suicidio",
    "logout": "desconexión",
}

def death_reason(death_type):
    if not death_type:
        return "desconocida"
    return DEATH_REASONS.get(death_type, death_type)

def map_name(map_id):
    if not map_id:
        return ""
    return MAP_NAMES.get(map_id, map_id)

def get_participants(match_json):
    participants = []
    for item in match_json.get("included", []):
        if item.get("type") != "participant":
            continue
        stats = dict(item["attributes"]["stats"])
        death_type = stats.get("deathType") or ""
        stats["deathType"] = death_type
        stats["deathReason"] = death_reason(death_type)
        participants.append(stats)
    return sorted(
        participants,
        key=lambda stats: (stats.get("winPlace", 0), -stats.get("kills", 0)),
    )

@pubg_api
def print_matches(api):
    player_name = "slyfoxcl"  # Default player name

    custom_matches = api.fetch_custom_matches(player_name)

    #save_custom_matches(custom_matches)
    for match_json in custom_matches:
        attributes = match_json["data"]["attributes"]
        print(f"\nPartida {match_json['data']['id']}")
        print(f"Fecha: {attributes.get('createdAt')} | Mapa: {map_name(attributes.get('mapName'))}")
        print(
            f"{'Jugador':<20}{'Puesto':>7}{'Kills':>7}{'Asist.':>8}"
            f"{'Daño':>9}{'Sobrev. (s)':>13}{'Muerte':>26}"
        )
        for stats in get_participants(match_json):
            marker = "*" if stats.get("name", "").lower() == player_name.lower() else " "
            death = f"{stats.get('deathReason')}"
            print(
                f"{marker}{stats.get('name', '?'):<19}"
                f"{stats.get('winPlace', 0):>7}"
                f"{stats.get('kills', 0):>7}"
                f"{stats.get('assists', 0):>8}"
                f"{stats.get('damageDealt', 0):>9.0f}"
                f"{stats.get('timeSurvived', 0):>13.0f}"
                f"{death:>26}"
            )
        

@pubg_api
def get_matches(api, player_name, bulk=False):
    """
    Devuelve un dict por match_id con fecha, mapa y los jugadores de la tabla.
    Sin bulk trae solo la partida custom más reciente de ese usuario.
    """
    player_name = player_name.strip() if isinstance(player_name, str) else ""
    if not player_name:
        raise ValueError("Falta el usuario.")
    custom_matches = (
        api.fetch_custom_match(player_name)
        if bulk
        else api.fetch_custom_match(player_name, items=1)
    )
    matches = {}
    for match_json in custom_matches:
        attributes = match_json["data"]["attributes"]
        match_id = match_json["data"]["id"]
        matches[match_id] = {
            "createdAt": attributes.get("createdAt"),
            "mapName": attributes.get("mapName"),
            "map": map_name(attributes.get("mapName")),
            "participants": [
                {
                    "name": stats.get("name"),
                    "winPlace": stats.get("winPlace", 0),
                    "kills": stats.get("kills", 0),
                    "assists": stats.get("assists", 0),
                    "damageDealt": stats.get("damageDealt", 0),
                    "timeSurvived": stats.get("timeSurvived", 0),
                    "deathType": stats.get("deathType") or ""
                }
                for stats in get_participants(match_json)
            ],
        }
    return matches

