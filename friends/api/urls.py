from django.urls import path, include
from .views import UserViewSet, RequestsViewSet, FriendsListViewSet
from rest_framework import routers


router = routers.SimpleRouter()
router.register('users', UserViewSet)
router.register('requests', RequestsViewSet)
router.register('friends', FriendsListViewSet)


urlpatterns = [
    path('api/v1/', include(router.urls)),
]
