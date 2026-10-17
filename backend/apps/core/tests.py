import uuid
from datetime import datetime, timezone as dt_timezone
from unittest.mock import Mock, call, patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token

from apps.core.models import Match, MatchRecord, Player, Tournament
from apps.core.utils import save_match
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
    def setUp(self):
        user = User.objects.create_superuser("admin", "admin@example.com", "Clave-segura-1")
        self.token = Token.objects.create(user=user)

    def post_load(self, data, query=""):
        return self.client.post(
            f"/api/match/load/{query}",
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

    def test_post_saves_matches_and_returns_201(self):
        with patch("apps.core.utils.get_matches", return_value=pubg_payload()) as get_matches:
            response = self.post_load({"player_name": "slyfoxcl"})

        self.assertEqual(response.status_code, 201)
        get_matches.assert_called_once_with("slyfoxcl", bulk=False)
        body = response.json()
        self.assertEqual(body["saved"], 1)
        self.assertEqual(body["matches"], [MATCH_ID])

        match = Match.objects.get(match_id=MATCH_ID)
        self.assertEqual(match.map_name, "Erangel")
        self.assertFalse(match.training)
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

    def test_post_requires_an_admin_token(self):
        response = self.client.post(
            "/api/match/load/",
            data={"player_name": "slyfoxcl"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_bulk_flag_is_forwarded(self):
        with patch("apps.core.utils.get_matches", return_value=pubg_payload()) as get_matches:
            response = self.post_load({"player_name": "slyfoxcl"}, "?bulk=true")

        self.assertEqual(response.status_code, 201)
        get_matches.assert_called_once_with("slyfoxcl", bulk=True)

    def test_post_updates_existing_match_without_dropping_tournament_or_training(self):
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
            training=True,
        )
        with patch("apps.core.utils.get_matches", return_value=pubg_payload()):
            response = self.post_load({"player_name": "slyfoxcl"})

        self.assertEqual(response.status_code, 201)
        match = Match.objects.get(match_id=MATCH_ID)
        self.assertEqual(match.tournament_id, tournament.id)
        self.assertEqual(match.map_name, "Erangel")
        self.assertTrue(match.training)
        self.assertEqual(Match.objects.count(), 1)
        self.assertEqual(match.matchrecord_set.count(), 2)

    def test_post_returns_502_when_gateway_fails(self):
        with patch("apps.core.utils.get_matches", side_effect=RuntimeError("sin api")):
            response = self.post_load({"player_name": "slyfoxcl"})

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"], "No se pudieron guardar las partidas.")
        self.assertEqual(Match.objects.count(), 0)

    def test_post_returns_404_when_player_is_missing_in_pubg(self):
        with patch("apps.core.utils.get_matches", side_effect=ValueError("no está")):
            response = self.post_load({"player_name": "slyfoxcl"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "No se encontró al jugador en PUBG.")
        self.assertEqual(Match.objects.count(), 0)

    def test_post_returns_500_when_database_save_fails(self):
        with patch("apps.core.utils.get_matches", return_value=pubg_payload()):
            with patch(
                "apps.core.utils.Match.objects.update_or_create",
                side_effect=RuntimeError("db"),
            ):
                response = self.post_load({"player_name": "slyfoxcl"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "No se pudieron guardar las partidas.")
        self.assertEqual(Match.objects.count(), 0)
        self.assertEqual(Player.objects.count(), 0)

    def test_post_rejects_a_player_name_that_is_not_text(self):
        response = self.post_load({"player_name": 12})
        self.assertEqual(response.status_code, 400)

    def test_post_rejects_a_missing_player_name(self):
        response = self.post_load({})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Ingresa el usuario para traer las partidas.")

    def test_save_match_rolls_back_when_a_later_match_is_invalid(self):
        payload = pubg_payload()
        payload["no-es-uuid"] = {"map": "Miramar", "participants": []}
        with patch("apps.core.utils.get_matches", return_value=payload):
            with self.assertRaises(Exception):
                save_match("slyfoxcl")
        self.assertEqual(Match.objects.count(), 0)
        self.assertEqual(Player.objects.count(), 0)


class MatchAdminTests(TestCase):
    def setUp(self):
        user = User.objects.create_superuser("admin", "admin@example.com", "Clave-segura-1")
        self.token = Token.objects.create(user=user)
        self.match = Match.objects.create(map_name="Erangel", training=False)
        player = Player.objects.create(name="slyfoxcl")
        MatchRecord.objects.create(
            match=self.match,
            player=player,
            kills=2,
            win_place=1,
            death_type="byzone",
        )

    def test_training_matches_are_left_out_of_the_public_table(self):
        counted = self.client.get("/api/match/records/")
        self.assertEqual(counted.json()[0]["player"], "slyfoxcl")

        response = self.client.patch(
            f"/api/match/{self.match.match_id}/",
            data={"training": True},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["training"])
        self.assertEqual(response.json()["participants"][0]["player"], "slyfoxcl")
        self.assertEqual(response.json()["participants"][0]["death"], "zona")
        self.assertEqual(self.client.get("/api/match/records/").json(), [])

    def test_list_requires_admin_and_returns_the_match(self):
        anonymous = self.client.get("/api/match/")
        self.assertEqual(anonymous.status_code, 401)

        response = self.client.get(
            "/api/match/",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body[0]["matchId"], str(self.match.match_id))
        self.assertEqual(body[0]["participantCount"], 1)
        self.assertFalse(body[0]["training"])


class RegistrationTests(TestCase):
    def test_first_account_is_admin_and_the_next_one_is_rejected(self):
        setup = self.client.get("/api/user/setup/")
        self.assertTrue(setup.json()["registrationOpen"])

        created = self.client.post(
            "/api/user/register/",
            data={"username": "rodo", "password": "Clave-segura-1"},
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        body = created.json()
        self.assertIn("token", body)
        user = User.objects.get(username="rodo")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        closed = self.client.get("/api/user/setup/")
        self.assertFalse(closed.json()["registrationOpen"])
        rejected = self.client.post(
            "/api/user/register/",
            data={"username": "otro", "password": "Clave-segura-1"},
            content_type="application/json",
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertFalse(User.objects.filter(username="otro").exists())

    def test_login_returns_a_token_and_rejects_a_wrong_password(self):
        User.objects.create_superuser("rodo", "rodo@example.com", "Clave-segura-1")
        ok = self.client.post(
            "/api/user/login/",
            data={"username": "rodo", "password": "Clave-segura-1"},
            content_type="application/json",
        )
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["token"])

        bad = self.client.post(
            "/api/user/login/",
            data={"username": "rodo", "password": "no-es"},
            content_type="application/json",
        )
        self.assertEqual(bad.status_code, 401)


class PubgApiDecoratorTests(SimpleTestCase):
    def tearDown(self):
        gateway._api = None

    def test_decorator_passes_the_pubg_api_instance(self):
        client = Mock()
        client.fetch_custom_match.return_value = []
        with patch.dict("os.environ", {"PUBG_API_KEY": "test-key"}):
            with patch("apps.pubg.gateway.PUBGAPI", return_value=client) as constructor:
                gateway._api = None
                first = gateway.get_matches("slyfoxcl")
                second = gateway.get_matches("otro", bulk=True)

        constructor.assert_called_once_with(api_key="test-key")
        self.assertIs(gateway._api, client)
        self.assertEqual(client.fetch_custom_match.call_args_list[0], call("slyfoxcl", items=1))
        self.assertEqual(client.fetch_custom_match.call_args_list[1], call("otro"))
        self.assertEqual(first, {})
        self.assertEqual(second, {})
