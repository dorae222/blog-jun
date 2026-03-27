from django.urls import path
from . import views

urlpatterns = [
    path(
        'posts/<slug:post_slug>/comments/',
        views.PostCommentViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='post-comments',
    ),
    path(
        'comments/<int:pk>/',
        views.CommentDetailViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy'}),
        name='comment-detail',
    ),
    # 관리자 전용
    path('admin/comments/', views.admin_comment_list, name='admin-comment-list'),
    path('admin/comments/stats/', views.admin_comment_stats, name='admin-comment-stats'),
    path('admin/comments/bulk-delete/', views.admin_comment_bulk_delete, name='admin-comment-bulk-delete'),
]
