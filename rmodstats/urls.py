from django.conf.urls import url, include
from rest_framework_nested import routers
from rmodstats.api import views

router = routers.DefaultRouter()
router.register(r'subreddit', views.SubredditViewSet)

edge_router = routers.NestedSimpleRouter(router, r'subreddit', lookup='sub')
edge_router.register(r'edge', views.EdgeViewSet, base_name='subreddit-edge')

urlpatterns = [
    url(r'^api/v1/', include(router.urls)),
    url(r'^api/v1/', include(edge_router.urls)),
    url(r'^api/v1/status', views.StatusView.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
