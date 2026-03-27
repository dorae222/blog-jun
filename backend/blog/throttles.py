from django.core.cache import caches
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


def _get_throttle_cache():
    """throttle 캐시가 있으면 사용, 없으면 default fallback."""
    try:
        return caches['throttle']
    except Exception:
        return caches['default']


class RedisAnonRateThrottle(AnonRateThrottle):
    @property
    def cache(self):
        return _get_throttle_cache()


class RedisUserRateThrottle(UserRateThrottle):
    @property
    def cache(self):
        return _get_throttle_cache()


class CommentRateThrottle(UserRateThrottle):
    scope = 'comment'

    @property
    def cache(self):
        return _get_throttle_cache()
