import logging
import uuid

from django.contrib.auth import authenticate, login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Match, MatchRecord, Player
from .serializers import UserDataSerializer
from .exceptions import (
    MatchFetchError, 
    MatchPersistenceError, 
    MatchPlayerNotFoundError
    )
from apps.pubg.gateway import get_matches

logger = logging.getLogger(__name__)


def auth_profile(request, username, password):
    user = authenticate(request, username=username, password=password)
    if user is None:
        return None
    login(request, user)
    return UserDataSerializer(user).data


def _player_payload(player):
    return {"name": player.name, "totalPoints": 0}


def get_all_players():
    return [_player_payload(player) for player in Player.objects.all()]


def get_player(player_name):
    player = Player.objects.filter(pk=player_name).first()
    if player is None:
        return None
    return _player_payload(player)


def create_player(player_name):
    try:
        player, _created = Player.objects.get_or_create(name=player_name)
    except Exception:
        logger.exception("No se pudo crear el jugador %s", player_name)
        return None
    return _player_payload(player)


def delete_player(player_name):
    deleted, _rows = Player.objects.filter(pk=player_name).delete()
    return deleted > 0


def get_match_by_id(match_id):
    try:
        return Match.objects.filter(match_id=match_id).first()
    except (ValueError, ValidationError):
        return None


def get_all_matches():
    return Match.objects.all()


def delete_match(match_id):
    try:
        deleted, _rows = Match.objects.filter(match_id=match_id).delete()
    except (ValueError, ValidationError):
        return False
    return deleted > 0


def update_match(match, player_scores):
    if not isinstance(player_scores, dict):
        return False

    normalized = []
    for player_name, score in player_scores.items():
        if not isinstance(score, dict):
            return False
        player = Player.objects.filter(pk=player_name).first()
        if player is None:
            continue
        placement = score.get("placement") or "none"
        normalized.append(
            (
                player,
                _as_int(score.get("kills")),
                {"winner": 1, "second": 2}.get(placement, 0),
            )
        )

    try:
        with transaction.atomic():
            for player, kills, win_place in normalized:
                MatchRecord.objects.update_or_create(
                    match=match,
                    player=player,
                    defaults={"kills": kills, "win_place": win_place},
                )
    except Exception:
        logger.exception("No se pudo actualizar la partida %s", match.match_id)
        return False
    return True


def get_matches_record():
    """Tabla con la sumatoria de puntos de cada jugador en todas las partidas.

    1 punto por kill, 1 al ganador, -1 por morir en la zona.
    """
    totals = {}
    for record in MatchRecord.objects.select_related("player"):
        row = totals.setdefault(
            record.player.name,
            {"player": record.player.name, "matches": 0, "kills": 0,
             "wins": 0, "zoneDeaths": 0, "score": 0},
        )
        won = record.win_place == 1
        zone_death = record.death_type == "byzone"
        row["matches"] += 1
        row["kills"] += record.kills
        row["wins"] += int(won)
        row["zoneDeaths"] += int(zone_death)
        row["score"] += record.kills + int(won) - int(zone_death)
    return sorted(totals.values(), key=lambda r: (-r["score"],     r["player"]))

def save_match(bulk=False):
    """Pide las partidas al gateway de PUBG y las guarda en los modelos."""
    
    matches_json = _fetch_matches(bulk) if bulk else _fetch_matches()
    if not isinstance(matches_json, dict):
        raise MatchFetchError()

    try:
        with transaction.atomic():
            saved = [
                _persist_match(match_id, payload)
                for match_id, payload in matches_json.items()
            ]
    except MatchPersistenceError:
        raise
    except Exception as exc:
        logger.exception("No se pudieron guardar las partidas")
        raise MatchPersistenceError() from exc
    return saved



def _fetch_matches(bulk=False):
    try:
        return get_matches(bulk)
    except ValueError as exc:
        logger.exception("No se encontró al jugador en PUBG")
        raise MatchPlayerNotFoundError() from exc
    except Exception as exc:
        logger.exception("No se pudieron obtener las partidas")
        raise MatchFetchError() from exc


def _persist_match(match_id, payload):
    if not isinstance(payload, dict):
        raise MatchFetchError()

    try:
        match_uuid = uuid.UUID(str(match_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise MatchFetchError() from exc

    match, _created = Match.objects.update_or_create(
        match_id=match_uuid,
        defaults={
            "created_at": _match_created_at(payload.get("createdAt")),
            "map_name": (payload.get("map") or payload.get("mapName") or "")[:100],
        },
    )

    participants = payload.get("participants") or []
    if not isinstance(participants, list):
        raise MatchFetchError()

    records = []
    seen_names = set()
    for stats in participants:
        if not isinstance(stats, dict):
            continue
        name = (stats.get("name") or "").strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        player, _created = Player.objects.get_or_create(name=name[:100])
        death_type = (stats.get("deathType") or "")[:50]
        records.append(
            MatchRecord(
                match=match,
                player=player,
                kills=_as_int(stats.get("kills")),
                assists=_as_int(stats.get("assists")),
                damage_dealt=_as_float(stats.get("damageDealt")),
                time_survived=_as_float(stats.get("timeSurvived")),
                win_place=_as_int(stats.get("winPlace")),
                death_type=death_type or None,
            )
        )

    MatchRecord.objects.filter(match=match).delete()
    MatchRecord.objects.bulk_create(records)
    return match


def _match_created_at(created_at):
    parsed = parse_datetime(created_at) if isinstance(created_at, str) else None
    if parsed is None:
        return timezone.now()
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.utc)
    return parsed


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
