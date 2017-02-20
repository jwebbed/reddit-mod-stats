from rest_framework import viewsets, views, response
from django.db.models import Max
from datetime import datetime
from rmodstats.api.models import Subreddit, User, Failure
from rmodstats.api.serializers import SubredditSerializer, UserSerializer, FailureSerializer


class SubredditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows subreddits to be viewed
    """
    queryset = Subreddit.objects.filter(forbidden=False)
    serializer_class = SubredditSerializer

class ModViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows subreddits to be viewed
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

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
