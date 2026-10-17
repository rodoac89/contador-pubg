from django.urls import path

from .apiviews import (
    Match,
    MatchBoardView,
    MatchDetailView,
    MatchListView,
    MatchRecordView,
    PlayerMatchesView,
)

urlpatterns = [
    path('records/', MatchRecordView.as_view()),
    path('records/<str:player_name>/', PlayerMatchesView.as_view()),
    path('board/', MatchBoardView.as_view()),
    path('load/', Match.as_view(action_method='_post_save_match')),
    path('', MatchListView.as_view()),
    path('<uuid:match_id>/', MatchDetailView.as_view()),
]
