from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from rest_framework.response import Response

from api.permissions import IsAdmin
from apps.core.exceptions import MatchPersistenceError
from apps.core.models import Match as MatchModel
from apps.core.utils import (
    discard_match,
    get_match_boards,
    get_match_by_id,
    get_matches_record,
    get_player_matches,
    save_match,
)
from apps.pubg.gateway import death_reason


def _player_name(request):
    raw = request.data.get("player_name")
    if not isinstance(raw, str):
        return None
    name = raw.strip()
    if not name:
        return None
    return name[:100]


def _match_summary(match):
    return {
        "matchId": str(match.match_id),
        "mapName": match.map_name,
        "createdAt": match.created_at.isoformat(),
        "training": match.training,
        "participantCount": match.participant_count,
    }


def _match_detail(match):
    participants = []
    records = match.matchrecord_set.select_related("player").order_by(
        "win_place",
        "-kills",
        "player__name",
    )
    for record in records:
        participants.append(
            {
                "player": record.player.name,
                "place": record.win_place,
                "kills": record.kills,
                "assists": record.assists,
                "damage": record.damage_dealt,
                "timeSurvived": record.time_survived,
                "death": death_reason(record.death_type),
            }
        )
    return {
        "matchId": str(match.match_id),
        "mapName": match.map_name,
        "createdAt": match.created_at.isoformat(),
        "training": match.training,
        "participants": participants,
    }


class Match(APIView):
    permission_classes = [IsAdmin]
    action_method = None

    def post(self, request, *args, **kwargs):
        handler = getattr(self, self.action_method, None)
        if not handler:
            return Response({"detail": "Acción no configurada."}, status=HTTP_400_BAD_REQUEST)
        return handler(request)

    def _post_save_match(self, request):
        """Carga la última partida, o varias si bulk=true, del usuario indicado."""
        player_name = _player_name(request)
        if player_name is None:
            return Response(
                {"detail": "Ingresa el usuario para traer las partidas."},
                status=HTTP_400_BAD_REQUEST,
            )

        bulk = request.GET.get("bulk", "false") in ["true", "1"]
        try:
            saved = save_match(player_name, bulk=bulk)
        except MatchPersistenceError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        return Response(
            {
                "saved": len(saved),
                "matches": [str(match.match_id) for match in saved],
            },
            status=HTTP_201_CREATED,
        )


class MatchRecordView(APIView):
    def get(self, request):
        return Response(get_matches_record(), status=HTTP_200_OK)


class PlayerMatchesView(APIView):
    def get(self, request, player_name):
        history = get_player_matches(player_name)
        if history is None:
            return Response({"detail": "No se encontró el jugador."}, status=HTTP_404_NOT_FOUND)
        return Response(history, status=HTTP_200_OK)


class MatchBoardView(APIView):
    def get(self, request):
        return Response(get_match_boards(), status=HTTP_200_OK)


class MatchListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        matches = (
            MatchModel.objects.filter(discarded=False)
            .annotate(participant_count=Count("matchrecord"))
            .order_by("-created_at", "match_id")
        )
        return Response([_match_summary(match) for match in matches], status=HTTP_200_OK)


class MatchDetailView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, match_id):
        match = get_match_by_id(match_id)
        if match is None or match.discarded:
            return Response({"detail": "No se encontró la partida."}, status=HTTP_404_NOT_FOUND)
        return Response(_match_detail(match), status=HTTP_200_OK)

    def delete(self, request, match_id):
        match = discard_match(match_id)
        if match is None:
            return Response({"detail": "No se encontró la partida."}, status=HTTP_404_NOT_FOUND)
        return Response(
            {"matchId": str(match.match_id), "discarded": True},
            status=HTTP_200_OK,
        )

    def patch(self, request, match_id):
        match = get_match_by_id(match_id)
        if match is None or match.discarded:
            return Response({"detail": "No se encontró la partida."}, status=HTTP_404_NOT_FOUND)
        training = request.data.get("training")
        if not isinstance(training, bool):
            return Response(
                {"detail": "Indica si la partida es de entrenamiento."},
                status=HTTP_400_BAD_REQUEST,
            )
        match.training = training
        match.save(update_fields=["training"])
        return Response(_match_detail(match), status=HTTP_200_OK)
