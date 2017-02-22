from rest_framework import serializers
from rmodstats.api.models import Subreddit, SubredditEvent, SubredditEventDetail, User, Failure

class SubredditEventDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubredditEventDetail
        fields = ('user', 'addition',)

class SubredditEventSerializer(serializers.ModelSerializer):
    details = SubredditEventDetailSerializer(many=True, read_only=True)

    class Meta:
        model = SubredditEvent
        fields = ('recorded', 'previous_check', 'new', 'details',)

class RetrieveSubredditSerializer(serializers.ModelSerializer):
    events = SubredditEventSerializer(many=True, read_only=True)

    class Meta:
        model = Subreddit
        fields = ('name', 'subscribers', 'nsfw', 'last_checked', 'last_changed', 'mods', 'events', )

class ListViewSubredditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subreddit
        fields = ('name', 'subscribers', 'nsfw', 'last_checked', 'last_changed', 'mods',)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'subreddit_set',)

class FailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Failure
        fields = ('time', 'traceback',)
