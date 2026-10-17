from django.contrib import admin
from django.urls import path, include
from .player.urls import urlpatterns as player_urls
from .user.urls import urlpatterns as user_urls 
from .match.urls import urlpatterns as match_urls
from .apiviews import HealthCheckAPIView
    

urlpatterns = [
    path('player/', include(player_urls)),
    path('user/', include(user_urls)),
    path('match/', include(match_urls)),
    path('health/', HealthCheckAPIView.as_view()),
]
