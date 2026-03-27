from django.contrib import admin
from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'post', 'short_content', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['content', 'author__username']
    raw_id_fields = ['post', 'author', 'parent']

    def short_content(self, obj):
        return obj.content[:80]
    short_content.short_description = 'Content'
