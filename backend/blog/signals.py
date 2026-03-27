import logging
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Post

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def invalidate_post_cache(sender, instance, **kwargs):
    """Post 변경 시 default 캐시(페이지 캐시) 전체 클리어.

    throttle 캐시는 별도 Redis DB(1)라 영향 없음.
    """
    cache.clear()
    logger.debug('Post cache cleared: %s', instance.slug)
