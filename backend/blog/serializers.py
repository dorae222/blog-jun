from rest_framework import serializers
from .mixins import ImageUrlMixin
from .models import (
    Category, Tag, Series, Post, PostImage, PostTemplate, PostLink,
    ArchitectureConcept, ArchitectureEntry, ArchitectureRelation,
    CloudServiceEntry, CloudServiceRelation,
)


class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)
    total_count = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'code', 'icon', 'color', 'parent', 'order',
                  'post_count', 'total_count', 'children']

    def get_total_count(self, obj):
        """자기 글 + 하위 글. 대탭은 직속 글이 없어 post_count가 0으로 보였다."""
        own = getattr(obj, 'post_count', 0) or 0
        kids = getattr(obj, 'children', None)
        if kids is None:
            return own
        return own + sum(getattr(k, 'post_count', 0) or 0 for k in kids.all())

    def get_children(self, obj):
        children = obj.children.all()  # prefetch 캐시 사용
        if children:
            return CategorySerializer(children, many=True).data
        return []


class TagSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'post_count']


class SeriesSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)
    # 홈에서 노출 순서를 섞을 때 쓰는 최신도. 뷰에서 annotate 한다.
    last_post_at = serializers.DateTimeField(read_only=True, required=False, allow_null=True)
    cover_image_url = serializers.SerializerMethodField()
    first_post_slug = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()
    category_group = serializers.SerializerMethodField()

    class Meta:
        model = Series
        fields = ['id', 'name', 'slug', 'description', 'order', 'post_count',
                  'last_post_at',
                  'cover_image', 'cover_image_url', 'first_post_slug', 'category_name',
                  'category_group']
        extra_kwargs = {'cover_image': {'write_only': True, 'required': False}}

    def _first_post(self, obj):
        """시리즈의 대표 글 - 편 번호가 가장 앞선 글."""
        if not hasattr(obj, '_cached_first'):
            obj._cached_first = (obj.posts.filter(status='published')
                                 .order_by('series_order', 'published_at')
                                 .select_related('category').first())
        return obj._cached_first

    def get_category_group(self, obj):
        """시리즈를 묶는 큰 단위. 하위 카테고리가 아니라 그 부모를 쓴다."""
        p = self._first_post(obj)
        c = p.category if p else None
        if not c:
            return None
        return (c.parent.name if c.parent else c.name)

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        p = self._first_post(obj)
        return p.cover_image.url if p and p.cover_image else None

    def get_first_post_slug(self, obj):
        p = self._first_post(obj)
        return p.slug if p else None

    def get_category_name(self, obj):
        p = self._first_post(obj)
        return p.category.name if p and p.category else None


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'image_type', 'caption', 'source_ref', 'order', 'alt_text', 'created_at']


class PostListSerializer(ImageUrlMixin, serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    series_name = serializers.CharField(source='series.name', read_only=True, default=None)
    cover_image_url = serializers.SerializerMethodField()
    figure_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'summary', 'category', 'categories', 'tags',
            'series_name', 'series_order', 'post_type', 'status', 'reading_time',
            'view_count', 'quality_score', 'is_pinned', 'cover_image_url',
            'figure_url', 'created_at', 'published_at',
        ]

    # get_cover_image_url는 ImageUrlMixin에서 제공

    def get_figure_url(self, obj):
        """ArchitectureEntry의 figure를 fallback으로 제공."""
        try:
            entry = obj.architecture_entries.first()
            if entry and entry.figure:
                return self._build_url(entry.figure)
        except Exception:
            pass
        return None


class PostLinkSerializer(serializers.ModelSerializer):
    """PostLink 관계를 위한 경량 serializer."""
    slug = serializers.CharField(source='to_post.slug', read_only=True)
    title = serializers.CharField(source='to_post.title', read_only=True)
    summary = serializers.CharField(source='to_post.summary', read_only=True, default='')
    category_name = serializers.CharField(source='to_post.category.name', read_only=True, default=None)
    category_color = serializers.CharField(source='to_post.category.color', read_only=True, default=None)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = PostLink
        fields = ['slug', 'title', 'summary', 'link_text', 'category_name', 'category_color', 'cover_image_url']

    def get_cover_image_url(self, obj):
        if obj.to_post.cover_image:
            return obj.to_post.cover_image.url  # 상대 경로 - mixed content 방지
        return None


