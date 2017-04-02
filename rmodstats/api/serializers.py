from rest_framework import serializers
from rmodstats.api.models import Subreddit, SubredditEvent, SubredditEventDetail, Failure, Graph, Edge

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
        fields = ('name', 'subscribers', 'graph', 'nsfw', 'last_checked', 'last_changed', 'mods', 'events',)

class ListViewSubredditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subreddit
        fields = ('name', 'subscribers', 'graph', 'nsfw', 'last_checked', 'last_changed', 'mods',)

class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = ('source', 'target', 'mods',)

class RetrieveGraphSerializer(serializers.ModelSerializer):
    edge_set = EdgeSerializer(many=True, read_only=True)

    class Meta:
        model = Graph
        fields = ('id', 'edge_set', )

class ListGraphSerializer(serializers.ModelSerializer):
    class Meta:
        model = Graph
        fields = ('id', )

class FailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Failure
        fields = ('time', 'traceback',)
