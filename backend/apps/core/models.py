import uuid
from django.db import models
from django.utils import timezone

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.name

class Player(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Match(models.Model):
    match_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    map_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.match_id)

class MatchRecord(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    kills = models.IntegerField(default=0)
    win_place = models.IntegerField(default=0)
    death_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.player.name} in match {self.match.match_id}"