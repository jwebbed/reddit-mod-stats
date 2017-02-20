from rest_framework import viewsets, views, response
from rest_framework import status
from django.db.models import Max, Count
from datetime import datetime
from queue import Queue
from rmodstats.api.models import Subreddit, User, Failure, ModRelation
from rmodstats.api.serializers import SubredditSerializer, UserSerializer, FailureSerializer


class SubredditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows subreddits to be viewed
    """
    queryset = Subreddit.objects.filter(forbidden=False)
    serializer_class = SubredditSerializer

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
