# Pipeline 개선 계획

## 완료된 작업

### A-1. preprocessor.py 버그 수정
- Phase C UUID 정리에서 이미지 링크 제외 (`(?<!!)` negative lookbehind 추가)
- Phase D에서 `/media/` 경로 재변환 방지 (스킵 조건 추가)

### A-2. image_processor.py 인덱스 확장
- vault 전체 탐색으로 확장 (90.Settings 외 인라인 이미지 포함)
- `.obsidian`, `.trash`, `node_modules`, `.git` 제외
- 한글 파일명 지원

### A-3. batch_prepare.py max_tokens 증가
- 4096 → 8192 (gpt-4o-mini 최대 16384 지원)

## 검증 방법
```bash
python pipeline/scanner.py
python pipeline/image_processor.py
python pipeline/preprocessor.py
# preprocess_report.json에서 unresolved ~280건 감소 확인
```

## 파이프라인 실행 절차 (batch_process → import)

### 1. batch_process 실행 (MacBook)
```bash
cd /Users/dorae222/Documents/Obsidian/blog-jun
# .env에 OPENAI_API_KEY 설정 필요
python pipeline/batch_process.py
# → pipeline/data/batch_output.jsonl 생성 (OpenAI Batch API)
```

### 2. 서버 임포트 (SCP → docker exec)
```bash
# MacBook → blog-server로 파일 전송
scp pipeline/data/batch_output.jsonl blog-server:/opt/blog-jun/pipeline/data/

# blog-server에서 임포트 실행
ssh blog-server 'cd /opt/blog-jun && docker compose -f docker-compose.prod.yml exec backend python manage.py batch_import pipeline/data/batch_output.jsonl'
```

### 3. embedding_generator (보류)
- pgvector 필드 추가 마이그레이션 후 실행
- `backend/blog/models.py`에 embedding 필드 추가 필요
