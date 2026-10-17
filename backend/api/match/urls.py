from django.urls import path

from .apiviews import Match, MatchDetailView, MatchListView, MatchRecordView

urlpatterns = [
    path('records/', MatchRecordView.as_view()),
    path('load/', Match.as_view(action_method='_post_save_match')),
    path('', MatchListView.as_view()),
    path('<uuid:match_id>/', MatchDetailView.as_view()),
]
