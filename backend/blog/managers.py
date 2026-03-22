"""커스텀 QuerySet/Manager — 자주 사용하는 필터 체인을 메서드로 제공."""
from django.db import models
from django.db.models import Q


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status='published')

    def with_cover(self):
        return self.exclude(cover_image='').exclude(cover_image__isnull=True)

    def without_cover(self):
        return self.filter(Q(cover_image='') | Q(cover_image__isnull=True))

    def by_category(self, slug):
        return self.filter(Q(category__slug=slug) | Q(category__parent__slug=slug))


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def with_cover(self):
        return self.get_queryset().with_cover()

    def without_cover(self):
        return self.get_queryset().without_cover()

    def by_category(self, slug):
        return self.get_queryset().by_category(slug)
