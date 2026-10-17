from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Match


class UserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ["match_id", "tournament", "created_at", "map_name"]
