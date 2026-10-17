from django.contrib import admin
from django.urls import path
from .apiviews import PlayerApiView

urlpatterns = [
    path('<str:player_name>/', PlayerApiView.as_view()),
    path('create', PlayerApiView.as_view()),

]
