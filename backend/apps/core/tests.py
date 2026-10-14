import uuid
from datetime import datetime, timezone as dt_timezone
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.core.models import Match, MatchRecord, Player, Tournament
from apps.core.utils import save_matches
from apps.pubg import gateway

MATCH_ID = "11111111-1111-1111-1111-111111111111"


def pubg_payload():
    return {
        MATCH_ID: {
            "createdAt": "2024-05-01T12:00:00Z",
            "mapName": "Baltic_Main",
            "map": "Erangel",
            "participants": [
                {
                    "name": "slyfoxcl",
                    "winPlace": 1,
                    "kills": 3,
                    "assists": 1,
                    "damageDealt": 250.5,
                    "timeSurvived": 1200,
                    "deathType": "byplayer",
                },
                {
                    "name": "otro",
                    "winPlace": 2,
                    "kills": 0,
                    "assists": 2,
                    "damageDealt": 40,
                    "timeSurvived": 800,
                    "deathType": "",
                },
            ],
        }
    }


class SaveMatchesTests(TestCase):
    def test_post_saves_matches_and_returns_201(self):
        with patch("apps.pubg.gateway.get_matches", return_value=pubg_payload()) as get_matches:
            response = self.client.post(
                "/api/match/create/",
                data={"player_name": "slyfoxcl"},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        get_matches.assert_called_once_with("slyfoxcl")
        body = response.json()
        self.assertEqual(body["saved"], 1)
        self.assertEqual(body["matches"], [MATCH_ID])

        match = Match.objects.get(match_id=MATCH_ID)
        self.assertEqual(match.map_name, "Erangel")
        self.assertEqual(
            match.created_at,
            datetime(2024, 5, 1, 12, 0, tzinfo=dt_timezone.utc),
        )
        record = MatchRecord.objects.get(match=match, player__name="slyfoxcl")
        self.assertEqual(record.kills, 3)
        self.assertEqual(record.assists, 1)
        self.assertEqual(record.damage_dealt, 250.5)
        self.assertEqual(record.time_survived, 1200)
        self.assertEqual(record.win_place, 1)
        self.assertEqual(record.death_type, "byplayer")
        self.assertEqual(Player.objects.filter(name="otro").count(), 1)

    def test_post_updates_existing_match_without_dropping_tournament(self):
        tournament = Tournament.objects.create(
            name="Copa",
            rules="",
            start_date=timezone.now(),
            end_date=timezone.now(),
        )
        Match.objects.create(
            match_id=uuid.UUID(MATCH_ID),
            tournament=tournament,
            map_name="Viejo",
        )
        with patch("apps.pubg.gateway.get_matches", return_value=pubg_payload()):
            response = self.client.post("/api/match/create/", data={}, content_type="application/json")

        self.assertEqual(response.status_code, 201)
        match = Match.objects.get(match_id=MATCH_ID)
        self.assertEqual(match.tournament_id, tournament.id)
        self.assertEqual(match.map_name, "Erangel")
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(match.matchrecord_set.count(), 2)

    def test_post_returns_502_when_gateway_fails(self):
        with patch("apps.pubg.gateway.get_matches", side_effect=RuntimeError("sin api")):
            response = self.client.post("/api/match/create/", data={}, content_type="application/json")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "No se pudieron guardar las partidas.")
        self.assertEqual(Match.objects.count(), 0)

    def test_post_returns_404_when_player_is_missing_in_pubg(self):
        with patch("apps.pubg.gateway.get_matches", side_effect=ValueError("no está")):
            response = self.client.post("/api/match/create/", data={}, content_type="application/json")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Match.objects.count(), 0)

    def test_post_returns_500_when_database_save_fails(self):
        with patch("apps.pubg.gateway.get_matches", return_value=pubg_payload()):
            with patch(
                "apps.core.utils.Match.objects.update_or_create",
                side_effect=RuntimeError("db"),
            ):
                response = self.client.post(
                    "/api/match/create/",
                    data={},
                    content_type="application/json",
                )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "No se pudieron guardar las partidas.")
        self.assertEqual(Match.objects.count(), 0)
        self.assertEqual(Player.objects.count(), 0)

    def test_post_rejects_a_player_name_that_is_not_text(self):
        response = self.client.post(
            "/api/match/create/",
            data={"player_name": 12},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_save_matches_rolls_back_when_a_later_match_is_invalid(self):
        payload = pubg_payload()
        payload["no-es-uuid"] = {"map": "Miramar", "participants": []}
        with patch("apps.pubg.gateway.get_matches", return_value=payload):
            with self.assertRaises(Exception):
                save_matches("slyfoxcl")
        self.assertEqual(Match.objects.count(), 0)
        self.assertEqual(Player.objects.count(), 0)


class PubgApiDecoratorTests(SimpleTestCase):
    def tearDown(self):
        gateway._api = None

    def test_decorator_passes_the_pubg_api_instance(self):
        client = Mock()
        client.fetch_custom_matches.return_value = []
        with patch.dict("os.environ", {"PUBG_API_KEY": "test-key"}):
            with patch("apps.pubg.gateway.PUBGAPI", return_value=client) as constructor:
                gateway._api = None
                first = gateway.get_matches("slyfoxcl")
                second = gateway.get_matches(player_name="otro")

        constructor.assert_called_once_with(api_key="test-key")
        self.assertIs(gateway._api, client)
        self.assertEqual(client.fetch_custom_matches.call_args_list[0].args, ("slyfoxcl",))
        self.assertEqual(client.fetch_custom_matches.call_args_list[1].args, ("otro",))
        self.assertEqual(first, {})
        self.assertEqual(second, {})
