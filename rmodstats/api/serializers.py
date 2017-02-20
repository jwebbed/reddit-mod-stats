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

class SubredditSerializer(serializers.ModelSerializer):
    events = SubredditEventSerializer(many=True, read_only=True)

    class Meta:
        model = Subreddit
        fields = ('name', 'subscribers', 'nsfw', 'last_checked', 'last_changed', 'mods', 'events', )

class UserSubredditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subreddit
        fields = ('name',)

class UserSerializer(serializers.ModelSerializer):
    modded_subs = UserSubredditSerializer(source='subreddit_set', many=True, read_only=True)

    class Meta:
        model = User
        fields = ('username', 'modded_subs')

class FailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Failure
        fields = ('time', 'traceback',)
