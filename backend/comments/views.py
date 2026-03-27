from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes as perm_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from blog.models import Post
from blog.pagination import StandardPagination
from blog.throttles import CommentRateThrottle
from .models import Comment
from .permissions import IsCommentAuthorOrReadOnly
from .serializers import CommentSerializer, CommentCreateSerializer, AdminCommentSerializer


class PostCommentViewSet(viewsets.ViewSet):
    """포스트별 댓글 목록 조회 및 작성."""
    permission_classes = [IsCommentAuthorOrReadOnly]

    def list(self, request, post_slug=None):
        """GET /api/posts/{slug}/comments/ — 최상위 댓글 + replies"""
        post = get_object_or_404(Post, slug=post_slug, status='published')
        comments = (
            Comment.objects
            .filter(post=post, parent__isnull=True)
            .select_related('author')
            .prefetch_related(
                Prefetch('replies', queryset=Comment.objects.select_related('author').order_by('created_at'))
            )
            .order_by('created_at')
        )
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def create(self, request, post_slug=None):
        """POST /api/posts/{slug}/comments/ — 댓글/답글 작성"""
        post = get_object_or_404(Post, slug=post_slug, status='published')

        # Rate limiting
        throttle = CommentRateThrottle()
        if not throttle.allow_request(request, self):
            return Response(
                {'detail': '댓글 작성 제한을 초과했습니다. 잠시 후 다시 시도해주세요.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # parent가 같은 포스트에 속하는지 검증
        parent = serializer.validated_data.get('parent')
        if parent and parent.post_id != post.id:
            return Response(
                {'detail': '답글 대상이 이 포스트에 속하지 않습니다.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comment = serializer.save(post=post, author=request.user)
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )


class CommentDetailViewSet(viewsets.ViewSet):
    """개별 댓글 수정/삭제."""
    permission_classes = [IsCommentAuthorOrReadOnly]

    def partial_update(self, request, pk=None):
        """PATCH /api/comments/{id}/ — 댓글 수정"""
        comment = get_object_or_404(Comment, pk=pk)
        self.check_object_permissions(request, comment)

        if comment.is_deleted:
            return Response({'detail': '삭제된 댓글은 수정할 수 없습니다.'}, status=400)

        content = request.data.get('content')
        if not content:
            return Response({'detail': 'content 필드가 필요합니다.'}, status=400)
        if len(content) > 2000:
            return Response({'detail': '댓글은 2000자를 초과할 수 없습니다.'}, status=400)

        comment.content = content
        comment.is_edited = True
        comment.save(update_fields=['content', 'is_edited', 'updated_at'])
        return Response(CommentSerializer(comment).data)

    def destroy(self, request, pk=None):
        """DELETE /api/comments/{id}/ — 소프트 삭제"""
        comment = get_object_or_404(Comment, pk=pk)
        self.check_object_permissions(request, comment)

        comment.is_deleted = True
        comment.save(update_fields=['is_deleted', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── 관리자 전용 API ──

@api_view(['GET'])
@perm_classes([IsAdminUser])
def admin_comment_list(request):
    """GET /api/admin/comments/ — 관리자 댓글 목록 (페이지네이션)"""
    qs = Comment.objects.select_related('author', 'post').order_by('-created_at')

    # 필터
    is_deleted = request.query_params.get('is_deleted')
    if is_deleted == 'true':
        qs = qs.filter(is_deleted=True)
    elif is_deleted == 'false':
        qs = qs.filter(is_deleted=False)

    post_slug = request.query_params.get('post')
    if post_slug:
        qs = qs.filter(post__slug=post_slug)

    search = request.query_params.get('search')
    if search:
        qs = qs.filter(Q(content__icontains=search) | Q(author__username__icontains=search))

    paginator = StandardPagination()
    page = paginator.paginate_queryset(qs, request)
    serializer = AdminCommentSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@perm_classes([IsAdminUser])
def admin_comment_stats(request):
    """GET /api/admin/comments/stats/ — 댓글 통계"""
    stats = Comment.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_deleted=False)),
        deleted=Count('id', filter=Q(is_deleted=True)),
    )
    # 최근 7일 댓글 수
    from django.utils import timezone
    from datetime import timedelta
    week_ago = timezone.now() - timedelta(days=7)
    stats['recent_7d'] = Comment.objects.filter(created_at__gte=week_ago, is_deleted=False).count()

    return Response(stats)


@api_view(['DELETE'])
@perm_classes([IsAdminUser])
def admin_comment_bulk_delete(request):
    """DELETE /api/admin/comments/bulk-delete/ — 벌크 소프트 삭제"""
    ids = request.data.get('ids', [])
    if not ids:
        return Response({'detail': 'ids 필드가 필요합니다.'}, status=400)

    updated = Comment.objects.filter(id__in=ids).update(is_deleted=True)
    return Response({'deleted': updated})
