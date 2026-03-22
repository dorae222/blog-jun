from rest_framework import serializers
from .models import OperationLog, SessionLog


class OperationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationLog
        fields = ['id', 'log_type', 'action', 'detail', 'status',
                  'duration_ms', 'user', 'created_at']


class SessionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionLog
        fields = ['id', 'session_id', 'summary', 'files_modified',
                  'commits', 'duration_minutes', 'created_at']
