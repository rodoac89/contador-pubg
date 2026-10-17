import datetime
from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_200_OK
)
from rest_framework.response import Response

class HealthCheckAPIView(APIView):
    """
    API view to check the health status of the application.
    """
    def get(self, request, *args, **kwargs):
        return Response(
            { 
                'status': 'OK', 
                'timestamp': datetime.datetime.now(),
                'database': 'connected' 
            },
            status=HTTP_200_OK
        )