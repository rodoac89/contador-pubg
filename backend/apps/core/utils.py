from urllib import request
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import PlayerProfile, Match, MatchRecord
from .serializers import MatchRecordSerializer, PlayerProfileSerializer, UserDataSerializer
from django.db import transaction
from apps.utils import history_match as hm

# Authentication and User Management
def auth_profile(request, username, password):

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        serializer = UserDataSerializer(user)
        return serializer.data
    else:
        return None 

# Player Profile Management
def get_player(player_name):
    try:
        player = PlayerProfile.objects.get(player_name=player_name)
        serializer = UserDataSerializer(player)
        return serializer.data
    except PlayerProfile.DoesNotExist:
        return None
    
def get_all_players():
    data = PlayerProfile.objects.all()
    serializer = PlayerProfileSerializer(data, many=True)
    return serializer.data

def create_player(player_name):
    try:
        player = PlayerProfile.objects.create(name=player_name)
        player.save()
        serializer = PlayerProfileSerializer(player)
        return serializer.data
    except Exception as e:
        return None


def delete_player(player_name):
    try:
        player = PlayerProfile.objects.get(name=player_name)
        player.delete()
        return True
    except PlayerProfile.DoesNotExist:
        return False

# Match Management
def get_match_by_id(match_id):
    try:
        match = Match.objects.get(match_id=match_id)
        return match
    except Match.DoesNotExist:
        return None

def get_all_matches():
    return Match.objects.all()  

def create_match(m_id, player_scores):
    match = None
    try:
        with transaction.atomic():
            # Create match
            match = Match.objects.create(match_id=m_id)
            
            # Create match records for each player
            for player_name, score in player_scores.items():
                player = PlayerProfile.objects.get(name=player_name)
                MatchRecord.objects.create(
                    match_obj=match,
                    player_obj=player,
                    kills=score['kills'],
                    placement=score['placement']
                )
            
            # Update player total points
            for player_name in player_scores.keys():
                player = PlayerProfile.objects.get(name=player_name)
                
                # Calculate total points from all match records
                total_points = 0
                match_records = MatchRecord.objects.filter(player_obj=player)
                
                for record in match_records:
                    points = record.kills
                    if record.placement == 'winner':
                        points += 3
                    elif record.placement == 'second':
                        points += 1
                    total_points += points
                
                player.total_points = total_points
                player.save()

    except Exception as e:
        return None
    
    return match

def delete_match(m_id):
    try:
        with transaction.atomic():
            # Get the match object
            match = Match.objects.get(match_id=m_id)
            
            # Get all players that participated in this match
            match_records = MatchRecord.objects.filter(match_obj=match)
            affected_players = [record.player_obj for record in match_records]
            
            # Delete match records first
            match_records.delete()
            
            # Delete the match
            match.delete()
            
            # Recalculate total points for affected players
            for player in affected_players:
                total_points = 0
                remaining_records = MatchRecord.objects.filter(player_obj=player)
                
                for record in remaining_records:
                    points = record.kills
                    if record.placement == 'winner':
                        points += 3
                    elif record.placement == 'second':
                        points += 1
                    total_points += points
                
                player.total_points = total_points
                player.save()
            
            return True
            
    except Match.DoesNotExist:
        print("Match does not exist")
        return False
    except Exception as e:
        print("Error deleting match:", e)
        return False

def update_match(match, player_scores):
    try:
        with transaction.atomic():
            
            # Update match records for each player
            for player_name, score in player_scores.items():
                player = PlayerProfile.objects.get(name=player_name)
                match_record = MatchRecord.objects.get(match_obj=match, player_obj=player)
                match_record.kills = score['kills']
                match_record.placement = score['placement']
                match_record.save()
            
            # Update player total points
            for player_name in player_scores.keys():
                player = PlayerProfile.objects.get(name=player_name)
                
                # Calculate total points from all match records
                total_points = 0
                match_records = MatchRecord.objects.filter(player_obj=player)
                
                for record in match_records:
                    points = record.kills
                    if record.placement == 'winner':
                        points += 3
                    elif record.placement == 'second':
                        points += 1
                    total_points += points
                
                player.total_points = total_points
                player.save()

            return True

    except Match.DoesNotExist:
        return False
    return False


# Match Records Management
def get_matches_record():
    queryset = Match.objects.all()
    serializer = MatchRecordSerializer(queryset, many=True)
    return serializer.data

# Read last match from PUBG API and Save to Database
def save_last_match(player_name="slyfoxcl"):    

    custom_matches = hm.fetch_custom_matches(player_name)
    if not custom_matches:
        print("No se encontraron partidas custom recientes para este jugador.")
        return None

    for match_json in custom_matches:
        attributes = match_json["data"]["attributes"]
        match_id = match_json['data']['id']
        player_scores = {}
        attributes = match_json["data"]["attributes"]
        print(f"\nPartida {match_json['data']['id']}")
        print(f"Fecha: {attributes.get('createdAt')} | Mapa: {attributes.get('mapName')}")
        print(f"{'Jugador':<20}{'Puesto':>7}{'Kills':>7}{'Asist.':>8}{'Daño':>9}{'Sobrev. (s)':>13}")
        for stats in hm.get_participants(match_json):
            marker = "*" if stats.get("name", "").lower() == player_name.lower() else " "
            print(
                f"{marker}{stats.get('name', '?'):<19}"
                f"{stats.get('winPlace', 0):>7}"
                f"{stats.get('kills', 0):>7}"
                f"{stats.get('assists', 0):>8}"
                f"{stats.get('damageDealt', 0):>9.0f}"
                f"{stats.get('timeSurvived', 0):>13.0f}"
            )
        # for participant in attributes.get("participants", []):
        #     player_name = participant.get("playerName")
        #     kills = participant.get("stats", {}).get("kills", 0)
        #     placement = "none"
        #     win_place = participant.get("stats", {}).get("winPlace", 0)
        #     if win_place == 1:
        #         placement = "winner"
        #     elif win_place == 2:
        #         placement = "second"
        #     player_scores[player_name] = {
        #         "kills": kills,
        #         "placement": placement
        #     }
        #create_match(match_id, player_scores)