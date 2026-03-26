"""
published_at 날짜 분배 스크립트.

모든 published 포스트에 2023-01-01 ~ 2026-03-26 범위의 자연스러운 날짜를 부여한다.
- 카테고리별 정렬 후 글로벌 병합
- 연도별 비율 조절 (2023 20%, 2024 30%, 2025 35%, 2026 Q1 15%)
- 주중 70% / 주말 30%, 하루 최대 3개, 공휴일 제외
- random.seed(42)로 재현 가능

Usage:
    python pipeline/distribute_dates.py --dry-run    # 미리보기
    python pipeline/distribute_dates.py --apply       # DB 업데이트
"""
import argparse
import random
import sys
import os
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

# ── Django 환경 설정 ──────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if not BACKEND_DIR.exists():
    BACKEND_DIR = Path("/app")
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from django.utils import timezone
from blog.models import Post, ArchitectureEntry

# ── 상수 ──────────────────────────────────────────────────────
import zoneinfo
KST = zoneinfo.ZoneInfo("Asia/Seoul")

SEED = 42
START_DATE = date(2023, 1, 1)
END_DATE = date(2026, 3, 26)

# 연도별 포스트 비율
YEAR_WEIGHTS = {
    2023: 0.20,
    2024: 0.30,
    2025: 0.35,
    2026: 0.15,
}

MAX_POSTS_PER_DAY = 3
WEEKDAY_RATIO = 0.70  # 주중 비율
HOUR_MIN = 9
HOUR_MAX = 22

# 포스팅하지 않는 날 (월-일)
HOLIDAYS = {
    (1, 1),    # 새해
    (12, 25),  # 크리스마스
}


def is_holiday(d: date) -> bool:
    return (d.month, d.day) in HOLIDAYS


def is_weekday(d: date) -> bool:
    return d.weekday() < 5  # 0=Mon ~ 4=Fri


# ── 포스트 정렬 ───────────────────────────────────────────────

def get_sorted_posts():
    """
    모든 published 포스트를 카테고리별로 정렬한 뒤 글로벌 리스트로 병합.
    정렬 순서:
      1) paper_review → paper_year ASC, title ASC
      2) architecture (related_post가 있는 article) → release_date ASC
      3) 나머지 article/tutorial → slug ASC
    """
    posts = Post.objects.filter(status=Post.Status.PUBLISHED).select_related('category')

    # ArchitectureEntry와 연결된 포스트 id → release_date 매핑
    arch_map = {}
    for entry in ArchitectureEntry.objects.filter(related_post__isnull=False).select_related('related_post'):
        arch_map[entry.related_post_id] = entry.release_date

    # 카테고리별 버킷
    paper_reviews = []
    arch_posts = []
    other_posts = []

    for post in posts:
        if post.post_type == Post.PostType.PAPER_REVIEW:
            paper_reviews.append(post)
        elif post.pk in arch_map:
            arch_posts.append(post)
        else:
            other_posts.append(post)

    # 정렬
    paper_reviews.sort(key=lambda p: (p.paper_year or 9999, p.title))
    arch_posts.sort(key=lambda p: (arch_map.get(p.pk) or date.max, p.title))
    other_posts.sort(key=lambda p: p.slug)

    # 글로벌 병합: paper → arch → other 순으로 시간축에 배치
    # 각 그룹 내에서 이미 시간순 정렬되어 있으므로, 인터리브해서 자연스럽게 섞음
    all_posts = _interleave_groups(paper_reviews, arch_posts, other_posts)
    return all_posts


def _interleave_groups(*groups):
    """
    여러 그룹의 포스트를 비율에 맞게 인터리브하여 하나의 리스트로 병합.
    각 그룹 내 순서는 유지하면서, 전체적으로 균등하게 섞는다.
    """
    total = sum(len(g) for g in groups)
    if total == 0:
        return []

    # 각 그룹에서 하나씩 라운드로빈으로 뽑되, 비율에 맞게
    result = []
    indices = [0] * len(groups)
    group_sizes = [len(g) for g in groups]

    for i in range(total):
        # 아직 남은 그룹 중에서 "진행률이 가장 낮은" 그룹에서 뽑음
        best_group = -1
        best_progress = 2.0  # > 1.0

        for g_idx in range(len(groups)):
            if indices[g_idx] >= group_sizes[g_idx]:
                continue
            progress = indices[g_idx] / group_sizes[g_idx] if group_sizes[g_idx] > 0 else 1.0
            if progress < best_progress:
                best_progress = progress
                best_group = g_idx

        if best_group == -1:
            break

        result.append(groups[best_group][indices[best_group]])
        indices[best_group] += 1

    return result


