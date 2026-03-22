import time


class RequestLoggingMiddleware:
    """API 요청을 OperationLog에 기록. /api/ 경로 POST/PUT/PATCH/DELETE만, 헬스체크 제외."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/') or request.path == '/api/health/':
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration = int((time.monotonic() - start) * 1000)

        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            try:
                from operations.models import OperationLog
                OperationLog.objects.create(
                    log_type='api_request',
                    action=f'{request.method} {request.path}',
                    detail={'status_code': response.status_code},
                    status='success' if response.status_code < 400 else 'failed',
                    duration_ms=duration,
                    user=request.user if request.user.is_authenticated else None,
                )
            except Exception:
                pass  # 로깅 실패가 요청을 방해하면 안 됨

        return response
