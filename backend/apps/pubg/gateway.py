import argparse
import os
import sys
from pathlib import Path
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

api = PUBGAPI(api_key=get_pubg_api_key())

def get_participants(match_json):
    participants = [
        item["attributes"]["stats"]
        for item in match_json.get("included", [])
        if item.get("type") == "participant"
    ]
    return sorted(
        participants,
        key=lambda stats: (stats.get("winPlace", 0), -stats.get("kills", 0)),
    )

def print_matches():
    player_name = "slyfoxcl"  # Default player name

    custom_matches = api.fetch_custom_matches(player_name)

    #save_custom_matches(custom_matches)
    for match_json in custom_matches:
        attributes = match_json["data"]["attributes"]
        print(f"\nPartida {match_json['data']['id']}")
        print(f"Fecha: {attributes.get('createdAt')} | Mapa: {attributes.get('mapName')}")
        print(f"{'Jugador':<20}{'Puesto':>7}{'Kills':>7}{'Asist.':>8}{'Daño':>9}{'Sobrev. (s)':>13}")
        for stats in get_participants(match_json):
            marker = "*" if stats.get("name", "").lower() == player_name.lower() else " "
            print(
                f"{marker}{stats.get('name', '?'):<19}"
                f"{stats.get('winPlace', 0):>7}"
                f"{stats.get('kills', 0):>7}"
                f"{stats.get('assists', 0):>8}"
                f"{stats.get('damageDealt', 0):>9.0f}"
                f"{stats.get('timeSurvived', 0):>13.0f}"
            )

