from django.conf.urls import url, include
from rest_framework import routers
from rmodstats.api import views

router = routers.DefaultRouter()
router.register(r'subreddit', views.SubredditViewSet)
router.register(r'mods', views.ModViewSet, base_name='user')

urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/status', views.StatusView.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