class BacklinkSerializer(serializers.ModelSerializer):
    """역참조(backlink) 표시용 serializer."""
    slug = serializers.CharField(source='from_post.slug', read_only=True)
    title = serializers.CharField(source='from_post.title', read_only=True)
    summary = serializers.CharField(source='from_post.summary', read_only=True, default='')
    category_name = serializers.CharField(source='from_post.category.name', read_only=True, default=None)
    category_color = serializers.CharField(source='from_post.category.color', read_only=True, default=None)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = PostLink
        fields = ['slug', 'title', 'summary', 'link_text', 'category_name', 'category_color', 'cover_image_url']

    def get_cover_image_url(self, obj):
        if obj.from_post.cover_image:
            return obj.from_post.cover_image.url  # 상대 경로 - mixed content 방지
        return None


class FigureUrlMixin:
    """figure 필드의 절대 URL을 반환하는 공통 mixin."""
    def get_figure_url(self, obj):
        if not obj.figure:
            return None
        return obj.figure.url  # 상대 경로 - mixed content 방지


class CoverFirstFigureUrlMixin(FigureUrlMixin):
    """그림을 글의 현재 표지에서 가져오고, 표지가 없을 때만 figure로 물러난다.

    entry.figure는 표지 통일 재제작 이전에 따로 올린 자산이라 그 뒤로 갱신이 끊겼다.
    파일명이 무작위 해시(architecture_8yeWmlB.png)라 어느 글의 것인지 대조도 안 되고,
    그래서 트리 미리보기만 한 세대 뒤처져 있었다. 자산을 또 한 벌 복제하는 대신
    related_post의 cover_image를 가리키게 해 두면 표지를 다시 만들 때 트리가 저절로 따라온다.
    figure가 아예 없던 노드도 표지로 채워진다.

    쓰는 쪽에서 related_post를 select_related로 미리 당겨 두어야 노드마다 조회가 한 번씩 더 나가지 않는다.
    """
    def get_figure_url(self, obj):
        post = obj.related_post
        if post and post.cover_image:
            return post.cover_image.url  # 상대 경로 - mixed content 방지
        return super().get_figure_url(obj)


class ArchitectureConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitectureConcept
        # description을 빼 두면 태그에 마우스를 올려도 설명이 안 뜬다.
        # 개념 660개에 설명을 써 놓고도 화면에 못 내보내고 있었다.
        fields = ['id', 'name', 'slug', 'abbreviation', 'color', 'description']


class ArchitectureEntryBriefSerializer(FigureUrlMixin, serializers.ModelSerializer):
    """PostView에서 사용하는 아키텍처 간략 정보 (Lineage Card용)."""
    parent_names = serializers.SerializerMethodField()
    child_names = serializers.SerializerMethodField()
    concepts = ArchitectureConceptSerializer(many=True, read_only=True)
    figure_url = serializers.SerializerMethodField()
    related_post_slug = serializers.SlugRelatedField(
        source='related_post', slug_field='slug', read_only=True
    )

    class Meta:
        model = ArchitectureEntry
        fields = [
            'name', 'slug', 'organization', 'branch_type',
            'architecture_category', 'key_detail', 'param_scale',
            'context_length', 'attention_type', 'concepts',
            'paper_url', 'code_url', 'figure_url', 'release_date',
            'related_post_slug', 'parent_names', 'child_names',
        ]

    def get_parent_names(self, obj):
        # child_relations: from_entry=obj → obj가 자식 → to_entry가 부모
        return [{'name': r.to_entry.name, 'slug': r.to_entry.slug,
                 'relation_type': r.relation_type,
                 'post_slug': r.to_entry.related_post.slug if r.to_entry.related_post_id else None}
                for r in obj.child_relations.select_related('to_entry', 'to_entry__related_post').all()[:5]]

    def get_child_names(self, obj):
        # parent_relations: to_entry=obj → obj가 부모 → from_entry가 자식
        return [{'name': r.from_entry.name, 'slug': r.from_entry.slug,
                 'relation_type': r.relation_type,
                 'post_slug': r.from_entry.related_post.slug if r.from_entry.related_post_id else None}
                for r in obj.parent_relations.select_related('from_entry', 'from_entry__related_post').all()[:5]]


