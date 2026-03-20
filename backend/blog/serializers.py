from rest_framework import serializers
from .models import Category, Tag, Series, Post, PostImage, PostTemplate


class CategorySerializer(serializers.ModelSerializer):
    post_count = serializers.IntegerField(read_only=True, default=0)
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'code', 'icon', 'color', 'parent', 'order', 'post_count', 'children']

    def get_children(self, obj):
        children = obj.children.all()
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
        fields = ['id', 'image', 'alt_text', 'created_at']


class PostListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    series_name = serializers.CharField(source='series.name', read_only=True, default=None)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'summary', 'category', 'tags',
            'series_name', 'post_type', 'status', 'reading_time',
            'view_count', 'created_at', 'published_at',
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    series = SeriesSerializer(read_only=True)
    images = PostImageSerializer(many=True, read_only=True)
    adjacent_posts = serializers.SerializerMethodField()
    pdf_file = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'summary', 'category', 'tags',
            'series', 'series_order', 'post_type', 'status', 'quality_score',
            'reading_time', 'view_count', 'created_at', 'updated_at',
            'published_at', 'images', 'adjacent_posts', 'pdf_file',
        ]

    def get_pdf_file(self, obj):
        if not obj.pdf_file:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return obj.pdf_file.url

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


class PostWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )

    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'content', 'summary', 'category', 'tags',
            'series', 'series_order', 'post_type', 'status', 'published_at',
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


from .models import ArchitectureConcept, ArchitectureEntry, ArchitectureRelation


class ArchitectureConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchitectureConcept
        fields = ['id', 'name', 'slug', 'abbreviation', 'color']


class ArchitectureRelationSerializer(serializers.ModelSerializer):
    from_slug = serializers.SlugRelatedField(source='from_entry', slug_field='slug', read_only=True)
    to_slug = serializers.SlugRelatedField(source='to_entry', slug_field='slug', read_only=True)
    from_name = serializers.CharField(source='from_entry.name', read_only=True)
    to_name = serializers.CharField(source='to_entry.name', read_only=True)

    class Meta:
        model = ArchitectureRelation
        fields = ['id', 'from_slug', 'to_slug', 'from_name', 'to_name', 'relation_type', 'description']


class ArchitectureEntryListSerializer(serializers.ModelSerializer):
    concepts = ArchitectureConceptSerializer(many=True, read_only=True)
    figure_url = serializers.SerializerMethodField()

    class Meta:
        model = ArchitectureEntry
        fields = [
            'id', 'name', 'slug', 'organization', 'release_date',
            'decoder_type', 'concepts', 'param_scale', 'context_length',
            'attention_type', 'normalization', 'activation', 'key_detail',
            'figure_url', 'figure_placeholder', 'paper_url', 'license_type',
            'architecture_category', 'branch_type', 'is_open_source',
        ]

    def get_figure_url(self, obj):
        if not obj.figure:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.figure.url)
        return obj.figure.url


class ArchitectureEntryDetailSerializer(serializers.ModelSerializer):
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

    def get_figure_url(self, obj):
        if not obj.figure:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.figure.url)
        return obj.figure.url


class ArchitectureTreeNodeSerializer(serializers.ModelSerializer):
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

    def get_figure_url(self, obj):
        if not obj.figure:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.figure.url)
        return obj.figure.url


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
