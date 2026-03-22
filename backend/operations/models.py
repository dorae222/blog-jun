from django.db import models
from django.contrib.auth.models import User


class OperationLog(models.Model):
    """API 요청/관리 명령어 실행 기록."""
    LOG_TYPES = [
        ('api_request', 'API 요청'),
        ('management_cmd', '관리 명령어'),
        ('deployment', '배포'),
        ('error', '에러'),
        ('cover_generation', '커버 이미지 생성'),
        ('content_import', '컨텐츠 임포트'),
    ]

    log_type = models.CharField(max_length=30, choices=LOG_TYPES, db_index=True)
    action = models.CharField(max_length=200)
    detail = models.JSONField(default=dict)
    status = models.CharField(max_length=20)  # success, failed, partial
    duration_ms = models.IntegerField(null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['log_type', '-created_at'])]

    def __str__(self):
        return f'[{self.log_type}] {self.action} ({self.status})'


class SessionLog(models.Model):
    """Claude Code 세션 요약."""
    session_id = models.CharField(max_length=100, unique=True)
    summary = models.TextField()
    files_modified = models.JSONField(default=list)
    commits = models.JSONField(default=list)
    duration_minutes = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Session {self.session_id[:20]} ({self.created_at})'
