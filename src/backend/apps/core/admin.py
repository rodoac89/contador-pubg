from django.contrib import admin

from apps.core.models import Match, MatchRecord, Player, Tournament

admin.site.register(Tournament)
admin.site.register(Player)
admin.site.register(MatchRecord)
admin.site.register(Match)
