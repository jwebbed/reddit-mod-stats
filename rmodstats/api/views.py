from datetime import datetime
from queue import Queue

from rest_framework import viewsets, views, mixins, response, status
from django.db.models import Max, Count
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from rmodstats.api.models import Subreddit, User, Failure, ModRelation, Graph
from rmodstats.api.serializers import ListViewSubredditSerializer, RetrieveSubredditSerializer, FailureSerializer, RetrieveGraphSerializer, ListGraphSerializer


class SubredditViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API endpoint that allows subreddits to be viewed
    """
    queryset = Subreddit.objects.filter(forbidden=False)
    serializer_class = ListViewSubredditSerializer

    def retrieve(self, request, pk=None):
        queryset = Subreddit.objects.filter(forbidden=False)
        sub = get_object_or_404(queryset, pk=pk.lower())
        serializer = RetrieveSubredditSerializer(sub)
        return response.Response(serializer.data)

class GraphViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    '''
    API endpoint that exposes subreddit mod graphs
    '''
    queryset = Graph.objects.all()
    serializer_class = ListGraphSerializer

    def retrieve(self, request, pk=None, format=None):
        queryset = Graph.objects.all()
        graph = get_object_or_404(queryset, pk=pk)
        serializer = RetrieveGraphSerializer(graph)
        return response.Response(serializer.data)


class StatusView(views.APIView):
    def get(self, request, format=None):
        res = {}
        now = datetime.now()
        most_recent_check = Subreddit.objects.filter(forbidden=False).aggregate(Max('last_checked'))['last_checked__max']
        res['latest_check']= now - most_recent_check

        failures = Failure.objects.all()
        serializer = FailureSerializer(failures, many=True)
        res['failures'] = serializer.data

        return response.Response(res)