class PostDetailSerializer(ImageUrlMixin, serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    adjacent_posts = serializers.SerializerMethodField()
    related_posts = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    outgoing_links = PostLinkSerializer(many=True, read_only=True)
    incoming_links = BacklinkSerializer(many=True, read_only=True)
    architecture_entries = ArchitectureEntryBriefSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'summary', 'category', 'tags',
            'series', 'series_order', 'post_type', 'status', 'quality_score',
            'reading_time', 'view_count', 'arxiv_url', 'venue', 'paper_year',
            'paper_authors', 'created_at', 'updated_at',
            'published_at', 'images', 'adjacent_posts', 'related_posts',
            'pdf_file', 'cover_image_url', 'outgoing_links', 'incoming_links',
            'architecture_entries',
        ]

    # get_cover_image_url는 ImageUrlMixin에서 제공

    def get_pdf_file(self, obj):
        return self._build_url(obj.pdf_file)

    def get_adjacent_posts(self, obj):
        result = {}
        if obj.series:
            prev_post = Post.objects.filter(
                series=obj.series, series_order__lt=obj.series_order, status='published'
            ).order_by('-series_order').values('id', 'title', 'slug').first()
            next_post = Post.objects.filter(
                series=obj.series, series_order__gt=obj.series_order, status='published'
            ).order_by('series_order').values('id', 'title', 'slug').first()
            result['prev'] = prev_post
            result['next'] = next_post
        return result

    def get_related_posts(self, obj):
        """비시리즈 포스트용: 같은 카테고리의 최근 포스트 3개."""
        if obj.series:
            return []
        if not obj.category_id:
            return []
        qs = Post.objects.filter(
            status='published', category=obj.category
        ).exclude(pk=obj.pk).order_by('-published_at')[:3]
        return list(qs.values('id', 'title', 'slug'))


class PostWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'content', 'summary', 'category', 'tags',
            'series', 'series_order', 'post_type', 'status', 'published_at',
            'arxiv_url', 'venue', 'paper_year', 'paper_authors',
        ]

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        post = Post.objects.create(**validated_data)
        post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


class PostTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostTemplate
        fields = ['id', 'name', 'description', 'content_template', 'post_type', 'category']


class ArchitectureRelationSerializer(serializers.ModelSerializer):
    from_slug = serializers.SlugRelatedField(source='from_entry', slug_field='slug', read_only=True)
    to_slug = serializers.SlugRelatedField(source='to_entry', slug_field='slug', read_only=True)
    from_name = serializers.CharField(source='from_entry.name', read_only=True)
    to_name = serializers.CharField(source='to_entry.name', read_only=True)

    class Meta:
        model = ArchitectureRelation
        fields = ['id', 'from_slug', 'to_slug', 'from_name', 'to_name', 'relation_type', 'description']


class ArchitectureEntryListSerializer(FigureUrlMixin, serializers.ModelSerializer):
    concepts = ArchitectureConceptSerializer(many=True, read_only=True)
    figure_url = serializers.SerializerMethodField()
    related_post_slug = serializers.SlugRelatedField(
        source='related_post', slug_field='slug', read_only=True
    )

    class Meta:
        model = ArchitectureEntry
        fields = [
            'id', 'name', 'slug', 'organization', 'release_date',
            'decoder_type', 'concepts', 'param_scale', 'context_length',
            'attention_type', 'normalization', 'activation', 'key_detail',
            'figure_url', 'figure_placeholder', 'paper_url', 'license_type',
            'architecture_category', 'branch_type', 'entry_kind', 'is_open_source',
            'related_post_slug',
        ]


class ArchitectureEntryDetailSerializer(FigureUrlMixin, serializers.ModelSerializer):
    concepts = ArchitectureConceptSerializer(many=True, read_only=True)
    figure_url = serializers.SerializerMethodField()
    related_post = PostListSerializer(read_only=True)
    parent_relations = ArchitectureRelationSerializer(many=True, read_only=True)
    child_relations = ArchitectureRelationSerializer(many=True, read_only=True)

    class Meta:
        model = ArchitectureEntry
        fields = [
            'id', 'name', 'slug', 'organization', 'release_date',
            'decoder_type', 'concepts', 'param_scale', 'context_length',
            'attention_type', 'normalization', 'activation', 'position_encoding',
            'vocab_size', 'hidden_dim', 'num_layers', 'num_heads',
            'num_experts', 'active_experts',
            'description', 'key_detail', 'training_detail',
            'paper_url', 'code_url', 'license_type',
            'figure_url', 'figure_placeholder',
            'architecture_category', 'branch_type', 'entry_kind', 'is_open_source',
            'tree_x', 'tree_y',
            'parent_relations', 'child_relations',
            'related_post', 'created_at', 'updated_at',
        ]


