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

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content', 'summary', 'category', 'tags',
            'series', 'series_order', 'post_type', 'status', 'quality_score',
            'reading_time', 'view_count', 'created_at', 'updated_at',
            'published_at', 'images', 'adjacent_posts',
        ]

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
