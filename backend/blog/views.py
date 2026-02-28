from django.db.models import Count, Q, F, Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, Tag, Series, Post, PostImage, PostTemplate
from .serializers import (
    CategorySerializer, TagSerializer, SeriesSerializer,
    PostListSerializer, PostDetailSerializer, PostWriteSerializer,
    PostImageSerializer, PostTemplateSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'post_type', 'category__slug', 'series__slug']
    search_fields = ['title', 'content', 'summary']
    ordering_fields = ['created_at', 'published_at', 'view_count']
    lookup_field = 'slug'

    @method_decorator(cache_page(60 * 5))  # 5분 캐시 (목록)
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        qs = Post.objects.select_related('category', 'series', 'author').prefetch_related('tags')
        if self.request.user.is_authenticated:
            return qs
        return qs.filter(status='published')

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return PostWriteSerializer
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated or instance.author != request.user:
            Post.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
            instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @method_decorator(cache_page(60))  # 1분 캐시 (검색)
    @action(detail=False, methods=['get'])
    def search(self, request):
        q = request.query_params.get('q', '')
        if not q:
            return Response([])
        qs = self.get_queryset().filter(
            Q(title__icontains=q) | Q(content__icontains=q) | Q(summary__icontains=q)
        )[:20]
        serializer = PostListSerializer(qs, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True).annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).filter(post_count__gt=0)


class SeriesViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SeriesSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Series.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).filter(post_count__gt=0)


class PostTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PostTemplate.objects.all()
    serializer_class = PostTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


class ImageUploadView(generics.CreateAPIView):
    serializer_class = PostImageSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@cache_page(60 * 10)  # 10분 캐시
def dashboard_stats(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required'}, status=401)

    total_posts = Post.objects.filter(author=request.user).count()
    published = Post.objects.filter(author=request.user, status='published').count()
    drafts = Post.objects.filter(author=request.user, status='draft').count()
    total_views = Post.objects.filter(author=request.user).aggregate(
        total=Sum('view_count')
    )['total'] or 0

    category_dist = list(
        Post.objects.filter(author=request.user, status='published')
        .values('category__name', 'category__color')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    post_type_dist = list(
        Post.objects.filter(author=request.user, status='published')
        .values('post_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    recent_posts = list(
        Post.objects.filter(author=request.user)
        .order_by('-updated_at')
        .values('id', 'title', 'slug', 'status', 'updated_at')[:5]
    )

    return Response({
        'total_posts': total_posts,
        'published': published,
        'drafts': drafts,
        'total_views': total_views,
        'category_distribution': category_dist,
        'post_type_distribution': post_type_dist,
        'recent_posts': recent_posts,
    })


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})


@api_view(['GET'])
@cache_page(60 * 5)  # 5분 캐시
def public_stats(request):
    published = Post.objects.filter(status='published').count()
    categories = Category.objects.filter(parent__isnull=True).count()
    series_count = Series.objects.annotate(
        pc=Count('posts', filter=Q(posts__status='published'))
    ).filter(pc__gt=0).count()
    tags_count = Tag.objects.annotate(
        pc=Count('posts', filter=Q(posts__status='published'))
    ).filter(pc__gt=0).count()

    return Response({
        'total_posts': published,
        'categories': categories,
        'series': series_count,
        'tags': tags_count,
    })
