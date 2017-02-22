from rest_framework import viewsets, views, mixins, response, status
from django.db.models import Max, Count
from django.shortcuts import get_object_or_404
from datetime import datetime
from queue import Queue
from rmodstats.api.models import Subreddit, User, Failure, ModRelation
from rmodstats.api.serializers import ListViewSubredditSerializer, RetrieveSubredditSerializer, UserSerializer, FailureSerializer


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

class ModViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that returns all users that mod at least 2 subreddits. It
    restricts it to this as these are the only mods that contribute any
    relevent information.
    """
    serializer_class = UserSerializer
    queryset = User.objects.annotate(subs_modded=Count('subreddit')).filter(subs_modded__gt=1)

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


def get_edges(sub):
    edge_set = []
    sub_query = Subreddit.objects.get(name_lower=sub)
    for mod in sub_query.mods.all():
        for sub in mod.subreddit_set.all():
            if sub.name_lower == sub_query.name_lower:
                continue
            edge_set.append({
                'mod'  : mod.username,
                'from' : sub_query.name_lower,
                'to'   : sub.name_lower
            })

    return edge_set



class EdgeViewSet(viewsets.ViewSet):
    def list(self, request, sub_pk=None):
        edges = get_edges(sub_pk.lower())
        return response.Response(edges)
