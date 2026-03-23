from rest_framework import serializers
from .mixins import ImageUrlMixin
from .models import (
    Category, Tag, Series, Post, PostImage, PostTemplate, PostLink,
    ArchitectureConcept, ArchitectureEntry, ArchitectureRelation,
)


class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'code', 'icon', 'color', 'parent', 'order', 'post_count', 'children']

    def get_children(self, obj):
        from django.db.models import Count, Q
        children = obj.children.annotate(
            post_count=Count('posts', filter=Q(posts__status='published'))
        ).order_by('order', 'code')
        if children.exists():
            return CategorySerializer(children, many=True).data
        return []


class TagSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'post_count']


class SeriesSerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Series
        fields = ['id', 'name', 'slug', 'description', 'order', 'post_count']


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'image_type', 'caption', 'source_ref', 'order', 'alt_text', 'created_at']


class PostListSerializer(ImageUrlMixin, serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    series_name = serializers.CharField(source='series.name', read_only=True, default=None)
    cover_image_url = serializers.SerializerMethodField()
    figure_url = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'summary', 'category', 'tags',
            'series_name', 'post_type', 'status', 'reading_time',
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
                return entry.figure.url
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
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.to_post.cover_image.url)
            return obj.to_post.cover_image.url
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
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.from_post.cover_image.url)
            return obj.from_post.cover_image.url
        return None


class FigureUrlMixin:
    """figure 필드의 절대 URL을 반환하는 공통 mixin."""
    def get_figure_url(self, obj):
        if not obj.figure:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.figure.url)
        return obj.figure.url


class ArchitectureConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitectureConcept
        fields = ['id', 'name', 'slug', 'abbreviation', 'color']


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
        return [{'name': r.to_entry.name, 'slug': r.to_entry.slug,
                 'relation_type': r.relation_type,
                 'post_slug': r.to_entry.related_post.slug if r.to_entry.related_post_id else None}
                for r in obj.parent_relations.select_related('to_entry', 'to_entry__related_post').all()[:5]]

    def get_child_names(self, obj):
        return [{'name': r.from_entry.name, 'slug': r.from_entry.slug,
                 'relation_type': r.relation_type,
                 'post_slug': r.from_entry.related_post.slug if r.from_entry.related_post_id else None}
                for r in obj.child_relations.select_related('from_entry', 'from_entry__related_post').all()[:5]]


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
            'architecture_category', 'branch_type', 'is_open_source',
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
            'architecture_category', 'branch_type', 'is_open_source',
            'tree_x', 'tree_y',
            'parent_relations', 'child_relations',
            'related_post', 'created_at', 'updated_at',
        ]


class ArchitectureTreeNodeSerializer(FigureUrlMixin, serializers.ModelSerializer):
    """트리 시각화용 경량 serializer"""
    figure_url = serializers.SerializerMethodField()

    class Meta:
        model = ArchitectureEntry
        fields = [
            'id', 'name', 'slug', 'organization', 'release_date',
            'decoder_type', 'param_scale', 'context_length',
            'architecture_category', 'branch_type', 'is_open_source',
            'tree_x', 'tree_y', 'figure_url', 'paper_url',
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
            'architecture_category', 'branch_type', 'is_open_source',
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
