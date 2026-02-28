# Pipeline 개선 계획

> **마지막 업데이트**: 2026-03-01
> **담당**: @dorae222
> **관련 문서**: [CLAUDE.md](../CLAUDE.md)

## 개요
Obsidian → 블로그 콘텐츠 변환 파이프라인. scanner → preprocessor → batch_prepare → batch_process → batch_import 흐름. 전처리 버그 수정 완료, 서버 배치 실행 단계.

## 완료
### A-1. preprocessor.py 버그 수정 ✅
- **완료일**: 2025-02-28
- **내용**:
  - Phase C UUID 정리에서 이미지 링크 제외 (`(?<!!)` negative lookbehind 추가)
  - Phase D에서 `/media/` 경로 재변환 방지 (스킵 조건 추가)

### A-2. image_processor.py 인덱스 확장 ✅
- **완료일**: 2025-02-28
- **내용**:
  - vault 전체 탐색으로 확장 (90.Settings 외 인라인 이미지 포함)
  - `.obsidian`, `.trash`, `node_modules`, `.git` 제외
  - 한글 파일명 지원

### A-3. batch_prepare.py max_tokens 증가 ✅
- **완료일**: 2025-02-28
- **내용**:
  - 4096 → 8192 (gpt-4o-mini 최대 16384 지원)

### A-4. batch_process.py 테스트 모드 추가 ✅
- **완료일**: 2026-03-01
- **내용**:
  - `--test` 옵션: batch_input_test.jsonl 사용 (카테고리별 5건)
  - `--input` 옵션: 임의 입력 파일 경로 지정

## 보류
### A-5. embedding_generator ⏸️
- **보류 사유**: pgvector 필드 마이그레이션 미완료
- **선행 조건**: `backend/blog/models.py`에 embedding 필드 추가
- **우선순위**: P2

## 향후 계획
### A-6. 전체 배치 실행 (716건)
- **우선순위**: P0 (긴급)
- **예상 규모**: Small
- **내용**: 테스트 5건 검증 후 전체 batch_input.jsonl 실행
- **선행 조건**: 테스트 배치 결과 검증 완료

### A-7. 콘텐츠 템플릿 (PostTemplate) 개선
- **우선순위**: P1 (중요)
- **예상 규모**: Medium
- **내용**: batch_prepare.py 프롬프트 및 JSON 스키마 품질 개선
- **선행 조건**: 테스트 임포트 결과 리뷰

## 운영 절차

### batch_process 실행 (blog-server)
```bash
# 테스트 모드 (5건)
ssh blog-server 'cd /opt/blog-jun && python3 pipeline/batch_process.py --test'

# 전체 실행 (716건)
ssh blog-server 'cd /opt/blog-jun && python3 pipeline/batch_process.py'

# 재접속 (비동기 배치 완료 대기)
ssh blog-server 'cd /opt/blog-jun && python3 pipeline/batch_process.py --resume'

# 상태 확인
ssh blog-server 'cd /opt/blog-jun && python3 pipeline/batch_process.py --status'
```

### batch_import 실행 (Docker 내부)
```bash
ssh blog-server 'cd /opt/blog-jun && docker compose -f docker-compose.prod.yml exec backend python manage.py shell < pipeline/batch_import.py'
```

### 결과 확인
```bash
ssh blog-server 'cd /opt/blog-jun && docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "
from blog.models import Post, Category
print(f\"Posts: {Post.objects.count()}\")
for p in Post.objects.all()[:10]:
    print(f\"  [{p.post_type}] {p.title}\")"'
```

## 검증
```bash
python pipeline/scanner.py
python pipeline/image_processor.py
python pipeline/preprocessor.py
# preprocess_report.json에서 unresolved ~280건 감소 확인
```

## 체크리스트
- [x] preprocessor.py 이미지 링크 버그 수정
- [x] image_processor.py vault 전체 탐색
- [x] batch_prepare.py max_tokens 증가
- [x] batch_process.py 테스트 모드
- [ ] 테스트 배치 실행 (5건)
- [ ] 전체 배치 실행 (716건)
- [ ] batch_import 실행
- [ ] 웹 확인 (https://blog.dorae222.com)

## 참고사항
- pipeline/data/는 .gitignore에 포함 (JSONL 데이터 파일)
- OpenAI Batch API는 비동기 처리 (24h window), --resume으로 재접속 가능
- blog-server에서 직접 실행 시 .env의 OPENAI_API_KEY 필요
