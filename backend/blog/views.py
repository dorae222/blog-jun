import json
import os
from django.conf import settings
from django.db.models import Count, Q, F, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes, action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Category, Tag, Series, Post, PostImage, PostTemplate,
    ArchitectureConcept, ArchitectureEntry, ArchitectureRelation,
)
from .serializers import (
    CategorySerializer, TagSerializer, SeriesSerializer,
    PostListSerializer, PostDetailSerializer, PostWriteSerializer,
    PostImageSerializer, PostTemplateSerializer,
    PostLinkSerializer, BacklinkSerializer,
    ArchitectureConceptSerializer,
    ArchitectureEntryListSerializer,
    ArchitectureEntryDetailSerializer,
    ArchitectureEntryWriteSerializer,
    ArchitectureTreeNodeSerializer,
    ArchitectureRelationSerializer,
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
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'post_type', 'category__slug', 'series__slug']
    search_fields = ['title', 'content', 'summary']
    ordering_fields = ['created_at', 'published_at', 'view_count']
    lookup_field = 'slug'

    def list(self, request, *args, **kwargs):
        # 인증된 사용자(대시보드)는 캐시 bypass — 삭제 직후 즉시 반영
        if request.user.is_authenticated:
            return viewsets.ModelViewSet.list(self, request, *args, **kwargs)
        # 비인증 공개 목록에만 5분 캐시 적용
        return cache_page(60 * 5)(super().list)(request, *args, **kwargs)

    def get_queryset(self):
        qs = Post.objects.select_related('category', 'series', 'author').prefetch_related('tags')
        if self.action == 'retrieve':
            qs = qs.prefetch_related(
                'outgoing_links__to_post__category',
                'incoming_links__from_post__category',
                'architecture_entries__parent_relations__to_entry__related_post',
                'architecture_entries__child_relations__from_entry__related_post',
            )
        if self.request.user.is_authenticated:
            # has_cover 필터
            has_cover = self.request.query_params.get('has_cover')
            if has_cover == 'true':
                qs = qs.exclude(cover_image='').exclude(cover_image__isnull=True)
            elif has_cover == 'false':
                qs = qs.filter(Q(cover_image='') | Q(cover_image__isnull=True))
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
            Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
        ).annotate(
            relevance=Case(
                When(title__icontains=q, then=Value(3)),
                When(summary__icontains=q, then=Value(2)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('-relevance', '-view_count')[:20]
        serializer = PostListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_delete(self, request):
        slugs = request.data.get('slugs', [])
        if not slugs:
            return Response({'detail': 'slugs 필드가 필요합니다.'}, status=400)
        deleted, _ = Post.objects.filter(slug__in=slugs, author=request.user).delete()
        return Response({'deleted': deleted})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_cover(self, request, slug=None):
        """커버 이미지 생성/재생성."""
        from django.core.management import call_command
        post = self.get_object()
        try:
            call_command('generate_cover_images', slugs=slug, verbosity=0)
            post.refresh_from_db()
            cover_url = request.build_absolute_uri(post.cover_image.url) if post.cover_image else None
            return Response({
                'detail': '커버 이미지 생성 완료',
                'cover_image_url': cover_url,
            })
        except Exception as e:
            return Response({'detail': f'커버 생성 실패: {e}'}, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_update_status(self, request):
        slugs = request.data.get('slugs', [])
        new_status = request.data.get('status')
        valid_statuses = ['draft', 'published', 'archived']
        if not slugs:
            return Response({'detail': 'slugs 필드가 필요합니다.'}, status=400)
        if new_status not in valid_statuses:
            return Response({'detail': f'status는 {valid_statuses} 중 하나여야 합니다.'}, status=400)
        updated = Post.objects.filter(slug__in=slugs, author=request.user).update(status=new_status)
        return Response({'updated': updated})


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(parent__isnull=True).annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        )


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Tag.objects.annotate(post_count=Count('posts'))
        # 공개 목록은 포스트 있는 것만, 인증 사용자는 전체
        if not self.request.user.is_authenticated:
            qs = qs.filter(post_count__gt=0)
        return qs

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def merge(self, request):
        """source 태그의 포스트를 target으로 이전 후 source 삭제"""
        src_slug = request.data.get('source')
        dst_slug = request.data.get('target')
        if not src_slug or not dst_slug:
            return Response({'detail': 'source와 target이 필요합니다.'}, status=400)
        try:
            src = Tag.objects.get(slug=src_slug)
            dst = Tag.objects.get(slug=dst_slug)
        except Tag.DoesNotExist:
            return Response({'detail': '태그를 찾을 수 없습니다.'}, status=404)
        if src == dst:
            return Response({'detail': 'source와 target이 같습니다.'}, status=400)
        # 포스트 재연결
        for post in src.posts.all():
            post.tags.add(dst)
            post.tags.remove(src)
        moved = src.posts.count()
        src.delete()
        return Response({'merged': True, 'posts_moved': moved, 'target': dst_slug})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def cleanup(self, request):
        """포스트가 없는 고아 태그 일괄 삭제"""
        orphaned = Tag.objects.annotate(post_count=Count('posts')).filter(post_count=0)
        count = orphaned.count()
        orphaned.delete()
        return Response({'deleted_orphaned': count})


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

    base_qs = Post.objects.filter(author=request.user)
    stats = base_qs.aggregate(
        total_posts=Count('id'),
        published=Count('id', filter=Q(status='published')),
        drafts=Count('id', filter=Q(status='draft')),
        total_views=Sum('view_count'),
    )
    total_posts = stats['total_posts']
    published = stats['published']
    drafts = stats['drafts']
    total_views = stats['total_views'] or 0

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

    # 이미지 커버리지 통계
    published_qs = Post.objects.filter(author=request.user, status='published')
    with_cover = published_qs.exclude(cover_image='').exclude(cover_image__isnull=True).count()
    with_arch_figure = published_qs.filter(
        architecture_entries__figure__isnull=False
    ).exclude(architecture_entries__figure='').distinct().count()
    with_any_image = published_qs.filter(
        Q(~Q(cover_image=''), cover_image__isnull=False) |
        Q(architecture_entries__figure__isnull=False) & ~Q(architecture_entries__figure='')
    ).distinct().count()

    image_coverage = {
        'total_published': published,
        'with_cover_image': with_cover,
        'with_any_image': with_any_image,
        'missing_image': published - with_any_image,
    }

    image_coverage_by_category = list(
        published_qs
        .values('category__slug', 'category__name')
        .annotate(
            total=Count('id'),
            with_cover=Count('id', filter=~Q(cover_image='') & Q(cover_image__isnull=False)),
        )
        .order_by('-total')
    )

    return Response({
        'total_posts': total_posts,
        'published': published,
        'drafts': drafts,
        'total_views': total_views,
        'category_distribution': category_dist,
        'post_type_distribution': post_type_dist,
        'recent_posts': recent_posts,
        'image_coverage': image_coverage,
        'image_coverage_by_category': image_coverage_by_category,
    })


@api_view(['GET'])
@throttle_classes([])
def health_check(request):
    return Response({'status': 'ok'})


AUDIT_FILE = os.environ.get('AUDIT_FILE_PATH', os.path.join(settings.BASE_DIR, 'data', 'audit.json'))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_results(request):
    """감사 결과 JSON 파일을 읽어 반환"""
    if not os.path.exists(AUDIT_FILE):
        return Response({'total_audited': 0, 'total_issues': 0, 'results': []})
    try:
        with open(AUDIT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Response(data)
    except (json.JSONDecodeError, IOError) as e:
        return Response({'detail': f'감사 파일 읽기 오류: {e}'}, status=500)


class ArchitectureEntryViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['decoder_type', 'architecture_category', 'branch_type']

    def get_queryset(self):
        qs = ArchitectureEntry.objects.prefetch_related('concepts', 'related_post')
        concept = self.request.query_params.get('concept')
        if concept:
            qs = qs.filter(concepts__slug=concept)
        return qs.distinct()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ArchitectureEntryWriteSerializer
        if self.action == 'retrieve':
            return ArchitectureEntryDetailSerializer
        return ArchitectureEntryListSerializer

    @action(detail=False, methods=['get'])
    def concepts(self, request):
        qs = ArchitectureConcept.objects.all()
        serializer = ArchitectureConceptSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        stats = ArchitectureEntry.objects.values('decoder_type').annotate(
            count=Count('id')
        ).order_by('decoder_type')
        return Response(list(stats))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def upload_figure(self, request, slug=None):
        entry = self.get_object()
        figure = request.FILES.get('figure')
        if not figure:
            return Response({'detail': 'figure 파일이 필요합니다.'}, status=400)
        entry.figure = figure
        entry.figure_placeholder = False
        entry.save()
        return Response({'detail': 'Figure 업로드 완료', 'figure_url': request.build_absolute_uri(entry.figure.url)})

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """트리 시각화용 노드 + 엣지 반환. ?category=llm 으로 필터 가능"""
        entries = ArchitectureEntry.objects.select_related('related_post').all()
        relations = ArchitectureRelation.objects.select_related('from_entry', 'to_entry').all()

        category = request.query_params.get('category')
        if category:
            entries = entries.filter(architecture_category=category)
            slugs = set(entries.values_list('slug', flat=True))
            relations = relations.filter(
                Q(from_entry__slug__in=slugs) | Q(to_entry__slug__in=slugs)
            )

        return Response({
            'nodes': ArchitectureTreeNodeSerializer(entries, many=True, context={'request': request}).data,
            'edges': ArchitectureRelationSerializer(relations, many=True).data,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_position(self, request, slug=None):
        """트리 노드 위치 업데이트"""
        entry = self.get_object()
        entry.tree_x = request.data.get('x')
        entry.tree_y = request.data.get('y')
        entry.save(update_fields=['tree_x', 'tree_y'])
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def relations(self, request):
        """관계 생성/삭제"""
        if request.method == 'POST':
            from_slug = request.data.get('from_slug')
            to_slug = request.data.get('to_slug')
            relation_type = request.data.get('relation_type', 'evolved_from')
            description = request.data.get('description', '')
            try:
                from_entry = ArchitectureEntry.objects.get(slug=from_slug)
                to_entry = ArchitectureEntry.objects.get(slug=to_slug)
            except ArchitectureEntry.DoesNotExist:
                return Response({'detail': 'Entry를 찾을 수 없습니다.'}, status=404)
            relation, created = ArchitectureRelation.objects.get_or_create(
                from_entry=from_entry, to_entry=to_entry, relation_type=relation_type,
                defaults={'description': description}
            )
            return Response(
                ArchitectureRelationSerializer(relation).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        else:  # DELETE
            from_slug = request.data.get('from_slug')
            to_slug = request.data.get('to_slug')
            deleted, _ = ArchitectureRelation.objects.filter(
                from_entry__slug=from_slug, to_entry__slug=to_slug
            ).delete()
            return Response({'deleted': deleted})


class FeedView(generics.ListAPIView):
    """통합 피드 엔드포인트: Post + ArchitectureEntry를 통합 조회."""
    serializer_class = PostListSerializer

    # 프론트엔드 route key → DB Category slug 매핑
    CATEGORY_MAP = {
        'ai': 'ai-ml',
        'cloud': 'cloud',
        'data': 'data-engineering',
        'ml': 'ml',
    }

    def _get_sub_slugs(self, cat_slug):
        """DB에서 해당 카테고리의 서브카테고리 slug 목록을 동적 조회."""
        parent = Category.objects.filter(slug=cat_slug).first()
        if parent:
            return list(parent.children.values_list('slug', flat=True))
        return []

    def get_queryset(self):
        qs = Post.objects.filter(status='published').select_related(
            'category', 'category__parent', 'series', 'author'
        ).prefetch_related('tags')

        category = self.request.query_params.get('category')
        sub = self.request.query_params.get('sub')
        sort = self.request.query_params.get('sort', 'newest')
        q = self.request.query_params.get('q')
        tag = self.request.query_params.get('tag')
        pinned = self.request.query_params.get('pinned')

        # 카테고리 필터 (primary + secondary 모두 포함)
        if category and category in self.CATEGORY_MAP:
            cat_slug = self.CATEGORY_MAP[category]
            qs = qs.filter(
                Q(category__slug=cat_slug) | Q(category__parent__slug=cat_slug)
                | Q(categories__slug=cat_slug) | Q(categories__parent__slug=cat_slug)
            ).distinct()

        # 서브카테고리 필터 (DB에서 유효성 검증, primary + secondary)
        if sub and category and category in self.CATEGORY_MAP:
            cat_slug = self.CATEGORY_MAP[category]
            sub_slugs = self._get_sub_slugs(cat_slug)
            if sub in sub_slugs:
                qs = qs.filter(
                    Q(category__slug=sub) | Q(categories__slug=sub)
                ).distinct()

        # 태그 필터
        if tag:
            qs = qs.filter(tags__slug=tag)

        # 검색
        if q:
            qs = qs.filter(
                Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
            ).annotate(
                relevance=Case(
                    When(title__icontains=q, then=Value(3)),
                    When(summary__icontains=q, then=Value(2)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )

        # 고정글만
        if pinned == 'true':
            qs = qs.filter(is_pinned=True)

        # 정렬
        if q:
            qs = qs.order_by('-relevance', '-view_count')
        elif sort == 'popular':
            qs = qs.order_by('-view_count')
        else:
            qs = qs.order_by('-is_pinned', '-published_at', '-created_at')

        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        # 카운트 정보 (include_counts=true일 때만)
        if request.query_params.get('include_counts') == 'true':
            published = Post.objects.filter(status='published')
            categories_data = {}
            for key, cat_slug in self.CATEGORY_MAP.items():
                cat_posts = published.filter(
                    Q(category__slug=cat_slug) | Q(category__parent__slug=cat_slug)
                )
                total = cat_posts.count()
                # DB에서 서브카테고리 동적 조회 후 카운트
                sub_slugs = self._get_sub_slugs(cat_slug)
                subs = {}
                if sub_slugs:
                    subs = dict(
                        cat_posts.filter(category__slug__in=sub_slugs)
                        .values_list('category__slug')
                        .annotate(c=Count('id'))
                        .values_list('category__slug', 'c')
                    )
                categories_data[key] = {'count': total, 'subs': subs}
            response.data['categories'] = categories_data

        return response


@api_view(['GET'])
@cache_page(60 * 5)
def feed_popular(request):
    """인기글 Top N (조회수 기준)."""
    limit = int(request.query_params.get('limit', 5))
    limit = min(limit, 20)
    qs = Post.objects.filter(status='published').select_related(
        'category', 'series'
    ).prefetch_related('tags').order_by('-view_count')[:limit]
    serializer = PostListSerializer(qs, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cover_template_list(request):
    """사용 가능한 커버 템플릿 목록 반환."""
    templates = [
        {'id': 'paper_cover', 'name': 'Paper Cover', 'description': '논문 리뷰용 다크 학술 스타일'},
        {'id': 'category_gradient', 'name': 'Category Gradient', 'description': '카테고리 색상 그라디언트 + 아이콘'},
        {'id': 'architecture_diagram', 'name': 'Architecture Diagram', 'description': 'AI 아키텍처 다이어그램'},
    ]
    return Response(templates)


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
