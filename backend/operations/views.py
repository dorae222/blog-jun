from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count

from .models import OperationLog, SessionLog
from .serializers import OperationLogSerializer, SessionLogSerializer


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """운영 로그 조회 API."""
    queryset = OperationLog.objects.all()
    serializer_class = OperationLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['log_type', 'status']

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """로그 타입별 요약 통계."""
        stats = (
            OperationLog.objects
            .values('log_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response(list(stats))


class SessionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Claude Code 세션 로그 조회 API."""
    queryset = SessionLog.objects.all()
    serializer_class = SessionLogSerializer
    permission_classes = [permissions.IsAdminUser]
