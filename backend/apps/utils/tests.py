from django.test import TestCase

from apps.core.models import Match, MatchRecord, PlayerProfile
from apps.utils.history_match import save_custom_matches


class SaveCustomMatchesTests(TestCase):
    def test_import_saves_pubg_fields_and_is_idempotent(self):
        match_json = {
            "data": {
                "id": "41c1db04-f36d-4b0b-a3d7-330c2c34601f",
                "attributes": {
                    "createdAt": "2026-10-13T20:00:00Z",
                    "mapName": "Baltic_Main",
                },
            },
            "included": [
                {
                    "type": "participant",
                    "attributes": {
                        "stats": {
                            "name": "winner",
                            "winPlace": 1,
                            "kills": 2,
                            "assists": 3,
                            "damageDealt": 120.5,
                            "timeSurvived": 1500.25,
                        }
                    },
                },
                {
                    "type": "participant",
                    "attributes": {
                        "stats": {
                            "name": "second",
                            "winPlace": 2,
                            "kills": 4,
                            "assists": 1,
                            "damageDealt": 250,
                            "timeSurvived": 1700,
                        }
                    },
                },
                {
                    "type": "participant",
                    "attributes": {
                        "stats": {
                            "name": "other",
                            "winPlace": 3,
                            "kills": 0,
                        }
                    },
                },
            ],
        }

        self.assertEqual(save_custom_matches([match_json]), 1)
        self.assertEqual(save_custom_matches([match_json]), 1)

        match = Match.objects.get()
        self.assertEqual(match.map_name, "Baltic_Main")
        self.assertEqual(match.match_date.isoformat(), "2026-10-13T20:00:00+00:00")
        self.assertEqual(MatchRecord.objects.count(), 3)

        winner = PlayerProfile.objects.get(name="winner")
        record = MatchRecord.objects.get(player_obj=winner)
        self.assertEqual(
            (record.win_place, record.kills, record.assists, record.damage_dealt, record.time_survived),
            (1, 2, 3, 120.5, 1500.25),
        )
        self.assertEqual(winner.total_points, 5)
        self.assertEqual(
            MatchRecord.objects.get(player_obj__name="other").placement,
            "none",
        )
