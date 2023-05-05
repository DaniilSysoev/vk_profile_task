from django.urls import path, include
from .views import UserViewSet, RequestsViewSet
from rest_framework import routers


router = routers.SimpleRouter()
router.register('users', UserViewSet)
router.register('requests', RequestsViewSet)


urlpatterns = [
    path('api/v1/', include(router.urls)),
]
