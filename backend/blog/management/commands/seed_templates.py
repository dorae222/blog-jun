from django.core.management.base import BaseCommand
from blog.models import PostTemplate


TEMPLATES = [
    {
        'name': 'AI 논문 리뷰',
        'description': 'AI/ML 논문 리뷰 템플릿',
        'post_type': 'paper_review',
        'content_template': """# {논문 제목}

## 메타 정보
- **저자**:
- **학회/저널**:
- **년도**:
- **링크**:

## Abstract 요약


## 핵심 기여 (Key Contributions)
1.
2.
3.

## 방법론 (Methodology)


## 실험 결과


## 한계점 및 향후 연구


## 개인 의견

""",
    },
    {
        'name': '기술 튜토리얼',
        'description': '단계별 기술 가이드',
        'post_type': 'tutorial',
        'content_template': """# {제목}

## 개요


## 사전 지식
-

## 환경 설정

```bash
# 설치 명령어
```

## 단계별 구현

### Step 1:

### Step 2:

### Step 3:

## 트러블슈팅

## 결론

## 참고 자료
-
""",
    },
    {
        'name': 'TIL (Today I Learned)',
        'description': '오늘 배운 것 기록',
        'post_type': 'til',
        'content_template': """# {주제}

## 핵심 내용


## 코드 스니펫

```python
# 코드
```

## 참고 자료
-
""",
    },
    {
        'name': '프로젝트 소개',
        'description': '프로젝트 문서화 템플릿',
        'post_type': 'project',
        'content_template': """# {프로젝트명}

## 개요


## 동기


## 기술 스택
| 영역 | 기술 |
|------|------|
| Backend | |
| Frontend | |
| DB | |
| Infra | |

## 아키텍처


## 주요 기능
1.
2.
3.

## 데모 / 결과


## 회고

### 잘한 점

### 개선할 점

### 배운 점

""",
    },
    {
        'name': '활동 기록',
        'description': '프로그램/부트캠프 참여 기록',
        'post_type': 'activity_log',
        'content_template': """# {프로그램명}

## 기본 정보
- **기간**:
- **주최**:
- **역할**:

## 핵심 활동


## 배운 점


## 성과

""",
    },
    {
        'name': 'AWS 서비스 정리',
        'description': 'AWS 서비스 학습 정리',
        'post_type': 'article',
        'content_template': """# {서비스명}

## 카테고리


## 핵심 개념


## 유스케이스
1.
2.
3.

## 주요 설정 및 옵션


## 관련 서비스
-

## 주의사항 / 비용

## 실습 코드

```bash
# AWS CLI 예제
```
""",
    },
]


class Command(BaseCommand):
    help = 'Seed post templates'

    def handle(self, *args, **options):
        created = 0
        for tmpl in TEMPLATES:
            _, was_created = PostTemplate.objects.get_or_create(
                name=tmpl['name'],
                defaults=tmpl,
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created} templates (total: {len(TEMPLATES)})'))
