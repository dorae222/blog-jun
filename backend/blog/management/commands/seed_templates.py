from django.core.management.base import BaseCommand
from blog.models import PostTemplate


TEMPLATES = [
    {
        'name': 'AI 논문 리뷰',
        'description': 'AI/ML 논문 리뷰 종합 템플릿',
        'post_type': 'paper_review',
        'content_template': """## 논문 정보
- **제목**:
- **저자**:
- **학회/저널**: NeurIPS 2024
- **arXiv**: [arXiv:XXXX.XXXXX](https://arxiv.org/abs/XXXX.XXXXX)
- **코드**: [GitHub](https://github.com/...)

## 개요
[1-2 문단 요약]

![Architecture Diagram](figures/architecture.png)
*Figure 1: 아키텍처 다이어그램 — [논문제목](arxiv_url)*

## 핵심 기여
1.
2.
3.

## 수학적 배경
$$
\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V
$$

## 아키텍처 상세
### [컴포넌트 1]
### [컴포넌트 2]

## 실험 결과
| 모델 | 데이터셋 | 지표 | 값 |
|-----|---------|-----|---|
|     |         |     |   |

## 강점 / 한계
**강점**:
**한계**:

## 관련 논문
- [[related-paper|관련 논문]] — 한 줄 설명
""",
    },
    {
        'name': 'ML 튜토리얼',
        'description': 'ML 알고리즘/기법 튜토리얼 템플릿',
        'post_type': 'tutorial',
        'content_template': """## 개요
[알고리즘 한 줄 설명]

## 수학적 배경
$$[핵심 수식]$$

## 알고리즘
1.
2.

## Python 구현

### 필요 패키지
```
numpy>=1.24
scikit-learn>=1.2
matplotlib>=3.6
```

```python
# 구현 코드
```

## 시각화 결과
[Figure 자동 삽입 위치]

## 실전 팁
-
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

    def add_arguments(self, parser):
        parser.add_argument('--update', action='store_true', help='기존 템플릿도 업데이트')

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for tmpl in TEMPLATES:
            obj, was_created = PostTemplate.objects.get_or_create(
                name=tmpl['name'],
                defaults=tmpl,
            )
            if was_created:
                created += 1
            elif options.get('update'):
                for key, val in tmpl.items():
                    setattr(obj, key, val)
                obj.save()
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Created {created}, updated {updated} templates (total: {len(TEMPLATES)})'
        ))
