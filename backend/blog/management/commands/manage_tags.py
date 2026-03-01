"""
태그 관리 커맨드

사용법:
  python manage.py manage_tags --list           # 태그 목록 + 카운트
  python manage.py manage_tags --orphaned       # 0개 포스트 태그 삭제
  python manage.py manage_tags --cleanup        # 깨진 slug 수정
"""
import re
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils.text import slugify
from blog.models import Tag


class Command(BaseCommand):
    help = '태그를 관리합니다 (목록, 고아 태그 삭제, slug 정리).'

    def add_arguments(self, parser):
        parser.add_argument('--list', action='store_true', help='태그 목록 + 포스트 수 출력')
        parser.add_argument('--orphaned', action='store_true', help='포스트 0개인 태그 삭제')
        parser.add_argument('--cleanup', action='store_true', help='깨진 slug 수정')

    def handle(self, *args, **options):
        if options['list']:
            self._list_tags()
        elif options['orphaned']:
            self._delete_orphaned()
        elif options['cleanup']:
            self._cleanup_slugs()
        else:
            self.stderr.write('옵션을 지정하세요: --list | --orphaned | --cleanup')

    def _list_tags(self):
        tags = Tag.objects.annotate(post_count=Count('posts')).order_by('-post_count')
        self.stdout.write(f'{"이름":<30} {"slug":<35} {"포스트 수":>6}')
        self.stdout.write('-' * 75)
        for t in tags:
            self.stdout.write(f'{t.name:<30} {t.slug:<35} {t.post_count:>6}')
        self.stdout.write(f'\n총 {tags.count()}개 태그')

    def _delete_orphaned(self):
        orphaned = Tag.objects.annotate(post_count=Count('posts')).filter(post_count=0)
        count = orphaned.count()
        if count == 0:
            self.stdout.write('고아 태그 없음')
            return
        for t in orphaned:
            self.stdout.write(f'  삭제: {t.name} ({t.slug})')
        orphaned.delete()
        self.stdout.write(self.style.SUCCESS(f'{count}개 고아 태그 삭제 완료'))

    def _cleanup_slugs(self):
        """slug에 특수문자나 비ASCII 문자가 있는 태그 slug를 재생성"""
        VALID_SLUG = re.compile(r'^[-a-zA-Z0-9_]+$')
        fixed = 0
        for tag in Tag.objects.all():
            if not VALID_SLUG.match(tag.slug):
                new_slug = slugify(tag.name, allow_unicode=False)
                if not new_slug:
                    new_slug = slugify(tag.name, allow_unicode=True)
                # 중복 방지
                if new_slug != tag.slug and not Tag.objects.filter(slug=new_slug).exclude(pk=tag.pk).exists():
                    self.stdout.write(f'  slug 수정: {tag.slug!r} → {new_slug!r}')
                    tag.slug = new_slug
                    tag.save(update_fields=['slug'])
                    fixed += 1
                else:
                    self.stdout.write(f'  slug 충돌 건너뜀: {tag.slug!r}')
        self.stdout.write(self.style.SUCCESS(f'{fixed}개 slug 수정 완료'))
