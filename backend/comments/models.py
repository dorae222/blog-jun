from django.conf import settings
from django.db import models


class Comment(models.Model):
    post = models.ForeignKey(
        'blog.Post', on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments'
    )
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies'
    )
    content = models.TextField(max_length=2000)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f'{self.author.username}: {self.content[:50]}'

    def save(self, *args, **kwargs):
        # 2레벨 제한: parent의 parent가 있으면 자동 평탄화
        if self.parent and self.parent.parent_id:
            self.parent = self.parent.parent
        super().save(*args, **kwargs)
