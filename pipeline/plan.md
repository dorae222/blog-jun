# Pipeline 개선 계획

> **마지막 업데이트**: 2026-03-27
> **담당**: @dorae222

## 개요
컨텐츠 작성은 Claude Code가 직접 content.md를 편집. import 스크립트로 Django DB에 반영.

## 워크플로우

```
content.md 직접 편집 (Claude Code)
        ↓
import_{type}_written.py --update
        ↓
Django DB 반영 → 배포
```

## 완료
### A-1. preprocessor.py 버그 수정 ✅
- **완료일**: 2025-02-28
- Phase C UUID 정리에서 이미지 링크 제외, Phase D `/media/` 경로 재변환 방지

### A-2. image_processor.py 인덱스 확장 ✅
- **완료일**: 2025-02-28
- vault 전체 탐색, 한글 파일명 지원

## 보류
### A-5. embedding_generator ⏸️
- **보류 사유**: pgvector 필드 마이그레이션 미완료
- **선행 조건**: `backend/blog/models.py`에 embedding 필드 추가

## 체크리스트
- [x] preprocessor.py 이미지 링크 버그 수정
- [x] image_processor.py vault 전체 탐색
- [ ] 26개 컨텐츠 품질 개선 (colab 16 + papers 9 + ml 1)
- [ ] em dash 전체 제거
- [ ] 서버 배포 + DB 임포트
