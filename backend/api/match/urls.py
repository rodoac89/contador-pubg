from django.contrib import admin
from django.urls import path
from .apiviews import Match, MatchRecordView

urlpatterns = [
    path('records/', MatchRecordView.as_view()),
    path('<str:match_id>', Match.as_view()),
    path('create/', Match.as_view()),  
]