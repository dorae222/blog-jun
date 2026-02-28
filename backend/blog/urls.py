from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'tags', views.TagViewSet, basename='tag')
router.register(r'series', views.SeriesViewSet, basename='series')
router.register(r'templates', views.PostTemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.ImageUploadView.as_view(), name='image-upload'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    path('stats/', views.public_stats, name='public-stats'),
    path('health/', views.health_check, name='health-check'),
]
