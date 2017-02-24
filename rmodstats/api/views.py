from datetime import datetime
from queue import Queue

from rest_framework import viewsets, views, mixins, response, status
from django.db.models import Max, Count
from django.shortcuts import get_object_or_404
from django.core.cache import cache

from rmodstats.api.models import Subreddit, User, Failure, ModRelation
from rmodstats.api.serializers import ListViewSubredditSerializer, RetrieveSubredditSerializer, FailureSerializer


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

def get_edges(initial_sub):
    visited_subs = set()
    sub_queue = Queue()
    edge_set = {}

    sub_queue.put(initial_sub)
    while not sub_queue.empty():
        sub = sub_queue.get()
        if sub in visited_subs:
            continue

        edge_set[sub] = {}
        visited_subs.add(sub)
        local_subs = set()
        
        sub_query = Subreddit.objects.only('mods').get(name_lower=sub)
        for mod in sub_query.mods.all().prefetch_related('subreddit_set'):
            for child_sub in mod.subreddit_set.values_list('name_lower', flat=True):
                if child_sub == sub_query.name_lower:
                    continue

                if child_sub in edge_set[sub]:
                    edge_set[sub][child_sub].append(mod.username)
                else:
                    edge_set[sub][child_sub] = [mod.username]

                if child_sub not in visited_subs and child_sub not in local_subs:
                    sub_queue.put(child_sub)
                    local_subs.add(child_sub)

    edge_list = []
    for outer in edge_set:
        for inner in edge_set[outer]:
            edge = {
                'from' : outer,
                'to' : inner,
                'mods' : edge_set[outer][inner]
            }
            edge_list.append(edge)
    return edge_list

class EdgeViewSet(viewsets.ViewSet):
    def list(self, request, sub_pk=None):
        edges = get_edges(sub_pk.lower())
        return response.Response(edges)

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
