from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK
)
from rest_framework.response import Response
from apps.core.utils import create_player, get_player, get_all_players, delete_player

class PlayerApiView(APIView):
    """
    API view to handle player retrieval and creation.
    """
    def get(self, request, player_name=None, *args, **kwargs):
        
        if player_name == 'all':
            players = get_all_players()
            return Response(players, status=HTTP_200_OK)

        elif player_name is not None:

            player = get_player(player_name)
            if player is None:
                return Response(
                    {"detail": "Player not found."},
                    status=HTTP_404_NOT_FOUND
                )

            
            return Response(player, status=HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        player_name = request.data.get('name')
        if not player_name:
            return Response(
                {"detail": "Player name is required."},
                status=HTTP_400_BAD_REQUEST
            )
        player = create_player(player_name)
        if player is None:
            return Response(
                {"detail": "Player creation not successful."},
                status=HTTP_400_BAD_REQUEST
            )
        return Response(player, status=HTTP_200_OK)
        
    
    def delete(self, request, player_name, *args, **kwargs):
        if delete_player(player_name):
            return Response(
                {"detail": "Player deleted successfully."},
                status=HTTP_200_OK
            )
        
        return Response(
            {"detail": "Player deletion not successful."},
            status=HTTP_400_BAD_REQUEST
        )
