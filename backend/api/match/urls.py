from django.contrib import admin
from django.urls import path
from .apiviews import Match, MatchRecordView

urlpatterns = [
    path('records/', MatchRecordView.as_view()),
    path('load/', Match.as_view(action_method='_post_save_match')), 
]