# ── 날짜 생성 ─────────────────────────────────────────────────

def generate_dates(num_posts: int, rng: random.Random) -> list[datetime]:
    """
    num_posts개의 datetime을 생성한다.
    - 연도별 비율에 맞게 각 연도에 할당
    - 주중/주말 비율 적용
    - 하루 최대 3포스트
    - 1~3일 간격 지터
    - 공휴일 제외
    """
    # 연도별 포스트 수 계산
    year_counts = {}
    remaining = num_posts
    years = sorted(YEAR_WEIGHTS.keys())

    for i, year in enumerate(years):
        if i == len(years) - 1:
            year_counts[year] = remaining
        else:
            count = round(num_posts * YEAR_WEIGHTS[year])
            year_counts[year] = count
            remaining -= count

    # 연도별 날짜 범위
    year_ranges = {}
    for year in years:
        y_start = max(START_DATE, date(year, 1, 1))
        y_end = min(END_DATE, date(year, 12, 31))
        year_ranges[year] = (y_start, y_end)

    # 연도별로 사용 가능한 날짜 목록 생성 (공휴일 제외)
    all_dates = []
    for year in years:
        y_start, y_end = year_ranges[year]
        count_needed = year_counts[year]
        dates = _generate_year_dates(y_start, y_end, count_needed, rng)
        all_dates.extend(dates)

    # datetime으로 변환 (시간 추가)
    result = []
    for d in all_dates:
        hour = rng.randint(HOUR_MIN, HOUR_MAX)
        minute = rng.randint(0, 59)
        second = rng.randint(0, 59)
        dt = datetime(d.year, d.month, d.day, hour, minute, second, tzinfo=KST)
        result.append(dt)

    return result


def _generate_year_dates(start: date, end: date, count: int, rng: random.Random) -> list[date]:
    """
    start~end 범위에서 count개의 날짜를 생성.
    주중/주말 비율과 하루 최대 제한을 적용.
    """
    if count == 0:
        return []

    # 사용 가능한 날짜 모으기
    weekdays = []
    weekends = []
    d = start
    while d <= end:
        if not is_holiday(d):
            if is_weekday(d):
                weekdays.append(d)
            else:
                weekends.append(d)
        d += timedelta(days=1)

    # 주중/주말 할당 수
    weekday_count = min(round(count * WEEKDAY_RATIO), len(weekdays) * MAX_POSTS_PER_DAY)
    weekend_count = count - weekday_count

    # 주말 날짜가 부족하면 주중으로 재배분
    if weekend_count > len(weekends) * MAX_POSTS_PER_DAY:
        weekend_count = len(weekends) * MAX_POSTS_PER_DAY
        weekday_count = count - weekend_count

    # 주중 날짜가 부족하면 주말로 재배분
    if weekday_count > len(weekdays) * MAX_POSTS_PER_DAY:
        weekday_count = len(weekdays) * MAX_POSTS_PER_DAY
        weekend_count = count - weekday_count

    # 각 풀에서 날짜 선택 (하루 최대 MAX_POSTS_PER_DAY)
    selected_weekdays = _pick_dates_from_pool(weekdays, weekday_count, rng)
    selected_weekends = _pick_dates_from_pool(weekends, weekend_count, rng)

    result = sorted(selected_weekdays + selected_weekends)

    # 지터 적용: 날짜 간 최소 간격이 너무 가까운 건 이미 허용 (하루 최대 3개)
    return result


def _pick_dates_from_pool(pool: list[date], count: int, rng: random.Random) -> list[date]:
    """
    날짜 풀에서 count개의 날짜를 선택. 하루 최대 MAX_POSTS_PER_DAY개.
    균등 분포 + 지터로 자연스러운 간격을 만든다.
    """
    if count == 0 or not pool:
        return []

    # 풀 내에서 균등하게 분배할 기본 날짜 선택
    # 먼저 각 날짜에 1개씩 할당할 수 있는 날짜 수 계산
    available = list(pool)  # 이미 정렬된 상태

    result = []
    date_usage = defaultdict(int)

    if count <= len(available):
        # 포스트 수가 날짜 수보다 적으면 간격을 두고 선택
        step = len(available) / count
        for i in range(count):
            # 기본 인덱스 + 지터
            base_idx = int(i * step)
            jitter = rng.randint(-1, 1)
            idx = max(0, min(len(available) - 1, base_idx + jitter))
            chosen = available[idx]
            date_usage[chosen] += 1

            # 하루 최대 초과 시 인접 날짜로 이동
            if date_usage[chosen] > MAX_POSTS_PER_DAY:
                date_usage[chosen] -= 1
                # 앞뒤로 빈 날짜 찾기
                for offset in range(1, len(available)):
                    for direction in [1, -1]:
                        new_idx = idx + offset * direction
                        if 0 <= new_idx < len(available):
                            alt = available[new_idx]
                            if date_usage[alt] < MAX_POSTS_PER_DAY:
                                chosen = alt
                                date_usage[chosen] += 1
                                break
                    else:
                        continue
                    break

            result.append(chosen)
    else:
        # 포스트 수가 날짜 수보다 많으면 날짜를 반복 사용
        # 먼저 모든 날짜에 1개씩
        for d in available:
            result.append(d)
            date_usage[d] += 1

        remaining = count - len(available)
        # 나머지는 랜덤으로 배분 (최대 제한 준수)
        attempts = 0
        while remaining > 0 and attempts < count * 10:
            d = rng.choice(available)
            if date_usage[d] < MAX_POSTS_PER_DAY:
                result.append(d)
                date_usage[d] += 1
                remaining -= 1
            attempts += 1

        # 그래도 남으면 강제 배분
        if remaining > 0:
            for d in available:
                while date_usage[d] < MAX_POSTS_PER_DAY and remaining > 0:
                    result.append(d)
                    date_usage[d] += 1
                    remaining -= 1

    return sorted(result)


