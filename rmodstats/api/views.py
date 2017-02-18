from rest_framework import viewsets
from rmodstats.api.models import Subreddit
from rmodstats.api.serializers import SubredditSerializer


class SubredditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Subreddit.objects.filter(forbidden=False)
    serializer_class = SubredditSerializer
