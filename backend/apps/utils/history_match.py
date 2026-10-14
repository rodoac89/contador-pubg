import argparse
import os
import sys
from pathlib import Path

import requests


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


def fetch_custom_matches(player_name):
    api_key = os.environ.get("PUBG_API_KEY", default="")
    if not api_key:
        raise RuntimeError("Configura la variable de entorno PUBG_API_KEY.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
    }
    response = requests.get(
        "https://api.pubg.com/shards/steam/players",
        params={"filter[playerNames]": player_name},
        headers=headers,
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
            f"https://api.pubg.com/shards/steam/matches/{match_id}",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        match_json = response.json()
        if match_json["data"].get("attributes", {}).get("isCustomMatch") is True:
            custom_matches.append(match_json)
    return custom_matches

def test():
    player_name = "slyfoxcl"  # Default player name

    custom_matches = fetch_custom_matches(player_name)

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

