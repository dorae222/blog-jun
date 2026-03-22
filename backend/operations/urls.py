from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('logs', views.OperationLogViewSet, basename='operation-log')
router.register('sessions', views.SessionLogViewSet, basename='session-log')

urlpatterns = [
    path('', include(router.urls)),
]