class ArchitectureTreeNodeSerializer(CoverFirstFigureUrlMixin, serializers.ModelSerializer):
    """트리 시각화용 경량 serializer - D3.js 그래프에서 사용

    figure_url은 글의 현재 표지를 따라간다. CoverFirstFigureUrlMixin 설명을 보라.
    """
    figure_url = serializers.SerializerMethodField()
    # 가지 색과 이름을 노드마다 실어 보낸다. 화면이 색을 따로 들고 있으면
    # 가지를 하나 늘릴 때마다 프론트엔드도 같이 고쳐야 한다.
    branch_name = serializers.CharField(source='branch.name', read_only=True, default='')
    branch_color = serializers.CharField(source='branch.color', read_only=True, default='')
    branch_order = serializers.IntegerField(source='branch.order', read_only=True, default=0)
    related_post_slug = serializers.SlugRelatedField(
        source='related_post', slug_field='slug', read_only=True
    )

    class Meta:
        model = ArchitectureEntry
        fields = [
            'id', 'name', 'slug', 'organization', 'release_date',
            'decoder_type', 'param_scale', 'context_length',
            'architecture_category', 'branch_type', 'is_open_source',
            'branch_name', 'branch_color', 'branch_order', 'entry_kind',
            'tree_x', 'tree_y', 'figure_url', 'paper_url',
            'related_post_slug', 'key_detail',
        ]


class ArchitectureEntryWriteSerializer(serializers.ModelSerializer):
    concepts = serializers.SlugRelatedField(
        many=True, slug_field='slug', queryset=ArchitectureConcept.objects.all(), required=False
    )

    class Meta:
        model = ArchitectureEntry
        fields = [
            'name', 'slug', 'organization', 'release_date',
            'decoder_type', 'param_scale', 'context_length',
            'attention_type', 'normalization', 'activation', 'position_encoding',
            'vocab_size', 'hidden_dim', 'num_layers', 'num_heads',
            'num_experts', 'active_experts',
            'description', 'key_detail', 'training_detail',
            'paper_url', 'code_url', 'license_type',
            'architecture_category', 'branch_type', 'entry_kind', 'is_open_source',
            'tree_x', 'tree_y', 'concepts',
        ]

    def create(self, validated_data):
        concepts = validated_data.pop('concepts', [])
        entry = ArchitectureEntry.objects.create(**validated_data)
        entry.concepts.set(concepts)
        return entry

    def update(self, instance, validated_data):
        concepts = validated_data.pop('concepts', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if concepts is not None:
            instance.concepts.set(concepts)
        return instance


# ── Cloud Service Serializers ───────────────────────────

class CloudServiceRelationSerializer(serializers.ModelSerializer):
    from_slug = serializers.SlugRelatedField(
        source='from_service', slug_field='slug', read_only=True
    )
    to_slug = serializers.SlugRelatedField(
        source='to_service', slug_field='slug', read_only=True
    )
    from_name = serializers.CharField(source='from_service.name', read_only=True)
    to_name = serializers.CharField(source='to_service.name', read_only=True)

    class Meta:
        model = CloudServiceRelation
        fields = [
            'id', 'from_slug', 'to_slug', 'from_name', 'to_name',
            'relation_type', 'description',
        ]


class CloudServiceTreeNodeSerializer(serializers.ModelSerializer):
    related_post_slug = serializers.SlugRelatedField(
        source='related_post', slug_field='slug', read_only=True
    )

    class Meta:
        model = CloudServiceEntry
        fields = [
            'id', 'name', 'slug', 'provider', 'service_domain', 'layer',
            'launch_year', 'is_serverless', 'is_managed', 'importance',
            'tree_x', 'tree_y', 'key_detail', 'docs_url',
            'related_post_slug',
        ]


class CloudServiceDetailSerializer(serializers.ModelSerializer):
    related_post_slug = serializers.SlugRelatedField(
        source='related_post', slug_field='slug', read_only=True
    )
    outgoing_relations = CloudServiceRelationSerializer(many=True, read_only=True)
    incoming_relations = CloudServiceRelationSerializer(many=True, read_only=True)

    class Meta:
        model = CloudServiceEntry
        fields = [
            'id', 'name', 'slug', 'provider', 'service_domain',
            'launch_year', 'is_serverless', 'is_managed', 'pricing_model',
            'description', 'key_detail', 'use_cases', 'docs_url',
            'icon_name', 'importance', 'tree_x', 'tree_y',
            'related_post_slug', 'outgoing_relations', 'incoming_relations',
            'created_at', 'updated_at',
        ]
