"""
Obsidian import 포스트에서 깨진 이미지 레퍼런스 제거

패턴: ![...]( /media/posts/imported/.../Pasted image yyyymmddHHMMSS.png)

사용법:
  # 영향 범위 미리 확인 (수정 없음)
  python manage.py clean_broken_images --dry-run

  # 실제 정리 실행
  python manage.py clean_broken_images
"""

import re
from django.core.management.base import BaseCommand
from blog.models import Post

# Obsidian "Pasted image" 패턴 — /media/posts/imported/ 아래 경로만 대상
BROKEN_IMAGE_RE = re.compile(
    r'!\[.*?\]\(/media/posts/imported/[^\)]*?Pasted image[^\)]*?\)',
    re.IGNORECASE,
)


class Command(BaseCommand):
    help = '포스트 content에서 깨진 Pasted image 레퍼런스를 제거합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 수정 없이 영향 받는 포스트와 이미지 레퍼런스만 출력',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        mode_label = '[DRY-RUN]' if dry_run else '[ACTUAL]'
        self.stdout.write(f'{mode_label} 깨진 이미지 레퍼런스 탐색 시작...\n')

        posts = Post.objects.all()
        affected_count = 0
        total_removed = 0

        for post in posts:
            if not post.content:
                continue

            matches = BROKEN_IMAGE_RE.findall(post.content)
            if not matches:
                continue

            affected_count += 1
            total_removed += len(matches)
            self.stdout.write(
                self.style.WARNING(
                    f'  [{post.slug}] {len(matches)}개 발견:\n' +
                    '\n'.join(f'    {m}' for m in matches)
                )
            )

            if not dry_run:
                post.content = BROKEN_IMAGE_RE.sub('', post.content)
                post.save(update_fields=['content'])

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[DRY-RUN 완료] 영향 포스트: {affected_count}개, '
                    f'제거 예정 레퍼런스: {total_removed}개\n'
                    '실제 정리하려면 --dry-run 옵션 없이 실행하세요.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[완료] {affected_count}개 포스트에서 '
                    f'{total_removed}개 깨진 이미지 레퍼런스 제거'
                )
            )
