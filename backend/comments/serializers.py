from rest_framework import serializers
from .models import Comment


class CommentAuthorSerializer(serializers.Serializer):
    """댓글 작성자 정보 (소셜 계정 포함)."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    profile_url = serializers.SerializerMethodField()

    def get_display_name(self, user):
        social = self._get_social(user)
        if social:
            extra = social.extra_data
            if social.provider == 'github':
                return extra.get('name') or extra.get('login', user.username)
            elif social.provider == 'google':
                return extra.get('name', user.username)
        return user.username

    def get_avatar_url(self, user):
        social = self._get_social(user)
        if social:
            extra = social.extra_data
            if social.provider == 'github':
                return extra.get('avatar_url', '')
            elif social.provider == 'google':
                return extra.get('picture', '')
        return ''

    def get_provider(self, user):
        social = self._get_social(user)
        return social.provider if social else None

    def get_profile_url(self, user):
        social = self._get_social(user)
        if social and social.provider == 'github':
            return social.extra_data.get('html_url', '')
        return ''

    def _get_social(self, user):
        # prefetch 캐시 사용 (ViewSet에서 prefetch_related 적용)
        if hasattr(user, '_prefetched_social'):
            return user._prefetched_social
        try:
            from allauth.socialaccount.models import SocialAccount
            social = SocialAccount.objects.filter(user=user).first()
            user._prefetched_social = social
            return social
        except Exception:
            return None


class ReplySerializer(serializers.ModelSerializer):
    """답글 serializer (중첩 없음)."""
    author = CommentAuthorSerializer(read_only=True)
    content = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'parent', 'is_edited', 'is_deleted', 'created_at']

    def get_content(self, obj):
        if obj.is_deleted:
            return '[삭제된 댓글입니다]'
        return obj.content


class CommentSerializer(serializers.ModelSerializer):
    """최상위 댓글 serializer (replies 포함)."""
    author = CommentAuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'parent', 'replies', 'reply_count',
            'is_edited', 'is_deleted', 'created_at',
        ]

    def get_content(self, obj):
        if obj.is_deleted:
            return '[삭제된 댓글입니다]'
        return obj.content

    def get_replies(self, obj):
        replies = obj.replies.all()  # prefetch 캐시 사용
        return ReplySerializer(replies, many=True).data

    def get_reply_count(self, obj):
        return obj.replies.count()


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'parent']

    def validate_parent(self, value):
        if value:
            # parent가 같은 포스트에 속하는지 검증은 view에서 처리
            if value.is_deleted:
                raise serializers.ValidationError('삭제된 댓글에는 답글을 달 수 없습니다.')
        return value


class AdminCommentSerializer(serializers.ModelSerializer):
    """관리자용 댓글 serializer — 포스트 정보 포함."""
    author = CommentAuthorSerializer(read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_slug = serializers.CharField(source='post.slug', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'post_title', 'post_slug',
            'parent', 'is_edited', 'is_deleted', 'created_at', 'updated_at',
        ]
