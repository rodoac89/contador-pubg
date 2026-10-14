from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from rest_framework.response import Response
from apps.core.utils import (
    MatchPersistenceError,
    delete_match,
    get_all_matches,
    get_match_by_id,
    get_matches_record,
    save_matches,
    update_match,
)
from apps.core.serializers import MatchSerializer


class Match(APIView):
    def get(self, request, match_id=None):
        if match_id:
            match = get_match_by_id(match_id)
            if not match:
                return Response({"error": "Match not found"}, status=HTTP_404_NOT_FOUND)
            serializer = MatchSerializer(match)
            return Response(serializer.data, status=HTTP_200_OK)
        matches = get_all_matches()
        serializer = MatchSerializer(matches, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        player_name = "slyfoxcl"
        if hasattr(request.data, "get"):
            raw_name = request.data.get("player_name")
            if isinstance(raw_name, str) and raw_name.strip():
                player_name = raw_name.strip()
            elif raw_name not in (None, ""):
                return Response(
                    {"detail": "No se pudieron guardar las partidas."},
                    status=HTTP_400_BAD_REQUEST,
                )

        try:
            saved = save_matches(player_name)
        except MatchPersistenceError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)

        return Response(
            {
                "saved": len(saved),
                "matches": [str(match.match_id) for match in saved],
            },
            status=HTTP_201_CREATED,
        )

    def delete(self, request, match_id):
        match = get_match_by_id(match_id)
        if not match:
            return Response({"error": "Match not found"}, status=HTTP_404_NOT_FOUND)
        delete_success = delete_match(match_id)
        if delete_success:
            return Response(status=HTTP_200_OK)
        return Response(status=HTTP_400_BAD_REQUEST)

    def put(self, request, match_id):
        match = get_match_by_id(match_id)
        if not match:
            return Response({"error": "Match not found"}, status=HTTP_404_NOT_FOUND)
        update_success = update_match(match, request.data.get("playerScores"))
        if update_success:
            return Response(status=HTTP_200_OK)
        return Response(status=HTTP_400_BAD_REQUEST)


class MatchRecordView(APIView):
    def get(self, request):
        matches_record = get_matches_record()
        return Response(matches_record, status=HTTP_200_OK)
