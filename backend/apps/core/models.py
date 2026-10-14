import uuid
from django.db import models
from django.utils import timezone

class PlayerProfile(models.Model):
    name = models.CharField(max_length=100, unique=True, primary_key=True)
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class MatchRecord(models.Model):
    player_obj = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE)
    match_obj = models.ForeignKey('Match', on_delete=models.CASCADE)
    placement = models.CharField(
        max_length=6,
        choices=[('winner', 'Winner'), ('second', 'Second'), ('none', 'None')],
        default='none',
    )
    kills = models.IntegerField(default=0)
    win_place = models.PositiveSmallIntegerField(default=0)
    assists = models.PositiveSmallIntegerField(default=0)
    damage_dealt = models.FloatField(default=0)
    time_survived = models.FloatField(default=0)
    date_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id} - winner: {self.placement} - player: {self.player_obj.name} - match: {self.match_obj.match_id}"
    
class Match(models.Model):
    match_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match_date = models.DateTimeField(default=timezone.now)
    map_name = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.match_id)[-6:]

class Tournament(models.Model):
    tournament_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
