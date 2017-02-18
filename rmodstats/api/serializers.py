from rest_framework import serializers
from rmodstats.api.models import Subreddit


class SubredditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subreddit
        fields = ('name', 'subscribers', 'last_checked', 'last_changed', 'mods')
