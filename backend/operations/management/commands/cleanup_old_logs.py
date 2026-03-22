"""90일 이상 된 운영 로그 삭제."""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from operations.models import OperationLog


class Command(BaseCommand):
    help = '오래된 운영 로그를 삭제합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='삭제 기준 일수 (기본: 90일)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 미리보기',
        )

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=options['days'])
        qs = OperationLog.objects.filter(created_at__lt=cutoff)
        count = qs.count()

        if options['dry_run']:
            self.stdout.write(f'[DRY-RUN] {count}개 로그 삭제 대상 ({options["days"]}일 이전)')
        else:
            qs.delete()
            self.stdout.write(self.style.SUCCESS(f'{count}개 로그 삭제 완료'))
