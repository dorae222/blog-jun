from django.contrib import admin
from .models import OperationLog, SessionLog


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'log_type', 'action', 'status', 'duration_ms']
    list_filter = ['log_type', 'status']
    search_fields = ['action']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(SessionLog)
class SessionLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'session_id', 'duration_minutes']
    readonly_fields = ['imported_at']
    ordering = ['-created_at']