# ── 메인 로직 ─────────────────────────────────────────────────

def distribute_dates(dry_run: bool = True):
    random.seed(SEED)
    rng = random.Random(SEED)

    # 포스트 정렬
    posts = get_sorted_posts()
    num_posts = len(posts)

    if num_posts == 0:
        print("게시된 포스트가 없습니다.")
        return

    print(f"총 포스트 수: {num_posts}")

    # 날짜 생성
    dates = generate_dates(num_posts, rng)

    if len(dates) < num_posts:
        print(f"경고: 날짜가 부족합니다. (생성: {len(dates)}, 필요: {num_posts})")
        return

    # 포스트-날짜 매핑
    assignments = list(zip(posts, dates))

    # 통계 출력
    _print_stats(assignments, dry_run)

    if dry_run:
        print("\n--dry-run 모드: DB 변경 없음")
        print("실제 적용하려면 --apply 옵션을 사용하세요.")
        return

    # DB 업데이트
    print("\n=== DB 업데이트 시작 ===")
    updated = 0
    for post, dt in assignments:
        Post.objects.filter(pk=post.pk).update(published_at=dt)
        updated += 1

    print(f"완료: {updated}개 포스트 업데이트")


def _print_stats(assignments: list[tuple], dry_run: bool):
    """분배 결과 통계를 출력한다."""
    if dry_run:
        print("\n=== 날짜 분배 미리보기 ===")
    else:
        print("\n=== 날짜 분배 결과 ===")

    # 월별 집계
    monthly = defaultdict(int)
    daily = defaultdict(int)

    for post, dt in assignments:
        key = f"{dt.year}-{dt.month:02d}"
        monthly[key] += 1
        day_key = dt.date()
        daily[day_key] += 1

    # 월별 출력
    for key in sorted(monthly.keys()):
        print(f"  {key}: {monthly[key]} posts")

    # 연도별 집계
    print("\n--- 연도별 ---")
    yearly = defaultdict(int)
    for post, dt in assignments:
        yearly[dt.year] += 1
    total = len(assignments)
    for year in sorted(yearly.keys()):
        count = yearly[year]
        pct = count / total * 100
        print(f"  {year}: {count} posts ({pct:.1f}%)")

    # 주중/주말 통계
    weekday_count = sum(1 for _, dt in assignments if is_weekday(dt.date()))
    weekend_count = len(assignments) - weekday_count
    print(f"\n--- 주중/주말 ---")
    print(f"  주중 (Mon-Fri): {weekday_count} ({weekday_count/total*100:.1f}%)")
    print(f"  주말 (Sat-Sun): {weekend_count} ({weekend_count/total*100:.1f}%)")

    # 하루 최대 포스트 수
    max_daily = max(daily.values()) if daily else 0
    days_with_max = sum(1 for v in daily.values() if v == max_daily)

    # 요약
    all_dates = [dt for _, dt in assignments]
    first = min(all_dates)
    last = max(all_dates)

    print(f"\n최초 게시일: {first.strftime('%Y-%m-%d %H:%M KST')}")
    print(f"최종 게시일: {last.strftime('%Y-%m-%d %H:%M KST')}")
    print(f"하루 최대: {max_daily} posts ({days_with_max}일)")
    print(f"총 포스트: {total}")


# ── CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="published_at 날짜 분배")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="미리보기 (DB 변경 없음)")
    group.add_argument("--apply", action="store_true", help="실제 DB 업데이트")
    args = parser.parse_args()

    distribute_dates(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
