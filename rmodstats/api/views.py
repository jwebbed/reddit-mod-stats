from rest_framework import viewsets, views, response
from django.db.models import Max
from datetime import datetime
from rmodstats.api.models import Subreddit
from rmodstats.api.serializers import SubredditSerializer


class SubredditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Subreddit.objects.filter(forbidden=False)
    serializer_class = SubredditSerializer

class StatusView(views.APIView):
    def get(self, request, format=None):
        last_checked = Subreddit.objects.filter(forbidden=False).aggregate(Max('last_checked'))['last_checked__max']
        return response.Response(datetime.now() - last_checked)
