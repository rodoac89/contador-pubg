import uuid
from django.db import models
from django.utils import timezone

class Tournament(models.Model):
    name = models.CharField(max_length=100)
    rules = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.name

class Player(models.Model):
    name = models.CharField(primary_key=True, max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Match(models.Model):
    match_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    training = models.BooleanField(default=False)
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    map_name = models.CharField(max_length=100)
    discarded = models.BooleanField(default=False)
    discarded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.match_id)

class MatchRecord(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    kills = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    damage_dealt = models.FloatField(default=0.0)
    time_survived = models.FloatField(default=0.0)
    win_place = models.IntegerField(default=0)
    death_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.player.name} in match {self.match.match_id}"