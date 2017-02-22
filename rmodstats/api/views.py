from rest_framework import viewsets, views, mixins, response, status
from django.db.models import Max, Count
from django.shortcuts import get_object_or_404
from datetime import datetime
from queue import Queue
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

def get_edges(sub, prev_checked, depth_cap):
    edge_set, ancestor_set = [], []
    sub_query = Subreddit.objects.get(name_lower=sub)
    for mod in sub_query.mods.all():
        for sub in mod.subreddit_set.all():
            if sub.name_lower == sub_query.name_lower or sub.name_lower in prev_checked:
                continue
            edge = {
                'mod'  : mod.username,
                'from' : sub_query.name_lower,
                'to'   : sub.name_lower
            }
            edge_set.append(edge)
            ancestor_set.append(sub.name_lower)


    if depth_cap > len(prev_checked) + 1:
        new_checked = prev_checked + [sub]
        for sub in ancestor_set:
            edge_set += get_edges(sub, new_checked, depth_cap)
    return edge_set

class EdgeViewSet(viewsets.ViewSet):
    def list(self, request, sub_pk=None):
        edges = get_edges(sub_pk.lower(), [], 2)
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
