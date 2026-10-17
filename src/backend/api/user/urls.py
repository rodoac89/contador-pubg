from django.urls import path

from .apiviews import (
    LoginAPIView,
    LogoutAPIView,
    RegisterAPIView,
    SetupAPIView,
    UserDataAPIView,
)

urlpatterns = [
    path('setup/', SetupAPIView.as_view()),
    path('register/', RegisterAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('logout/', LogoutAPIView.as_view()),
    path('data/', UserDataAPIView.as_view()),
]
