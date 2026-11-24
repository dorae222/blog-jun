import json
import os
from collections import Counter, defaultdict

from django.core.cache import cache
from django.conf import settings
from django.db.models import Count, Q, F, Sum, Case, When, Value, IntegerField, Prefetch, Max
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes, action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Category, Tag, Series, Post, PostImage, PostTemplate,
    ArchitectureConcept, ArchitectureEntry, ArchitectureRelation, Branch,
    CloudServiceEntry, CloudServiceRelation, PostLink,
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
    CloudServiceTreeNodeSerializer,
    CloudServiceDetailSerializer,
    CloudServiceRelationSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """관리자만 글 작성/수정/삭제 가능, 나머지는 읽기만."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['status', 'post_type', 'category__slug', 'series__slug']
    search_fields = ['title', 'content', 'summary']
    ordering_fields = ['created_at', 'published_at', 'view_count', 'series_order']
    lookup_field = 'slug'

    def list(self, request, *args, **kwargs):
        # 인증된 사용자(대시보드)는 캐시 bypass - 삭제 직후 즉시 반영
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

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser],
            parser_classes=[MultiPartParser, FormParser])
    def cover(self, request, slug=None):
        """글 표지 업로드.

        지금까지 표지는 파이프라인 스크립트로만 갈아 끼울 수 있었다. 한 편만 바꾸려고
        서버에 붙는 것은 과하니 관리 화면에서 바로 올릴 수 있게 연다.
        """
        post = self.get_object()
        f = request.FILES.get('file') or request.FILES.get('cover_image')
        if not f:
            return Response({'detail': 'file 필드가 필요합니다.'}, status=400)
        post.cover_image.save(f.name, f, save=True)
        return Response({'cover_image_url': post.cover_image.url})

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_delete(self, request):
        slugs = request.data.get('slugs', [])
        if not slugs:
            return Response({'detail': 'slugs 필드가 필요합니다.'}, status=400)
        deleted, _ = Post.objects.filter(slug__in=slugs).delete()
        return Response({'deleted': deleted})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def generate_cover(self, request, slug=None):
        """커버 이미지 생성/재생성."""
        from django.core.management import call_command
        post = self.get_object()
        try:
            call_command('generate_cover_images', slugs=slug, verbosity=0)
            post.refresh_from_db()
            cover_url = request.build_absolute_uri(post.cover_image.url).replace('http://', 'https://', 1) if post.cover_image else None
            return Response({
                'detail': '커버 이미지 생성 완료',
                'cover_image_url': cover_url,
            })
        except Exception as e:
            return Response({'detail': f'커버 생성 실패: {e}'}, status=500)

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def bulk_update_status(self, request):
        slugs = request.data.get('slugs', [])
        new_status = request.data.get('status')
        valid_statuses = ['draft', 'published', 'archived']
        if not slugs:
            return Response({'detail': 'slugs 필드가 필요합니다.'}, status=400)
        if new_status not in valid_statuses:
            return Response({'detail': f'status는 {valid_statuses} 중 하나여야 합니다.'}, status=400)
        updated = Post.objects.filter(slug__in=slugs).update(status=new_status)
        return Response({'updated': updated})


class CategoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer

    def get_queryset(self):
        children_qs = Category.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).order_by('order', 'code')
        return Category.objects.filter(parent__isnull=True).annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).prefetch_related(
            Prefetch('children', queryset=children_qs)
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


class SeriesViewSet(viewsets.ModelViewSet):
    """시리즈 CRUD.

    목록/상세는 누구나 읽지만 쓰기는 관리자만. 관리 화면에서 글이 아직 없는
    시리즈도 만들어야 하므로, 편수 0 필터는 공개 조회에만 건다.
    """
    serializer_class = SeriesSerializer
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Series.objects.annotate(
            post_count=Count('posts', filter=Q(posts__status='published')),
            # 홈에서 노출 순서를 섞을 때 쓴다. 시리즈 자체에는 시각이 없어서
            # 소속 글 중 가장 최근 발행 시각을 시리즈의 최신도로 삼는다.
            last_post_at=Max('posts__published_at', filter=Q(posts__status='published')),
        )
        user = self.request.user
        if not (user and user.is_authenticated and user.is_staff):
            qs = qs.filter(post_count__gt=0)
        return qs.order_by('order', 'name')

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser],
            parser_classes=[MultiPartParser, FormParser])
    def cover(self, request, slug=None):
        """시리즈 표지 업로드. 관리 화면에서 파일을 바로 올린다."""
        series = self.get_object()
        f = request.FILES.get('file') or request.FILES.get('cover_image')
        if not f:
            return Response({'detail': 'file 필드가 필요합니다.'}, status=400)
        series.cover_image.save(f.name, f, save=True)
        return Response({'cover_image_url': series.cover_image.url})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reorder(self, request, slug=None):
        """편 순서 재배치. slugs 배열 순서대로 series_order 를 1부터 다시 매긴다."""
        series = self.get_object()
        slugs = request.data.get('slugs') or []
        if not isinstance(slugs, list):
            return Response({'detail': 'slugs 배열이 필요합니다.'}, status=400)
        changed = 0
        for i, ps in enumerate(slugs, start=1):
            p = Post.objects.filter(slug=ps, series=series).first()
            if p and p.series_order != i:
                p.series_order = i
                p.save(update_fields=['series_order'])
                changed += 1
        return Response({'reordered': changed})

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def members(self, request, slug=None):
        """글을 시리즈에 넣거나 뺀다. {add: [slug], remove: [slug]}"""
        series = self.get_object()
        added = removed = 0
        start = (Post.objects.filter(series=series)
                 .aggregate(m=Max('series_order'))['m'] or 0)
        for ps in request.data.get('add', []) or []:
            p = Post.objects.filter(slug=ps).first()
            if p and p.series_id != series.id:
                start += 1
                p.series = series
                p.series_order = start
                p.save(update_fields=['series', 'series_order'])
                added += 1
        for ps in request.data.get('remove', []) or []:
            p = Post.objects.filter(slug=ps, series=series).first()
            if p:
                p.series = None
                p.series_order = None
                p.save(update_fields=['series', 'series_order'])
                removed += 1
        return Response({'added': added, 'removed': removed})


class PostTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PostTemplate.objects.all()
    serializer_class = PostTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


class ImageUploadView(generics.CreateAPIView):
    serializer_class = PostImageSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAdminUser])
@cache_page(60 * 10)  # 10분 캐시
def dashboard_stats(request):
    base_qs = Post.objects.all()
    # 기본 통계 + 이미지 커버리지를 단일 aggregate로 통합
    stats = base_qs.aggregate(
        total_posts=Count('id'),
        published=Count('id', filter=Q(status='published')),
        drafts=Count('id', filter=Q(status='draft')),
        total_views=Sum('view_count'),
        with_cover_image=Count('id', filter=Q(
            status='published',
        ) & ~Q(cover_image='') & Q(cover_image__isnull=False)),
    )
    published = stats['published']

    # 카테고리 분포 + 이미지 커버리지 by 카테고리 통합
    published_qs = base_qs.filter(status='published')
    category_dist = list(
        published_qs
        .values('category__name', 'category__color', 'category__slug')
        .annotate(
            count=Count('id'),
            with_cover=Count('id', filter=~Q(cover_image='') & Q(cover_image__isnull=False)),
        )
        .order_by('-count')
    )

    post_type_dist = list(
        published_qs
        .values('post_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    recent_posts = list(
        base_qs.order_by('-updated_at')
        .values('id', 'title', 'slug', 'status', 'updated_at')[:5]
    )

    # with_any_image: 커버 또는 아키텍처 figure가 있는 포스트
    with_any_image = published_qs.filter(
        Q(~Q(cover_image=''), cover_image__isnull=False) |
        Q(architecture_entries__figure__isnull=False) & ~Q(architecture_entries__figure='')
    ).distinct().count()

    image_coverage = {
        'total_published': published,
        'with_cover_image': stats['with_cover_image'],
        'with_any_image': with_any_image,
        'missing_image': published - with_any_image,
    }

    # category_dist에서 이미 with_cover를 포함하므로 별도 쿼리 불필요
    image_coverage_by_category = [
        {
            'category__slug': c['category__slug'],
            'category__name': c['category__name'],
            'total': c['count'],
            'with_cover': c['with_cover'],
        }
        for c in category_dist
    ]

    return Response({
        'total_posts': stats['total_posts'],
        'published': published,
        'drafts': stats['drafts'],
        'total_views': stats['total_views'] or 0,
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
@permission_classes([IsAdminUser])
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
    filterset_fields = ['decoder_type', 'architecture_category', 'branch_type',
                        'branch__slug', 'entry_kind']

    def get_queryset(self):
        qs = ArchitectureEntry.objects.prefetch_related('concepts').select_related('related_post')
        if self.action == 'retrieve':
            qs = qs.prefetch_related(
                Prefetch('parent_relations',
                         queryset=ArchitectureRelation.objects.select_related(
                             'from_entry', 'from_entry__related_post')),
                Prefetch('child_relations',
                         queryset=ArchitectureRelation.objects.select_related(
                             'to_entry', 'to_entry__related_post')),
            )
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
        """트리 시각화용 노드 + 엣지 + 가지 목록 반환. ?category=llm 으로 필터 가능

        가지를 함께 내려보내는 이유는 범례 때문이다. 화면이 색과 이름을 따로 들고 있으면
        가지를 하나 늘릴 때마다 프론트엔드도 같이 고쳐야 한다.
        """
        # branch를 select_related에 넣지 않으면 노드마다 가지 조회가 한 번씩 더 나간다.
        entries = ArchitectureEntry.objects.select_related('related_post', 'branch').all()
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
            'branches': list(Branch.objects.values('slug', 'name', 'color', 'order', 'axis')),
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


class CloudServiceViewSet(viewsets.ModelViewSet):
    lookup_field = 'slug'
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'service_domain']

    def get_queryset(self):
        qs = CloudServiceEntry.objects.select_related('related_post')
        if self.action == 'retrieve':
            qs = qs.prefetch_related(
                Prefetch('outgoing_relations',
                         queryset=CloudServiceRelation.objects.select_related('to_service')),
                Prefetch('incoming_relations',
                         queryset=CloudServiceRelation.objects.select_related('from_service')),
            )
        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CloudServiceDetailSerializer
        return CloudServiceTreeNodeSerializer

    @action(detail=False, methods=['get'])
    def tree(self, request):
        entries = CloudServiceEntry.objects.select_related('related_post').all()
        relations = CloudServiceRelation.objects.select_related(
            'from_service', 'to_service'
        ).all()

        domain = request.query_params.get('domain')
        if domain:
            entries = entries.filter(service_domain=domain)
            slugs = set(entries.values_list('slug', flat=True))
            relations = relations.filter(
                Q(from_service__slug__in=slugs) | Q(to_service__slug__in=slugs)
            )

        # 층과 계열을 함께 싣는다. AI 트리가 `branches` 를 보내는 것과 같은 이유다.
        # 프런트가 같은 목록을 또 적어 두면 한쪽만 늘어난다. 실제로 `CLOUD_DOMAIN_COLORS`
        # 는 12종인데 필터 칩은 10종이어서 container·devops 노드가 그려지면서 필터에서
        # 사라진 적이 있다. AI 쪽 레인에서도 가지 6종이 같은 식으로 빠졌다.
        #
        # `order` 가 작을수록 위다. 층은 위가 추상이고 아래가 물리다.
        layers = [{'slug': v, 'name': lbl, 'order': i}
                  for i, (v, lbl) in enumerate(CloudServiceEntry.Layer.choices)]
        domains = [{'slug': v, 'name': lbl, 'order': i}
                   for i, (v, lbl) in enumerate(CloudServiceEntry.ServiceDomain.choices)]
        return Response({
            'nodes': CloudServiceTreeNodeSerializer(entries, many=True).data,
            'edges': CloudServiceRelationSerializer(relations, many=True).data,
            'layers': layers,
            'domains': domains,
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_position(self, request, slug=None):
        entry = self.get_object()
        entry.tree_x = request.data.get('x')
        entry.tree_y = request.data.get('y')
        entry.save(update_fields=['tree_x', 'tree_y'])
        return Response({'status': 'ok'})

    @action(detail=False, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def relations(self, request):
        if request.method == 'POST':
            from_slug = request.data.get('from_slug')
            to_slug = request.data.get('to_slug')
            relation_type = request.data.get('relation_type', 'integrates_with')
            description = request.data.get('description', '')
            try:
                from_svc = CloudServiceEntry.objects.get(slug=from_slug)
                to_svc = CloudServiceEntry.objects.get(slug=to_slug)
            except CloudServiceEntry.DoesNotExist:
                return Response({'detail': 'Service not found.'}, status=404)
            relation, created = CloudServiceRelation.objects.get_or_create(
                from_service=from_svc, to_service=to_svc, relation_type=relation_type,
                defaults={'description': description}
            )
            return Response(
                CloudServiceRelationSerializer(relation).data,
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        else:
            from_slug = request.data.get('from_slug')
            to_slug = request.data.get('to_slug')
            deleted, _ = CloudServiceRelation.objects.filter(
                from_service__slug=from_slug, to_service__slug=to_slug
            ).delete()
            return Response({'deleted': deleted})


class FeedView(generics.ListAPIView):
    """통합 피드 엔드포인트: Post + ArchitectureEntry를 통합 조회."""
    serializer_class = PostListSerializer

    # 프론트엔드 route key → DB Category slug 매핑
    # 대탭을 9개로 쪼개면서 슬러그가 곧 URL 조각이 됐다. 여기 남은 것은
    # 예전 주소로 들어오는 링크를 죽이지 않기 위한 호환 별칭뿐이다.
    CATEGORY_MAP = {
        'ai': 'llm',
        'ai-ml': 'llm',
        'cloud': 'aws',
        'data-engineering': 'data',
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

        # 카테고리 필터.
        # 예전에는 route key(ai/tool/cloud/data/ml)만 받아서, 'graphdb' 같은 소분류
        # 슬러그를 주면 매핑에 없다고 필터가 통째로 무시됐다. 결과가 전체 목록이라
        # 필터가 먹은 것처럼 보였고 오히려 더 헷갈렸다. 이제 DB에서 직접 해소한다.
        if category:
            cat_slug = self.CATEGORY_MAP.get(category, category)
            node = Category.objects.filter(slug=cat_slug).first()
            if node is None:
                qs = qs.none()
            elif node.parent_id is None:
                qs = qs.filter(
                    Q(category__slug=cat_slug) | Q(category__parent__slug=cat_slug)
                    | Q(categories__slug=cat_slug) | Q(categories__parent__slug=cat_slug)
                ).distinct()
            else:
                qs = qs.filter(
                    Q(category__slug=cat_slug) | Q(categories__slug=cat_slug)
                ).distinct()

        # 소분류 필터. category 없이 sub만 와도 동작하게 둔다.
        if sub:
            if Category.objects.filter(slug=sub).exists():
                qs = qs.filter(
                    Q(category__slug=sub) | Q(categories__slug=sub)
                ).distinct()
            else:
                qs = qs.none()

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
    # 글이 하나도 없는 대탭은 화면에도 안 나오므로 숫자에서도 뺀다
    categories = sum(
        1 for c in Category.objects.filter(parent__isnull=True).prefetch_related('children')
        if Post.objects.filter(
            Q(category=c) | Q(category__parent=c), status='published').exists()
    )
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

class KnowledgeGraphView(APIView):
    """홈 지식 그래프.

    링크가 하나도 없는 글까지 그리면 점만 흩뿌려지고, 위키링크만 쓰면 주제별로 섬이 생긴다.
    그래서 세 종류의 연결을 겹쳐 하나의 망으로 만든다.
      1) 위키링크 - 실제로 글이 글을 가리키는 강한 연결
      2) 태그 공유 - 같은 구체 태그를 쓰는 글끼리의 약한 연결
      3) 컴포넌트 잇기 - 그래도 떨어진 덩어리는 대표 노드끼리 이어 전체를 한 망으로
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 160)), 400)
        cache_key = f'knowledge_graph_v2_{limit}'
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)

        wiki = [
            (a, b) for a, b in PostLink.objects
            .filter(from_post__status='published', to_post__status='published')
            .values_list('from_post__slug', 'to_post__slug') if a != b
        ]

        deg = Counter()
        for a, b in wiki:
            deg[a] += 1
            deg[b] += 1

        # 태그를 많이 공유하는 글일수록 중심에 가깝다 - 후보를 넓혀 잡는다
        tag_rows = list(
            Post.objects.filter(status='published', tags__isnull=False)
            .values_list('tags__id', 'slug')
        )
        by_tag = defaultdict(list)
        for tid, slug in tag_rows:
            by_tag[tid].append(slug)

        tag_pairs = Counter()
        for tid, slugs in by_tag.items():
            # 너무 흔한 태그(수십 편)는 의미 있는 이웃 관계가 아니다
            if not (2 <= len(slugs) <= 8):
                continue
            uniq = sorted(set(slugs))
            for i in range(len(uniq)):
                for j in range(i + 1, len(uniq)):
                    tag_pairs[(uniq[i], uniq[j])] += 1

        for (a, b), w in tag_pairs.items():
            deg[a] += w * 0.35
            deg[b] += w * 0.35

        keep = {s for s, _ in deg.most_common(limit)}

        posts = (Post.objects.filter(status='published', slug__in=keep)
                 .select_related('category', 'category__parent')
                 .values('slug', 'title', 'category__slug', 'category__name',
                         'category__color', 'category__parent__slug'))

        nodes = [{
            'id': p['slug'],
            'title': p['title'],
            'category': p['category__slug'] or '',
            'categoryName': p['category__name'] or '',
            'group': p['category__parent__slug'] or p['category__slug'] or 'etc',
            'color': p['category__color'] or '',
            'degree': int(deg[p['slug']]),
        } for p in posts]

        node_ids = {n['id'] for n in nodes}
        edges = {}
        for a, b in wiki:
            if a in node_ids and b in node_ids:
                edges[(a, b)] = 'link'
        for (a, b), w in tag_pairs.items():
            if a in node_ids and b in node_ids and (a, b) not in edges and (b, a) not in edges:
                if w >= 2:               # 태그 두 개 이상 겹칠 때만
                    edges[(a, b)] = 'tag'

        # 3) 남은 섬을 잇는다 - 유니온 파인드로 덩어리를 찾고 대표끼리 연결
        parent = {n: n for n in node_ids}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for (a, b) in edges:
            union(a, b)

        comps = defaultdict(list)
        for n in node_ids:
            comps[find(n)].append(n)

        deg_of = {n['id']: n['degree'] for n in nodes}
        reps = [max(members, key=lambda s: deg_of.get(s, 0)) for members in comps.values()]
        reps.sort(key=lambda s: deg_of.get(s, 0), reverse=True)
        for other in reps[1:]:
            edges[(reps[0], other)] = 'bridge'

        edge_list = [{'source': a, 'target': b, 'kind': k} for (a, b), k in edges.items()]

        data = {
            'nodes': nodes,
            'edges': edge_list,
            'total_posts': Post.objects.filter(status='published').count(),
            'total_links': len(wiki),
            'components': 1 if nodes else 0,
        }
        cache.set(cache_key, data, 60 * 30)
        return Response(data)
