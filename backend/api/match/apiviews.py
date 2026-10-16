from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from rest_framework.response import Response
from apps.core.exceptions import MatchPersistenceError
from apps.core.utils import (
    get_all_matches,
    get_match_by_id,
    get_matches_record,
    save_match,
)
from apps.core.serializers import MatchSerializer


class Match(APIView):
    
    action_method = None 


    def post(self, request, *args, **kwargs):

        handler = getattr(self, self.action_method, None)
        
        if not handler:
            return Response({"error": "Acción no configurada"}, status=400)
        return handler(request)

    def _post_save_match(self, request):
        """
        Endpoint para cargar la(s) última(s) partida(s) desde el gateway de PUBG.
        """

        try:
            bulk = request.GET.get('bulk', 'false') in ['true', '1']
            saved = save_match(bulk)
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
        matches_record = get_matches_record()
        return Response(matches_record, status=HTTP_200_OK)
